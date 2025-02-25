from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms.models import ModelChoiceIteratorValue

from .models import Brand, Product, Quotation, QuotationLine

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'logo', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['brand', 'name', 'description', 'original_price', 'sku', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError('Only JPEG, PNG, or GIF files are allowed.')
        return image

# Custom widget to attach data-price for each product option, enabling auto-fill of Unit Price.
class ProductSelectWidget(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        # If value is a ModelChoiceIteratorValue, extract its underlying value.
        if isinstance(value, ModelChoiceIteratorValue):
            value = value.value
        option_dict = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value:
            try:
                product = self.choices.queryset.get(pk=value)
                option_dict['attrs']['data-price'] = str(product.original_price)
            except Product.DoesNotExist:
                pass
        return option_dict

#
# QuotationHeaderForm now includes 'subject' as a TextArea,
# plus 'notes' (also a TextArea).
#
class QuotationHeaderForm(forms.ModelForm):
    subject = forms.CharField(
        required=False,
        label="Subject",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    class Meta:
        model = Quotation
        fields = ['subject', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        }

class QuotationLineForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=ProductSelectWidget(attrs={'class': 'form-select product-select'})
    )

    class Meta:
        model = QuotationLine
        fields = ['product', 'description', 'quantity', 'unit_price', 'discount_percent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['quantity'].widget.attrs.update({'class': 'form-control quantity-input'})
        self.fields['unit_price'].widget.attrs.update({'class': 'form-control unit-price-input'})
        self.fields['discount_percent'].widget.attrs.update({'class': 'form-control discount-input'})

# Inline formset linking Quotation to QuotationLine.
QuotationLineFormSet = inlineformset_factory(
    Quotation,
    QuotationLine,
    form=QuotationLineForm,
    extra=1,
    can_delete=True
)
