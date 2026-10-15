from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage
# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "product_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "image_thumbnail", "alt_text", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("product__title", "alt_text")

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:3px;" />',
                obj.image.url,
            )
        return "No image"
    image_thumbnail.short_description = "Preview"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_primary")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title", "price", "stock_quantity", "is_active",
        "category", "created_at", "image_thumbnail",
    )
    list_filter = ("is_active", "category", "created_at")
    search_fields = ("title", "description")
    list_editable = ("is_active", "price", "stock_quantity")
    list_per_page = 25
    inlines = [ProductImageInline]
    actions = ["mark_active", "mark_inactive", "increase_stock"]

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} product(s) marked as active")
    mark_active.short_description = "Mark selected products as active"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} product(s) marked as inactive")
    mark_inactive.short_description = "Mark selected products as inactive"

    def increase_stock(self, request, queryset):
        for product in queryset:
            product.stock_quantity += 10
            product.save(update_fields=["stock_quantity"])
        self.message_user(request, f"Added 10 units to each selected product")
    increase_stock.short_description = "Increase stock by 10 for selected products"

    def image_thumbnail(self, obj):
        img = obj.primary_image()
        if img and img.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:3px;" />',
                img.image.url,
            )
        return "No image"
    image_thumbnail.short_description = "Preview"
