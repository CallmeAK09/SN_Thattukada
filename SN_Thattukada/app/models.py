from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Item(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Item Name")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Price"
    )

    def __str__(self):
        return f"{self.name} - ₹{self.price}"

