from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.conf import settings
import os

def generate_invoice_pdf(invoice):
    """Generate PDF invoice"""
    # Create invoices directory if it doesn't exist
    invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(invoice_dir, exist_ok=True)
    
    filename = f"invoice_{invoice.invoice_number}.pdf"
    filepath = os.path.join(invoice_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkgreen
    )
    story.append(Paragraph("FRESH PRODUCE INVOICE", title_style))
    story.append(Spacer(1, 20))
    
    # Invoice details
    invoice_data = [
        ['Invoice Number:', invoice.invoice_number],
        ['Order Number:', invoice.order.order_number],
        ['Issue Date:', invoice.issue_date.strftime('%Y-%m-%d')],
        ['Due Date:', invoice.due_date.strftime('%Y-%m-%d')],
        ['Customer:', invoice.order.customer.get_full_name()],
        ['Email:', invoice.order.customer.email],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 30))
    
    # Order items
    items_data = [['Product', 'Quantity', 'Unit Price', 'Total']]
    for item in invoice.order.items.all():
        items_data.append([
            item.product.name,
            f"{item.quantity} {item.product.unit}",
            f"${item.price_per_unit}",
            f"${item.total_price}"
        ])
    
    # Add totals
    items_data.extend([
        ['', '', 'Subtotal:', f"${invoice.order.subtotal}"],
        ['', '', 'Tax:', f"${invoice.order.tax}"],
        ['', '', 'TOTAL:', f"${invoice.order.total}"],
    ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
    ]))
    story.append(items_table)
    
    # Build PDF
    doc.build(story)
    
    return f"invoices/{filename}"