class Cart:
    """Session-backed shopping cart.

    Stores items as a dict in the Django session:
        {"<product_pk>": {"product": title, "quantity": N, "price": "19.99"}, ...}

    No model — works for anonymous users (no login required).
    """

    def __init__(self, request):
        """Load the cart from the session, creating an empty one if it doesn't exist."""
        self.session = request.session
        cart = self.session.get("cart")
        if not cart:
            cart = self.session["cart"] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        """Add a product (or increment its quantity) in the session cart."""
        product_id = str(product.pk)
        if product_id not in self.cart:
            self.cart[product_id] = {
                "product": product.title,
                "quantity": quantity,
                # Decimal → str for session serialization
                "price": str(product.price),
            }
        else:
            self.cart[product_id]["quantity"] += quantity
        self.save()

    def remove(self, product):
        """Remove a product entirely from the cart (use for 'remove' button, not decrease)."""
        self.cart.pop(str(product.pk), None)
        self.save()

    def get_total_price(self):
        """Return the total price of all items as a float (sum of qty × unit price)."""
        total_price = 0
        for product in self.cart.values():
            total_price += int(product["quantity"]) * float(product["price"])
        return total_price

    def get_item_count(self):
        """Return the number of unique products in the cart (for navbar badge)."""
        return len(self.cart)

    def save(self):
        """Mark the session as modified so Django persists the changes."""
        self.session.modified = True

    def clear(self):
        """Remove all items from the cart (used on successful purchase)."""
        del self.session["cart"]
        self.session.modified = True

