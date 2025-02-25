import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import Category, Banner, Brand, Product, Quotation
from .forms import BrandForm, ProductForm, QuotationHeaderForm, QuotationLineFormSet


def home_view(request):
    categories = Category.objects.filter(parent__isnull=True)
    banner = Banner.objects.first()
    vfd_products = Product.objects.filter(category__name__iexact='VFD').order_by('-id')[:8]
    plc_products = Product.objects.filter(category__name__iexact='PLC').order_by('-id')[:8]
    hmi_products = Product.objects.filter(category__name__iexact='HMI').order_by('-id')[:8]
    return render(request, 'home.html', {
        'categories': categories,
        'banner': banner,
        'vfd_products': vfd_products,
        'plc_products': plc_products,
        'hmi_products': hmi_products,
    })


def product_detail_view(request, sku):
    if not sku or sku.lower() == 'none':
        return redirect('home')
    product = get_object_or_404(Product, sku=sku)
    return render(request, 'product_detail.html', {'product': product})


def fx_series_view(request):
    """
    Placeholder view for FX Series.
    Create a corresponding template 'fx_series.html' as needed.
    """
    return render(request, 'fx_series.html')


def vfd_view(request):
    """
    Placeholder view for VFD products.
    Create a corresponding template 'vfd.html' as needed.
    """
    return render(request, 'vfd.html')


def category_filter_view(request, cat_name):
    """
    Placeholder view that filters products by category.
    Adjust the query and template as required.
    """
    products = Product.objects.filter(category__name__iexact=cat_name)
    return render(request, 'category_filter.html', {
        'cat_name': cat_name,
        'products': products,
    })


def brand_detail_view(request, brand_id):
    """
    Placeholder view for brand detail.
    Create 'brand_detail.html' as needed.
    """
    brand = get_object_or_404(Brand, id=brand_id)
    return render(request, 'brand_detail.html', {'brand': brand})


def search_view(request):
    """
    Placeholder view for search results.
    Adjust the query and template as needed.
    """
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query) if query else []
    return render(request, 'search.html', {
        'query': query,
        'products': products,
    })


@login_required
def ask_for_discount_view(request, sku):
    """
    Handles the discount request form:
      - Validates and saves the quotation header and line items.
      - Automatically generates order number and subject.
      - Generates a professional PDF of the quotation.
      - Attaches the PDF to an email and sends it.
      - Renders a confirmation page that includes a download link for the PDF.
    """
    product = get_object_or_404(Product, sku=sku)

    if request.method == 'POST':
        header_form = QuotationHeaderForm(request.POST)
        new_quote = Quotation()

        if header_form.is_valid():
            new_quote = header_form.save(commit=False)
            new_quote.customer = request.user

            # Auto-generate order number and subject
            generated_order_number = "ORD" + timezone.now().strftime("%Y%m%d%H%M%S")
            new_quote.order_number = generated_order_number
            new_quote.subject = f"Discount Request for order no: {generated_order_number} on {timezone.now().strftime('%Y-%m-%d')}"

            formset = QuotationLineFormSet(request.POST, instance=new_quote, prefix='lines')
            if formset.is_valid():
                new_quote.save()
                formset.save()
                new_quote.compute_total()

                # 1) Generate the PDF file
                pdf_file_path, pdf_file_name = generate_pdf_file(new_quote)

                # 2) Build a public URL for the PDF for download
                shareable_file_url = os.path.join(
                    settings.MEDIA_URL,
                    "quotations",
                    pdf_file_name
                )

                # 3) Prepare an email with the PDF attached
                subject_email = f"Discount request for {product.name}"
                body = (
                    f"User {request.user} requested a multi-line discount.\n"
                    f"Quotation ID: {new_quote.pk}\n\n"
                    f"Please find the attached PDF for full details."
                )
                email = EmailMessage(
                    subject=subject_email,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.DEFAULT_FROM_EMAIL],  # Adjust recipient as needed
                )
                email.attach_file(pdf_file_path)
                email.send()

                messages.success(request,
                    f"Your discount request for Order No: {new_quote.order_number} has been successfully submitted! "
                    "A professional PDF file has also been emailed."
                )
                
                return render(request, 'discount_submitted.html', {
                    'product': product,
                    'quotation': new_quote,
                    'shareable_file_url': shareable_file_url,
                })
        else:
            formset = QuotationLineFormSet(request.POST, prefix='lines')
        # On a POST failure, pass a dummy quotation to avoid template lookup errors.
        dummy_quote = Quotation()
        dummy_quote.order_number = ""
        return render(request, 'ask_for_discount.html', {
            'header_form': header_form,
            'formset': formset,
            'product': product,
            'quotation': dummy_quote,
        })
    else:
        header_form = QuotationHeaderForm()
        new_quote = Quotation()
        new_quote.order_number = ""
        formset = QuotationLineFormSet(
            instance=new_quote,
            prefix='lines',
            initial=[{
                'product': product.pk,
                'quantity': 1,
                'unit_price': product.original_price,
                'discount_percent': 0
            }]
        )
        return render(request, 'ask_for_discount.html', {
            'header_form': header_form,
            'formset': formset,
            'product': product,
            'quotation': new_quote,
        })


def generate_pdf_file(quotation):
    """
    Generate a professional PDF file with quotation details in a table layout.
    The PDF is saved under MEDIA_ROOT/quotations.
    Returns a tuple: (pdf_file_path, pdf_file_name).
    """
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    file_name = f"quotation_{quotation.pk}_{timestamp}.pdf"
    quotations_dir = os.path.join(settings.MEDIA_ROOT, "quotations")
    os.makedirs(quotations_dir, exist_ok=True)
    file_path = os.path.join(quotations_dir, file_name)

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    story.append(Paragraph("Professional Quotation Details", styles['Title']))
    story.append(Spacer(1, 12))

    # Header Table
    header_data = [
        ["Field", "Value"],
        ["Quotation ID", str(quotation.pk)],
        ["Customer", str(quotation.customer)],
        ["Notes", quotation.notes or "N/A"],
    ]
    header_table = Table(header_data, colWidths=[120, 380])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 24))

    # Line Items Table
    line_items_data = [
        ["Product", "Description", "Quantity", "Unit Price", "Discount (%)", "Line Total"]
    ]
    for line in quotation.lines.all():
        line_total = line.line_total()
        line_items_data.append([
            line.product.name,
            line.description or "",
            str(line.quantity),
            f"{line.unit_price:.2f}",
            f"{line.discount_percent:.2f}",
            f"{line_total:.2f}"
        ])
    # Total row
    line_items_data.append(["", "", "", "", "Total Amount", f"{quotation.total_amount:.2f}"])

    items_table = Table(line_items_data, colWidths=[100, 200, 60, 80, 80, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))

    doc.build(story)
    return file_path, file_name


def quotation_detail_view(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    return render(request, 'quotation_detail.html', {
        'quotation': quotation,
        'lines': quotation.lines.all(),
    })


@staff_member_required
def order_management_view(request):
    """
    A simple order management dashboard for staff users.
    Filters orders by status if provided.
    """
    orders = Quotation.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    context = {
        'orders': orders,
    }
    return TemplateResponse(request, 'order_management.html', context)
