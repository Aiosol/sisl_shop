from django.db import models
from django.contrib.auth.models import User  # used if Quotation links to user

# Order status choices for managing orders
class OrderStatus(models.TextChoices):
    PENDING = 'P', 'Pending'
    CONFIRMED = 'C', 'Confirmed'
    CANCELED = 'X', 'Canceled'
    DELIVERED = 'D', 'Delivered'

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self',
        related_name='children',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

class Banner(models.Model):
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='banners/', null=True, blank=True)

    def __str__(self):
        return self.title if self.title else "Banner"

class Brand(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='brands/logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    # Mandatory fields
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField("Model Name", max_length=255, unique=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=50, unique=True)
    image = models.ImageField(upload_to='products/')
    country_of_origin = models.CharField(max_length=100)

    # Optional fields
    description = models.TextField(blank=True, null=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Extra technical specification fields
    servo_amplifier = models.CharField(max_length=100, blank=True, null=True)
    supply_voltage = models.CharField(max_length=50, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    resolution = models.CharField(max_length=100, blank=True, null=True)
    output_frequency_range = models.CharField(max_length=100, blank=True, null=True)
    output_voltage = models.CharField(max_length=50, blank=True, null=True)
    compatible_software_package = models.CharField(max_length=100, blank=True, null=True)
    rated_speed = models.CharField(max_length=50, blank=True, null=True)
    external_dimensions = models.CharField(max_length=100, blank=True, null=True)
    input_frequency = models.CharField(max_length=50, blank=True, null=True)
    encoder_resolution = models.CharField(max_length=100, blank=True, null=True)
    rated_output_power = models.CharField(max_length=100, blank=True, null=True)
    communication = models.CharField(max_length=100, blank=True, null=True)
    maximum_speed = models.CharField(max_length=50, blank=True, null=True)
    rated_voltage = models.CharField(max_length=50, blank=True, null=True)
    output_type = models.CharField(max_length=50, blank=True, null=True)
    dynamic_brake = models.CharField(max_length=50, blank=True, null=True)
    plc_input = models.CharField(max_length=50, blank=True, null=True)
    display_device = models.CharField(max_length=100, blank=True, null=True)
    maximum_current = models.CharField(max_length=50, blank=True, null=True)
    control_method = models.CharField(max_length=100, blank=True, null=True)
    servo_motor = models.CharField(max_length=100, blank=True, null=True)
    power_supply_capacity = models.CharField(max_length=50, blank=True, null=True)
    input_voltage = models.CharField(max_length=50, blank=True, null=True)
    built_in_interface = models.CharField(max_length=100, blank=True, null=True)
    rated_current = models.CharField(max_length=50, blank=True, null=True)
    power_supply_input = models.CharField(max_length=50, blank=True, null=True)
    encoder_type = models.CharField(max_length=50, blank=True, null=True)
    display_size = models.CharField(max_length=50, blank=True, null=True)
    rated_torque = models.CharField(max_length=50, blank=True, null=True)
    plc_output = models.CharField(max_length=50, blank=True, null=True)
    rated_output_current = models.CharField(max_length=50, blank=True, null=True)
    screen_size = models.CharField(max_length=50, blank=True, null=True)
    rated_output = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    maximum_torque = models.CharField(max_length=50, blank=True, null=True)
    display_color = models.CharField(max_length=50, blank=True, null=True)

    # ManyToMany relationships
    related_products = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='linked_products'
    )
    compatible_modules = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='plc_or_hmi_compatible'
    )

    def __str__(self):
        return self.name

class Quotation(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Fields for order management:
    order_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=1,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    def __str__(self):
        return f"Quotation #{self.pk} for {self.customer or 'Anonymous'}"

    def compute_total(self):
        total = sum(line.line_total() for line in self.lines.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])

class QuotationLine(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def line_total(self):
        subtotal = self.quantity * self.unit_price
        discount_amount = subtotal * (self.discount_percent / 100)
        return subtotal - discount_amount

    def __str__(self):
        return f"Line {self.pk} in Quotation #{self.quotation.pk}"
