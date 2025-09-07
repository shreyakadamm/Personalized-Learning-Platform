from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import io
import base64

class CertificateGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for certificate"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB')
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#A23B72')
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        self.signature_style = ParagraphStyle(
            'Signature',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
    
    def generate_completion_certificate(self, user_name, course_name, completion_date, score=None):
        """Generate a course completion certificate"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add certificate header
        elements.append(Spacer(1, 0.5*inch))
        
        # Title
        title = Paragraph("CERTIFICATE OF COMPLETION", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Subtitle
        subtitle = Paragraph("This is to certify that", self.body_style)
        elements.append(subtitle)
        elements.append(Spacer(1, 0.2*inch))
        
        # User name
        name_style = ParagraphStyle(
            'UserName',
            parent=self.styles['Normal'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB'),
            fontName='Helvetica-Bold'
        )
        user_name_para = Paragraph(user_name, name_style)
        elements.append(user_name_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Completion text
        completion_text = Paragraph(f"has successfully completed the course", self.body_style)
        elements.append(completion_text)
        elements.append(Spacer(1, 0.2*inch))
        
        # Course name
        course_style = ParagraphStyle(
            'CourseName',
            parent=self.styles['Normal'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#A23B72'),
            fontName='Helvetica-Bold'
        )
        course_para = Paragraph(course_name, course_style)
        elements.append(course_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Score if provided
        if score is not None:
            score_text = Paragraph(f"with a score of {score}%", self.body_style)
            elements.append(score_text)
            elements.append(Spacer(1, 0.2*inch))
        
        # Date
        date_text = Paragraph(f"on {completion_date}", self.body_style)
        elements.append(date_text)
        elements.append(Spacer(1, 0.5*inch))
        
        # Signature section
        signature_table_data = [
            ['', ''],
            ['_' * 30, '_' * 30],
            ['Platform Administrator', 'Date of Issue']
        ]
        
        signature_table = Table(signature_table_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            ('TOPPADDING', (0, 1), (-1, 1), 20),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer = Paragraph("Personalized Learning Platform", self.signature_style)
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and return it
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def generate_achievement_certificate(self, user_name, achievement_type, achievement_details, date):
        """Generate an achievement certificate"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        elements = []
        
        # Add certificate header
        elements.append(Spacer(1, 0.5*inch))
        
        # Title
        title = Paragraph("CERTIFICATE OF ACHIEVEMENT", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Achievement text
        achievement_text = Paragraph("This certificate is awarded to", self.body_style)
        elements.append(achievement_text)
        elements.append(Spacer(1, 0.2*inch))
        
        # User name
        name_style = ParagraphStyle(
            'UserName',
            parent=self.styles['Normal'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB'),
            fontName='Helvetica-Bold'
        )
        user_name_para = Paragraph(user_name, name_style)
        elements.append(user_name_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Achievement details
        for_text = Paragraph(f"for {achievement_type}", self.body_style)
        elements.append(for_text)
        elements.append(Spacer(1, 0.2*inch))
        
        # Achievement specifics
        details_style = ParagraphStyle(
            'Details',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#A23B72')
        )
        details_para = Paragraph(achievement_details, details_style)
        elements.append(details_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Date
        date_text = Paragraph(f"Awarded on {date}", self.body_style)
        elements.append(date_text)
        elements.append(Spacer(1, 0.5*inch))
        
        # Signature section
        signature_table_data = [
            ['', ''],
            ['_' * 30, '_' * 30],
            ['Platform Administrator', 'Date of Issue']
        ]
        
        signature_table = Table(signature_table_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            ('TOPPADDING', (0, 1), (-1, 1), 20),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer = Paragraph("Personalized Learning Platform", self.signature_style)
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and return it
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data

def create_download_link(pdf_data, filename):
    """Create a download link for PDF data"""
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download Certificate</a>'
    return href
