from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import User, Patient

from random import choices



# from django.contrib.auth import get_user_model
# User = get_user_model()


# class CustomUserCreationForm(UserCreationForm):

#     class Meta(UserCreationForm.Meta):
#         model = User
#         fields = UserCreationForm.Meta.fields 

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        max_length=100,
        required = True,
    )
    first_name = forms.CharField(
        max_length=100,
        required = True,
    )
    last_name = forms.CharField(
        max_length=100,
        required = True,
    )
    password1 = forms.CharField(
        required = True,
    )
    password2 = forms.CharField(
        required = True,
    )
    # username = forms.RegexField(label=("Email"), max_length=30, regex=r'^[\w.@+-]+$',
    #     help_text = ("Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only."),
    #     error_messages = {'invalid': ("This value may contain only letters, numbers and @/./+/-/_ characters.")})

    # username = forms.EmailField(
    #     label=("Emaifl"),
    #     max_length=100,
    #     required = False,)

    # email = username

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

