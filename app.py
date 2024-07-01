# app.py
from flask import Flask, render_template, request, send_file
from io import BytesIO
import uuid
import os
from werkzeug.utils import secure_filename
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from datetime import datetime

app = Flask(__name__)

# Set the correct working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create the uploads directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('home.html')

def format_invoice_number(invoice_number):
    if not invoice_number.startswith('INV-'):
        # If the invoice number doesn't start with 'INV-', add it
        invoice_number = f"INV-{invoice_number}"
    
    # Ensure the number part is at least 3 digits
    number_part = invoice_number.split('-')[-1]
    formatted_number = number_part.zfill(3)
    
    return f"INV-{formatted_number}"

def create_pdf(invoice_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    elements = []

    # Custom styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, fontName='Helvetica-Bold', fontSize=12, textColor=HexColor('#333333')))
    styles.add(ParagraphStyle(name='Right', alignment=2, fontName='Helvetica', fontSize=10))
    styles.add(ParagraphStyle(name='Left', alignment=0, fontName='Helvetica', fontSize=10))
    
    # Header
    header_data = [
        [Paragraph(f"<font size=20><b>{invoice_data['invoice_name']}</b></font>", styles['Left']),
         Paragraph(f"<font size=20><b>INVOICE</b></font>", styles['Right'])],
        [Paragraph("", styles['Left']),
         Paragraph(f"<font size=14><b>{invoice_data['invoice_number']}</b></font>", styles['Right'])],
    ]
    header = Table(header_data, colWidths=[4*inch, 3*inch])
    header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 0.25*inch))

    # Logo
    if invoice_data['logo'] and os.path.exists(invoice_data['logo']):
        logo = Image(invoice_data['logo'])
        logo.drawHeight = 1*inch
        logo.drawWidth = 1*inch
        elements.append(logo)
        elements.append(Spacer(1, 0.25*inch))

    # Business and Client Information
    business_info = f"""
    <b>{invoice_data['business_name']}</b><br/>
    {invoice_data['business_address']}<br/>
    Phone: {invoice_data['business_phone']}<br/>
    Email: {invoice_data['business_email']}
    """
    
    client_info = f"""
    <b>Bill To:</b><br/>
    {invoice_data['client_name']}<br/>
    {invoice_data['client_address']}<br/>
    Email: {invoice_data['client_email']}
    """
    
    info_data = [
        [Paragraph(business_info, styles['Left']), Paragraph(client_info, styles['Left'])]
    ]
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#f3f3f3')),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.25*inch))

    # Invoice details
    invoice_details = [
        [Paragraph(f"<b>Invoice #:</b> {invoice_data['invoice_number']}", styles['Left']),
         Paragraph(f"<b>Date:</b> {invoice_data['date']}", styles['Right'])],
        [Paragraph(f"<b>Due Date:</b> {invoice_data['due_date']}", styles['Right'])]
    ]
    invoice_table = Table(invoice_details, colWidths=[4*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TEXTCOLOR', (0,0), (-1,-1), HexColor('#333333')),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.25*inch))

    # Items
    items_data = [['Description', 'Quantity', 'Price', 'Amount']]
    for item in invoice_data['items']:
        items_data.append([
            item['description'],
            str(item['quantity']),
            f"{invoice_data['currency']}{item['price']:.2f}",
            f"{invoice_data['currency']}{item['amount']:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[4*inch, 1*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#1a73e8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('TEXTCOLOR', (0,1), (-1,-1), HexColor('#333333')),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 1, HexColor('#dddddd'))
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.25*inch))

    # Totals
    totals_data = [
        ['', '', 'Subtotal', f"{invoice_data['currency']}{invoice_data['subtotal']:.2f}"],
        ['', '', f"Tax ({invoice_data['tax_rate']}%)", f"{invoice_data['currency']}{invoice_data['tax']:.2f}"],
        ['', '', 'Total', f"{invoice_data['currency']}{invoice_data['total']:.2f}"]
    ]
    totals_table = Table(totals_data, colWidths=[4*inch, 1*inch, 1*inch, 1*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (-2,-1), (-1,-1), 'RIGHT'),
        ('TEXTCOLOR', (-2,-1), (-1,-1), HexColor('#1a73e8')),
        ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (-2,-1), (-1,-1), 14),
        ('TOPPADDING', (-2,-1), (-1,-1), 6),
        ('BOTTOMPADDING', (-2,-1), (-1,-1), 6),
        ('LINEABOVE', (-2,-1), (-1,-1), 1, HexColor('#1a73e8')),
    ]))
    elements.append(totals_table)

    # Payment Details
    elements.append(Spacer(1, 0.25*inch))
    payment_info = f"""
    <b>Payment Details:</b><br/>
    Bank: {invoice_data['bank_name']}<br/>
    Account Name: {invoice_data['account_name']}<br/>
    BIC: {invoice_data['bic']}<br/>
    IBAN: {invoice_data['iban']}
    """
    elements.append(Paragraph(payment_info, styles['Left']))

    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Thank you for your business!", styles['Center']))

    # Calculate payment due
    invoice_date = datetime.strptime(invoice_data['date'], '%Y-%m-%d')
    due_date = datetime.strptime(invoice_data['due_date'], '%Y-%m-%d')
    days_until_due = (due_date - invoice_date).days

    if days_until_due == 0:
        payment_due_text = "Payment is due today."
    elif days_until_due == 1:
        payment_due_text = "Payment is due tomorrow."
    elif days_until_due > 1:
        payment_due_text = f"Payment is due within {days_until_due} days."
    else:
        payment_due_text = "Payment is overdue."

    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(payment_due_text, styles['Center']))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/create-invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        # Process form data
        invoice_data = {
            'invoice_name': request.form['invoice_name'],
            'invoice_number': format_invoice_number(request.form['invoice_number']),
            'date': request.form['date'],
            'due_date': request.form['due_date'],
            'business_name': request.form['business_name'],
            'business_address': request.form['business_address'],
            'business_phone': request.form['business_phone'],
            'business_email': request.form['business_email'],
            'client_name': request.form['client_name'],
            'client_email': request.form['client_email'],
            'client_address': request.form['client_address'],
            'bank_name': request.form['bank_name'],
            'account_name': request.form['account_name'],
            'bic': request.form['bic'],
            'iban': request.form['iban'],
            'items': [],
            'subtotal': 0,
            'tax_rate': float(request.form['tax_rate']),
            'tax': 0,
            'total': 0,
            'currency': request.form['currency'],
            'logo': None
        }

        # Process logo
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and allowed_file(logo.filename):
                filename = secure_filename(logo.filename)
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logo.save(logo_path)
                invoice_data['logo'] = logo_path
            else:
                invoice_data['logo'] = None
        else:
            invoice_data['logo'] = None

        # Process items
        i = 1
        while f'item_description_{i}' in request.form:
            item = {
                'description': request.form[f'item_description_{i}'],
                'quantity': int(request.form[f'item_quantity_{i}']),
                'price': float(request.form[f'item_price_{i}']),
                'amount': 0
            }
            item['amount'] = item['quantity'] * item['price']
            invoice_data['items'].append(item)
            invoice_data['subtotal'] += item['amount']
            i += 1

        # Calculate totals
        invoice_data['tax'] = invoice_data['subtotal'] * (invoice_data['tax_rate'] / 100)
        invoice_data['total'] = invoice_data['subtotal'] + invoice_data['tax']

        # Generate PDF
        pdf_buffer = create_pdf(invoice_data)
        
        # Generate filename based on invoice name and number
        filename = f"invoice_{invoice_data['invoice_name'].replace(' ', '_')}_{invoice_data['invoice_number']}.pdf"

        return send_file(pdf_buffer, download_name=filename, as_attachment=True, mimetype='application/pdf')

    return render_template('invoice.html')

if __name__ == '__main__':
    app.run(debug=True)
