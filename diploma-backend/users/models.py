from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    fullName = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'auth_user'
        app_label = 'users'
