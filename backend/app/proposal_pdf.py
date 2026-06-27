import os
import json
from fpdf import FPDF
from datetime import datetime

class ProposalPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, 'Nexora OS Proposal', 0, 0, 'L')
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_proposal_pdf(proposal_id: int, proposal_data: str, business_name: str) -> str:
    """Generate a premium branded PDF for the proposal"""
    data = json.loads(proposal_data) if isinstance(proposal_data, str) else proposal_data
    
    pdf = ProposalPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42) # Slate 900
    pdf.cell(0, 20, f'Revenue Optimization Proposal', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(71, 85, 105) # Slate 500
    pdf.cell(0, 10, f'Prepared for {business_name}', 0, 1, 'C')
    pdf.cell(0, 10, f'Date: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')
    pdf.ln(20)
    
    # Sections
    sections = [
        ("Executive Summary", data.get("executive_summary", "")),
        ("Current Situation", data.get("current_situation", "")),
        ("Problems Found", "\n".join([f"• {p}" for p in data.get("problems_found", [])])),
        ("Recommended Services", "\n".join([f"• {s}" for s in data.get("recommended_services", [])])),
        ("Deliverables", "\n".join([f"• {d}" for d in data.get("deliverables", [])])),
        ("Timeline", data.get("timeline", "")),
        ("Investment", f"Setup Fee: ${data.get('investment', {}).get('setup_fee', 0):,.2f}\nMonthly Retainer: ${data.get('investment', {}).get('monthly_retainer', 0):,.2f}"),
        ("Expected Outcomes", "\n".join([f"• {o}" for o in data.get("expected_outcomes", [])])),
        ("Next Steps", data.get("next_steps", ""))
    ]
    
    for title, content in sections:
        if not content: continue
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 15, title, 0, 1, 'L')
        
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(0, 8, str(content))
        pdf.ln(10)
        
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "proposals")
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, f"proposal_{proposal_id}.pdf")
    pdf.output(file_path)
    return file_path
