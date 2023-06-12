from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель создания юзера для бд."""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    username = models.CharField(
        'Username',
        max_length=150,
        unique=True,
        null=False,
        blank=False
    )
    email = models.EmailField(
        'Email address',
        max_length=254,
        blank=False,
        null=False,
        unique=True
    )
    first_name = models.CharField(
        'First name',
        max_length=150,
        blank=False
    )
    last_name = models.CharField(
        'Last name',
        max_length=150,
        blank=False
    )
    password = models.CharField('Password', max_length=150)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['pk']

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель юзера и автора"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriber",
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]
