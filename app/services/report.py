import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.case import RegisteredCases
from app.models.submission import PublicSubmissions
from app.models.doc import SightingMatch, InvestigationDoc

def generate_case_summary_html(db: Session, case_id: str) -> str:
    """
    Generates a print-ready HTML report for the case.
    """
    case = db.query(RegisteredCases).filter(RegisteredCases.id == case_id).first()
    if not case:
        return "<h1>Case not found</h1>"
        
    docs = db.query(InvestigationDoc).filter(InvestigationDoc.case_id == case_id).all()
    matches = db.query(SightingMatch).filter(SightingMatch.case_id == case_id).all()
    
    docs_html = ""
    for d in docs:
        docs_html += f"""
        <div class="doc-item">
            <h3>{d.doc_type} - {d.title or 'Untitled'}</h3>
            <p class="meta">Logged on: {d.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <p>{d.content}</p>
        </div>
        """
        
    matches_html = ""
    for m in matches:
        sub = db.query(PublicSubmissions).filter(PublicSubmissions.id == m.submission_id).first()
        if sub:
            matches_html += f"""
            <tr>
                <td>{sub.id[:8]}</td>
                <td>{sub.location or 'Unknown'}</td>
                <td>{sub.submitted_on.strftime('%Y-%m-%d')}</td>
                <td>{m.confidence:.1f}%</td>
                <td><strong>{m.status}</strong></td>
            </tr>
            """

    if matches_html:
        matches_section = f"""
            <table>
                <thead>
                    <tr>
                        <th>Submission ID</th>
                        <th>Sighting Location</th>
                        <th>Sighting Date</th>
                        <th>Similarity Confidence</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {matches_html}
                </tbody>
            </table>
            """
    else:
        matches_section = '<p style="font-size: 13px; color: #777;">No facial matches verified yet.</p>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>TraceAI - Case Report: {case.name}</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #333;
                line-height: 1.6;
                padding: 40px;
                background: #fff;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px double #1a237e;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                color: #1a237e;
                font-size: 28px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .header p {{
                margin: 5px 0 0 0;
                font-size: 14px;
                color: #555;
            }}
            .section {{
                margin-bottom: 30px;
                page-break-inside: avoid;
            }}
            .section-title {{
                font-size: 18px;
                color: #1a237e;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
                margin-bottom: 15px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
                font-size: 13px;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
            }}
            .doc-item {{
                border-left: 3px solid #1a237e;
                padding-left: 15px;
                margin-bottom: 15px;
            }}
            .doc-item h3 {{
                margin: 0 0 5px 0;
                font-size: 14px;
            }}
            .meta {{
                font-size: 11px;
                color: #777;
                margin-top: 0;
            }}
            .disclaimer {{
                margin-top: 50px;
                font-size: 11px;
                color: #666;
                text-align: center;
                border-top: 1px solid #eee;
                padding-top: 15px;
            }}
            @media print {{
                body {{
                    padding: 0;
                }}
                .no-print {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: right; margin-bottom: 20px;">
            <button onclick="window.print()" style="padding: 8px 16px; background-color: #1a237e; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Print / Save as PDF
            </button>
        </div>
        
        <div class="header">
            <h1>TraceAI Sighting &amp; Case Report</h1>
            <p>Government of India Missing Person Investigation Platform</p>
            <p>Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>

        <div class="section">
            <div class="section-title">Case Profile Details</div>
            <table>
                <tr>
                    <th>Case ID</th>
                    <td>{case.id}</td>
                    <th>Case Status</th>
                    <td>{case.status} (NF = Not Found, F = Found)</td>
                </tr>
                <tr>
                    <th>Name</th>
                    <td>{case.name}</td>
                    <th>Age Registered</th>
                    <td>{case.age} yrs</td>
                </tr>
                <tr>
                    <th>Father's Name</th>
                    <td>{case.father_name or 'N/A'}</td>
                    <th>Adhaar Card</th>
                    <td>{case.adhaar_card or 'N/A'}</td>
                </tr>
                <tr>
                    <th>Last Seen Place</th>
                    <td>{case.last_seen}</td>
                    <th>Date Registered</th>
                    <td>{case.submitted_on.strftime('%Y-%m-%d')}</td>
                </tr>
                <tr>
                    <th>Complainant</th>
                    <td>{case.complainant_name}</td>
                    <th>Complainant Mobile</th>
                    <td>{case.complainant_mobile or 'N/A'}</td>
                </tr>
                <tr>
                    <th>Birth Marks</th>
                    <td colspan="3">{case.birth_marks or 'None reported'}</td>
                </tr>
                <tr>
                    <th>Physical Desc.</th>
                    <td colspan="3">{case.physical_description or 'None reported'}</td>
                </tr>
                <tr>
                    <th>Medical Info</th>
                    <td colspan="3">{case.medical_info or 'None reported'}</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">Investigation Logs &amp; Evidence</div>
            {docs_html if docs_html else '<p style="font-size: 13px; color: #777;">No investigative documents logged.</p>'}
        </div>

        <div class="section">
            <div class="section-title">AI Facial Recognition Matches</div>
            {matches_section}
        </div>


        <div class="disclaimer">
            <strong>Disclaimer:</strong> AI Generated Investigative Estimate. The matches and age progressed models of TraceAI are tools to assist investigations and must not be used as standalone proof of identity or criminal verification.
        </div>
    </body>
    </html>
    """
    return html_content
