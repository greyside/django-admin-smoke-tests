import datetime

from django.db.models.fields.files import ImageFieldFile
from django.test import TestCase
from djmoney.money import Money
from freezegun import freeze_time
from model_bakery import baker

from django_admin_smoke_tests import baker_field_generators  # noqa: F401


@freeze_time("2020-01-01")
class BakerFieldGeneratorTests(TestCase):
    def test_baker_field_generators(self):
        baker_fields = baker.make("BakerFields", _fill_optional=True)
        self.assertEquals(baker_fields.phone_number, "123456789")
        self.assertEquals(
            baker_fields.modified,
            datetime.datetime(2020, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEquals(
            baker_fields.created,
            datetime.datetime(2020, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
        )
        # TODO: this doesn't really test avatar generator
        self.assertEquals(
            baker_fields.avatar, ImageFieldFile(baker_fields, baker_fields.avatar, None)
        )
        self.assertEquals(baker_fields.json, "{}")
        self.assertEquals(baker_fields.money, Money(100, "USD"))
