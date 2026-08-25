import logging
from pathlib import Path
import html
from typing import Dict, Any

logger = logging.getLogger(__name__)

def generate_resume_html(state: Dict[str, Any]) -> str:
    """Generate clean, ATS-friendly HTML from workflow state."""
    full_name = state.get("full_name") or "[Full Name]"
    email = state.get("email") or state.get("email_address") or "[Email Address]"
    phone = state.get("phone") or state.get("phone_number") or "[Phone Number]"
    linkedin_url = state.get("linkedin_url") or "[LinkedIn URL]"
    github_url = state.get("github_url") or "[GitHub URL]"
    role = state.get("role") or "Software Engineer"
    
    # Skills
    matching_skills = state.get("matching_skills", [])
    if isinstance(matching_skills, list):
        skills_str = ", ".join([str(s) for s in matching_skills])
    else:
        skills_str = str(matching_skills)

    # Rewritten resume data
    rewritten_resume = state.get("rewritten_resume", {})
    summary = ""
    sections = []
    
    if isinstance(rewritten_resume, dict):
        summary = rewritten_resume.get("summary", "")
        sections = rewritten_resume.get("sections", [])
    elif isinstance(rewritten_resume, str):
        summary = rewritten_resume

    # Fallback summary if empty
    if not summary:
        resume_text = state.get("resume_text", "")
        summary = resume_text[:300] + "..." if len(resume_text) > 300 else resume_text

    # Contact line
    contact_parts = []
    if email and email != "[Email Address]":
        contact_parts.append(html.escape(email))
    if phone and phone != "[Phone Number]":
        contact_parts.append(html.escape(phone))
    if linkedin_url and linkedin_url != "[LinkedIn URL]":
        contact_parts.append(f'<a href="{html.escape(linkedin_url)}">{html.escape(linkedin_url)}</a>')
    if github_url and github_url != "[GitHub URL]":
        contact_parts.append(f'<a href="{html.escape(github_url)}">{html.escape(github_url)}</a>')

    contact_html = " &bull; ".join(contact_parts) if contact_parts else html.escape(f"{email} | {phone}")

    # Build sections HTML
    sections_html = ""
    if sections and isinstance(sections, list):
        for sec in sections:
            if isinstance(sec, dict):
                stitle = html.escape(sec.get("section_title", "Experience"))
                bullets = sec.get("bullet_points", [])
                bullets_html = "".join([f"<li>{html.escape(str(b))}</li>" for b in bullets])
                sections_html += f"""
                <div class="section-title">{stitle}</div>
                <ul>{bullets_html}</ul>
                """

    if not sections_html:
        # Generic sections built from resume_text
        sections_html = f"""
        <div class="section-title">Experience & Key Highlights</div>
        <p style="font-size: 11px; white-space: pre-line;">{html.escape(state.get("resume_text", ""))}</p>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 15mm 15mm 15mm 15mm;
  }}
  body {{
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    color: #2c3e50;
    line-height: 1.4;
    font-size: 11px;
    margin: 0;
    padding: 0;
  }}
  .header {{
    text-align: center;
    border-bottom: 2px solid #1a2b4c;
    padding-bottom: 10px;
    margin-bottom: 12px;
  }}
  .name {{
    font-size: 24px;
    font-weight: bold;
    color: #1a2b4c;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .target-role {{
    font-size: 13px;
    font-weight: 600;
    color: #34495e;
    margin-bottom: 6px;
  }}
  .contact {{
    font-size: 10.5px;
    color: #555;
  }}
  .contact a {{
    color: #2980b9;
    text-decoration: none;
  }}
  .section-title {{
    font-size: 13px;
    font-weight: bold;
    text-transform: uppercase;
    color: #1a2b4c;
    border-bottom: 1px solid #bdc3c7;
    margin-top: 14px;
    margin-bottom: 6px;
    padding-bottom: 3px;
    letter-spacing: 0.5px;
  }}
  .summary {{
    font-size: 11px;
    text-align: justify;
    margin-bottom: 10px;
  }}
  .skills-box {{
    background-color: #f8f9fa;
    border-left: 3px solid #1a2b4c;
    padding: 6px 10px;
    margin-bottom: 10px;
    font-size: 10.5px;
  }}
  ul {{
    margin: 4px 0 10px 18px;
    padding: 0;
  }}
  li {{
    margin-bottom: 4px;
    font-size: 11px;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="name">{html.escape(full_name)}</div>
    <div class="target-role">{html.escape(role)}</div>
    <div class="contact">{contact_html}</div>
  </div>

  <div class="section-title">Professional Summary</div>
  <div class="summary">{html.escape(summary)}</div>

  {f'<div class="section-title">Technical Skills & Competencies</div><div class="skills-box"><strong>Core Skills:</strong> {html.escape(skills_str)}</div>' if skills_str else ''}

  {sections_html}
</body>
</html>"""
    return html_content


def render_alternative_pdf(state: Dict[str, Any], output_pdf: Path) -> Path:
    """
    Alternative PDF Generator using WeasyPrint (HTML/CSS to PDF) or ReportLab.
    Guaranteed zero LaTeX compilation errors.
    """
    output_pdf = Path(output_pdf).expanduser().resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    
    html_str = generate_resume_html(state)

    try:
        import weasyprint
        logger.info("Generating PDF via WeasyPrint HTML renderer...")
        weasyprint.HTML(string=html_str).write_pdf(output_pdf)
        if output_pdf.exists() and output_pdf.stat().st_size > 0:
            return output_pdf
    except Exception as exc:
        logger.warning(f"WeasyPrint PDF rendering failed, falling back to ReportLab: {exc}")

    # Fallback to ReportLab if WeasyPrint fails or is unavailable
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        logger.info("Generating PDF via ReportLab renderer...")
        doc = SimpleDocTemplate(str(output_pdf), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, leading=24, textColor='#1a2b4c')
        sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, leading=13, textColor='#555555')
        heading_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, leading=16, textColor='#1a2b4c')
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)

        story = []
        full_name = state.get("full_name") or "[Full Name]"
        role = state.get("role") or "Software Engineer"
        
        story.append(Paragraph(full_name, title_style))
        story.append(Paragraph(role, sub_style))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("Professional Summary", heading_style))
        summary_text = state.get("rewritten_resume", {}).get("summary", state.get("resume_text", ""))
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 10))

        doc.build(story)
        return output_pdf
    except Exception as exc:
        logger.error(f"ReportLab PDF rendering also failed: {exc}")
        raise RuntimeError("All alternative PDF generators failed.") from exc
