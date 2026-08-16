# 🔍 TraceAI - Finding Hope Through Intelligence

TraceAI is a comprehensive, Python-based case management and facial recognition platform designed to assist law enforcement in tracking and finding missing persons. 

## 🚀 Features
* **AI Case Summarization:** Utilizes local LLMs (LLaMA 3 via Ollama) to instantly analyze and summarize investigation documents, demographic data, and witness reports using Retrieval-Augmented Generation (RAG).
* **Facial Analysis & Matching:** Integrates MediaPipe for advanced face landmarking, age progression, and sighting verification.
* **Dual Portals:** Secure, role-based dashboards for law enforcement officers (to manage cases) and public-facing submission forms (for community sightings).
* **Interactive Mapping:** Built-in Leaflet.js integration to map last-known locations and reported sightings.
* **Modern UI:** A seamless, responsive web interface built entirely in Python using NiceGUI and FastAPI.

## 💻 Tech Stack
* **Frontend/Backend:** Python, NiceGUI, FastAPI
* **Database:** MySQL, SQLAlchemy (ORM)
* **AI/ML:** Ollama (LLaMA 3), MediaPipe, Sentence-Transformers
* **Deployment:** Render, GitHub

## 🛠️ How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/tasneemu-13/TraceAI-main.git](https://github.com/tasneemu-13/TraceAI-main.git)
   cd TraceAI-main```
### Step 2: Push the README to GitHub
Now that you have created the file locally, you just need to send this specific file up to the cloud. Run these three quick commands in your terminal:

```powershell
git add README.md
git commit -m "Added README documentation"
git push
