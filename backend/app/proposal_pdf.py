import os
import json
from fpdf import FPDF
from datetime import datetime

class ProposalPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)
        
    def header(self):
        if self.page_no() == 1:
            return
            
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(15, 23, 42)
        self.cell(100, 10, 'NEXORA', border=0, align='L')
        
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, 'Intelligence Reimagined', border=0, align='R')
        self.ln(15)
        
        self.set_draw_color(226, 232, 240)
        self.line(20, 32, 190, 32)
        self.ln(5)
        
    def footer(self):
        if self.page_no() == 1:
            return
            
        self.set_y(-20)
        self.set_draw_color(226, 232, 240)
        self.line(20, 277, 190, 277)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def sanitize_text(text: str) -> str:
    text = text.replace('•', '-')
    text = text.replace('★', '*')
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('–', '-').replace('—', '-')
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_proposal_pdf(proposal_id: int, proposal_data: str, business_name: str) -> str:
    data = json.loads(proposal_data) if isinstance(proposal_data, str) else proposal_data
    pdf = ProposalPDF()
    
    # ---------------------------------------------------------
    # 1. Executive Cover
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 297, style="F")
    
    pdf.set_y(60)
    pdf.set_font('Helvetica', 'B', 36)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "NEXORA", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 10, "INTELLIGENCE REIMAGINED", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_y(130)
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(248, 250, 252)
    pdf.cell(0, 15, "Revenue Growth Proposal", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_y(190)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 8, "PREPARED FOR:", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, sanitize_text(business_name), align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_y(240)
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, sanitize_text(f"Proposal Number: PRP-{proposal_id}"), align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, sanitize_text(f"Date: {datetime.now().strftime('%B %d, %Y')}"), align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Prepared By: Nexora Growth Engineering", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_fill_color(255, 255, 255)

    # ---------------------------------------------------------
    # 2. Executive Summary
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Executive Summary", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, "Current Business Position", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 8, sanitize_text(data.get("current_situation", "")))
    pdf.ln(10)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, "Current Digital Situation & Opportunity", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 8, sanitize_text(data.get("executive_summary", "")))
    
    # ---------------------------------------------------------
    # 3. Competitive Positioning
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Competitive Positioning", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, "Market Reality", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 8, "Customer expectations have evolved. A digital presence is no longer just a brochure; it is the primary engine for customer acquisition, trust building, and revenue generation.")
    pdf.ln(10)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, "The Competitive Gap", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    positioning_text = data.get("market_positioning", "Businesses investing in modern visibility, analytics, and conversion systems continue to widen the digital gap. Delayed action increases customer acquisition costs over time.")
    pdf.multi_cell(0, 8, sanitize_text(positioning_text))
    
    # ---------------------------------------------------------
    # 4. Visual Revenue Dashboard
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Executive Metrics Dashboard", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    metrics = data.get("metrics", {})
    cards = [
        ("Revenue Potential", f"{metrics.get('revenue_potential', 0)}/100", 79, 70, 229),
        ("Sales Readiness", f"{metrics.get('sales_readiness', 0)}/100", 14, 165, 233),
        ("Conversion Score", f"{metrics.get('conversion_score', 0)}/100", 16, 185, 129),
        ("Audit Score", f"{metrics.get('audit_score', 0)}/100", 245, 158, 11)
    ]
    
    y_start = pdf.get_y()
    for i, (label, val, r, g, b) in enumerate(cards):
        col = i % 2
        row = i // 2
        x = 20 + col * 85
        y = y_start + row * 30
        
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(x, y, 80, 25, style="DF")
        
        pdf.set_xy(x + 5, y + 3)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(70, 5, sanitize_text(label.upper()), align='L')
        
        pdf.set_xy(x + 5, y + 10)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(r, g, b)
        pdf.cell(70, 7, sanitize_text(val), align='L')
        
    pdf.set_y(y_start + 70)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(20, pdf.get_y(), 170, 25, style="DF")
    pdf.set_xy(25, pdf.get_y() + 5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(100, 5, "OPPORTUNITY TYPE", align='L')
    pdf.set_xy(25, pdf.get_y() + 5)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(100, 7, sanitize_text(str(metrics.get('opportunity_type', 'Unknown'))), align='L')
    
    # ---------------------------------------------------------
    # 5. Website Intelligence Review (Annotations)
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Website Intelligence Annotations", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    screenshots = data.get("screenshots", {})
    base_screenshot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "screenshots"))
    home_path = screenshots.get("homepage")
    conv_path = screenshots.get("conversion")
    
    if home_path and conv_path:
        h_file = home_path.replace("/screenshots/", "")
        c_file = conv_path.replace("/screenshots/", "")
        h_abs = os.path.join(base_screenshot_dir, h_file)
        c_abs = os.path.join(base_screenshot_dir, c_file)
        
        if os.path.exists(h_abs) and os.path.exists(c_abs):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(71, 85, 105)
            y_img = pdf.get_y()
            pdf.cell(80, 8, "Homepage Analysis", align='C')
            pdf.set_x(110)
            pdf.cell(80, 8, "Conversion Path Analysis", align='C', new_x="LMARGIN", new_y="NEXT")
            
            try:
                pdf.image(h_abs, x=20, y=y_img+10, w=80)
                pdf.image(c_abs, x=110, y=y_img+10, w=80)
                pdf.set_y(y_img + 105)
                
                # Annotations
                findings = data.get("audit_findings_detailed", [])
                if findings:
                    f = findings[0]
                    pdf.set_fill_color(248, 250, 252)
                    pdf.rect(20, pdf.get_y(), 170, 35, style="DF")
                    pdf.set_xy(25, pdf.get_y() + 5)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(160, 6, sanitize_text(f"Observed: {f.get('leak')}"))
                    pdf.set_xy(25, pdf.get_y() + 6)
                    pdf.set_text_color(225, 29, 72)
                    pdf.cell(160, 6, sanitize_text(f"Impact: {f.get('business_impact', '')[:100]}"))
                    pdf.set_xy(25, pdf.get_y() + 6)
                    pdf.set_text_color(79, 70, 229)
                    pdf.cell(160, 6, sanitize_text(f"Action: {f.get('action')}"))
            except Exception:
                pass
    else:
        pdf.set_font('Helvetica', 'I', 12)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 10, "Visual intelligence rendering pending.", align='C', new_x="LMARGIN", new_y="NEXT")

    # ---------------------------------------------------------
    # 6. Revenue Leak Analysis
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Revenue Risk Analysis", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    narrative = data.get("lost_revenue_narrative", "")
    if narrative:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(225, 29, 72)
        pdf.multi_cell(0, 8, sanitize_text(narrative))
        pdf.ln(10)
    
    findings = data.get("audit_findings_detailed", [])
    for f in findings:
        y = pdf.get_y()
        if y > 240:
            pdf.add_page()
            y = pdf.get_y()
            
        pdf.set_fill_color(248, 250, 252)
        pdf.rect(20, y, 170, 35, style="DF")
        
        pdf.set_xy(25, y + 5)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(100, 6, sanitize_text(f.get('leak', '')), align='L')
        
        pdf.set_xy(145, y + 5)
        risk = f.get("risk_level", "")
        if risk == "Critical":
            pdf.set_text_color(225, 29, 72)
        else:
            pdf.set_text_color(234, 179, 8)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 6, sanitize_text(f"Risk: {risk}"), align='R')
        
        pdf.set_xy(25, y + 13)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(71, 85, 105)
        impact = f.get('business_impact', '')
        if len(impact) > 100: impact = impact[:97] + "..."
        pdf.multi_cell(160, 5, sanitize_text(impact))
        
        pdf.set_y(y + 42)

    # ---------------------------------------------------------
    # 7. Solution Blueprint
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Solution Blueprint", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pkg_name = data.get("package_name", "Custom Growth Plan")
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 10, sanitize_text(pkg_name), align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "Deliverables & Implementation", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    for d in data.get("deliverables", []):
        pdf.cell(5, 8, "", align='L')
        pdf.cell(0, 8, sanitize_text(f"✓ {d}"), align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "Expected Outcomes", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    for o in data.get("expected_outcomes", []):
        pdf.cell(5, 8, "", align='L')
        pdf.cell(0, 8, sanitize_text(f"✓ {o}"), align='L', new_x="LMARGIN", new_y="NEXT")

    # ---------------------------------------------------------
    # 8. ROI Roadmap
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Execution Roadmap", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    roadmap = [
        ("Phase 1: Audit & Strategy", "Comprehensive technical deep dive and competitive benchmarking."),
        ("Phase 2: Implementation", "Deploying conversion mechanisms, tracking infrastructure, and assets."),
        ("Phase 3: Optimization", "A/B testing, performance tuning, and funnel alignment."),
        ("Phase 4: Scaling & Measurement", "Go-live, analytics observation, and continuous growth cycling.")
    ]
    
    y = pdf.get_y()
    for i, (title, desc) in enumerate(roadmap):
        pdf.set_fill_color(79, 70, 229)
        pdf.rect(20, y + (i*30), 10, 10, style="F")
        pdf.set_xy(20, y + (i*30))
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(10, 10, str(i+1), align='C')
        
        pdf.set_xy(35, y + (i*30))
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, sanitize_text(title), align='L', new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_xy(35, y + (i*30) + 5)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 5, sanitize_text(desc), align='L')
        
        if i < len(roadmap) - 1:
            pdf.set_draw_color(203, 213, 225)
            pdf.line(25, y + (i*30) + 10, 25, y + (i*30) + 30)

    # ---------------------------------------------------------
    # 9. Investment & ROI
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Investment Profile", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    inv = data.get("investment", {})
    setup = inv.get("setup_fee", 0)
    monthly = inv.get("monthly_retainer", 0)
    
    y_card = pdf.get_y()
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(20, y_card, 170, 80, style="F")
    
    pdf.set_xy(20, y_card + 15)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(170, 10, "TOTAL PROJECT INVESTMENT", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(20, y_card + 35)
    pdf.set_font('Helvetica', 'B', 32)
    pdf.set_text_color(255, 255, 255)
    if monthly > 0:
        pdf.cell(170, 15, f"${setup:,.0f} + ${monthly:,.0f}/mo", align='C', new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(170, 15, f"${setup:,.0f}", align='C', new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_xy(20, y_card + 55)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(170, 10, f"Project Duration: {sanitize_text(data.get('timeline', 'TBD'))}", align='C', new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_y(y_card + 100)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "Modeled ROI Profile", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 8, sanitize_text("By addressing the critical revenue leaks identified in our audit, this investment is strategically modeled to return capital through increased lead volume, higher conversion rates, and optimized customer acquisition costs."))

    # ---------------------------------------------------------
    # 10. Cost of Inaction 2.0
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Cost of Inaction", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_fill_color(254, 242, 242)
    pdf.set_draw_color(252, 165, 165)
    pdf.rect(20, pdf.get_y(), 170, 30, style="DF")
    pdf.set_xy(25, pdf.get_y() + 10)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(225, 29, 72)
    pdf.multi_cell(160, 8, sanitize_text("Every month without an optimized system represents permanently unrecoverable revenue."))
    
    pdf.ln(15)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "The compounding cost of delay:", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    coi = [
        ("Customer Loss", "High-intent visitors abandoning the funnel to transact with competitors."),
        ("Visibility Loss", "Organic ranking decay making acquisition increasingly reliant on paid media."),
        ("Conversion Loss", "Friction preventing interested prospects from converting."),
        ("Competitive Risk", "Competitors continuously innovating and widening the digital market gap.")
    ]
    
    for title, desc in coi:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(225, 29, 72)
        pdf.cell(45, 8, sanitize_text(title), align='L')
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(125, 8, sanitize_text(desc), align='L', new_x="LMARGIN", new_y="NEXT")

    # ---------------------------------------------------------
    # 11. Why Nexora (The Nexora Method)
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "The Nexora Method", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 10, "We do not sell websites. We build revenue systems.", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    methodology = [
        ("1. Discover", "Data-driven discovery powered by AI Website Intelligence."),
        ("2. Diagnose", "Identify the exact friction points costing you revenue."),
        ("3. Prioritize", "Rank solutions based on fastest path to ROI."),
        ("4. Execute", "Enterprise-grade deployment of high-converting infrastructure."),
        ("5. Measure", "Closed-loop analytics to track every visitor behavior."),
        ("6. Optimize", "Continuous refinement for maximum market capture.")
    ]
    
    for title, desc in methodology:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, sanitize_text(title), align='L', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 6, sanitize_text(desc))
        pdf.ln(4)

    # ---------------------------------------------------------
    # 12. Acceptance & Next Steps
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, "Acceptance & Next Steps", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 10, "Ready To Get Started?", align='L', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 8, "1. Sign the authorization below.\n2. We will schedule a Kickoff Call within 48 hours.\n3. Project execution immediately follows kickoff.")
    pdf.ln(15)
    
    pdf.set_draw_color(203, 213, 225)
    
    pdf.line(20, pdf.get_y() + 15, 90, pdf.get_y() + 15)
    pdf.set_xy(20, pdf.get_y() + 20)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(70, 5, "AUTHORIZED SIGNATURE", align='L')
    
    pdf.line(120, pdf.get_y() - 5, 190, pdf.get_y() - 5)
    pdf.set_xy(120, pdf.get_y())
    pdf.cell(70, 5, "DATE", align='L')
    
    pdf.ln(30)
    
    pdf.line(20, pdf.get_y() + 15, 90, pdf.get_y() + 15)
    pdf.set_xy(20, pdf.get_y() + 20)
    pdf.cell(70, 5, "PRINTED NAME", align='L')
    
    pdf.line(120, pdf.get_y() - 5, 190, pdf.get_y() - 5)
    pdf.set_xy(120, pdf.get_y())
    pdf.cell(70, 5, "COMPANY / TITLE", align='L')
    
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "proposals")
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, f"proposal_{proposal_id}.pdf")
    pdf.output(file_path)
    return file_path
