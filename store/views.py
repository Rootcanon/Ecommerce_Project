from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from django.views import View
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.contrib import messages
from decimal import Decimal

from .cart import Cart
from .models import Category, Product, Order, OrderItem
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


class CartView(View):
    def get(self, request):
        cart = Cart(request)

    # Fetch all Product objects for items in the session cart
        product_ids = [int(pid) for pid in cart.cart.keys()]
        products = Product.objects.filter(pk__in=product_ids)

    # Build list of dicts: {product, quantity, price, total}
        cart_items = []
        for product in products:
            qty = cart.cart[str(product.pk)]["quantity"]
            price = float(cart.cart[str(product.pk)]["price"])
            cart_items.append({
                "product": product,
                "quantity": qty,
                "price": price,
                "total": qty * price,
            })

    # Render the cart on url:"store/cart_detail.html"
        return render(request, "store/cart_detail.html", {
            "cart_items": cart_items,
            "total_price": cart.get_total_price(),
            "item_count": cart.get_item_count(),
        })

    def post(self, request):
        cart = Cart(request)

        if "remove" in request.POST:
            product_id = request.POST.get("remove")
            product = get_object_or_404(Product, pk=product_id)
            cart.remove(product)
            return redirect("store:cart_detail")

        action = request.POST.get("action")

        if not action:
            return redirect("store:cart_detail")

        if action == "add":
            product_id = request.POST.get("product_id")
            if not product_id:
                return redirect("store:product_list")
            product = get_object_or_404(Product, pk=product_id)
            qty = max(int(request.POST.get("quantity", 1)), 1)
            qty = min(qty, product.stock_quantity)
            cart.add(product, qty)
            return redirect("store:product_detail", slug=product.slug)

        elif action == "save":
            for key, value in request.POST.items():
                if key.startswith("qty_"):
                    product_pk = key.replace("qty_", "")
                    new_qty = max(int(value), 1)
                    target_product = get_object_or_404(Product, pk=product_pk)
                    # cap at stock
                    new_qty = min(new_qty, target_product.stock_quantity)

                    product_id_str = str(target_product.pk)
                    if product_id_str in cart.cart:
                        cart.cart[product_id_str]["quantity"] = new_qty
            cart.save()

        elif action == "purchase":
            return redirect("store:checkout")

    # Redirect the url:"store:cart_detail"
        return redirect("store:cart_detail")


class CheckoutView(View):

    def get(self, request):
        cart = Cart(request)
        if not cart.cart:
            return redirect("store:product_list")

        product_ids = [int(pid) for pid in cart.cart.keys()]
        products = Product.objects.filter(pk__in=product_ids)

        cart_items = []
        for product in products:
            qty = cart.cart[str(product.pk)]["quantity"]
            price = float(cart.cart[str(product.pk)]["price"])
            cart_items.append({
                "product": product,
                "quantity": qty,
                "price": price,
                "total": qty * price,
            })

        return render(request, "store/checkout.html", {
            "cart_items": cart_items,
            "total_price": cart.get_total_price(),
            "item_count": cart.get_item_count(),
        })

    def post(self, request):
        cart = Cart(request)
        if not cart.cart:
            return redirect("store:product_list")

        email = request.POST.get("email", "").strip()
        shipping_address = request.POST.get("shipping_address", "").strip()

        if not email or not shipping_address:
            messages.error(request, "Email and shipping address are required.")
            return redirect("store:checkout")

        product_ids = [int(pid) for pid in cart.cart.keys()]
        products = Product.objects.filter(pk__in=product_ids)
        for product in products:
            qty = cart.cart[str(product.pk)]["quantity"]
            if qty > product.stock_quantity:
                messages.error(
                    request, f"Not enough stock for {product.title}. Available: {product.stock_quantity}.")
                return redirect("store:cart_detail")

        order = Order.objects.create(
            email=email,
            shipping_address=shipping_address,
            total=cart.get_total_price(),
            user=request.user if request.user.is_authenticated else None,
        )

        order_items = []
        for product in products:
            product_price_from_cart = Decimal(
                cart.cart[str(product.pk)]["price"])
            qty = cart.cart[str(product.pk)]["quantity"]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=product_price_from_cart
            )
            product.stock_quantity -= qty
            product.save(update_fields=["stock_quantity"])

            line = f"- {product.title} x {qty} @ {product_price_from_cart}$"
            order_items.append(line)

        items_text = "\n".join(order_items)
        message = f"""
        Thank you for your order!

        Order Number: {order.pk}
        Order Total: {order.total}$
        
        Items Purchased:
            {items_text}
        
        Shipping Address:
            {order.shipping_address}

        We appreciate your business and hope you enjoy your purchase!
        """

        send_mail(
            subject="Your order confirmation from My Store",
            message=message,
            from_email="orders@yourstore.com",
            recipient_list=[email])

        cart.clear()

        return redirect("store:order_confirmation", pk=order.pk)


class OrderConfirmationView(DetailView):
    model = Order
    # tell me if i should change the name
    template_name = "store/order_confirmation.html"
    context_object_name = "order"
