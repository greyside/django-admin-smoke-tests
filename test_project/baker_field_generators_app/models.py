from avatar.models import AvatarField
from django.db import models
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from djmoney.models.fields import MoneyField
from jsonfield.fields import JSONField
from phonenumber_field.modelfields import PhoneNumberField


class BakerFields(models.Model):
    phone_number = PhoneNumberField(blank=False, null=False)
    modified = ModificationDateTimeField(blank=False, null=False)
    created = CreationDateTimeField(blank=False, null=False)
    avatar = AvatarField(blank=False, null=False, default=None)
    json = JSONField(blank=False, null=False)
    money = MoneyField(blank=False, null=False, max_digits=5)
