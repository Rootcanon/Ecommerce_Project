from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})


class LoginForm(AuthenticationForm):

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
