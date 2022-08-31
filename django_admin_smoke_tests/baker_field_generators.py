# This file contain model_bakery field genrators for field types that
# can be found in various Django apps.
# TODO: this should be moved to the apps where the field defined.
import shutil
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from model_bakery import baker


def gen_phonenumber():
    return "123456789"


def gen_datetime():
    return timezone.now()


def gen_avatar():
    shutil.copyfile(
        "./blenderhub/apps/assets/test_files/test.jpg",
        f"{settings.MEDIA_ROOT}/test_image",
    )
    return "test_image"


def gen_json():
    return "{}"


def gen_money():
    from djmoney.money import Money

    return Money(Decimal(100), "USD")


generator_params_list = [
    ("phonenumber_field.modelfields.PhoneNumberField", gen_phonenumber),
    ("django_extensions.db.fields.ModificationDateTimeField", gen_datetime),
    ("django_extensions.db.fields.CreationDateTimeField", gen_datetime),
    ("avatar.models.AvatarField", gen_avatar),
    ("jsonfield.fields.JSONField", gen_json),
    ("djmoney.models.fields.MoneyField", gen_money),
]

for generator_params in generator_params_list:
    try:
        baker.generators.add(*generator_params)
    except ModuleNotFoundError:
        pass
