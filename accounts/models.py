from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=11, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

