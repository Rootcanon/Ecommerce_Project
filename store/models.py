from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import User

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=150)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name",]

    def get_absolute_url(self):
        return reverse("store:category_products", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(help_text="Plain text – no HTML or images")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text="Show in catalog?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Auto-generates unique slug on creation. Same pattern as Blog_Project's Post."""
        if not self.pk:
            base = slugify(self.title)
            slug = base
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def primary_image(self):
        """Return the primary image, or the first image, or None."""
        return self.images.filter(is_primary=True).first() or self.images.first()

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/%Y/%m/%d/")
    alt_text = models.CharField(max_length=125, blank=True)
    is_primary = models.BooleanField(
        default=False, help_text="Used as catalog thumbnail")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "is_primary"],
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_product",
            )
        ]

    def save(self, *args, **kwargs):
        """Auto-unmark any other primary image for this product"""
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def validate_constraints(self, exclude=None):
        """
        Skip the unique_primary_image_per_product constraint during form validation.
        The save() method enforces this by auto-unmarking the old primary image.
        The database-level UniqueConstraint still catches race conditions.
        """
        if exclude is None:
            exclude = set()
        else:
            exclude = set(exclude)
        # Exclude 'is_primary' so the UniqueConstraint check is skipped during
        # form validation — the save() override handles it correctly
        exclude.add('is_primary')
        super().validate_constraints(exclude=exclude)

    def __str__(self):
        return f"Image for {self.product.title}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "p", "Pending"
        PAID = "P", "Paid"
        SHIPPED = "S", "Shipped"
        CANCEL = "C", "Cancelled"

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(max_length=254)
    state = models.CharField(
        choices=Status, default=Status.PENDING, max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()

    class Meta:
        verbose_name_plural = "orders"
        ordering = ["created_at",]

    def __str__(self):
        if self.user:
            return f"{self.user} - {self.total} | {self.created_at} - {self.state}"
        else:
            return f"anonymous - {self.total} | {self.created_at} - {self.state}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.order}. {self.product} {self.quantity} | {self.line_total}"
