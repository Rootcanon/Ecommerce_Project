from django.urls import path
from django.contrib.auth import views as auth_views

from .views import RegisterView, MyOrdersView, OrderDetailView
from .forms import LoginForm

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html",
         authentication_form=LoginForm,), name="login"),
    path("orders/", MyOrdersView.as_view(), name="order_list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout")
]
