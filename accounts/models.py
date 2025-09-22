# coding=utf-8

import re

from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin


class Institution(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        'Username', max_length=30, unique=True, validators=[
            validators.RegexValidator(
                re.compile('^[\w.@+-]+$'),
                'Enter a valid username. '
                'This value should contain only letters, numbers, and characters: @/./+/-/_ .'
                , 'invalid'
            )
        ], help_text='A short name that will be used to uniquely identify it on the platform'
    )
    name = models.CharField('Name', max_length=100, blank=True)
    email = models.EmailField('E-mail', unique=True)
    is_staff = models.BooleanField('Staff', default=False)
    is_active = models.BooleanField('Ative', default=True)
    date_joined = models.DateTimeField('Joined', auto_now_add=True)


    # news
    is_federated = models.BooleanField('Federation', default=False)
    avatar = models.ImageField('Avatar', default='/static/img/avatars/tenant.png')
    birthdate = models.DateField('Birthday', help_text='Your Birthday', default='1990-01-01')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.name or self.username

    def get_short_name(self):
        return self.name.split(" ")[0] or self.username
