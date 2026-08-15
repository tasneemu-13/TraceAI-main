import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models.doc import InvestigationDoc, SightingMatch
from app.models.case import RegisteredCases
from app.models.submission import PublicSubmissions

import numpy as np

# Try importing ML libraries; set fallbacks if they are not fully loaded yet.
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_ML = True
except Exception as e:
    HAS_ML = False
    print(f"[RAG Service] FAISS or SentenceTransformers not loaded ({e}). Fallback keyword search will be used.")

class RAGAssistant:
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.doc_store: List[Dict[str, Any]] = []
        
        # Initialize ML model if available
        if HAS_ML:
            try:
                # Lightweight sentence-transformers model
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                # 384 dimensions for all-MiniLM-L6-v2
                self.index = faiss.IndexFlatL2(384)
            except Exception as e:
                print(f"[RAG Init Warning] Failed to initialize ML models: {e}. Using fallback.")
                
    def reindex_all_docs(self, db: Session):
        """
        Reads all documents from DB and builds/updates the FAISS index.
        """
        docs = db.query(InvestigationDoc).all()
        self.doc_store = []
        
        if not docs:
            # Recreate empty index
            if HAS_ML and self.index:
                self.index = faiss.IndexFlatL2(384)
            return

        texts = []
        for d in docs:
            meta = json.loads(d.metadata_json) if d.metadata_json else {}
            doc_data = {
                "id": d.id,
                "case_id": d.case_id,
                "doc_type": d.doc_type,
                "title": d.title or d.doc_type,
                "content": d.content,
                "created_at": str(d.created_at),
                "meta": meta
            }
            self.doc_store.append(doc_data)
            
            # Context string for embedding
            context_str = f"Case ID: {d.case_id} | Type: {d.doc_type} | Title: {d.title or d.doc_type} | Content: {d.content}"
            texts.append(context_str)

        if HAS_ML and self.embedding_model and self.index:
            try:
                embeddings = self.embedding_model.encode(texts)
                embeddings_np = np.array(embeddings).astype("float32")
                self.index = faiss.IndexFlatL2(384)
                self.index.add(embeddings_np)
                print(f"[RAG] Successfully indexed {len(docs)} documents in FAISS.")
            except Exception as e:
                print(f"[RAG Indexing Error] FAISS index failed: {e}")

    def search_docs(self, db: Session, query: str, case_id: Optional[str] = None, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves the top k most relevant documents.
        Filters by case_id if provided.
        """
        # Always sync with database first
        self.reindex_all_docs(db)
        
        if not self.doc_store:
            return []

        # If ML is active, use FAISS
        if HAS_ML and self.embedding_model and self.index and self.index.ntotal > 0:
            try:
                query_emb = self.embedding_model.encode([query])
                query_emb_np = np.array(query_emb).astype("float32")
                distances, indices = self.index.search(query_emb_np, len(self.doc_store))
                
                results = []
                for idx, distance in zip(indices[0], distances[0]):
                    if idx < 0 or idx >= len(self.doc_store):
                        continue
                    doc = self.doc_store[idx]
                    if case_id and doc["case_id"] != case_id:
                        continue
                    doc_copy = doc.copy()
                    doc_copy["distance"] = float(distance)
                    results.append(doc_copy)
                return results[:top_k]
            except Exception as e:
                print(f"[RAG Search Error] FAISS search failed: {e}. Falling back to text matching.")

        # FALLBACK: Basic keyword/substring search
        query_words = query.lower().split()
        scored_docs = []
        for doc in self.doc_store:
            if case_id and doc["case_id"] != case_id:
                continue
            
            score = 0
            doc_content_lower = doc["content"].lower()
            doc_title_lower = doc["title"].lower()
            
            for word in query_words:
                if word in doc_content_lower:
                    score += 2
                if word in doc_title_lower:
                    score += 5
            
            if score > 0 or not query_words:
                doc_copy = doc.copy()
                doc_copy["score"] = score
                scored_docs.append(doc_copy)
                
        scored_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored_docs[:top_k]

    def _is_ollama_available(self) -> bool:
        """Quick check if Ollama service is reachable."""
        try:
            r = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=3)
            if r.status_code == 200:
                # Check if configured model exists
                models = [m.get("name", "") for m in r.json().get("models", [])]
                return any(settings.OLLAMA_MODEL in m for m in models)
            return False
        except Exception:
            return False

    def _rule_based_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generates a structured rule-based response when Ollama is unavailable.
        Parses the user_prompt to extract case context and returns a helpful summary.
        """
        lines = user_prompt.strip().split("\n")
        context_block = "\n".join(lines)

        # Detect the type of request from the system prompt
        if "summary" in system_prompt.lower() or "summarize" in user_prompt.lower():
            return (
                "📋 **Case Summary (Offline Mode)**\n\n"
                "**Note:** The AI model (Ollama) is currently unavailable. Displaying rule-based analysis.\n\n"
                "**1. Demographics & Context**\n"
                + "\n".join(l for l in lines if any(k in l for k in ["Name:", "Age:", "Last Seen:", "Address:", "Description:"])) +
                "\n\n**2. Evidence on File**\n"
                + ("\n".join(l for l in lines if "- [" in l) or "No investigation logs recorded yet.") +
                "\n\n**3. Recommendations**\n"
                "- Ensure all witness statements are logged under Investigation Docs.\n"
                "- Upload any CCTV or photo sightings via the Public Sighting portal.\n"
                "- Verify Aadhaar details and medical history are filled in the case profile.\n"
                "- Run AI Face Match from the Admin panel to cross-check public submissions.\n\n"
                "⚠️ *To enable full AI responses, install Ollama and run:* `ollama pull llama3`"
            )
        elif "missing" in system_prompt.lower() or "evidence" in user_prompt.lower():
            return (
                "🔍 **Missing Evidence Checklist (Offline Mode)**\n\n"
                "**Note:** AI model unavailable. Showing standard evidence checklist.\n\n"
                "The following are commonly missing in new cases:\n"
                "- 📄 Witness Statements — Interview family, neighbours, last-seen witnesses\n"
                "- 📍 Location History — Request GPS/cell tower data from telecom providers\n"
                "- 🪪 Aadhaar Card Copy — For demographic verification\n"
                "- 🏥 Medical Records — Psychological conditions, allergies, prescriptions\n"
                "- 📷 Recent Photographs — Multiple angles for face mesh accuracy\n"
                "- 📞 Call Records — Last known communications\n\n"
                "⚠️ *To enable full AI responses, install Ollama and run:* `ollama pull llama3`"
            )
        else:
            # Generic Q&A fallback — extract question
            question = ""
            for l in lines:
                if "Officer Question:" in l or "question" in l.lower():
                    question = l.replace("Officer Question:", "").strip()
                    break

            return (
                f"🤖 **TraceAI Assistant (Offline Mode)**\n\n"
                f"**Note:** The local AI model (Ollama / llama3) is not running. "
                f"Full natural language responses are unavailable.\n\n"
                f"**Your query:** {question or 'Received'}\n\n"
                "**Suggested Actions:**\n"
                "- Review the Investigation Logs for timeline clues\n"
                "- Check the AI Matches tab for face similarity scores\n"
                "- Log new Officer Notes with updated field observations\n"
                "- Use the 'Missing Evidence' button to audit case completeness\n\n"
                "⚠️ *To enable full AI responses:*\n"
                "1. Install Ollama from https://ollama.com\n"
                "2. Run: `ollama pull llama3`\n"
                "3. Restart the application"
            )

    def _query_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """
        Queries the local Ollama instance with Llama 3.
        Falls back to rule-based response if Ollama is unavailable.
        """
        if not self._is_ollama_available():
            return self._rule_based_response(system_prompt, user_prompt)

        url = f"{settings.OLLAMA_HOST}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        try:
            response = requests.post(url, json=payload, timeout=300)
            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                # Ollama returned an error — use fallback
                return self._rule_based_response(system_prompt, user_prompt)
        except Exception:
            return self._rule_based_response(system_prompt, user_prompt)

    def answer_officer_question(self, db: Session, case_id: str, question: str) -> str:
        """
        RAG question answering. Retrieves relevant notes/reports and queries Ollama.
        """
        relevant_docs = self.search_docs(db, question, case_id=case_id, top_k=5)
        
        # Build prompt context
        context_parts = []
        for i, d in enumerate(relevant_docs):
            context_parts.append(f"Document {i+1} ({d['doc_type']} - {d['title']}):\n{d['content']}")
        context_str = "\n\n".join(context_parts) if context_parts else "No specific documents found for this case."
        
        case_info = db.query(RegisteredCases).filter(RegisteredCases.id == case_id).first()
        case_meta = ""
        if case_info:
            case_meta = f"Missing Person: {case_info.name}, Age: {case_info.age}, Last Seen: {case_info.last_seen}, Birth Marks: {case_info.birth_marks}."

        system_prompt = (
            "You are TraceAI, an advanced AI Investigation Assistant helping police officers locate missing persons. "
            "Your tone is professional, objective, analytical, and supportive. "
            "Use the provided database context to answer the officer's question. "
            "Highlight critical clues, timeline indicators, and geographical leads. "
            "Never claim guilt or automatically identify suspects. Keep answers focused and actionable."
        )
        
        user_prompt = f"""
Missing Person Profile:
{case_meta}

Investigation Logs & Documents:
{context_str}

Officer Question: {question}

Please answer the question based strictly on the logs and profile provided:
"""
        return self._query_ollama(system_prompt, user_prompt)

    def summarize_case(self, db: Session, case_id: str) -> str:
        """
        Summarizes a case based on all available documents and details.
        """
        docs = db.query(InvestigationDoc).filter(InvestigationDoc.case_id == case_id).all()
        case_info = db.query(RegisteredCases).filter(RegisteredCases.id == case_id).first()
        
        if not case_info:
            return "Case not found."

        docs_str = ""
        for i, d in enumerate(docs):
            docs_str += f"- [{d.doc_type} - {d.title}]: {d.content}\n"
            
        system_prompt = "You are TraceAI, an analytical investigation assistant. Provide a structured case summary."
        user_prompt = f"""
Generate a concise, professional case summary for the following missing person case:
Name: {case_info.name}
Age: {case_info.age}
Address: {case_info.address}, {case_info.city}
Last Seen: {case_info.last_seen}
Description: {case_info.description}

Available Notes and Evidence:
{docs_str if docs_str else "No evidence or officer notes logged yet."}

Include sections for:
1. Demographics & Context
2. Chronology of Events (from logs)
3. Key Clues & Leads
4. Recommendations for Next Steps
"""
        return self._query_ollama(system_prompt, user_prompt)

    def show_missing_evidence(self, db: Session, case_id: str) -> str:
        """
        Identifies missing evidence by analyzing what forms of documentation have NOT been logged yet.
        """
        docs = db.query(InvestigationDoc).filter(InvestigationDoc.case_id == case_id).all()
        case_info = db.query(RegisteredCases).filter(RegisteredCases.id == case_id).first()
        
        if not case_info:
            return "Case not found."
            
        existing_types = [d.doc_type.lower() for d in docs]
        
        # Standard checklists
        checklist = {
            "witness statement": "Witness Statements (Witness interviews)",
            "location history": "Location History (Mobile GPS trace, cell tower logs)",
            "officer note": "Officer Notes (Initial investigation diary)",
            "email": "Email Records (Correspondence with family/witnesses)",
            "adhaar card": "Aadhaar Card copy (Demographic validation)"
        }
        
        missing = []
        for key, val in checklist.items():
            found = False
            for ext in existing_types:
                if key in ext:
                    found = True
                    break
            if not found:
                missing.append(val)
                
        # Validate additional physical demographics
        if not case_info.adhaar_card:
            missing.append("Aadhaar Number (Demographic validation)")
        if not case_info.birth_marks:
            missing.append("Identifying Marks / Birthmarks details")
        if not case_info.medical_info:
            missing.append("Medical History (Allergies, psychological conditions)")

        if not missing:
            return "All standard evidence, statements, and case files are successfully logged."
            
        missing_str = "\n".join([f"- {m}" for m in missing])
        
        system_prompt = "You are TraceAI. Generate a structured checklist of missing evidence for the officer."
        user_prompt = f"""
For the missing person case of {case_info.name}, the following files and details are currently MISSING from the database:
{missing_str}

Please generate an investigative action plan detailing:
1. Why each missing element is critical to resolve the case.
2. Best practices to obtain this missing evidence (e.g. contacting telecom carriers, family interviews).
"""
        return self._query_ollama(system_prompt, user_prompt)

    def generate_investigation_timeline(self, db: Session, case_id: str) -> List[Dict[str, Any]]:
        """
        Compiles a timeline of events for the case chronologically.
        """
        timeline = []
        
        # 1. Registration
        case = db.query(RegisteredCases).filter(RegisteredCases.id == case_id).first()
        if not case:
            return []
            
        timeline.append({
            "date": case.submitted_on,
            "title": "Case Registered",
            "description": f"Missing person report filed by {case.complainant_name} (Relation: Family/Informant). Registered by Officer {case.submitted_by} in {case.city}.",
            "icon": "app_registration",
            "type": "registered"
        })
        
        # 2. Sightings / Submissions
        # Query matches
        matches = db.query(SightingMatch).filter(SightingMatch.case_id == case_id).all()
        for m in matches:
            sub = db.query(PublicSubmissions).filter(PublicSubmissions.id == m.submission_id).first()
            if sub:
                timeline.append({
                    "date": sub.submitted_on,
                    "title": "Public Sighting Report",
                    "description": f"Citizen sighting report uploaded from {sub.location}. Bounding box matches face signature (similarity score: {m.similarity_score:.2f}, confidence: {m.confidence:.1f}%).",
                    "icon": "visibility",
                    "type": "sighting"
                })
                
                if m.status == "Approved":
                    timeline.append({
                        "date": m.reviewed_on or sub.submitted_on,
                        "title": "Officer Verification",
                        "description": f"Sighting matching submission {sub.id[:8]} confirmed by Officer {m.reviewed_by or 'System'}. Comments: {m.comments or 'Matches verified.'}",
                        "icon": "verified",
                        "type": "verification"
                    })
                elif m.status == "Rejected":
                    timeline.append({
                        "date": m.reviewed_on or sub.submitted_on,
                        "title": "Sighting Disproved",
                        "description": f"Officer {m.reviewed_by or 'System'} rejected the AI face match. Details: {m.comments or 'Disproved matching parameters.'}",
                        "icon": "cancel",
                        "type": "rejection"
                    })

        # 3. Documents/Logs timeline
        docs = db.query(InvestigationDoc).filter(InvestigationDoc.case_id == case_id).all()
        for d in docs:
            timeline.append({
                "date": d.created_at,
                "title": f"Logged: {d.doc_type}",
                "description": f"{d.title}: {d.content[:150]}...",
                "icon": "note_add",
                "type": "document"
            })
            
        # 4. Resolved status
        if case.status == "F":
            timeline.append({
                "date": datetime.utcnow(), # Placeholder or matched verification date
                "title": "Case Resolved (Found)",
                "description": f"Person successfully located and identified. Matched with submission ID: {case.matched_with[:8] if case.matched_with else 'N/A'}.",
                "icon": "check_circle",
                "type": "resolved"
            })
            
        # Sort chronologically
        timeline.sort(key=lambda x: x["date"])
        
        # Convert date to string for rendering
        for item in timeline:
            if isinstance(item["date"], datetime):
                item["date"] = item["date"].strftime("%d %b %Y, %I:%M %p")
                
        return timeline

# Singleton instance
rag_assistant = RAGAssistant()
