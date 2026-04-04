import os
from fpdf import FPDF

def create_report():
    pdf = FPDF()
    pdf.add_page()
    
    # Use typewriter font
    pdf.set_font("Courier", size=12)
    
    # Header
    pdf.set_font("Courier", style='B', size=16)
    pdf.cell(200, 10, txt="SAFEHANDS INITIATIVE", ln=1, align='C')
    pdf.cell(200, 10, txt="CRITICAL INCIDENT FIELD REPORT", ln=2, align='C')
    pdf.ln(10)
    
    # Body text
    pdf.set_font("Courier", size=12)
    
    report_text = """
INCIDENT LOCATION: Area 07B
TIME: 14:30 HOURS
PRIORITY: HIGH / URGENT

SITUATION SUMMARY:
There has been a catastrophic Water Pipe Burst localized entirely within the Area 07B temporary housing perimeter. The sudden flooding has displaced approximately 40 families and compromised the structural integrity of the emergency tents.

MEDICAL REPORT:
We have multiple individuals who have sustained lacerations and blunt force trauma from the collapsing heavy structures. We urgently require comprehensive Medical Kits and bandages to treat the wounded and prevent mass infections due to the standing water. Please dispatch immediately.

- Field Agent Marcus
"""
    
    pdf.multi_cell(0, 10, report_text)
    
    # Ensure directory exists
    os.makedirs('data', exist_ok=True)
    pdf.output('data/sample_field_report.pdf')
    print("PDF generated successfully at data/sample_field_report.pdf")

if __name__ == "__main__":
    create_report()
