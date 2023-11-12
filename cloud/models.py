from django.db import models
from django.utils import timezone
# Create your models here.

class User(models.Model):
    name=models.CharField(max_length=255)
    email=models.EmailField(max_length=300)
    password=models.BinaryField()

class Files(models.Model):
    title=models.CharField(max_length=300)
    file=models.BinaryField()
    name=models.CharField()
    size=models.IntegerField()
    file_name=models.CharField()
    charset=models.CharField(null=True)
    content_type=models.CharField()
    created_by=models.ForeignKey(User, on_delete=models.CASCADE)

class Shared(models.Model):
    shared_user=models.ForeignKey(User, on_delete=models.CASCADE)
    shared_file=models.ForeignKey(Files, on_delete=models.CASCADE)
    shared_date=models.DateTimeField(auto_now_add=True)