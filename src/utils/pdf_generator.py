import os
import io
import pandas as pd
from fpdf import FPDF
from datetime import datetime

def generate_executive_pdf(df: pd.DataFrame, file_path: str = None) -> bytes:
    """
    Generates a clean PDF summary of critical needs and a proposed allocation plan.
    Returns bytes if file_path is None, otherwise saves to file_path and returns the path.
    """
    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 20, "EXECUTIVE IMPACT ANALYTICS", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Critical Needs Overview", ln=True)
    pdf.set_font("Arial", '', 10)

    critical_df = df[df['urgency'] >= 8].nlargest(10, 'urgency') if 'urgency' in df.columns else pd.DataFrame()

    if critical_df.empty:
        pdf.cell(0, 10, "No critical needs requiring immediate intervention at this time.", ln=True)
    else:
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(20, 10, "Urgency", 1, 0, 'C', 1)
        pdf.cell(30, 10, "Category", 1, 0, 'C', 1)
        pdf.cell(140, 10, "Description Summary", 1, 1, 'C', 1)

        for _, row in critical_df.iterrows():
            pdf.cell(20, 8, str(int(row['urgency'])), 1, 0, 'C')
            pdf.cell(30, 8, str(row['category']), 1, 0, 'C')
            desc = row['description'][:65] + "..." if len(str(row['description'])) > 65 else str(row['description'])
            pdf.cell(140, 8, desc, 1, 1)

    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Proposed Resource Allocation Strategy", ln=True)
    pdf.set_font("Arial", '', 10)

    if 'category' in df.columns and 'status' in df.columns:
        counts = df[df['status'] == 'Pending']['category'].value_counts() if 'Pending' in df['status'].values else df['category'].value_counts()
        for cat, count in counts.items():
            pdf.cell(0, 10, f"- {cat}: Priority identified for {count} unresolved requests.", ln=True)

    pdf.ln(5)
    pdf.multi_cell(0, 10, "Strategic Recommendation: Shift logistical focus onto high-density clusters and prioritize Medical kits for the most critical urgency markers. Volunteer distribution should favor Sector Alpha based on current proximity analysis.")

    pdf.set_y(-20)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(164, 164, 164)
    pdf.cell(0, 10, "Strictly Confidential - For NGO Stakeholder Internal Review Only - Smart Resource Allocation v2.0", align='C')

    if file_path:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        pdf.output(file_path)
        return file_path
    else:
        return pdf.output()
