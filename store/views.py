from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView

from .models import Category, Product
# Create your views here.


class ProductListView(ListView):
    # Show all active products — the homepage of the store.
    model = Product
    template_name = "store/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        # Only show active products
        return Product.objects.filter(is_active=True).select_related("category")


class CategoryProductListView(ProductListView):
    # ProductListView but with added category filter
    def get_queryset(self):
        # Find the category by slug from the URL, 404 if not found
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        # Pass the category to the template
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ProductDetailView(DetailView):
    # Show a single product with its images and description.
    model = Product
    template_name = "store/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        # Only active products visible via URL
        return Product.objects.filter(is_active=True).select_related("category").prefetch_related("images")
