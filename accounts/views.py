from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from .forms import RegisterForm
from store.models import Order
# Create your views here.


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        messages.success(self.request, "Account created — please log in.")
        return super().form_valid(form)


class MyOrdersView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")
    context_object_name = "orders"
    template_name = "accounts/order_list.html"


class OrderDetailView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("orderitem_set")
    template_name = "accounts/order_detail.html"
    context_object_name = "order"
