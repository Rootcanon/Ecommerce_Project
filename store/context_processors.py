from .cart import Cart


def cart_item_count(request):
    return {'cart_obj': Cart(request)}
