from django import forms

class FileForm(forms.Form):
    title=forms.CharField(max_length=300)
    file=forms.FileField()

class RegisterForm(forms.Form):
    name=forms.CharField(max_length=255)
    email=forms.EmailField(max_length=255)
    password=forms.IntegerField()

class ShareForm(forms.Form):
    email=forms.EmailField(max_length=255)