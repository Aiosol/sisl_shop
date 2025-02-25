from django import forms
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.db import IntegrityError
from django.utils.html import format_html
from django.template.response import TemplateResponse

from .models import (
    Category, Banner, Brand, Product, Quotation, QuotationLine,
    # OrderStatus is defined in models.py
)

###############################################
# CATEGORY, BANNER, BRAND, & PRODUCT ADMIN
###############################################

class SubCategoryInline(admin.TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    inlines = [SubCategoryInline]

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class ProductForm(forms.ModelForm):
    """
    Use this form for any custom validation or auto-filling.
    """
    class Meta:
        model = Product
        fields = '__all__'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = (
        'name',
        'sku',
        'original_price',
        'discounted_price',
        'category',
        'brand',
        'clone_link'
    )
    filter_horizontal = ('related_products', 'compatible_modules')
    fieldsets = (
        ("General Mandatory Fields", {
            'fields': (
                "category",
                "brand",
                "name",
                "description",
                "original_price",
                "discounted_price",
                "sku",
                "image",
                "country_of_origin",
            )
        }),
        ("VFD Fields (optional)", {
            'fields': (
                "rated_output_power",
                "rated_output_current",
                "input_voltage",
                "input_frequency",
                "output_voltage",
                "output_frequency_range",
                "related_products",
            ),
            'classes': ('collapse',),
        }),
        ("PLC Fields (optional)", {
            'fields': (
                "plc_input",
                "plc_output",
                "supply_voltage",
                "output_type",
                "compatible_modules",
            ),
            'classes': ('collapse',),
        }),
        ("HMI Fields (optional)", {
            'fields': (
                "display_device",
                "screen_size",
                "external_dimensions",
                "resolution",
                "display_size",
                "display_color",
                "built_in_interface",
                "compatible_software_package",
                "weight",
            ),
            'classes': ('collapse',),
        }),
        ("SERVO Fields (optional)", {
            'fields': (
                "rated_output",
                "rated_torque",
                "maximum_torque",
                "rated_speed",
                "maximum_speed",
                "power_supply_capacity",
                "power_supply_input",
                "rated_voltage",
                "rated_current",
                "maximum_current",
                "control_method",
                "dynamic_brake",
                "encoder_type",
                "communication",
                "encoder_resolution",
                "servo_motor",
                "servo_amplifier",
                "dimensions",
            ),
            'classes': ('collapse',),
        }),
    )

    change_form_template = "admin/eshop/product/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:product_id>/clone/',
                self.admin_site.admin_view(self.clone_view),
                name='eshop_product_clone'
            ),
        ]
        return custom_urls + urls

    def clone_view(self, request, product_id):
        new_model_name = request.GET.get('model_name', '').strip()
        new_sku = request.GET.get('sku', '').strip()

        if not new_model_name:
            messages.error(request, "Model Name is required to clone the product.")
            return redirect(request.META.get('HTTP_REFERER', 'admin:index'))
        if not new_sku:
            messages.error(request, "SKU is required to clone the product.")
            return redirect(request.META.get('HTTP_REFERER', 'admin:index'))

        if Product.objects.filter(name=new_model_name).exists():
            messages.error(request, f"A product with Model Name '{new_model_name}' already exists.")
            return redirect(request.META.get('HTTP_REFERER', 'admin:index'))

        if Product.objects.filter(sku=new_sku).exists():
            messages.error(request, f"A product with SKU '{new_sku}' already exists.")
            return redirect(request.META.get('HTTP_REFERER', 'admin:index'))

        original_product = get_object_or_404(Product, pk=product_id)
        old_related = original_product.related_products.all()
        old_modules = original_product.compatible_modules.all()

        original_product.pk = None
        original_product.name = new_model_name
        original_product.sku = new_sku

        try:
            original_product.save()
        except IntegrityError as e:
            messages.error(request, f"Integrity error while saving clone: {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', 'admin:index'))

        original_product.related_products.set(old_related)
        original_product.compatible_modules.set(old_modules)

        messages.success(request, f"Product cloned successfully with Model Name '{new_model_name}' and SKU '{new_sku}'.")
        return redirect(f'../../{original_product.pk}/change/')

    def clone_link(self, obj):
        url = f"{obj.pk}/clone/"
        return format_html(
            '<a href="{}" onclick="return promptCloneNameAndSKU(this);">Clone</a>',
            url
        )
    clone_link.short_description = "Clone"

###############################################
# QUOTATION & QUOTATION LINE ADMIN + ORDER MANAGEMENT
###############################################

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'created_at', 'total_amount', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer__username', 'customer__email')
    change_list_template = "admin/eshop/quotation_change_list.html"  # Custom change list template

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('order-management/', self.admin_site.admin_view(self.order_management_view), name='order_management'),
        ]
        return custom_urls + urls

    def order_management_view(self, request):
        orders = Quotation.objects.all().order_by('-created_at')
        status_filter = request.GET.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        context = dict(
            self.admin_site.each_context(request),
            orders=orders,
        )
        return TemplateResponse(request, "admin/order_management.html", context)

@admin.register(QuotationLine)
class QuotationLineAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'product', 'quantity', 'unit_price', 'discount_percent')
