import logging
import warnings
from typing import List

import django
from django.contrib import admin, auth
from django.contrib.admin import SimpleListFilter
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.http.request import QueryDict
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from model_bakery import baker


logger = logging.getLogger(__name__)


def model_path(model):
    return f"{model.__module__}.{model.__name__}"


def for_all_model_admins(fn):
    def test_deco(self):
        modeladmins = self.get_modeladmins()
        for model, model_admin in modeladmins:
            with self.subTest(f"{model_path(model)} {model_admin}"):
                fn(self, model, model_admin)

    return test_deco


def form_data(form, item):
    data = {}
    for field in form.base_fields:
        value = getattr(item, field, None)
        if isinstance(value, FieldFile):
            pass
        elif isinstance(value, Model):
            data[field] = value.pk
        elif value is not None:
            data[field] = value
    return data


class AdminSiteSmokeTestMixin(object):
    modeladmins = None
    exclude_apps: List[str] = []
    exclude_modeladmins: List[str] = []
    recipes_prefix = ""

    single_attributes = ["date_hierarchy"]
    iter_attributes = [
        "filter_horizontal",
        "filter_vertical",
        "list_display",
        "list_display_links",
        "list_editable",
        "list_filter",
        "readonly_fields",
        "search_fields",
    ]
    iter_or_falsy_attributes = [
        "exclude",
        "fields",
        "ordering",
    ]

    strip_minus_attrs = ("ordering",)

    def get_modeladmins(self):
        if not self.modeladmins:
            modeladmins = admin.site._registry.items()
        else:
            modeladmins = self.modeladmins

        modeladmins = [
            (model, model_admin)
            for (model, model_admin) in modeladmins
            if (
                model_admin.__class__ not in self.exclude_modeladmins
                and model._meta.app_label not in self.exclude_apps
            )
        ]
        if getattr(self, "only_models", None):
            modeladmins = [
                (model, model_admin)
                for (model, model_admin) in modeladmins
                if model.__name__ in self.only_models
            ]
        return modeladmins

    def create_superuser(self):
        return auth.get_user_model().objects.create_superuser(
            "testuser", "testuser@example.com", "foo"
        )

    def setUp(self):
        super().setUp()

        self.superuser = self.create_superuser()

        self.factory = RequestFactory()

        admin.autodiscover()

        self.prepare_all_models()

    def get_url(self, model, model_admin):
        return "/"

    def get_request(self, model, model_admin, params=None):
        request = self.factory.get(self.get_url(model, model_admin), params)
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        setattr(request, "_messages", FallbackStorage(request))

        request.user = self.superuser
        return request

    def create_models(self, model, quantity=1):
        """Create models with model_bakery"""
        try:
            return baker.make_recipe(
                f"{self.recipes_prefix}.{model.__name__}",
                _quantity=quantity,
                _create_files=True,
            )
        except (AttributeError, TypeError):
            return baker.make(model, _quantity=quantity, _create_files=True)

    def prepare_models(self, model, quantity=1):
        """Prepare models by model_bakery, if it is not possible, return None"""
        try:
            with override_settings(MPTT_ALLOW_TESTING_GENERATORS=True):
                return self.create_models(model, quantity)
        except Exception as e:
            warning_string = f"Not able to create {model} data."
            logging.exception(e, warning_string)
            warnings.warn(warning_string)

    def prepare_all_models(self):
        """Prepare all models for all modeladmins"""
        for model, model_admin in self.get_modeladmins():
            with transaction.atomic():
                self.prepare_models(model, quantity=5)

    def post_request(self, model, model_admin, post_data={}, **params):
        request = self.factory.post(
            self.get_url(model, model_admin), post_data, **params
        )
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        setattr(request, "_messages", FallbackStorage(request))

        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        return request

    def strip(self, attr, val):
        if attr in self.strip_minus_attrs and val[0] == "-":
            val = val[1:]

        if attr == "search_fields":
            for ch in ["^", "=", "@"]:
                val = val.lstrip(ch)
        return val

    def get_fieldsets(self, model, model_admin):
        request = self.get_request(model, model_admin)
        return model_admin.get_fieldsets(request, obj=model())

    def get_attr_set(self, model, model_admin):
        attr_set = []

        for attr in self.iter_attributes:
            attr_set += [self.strip(attr, a) for a in getattr(model_admin, attr)]

        for attr in self.iter_or_falsy_attributes:
            attrs = getattr(model_admin, attr, None)

            if isinstance(attrs, list) or isinstance(attrs, tuple):
                attr_set += [self.strip(attr, a) for a in attrs]

        for fieldset in self.get_fieldsets(model, model_admin):
            for attr in fieldset[1]["fields"]:
                if isinstance(attr, list) or isinstance(attr, tuple):
                    attr_set += [self.strip(fieldset, a) for a in attr]
                else:
                    attr_set.append(attr)

        attr_set = set(attr_set)

        for attr in self.single_attributes:
            val = getattr(model_admin, attr, None)

            if val:
                attr_set.add(self.strip(attr, val))

        return attr_set

    def has_attr(self, model_instance, model, model_admin, attr):
        # FIXME: not all attributes can be used everywhere (e.g. you can't
        # use list_filter with a form field). This will have to be fixed
        # later.
        model_field_names = frozenset(model._meta.get_fields())
        form_field_names = frozenset(getattr(model_admin.form, "base_fields", []))

        has_model_field = attr in model_field_names
        has_form_field = attr in form_field_names
        has_model_class_attr = hasattr(model_instance.__class__, attr)
        has_admin_attr = hasattr(model_admin, attr)

        try:
            has_model_attr = hasattr(model_instance, attr)
        except (ValueError, ObjectDoesNotExist):
            has_model_attr = attr in model_instance.__dict__

        return (
            has_model_field
            or has_form_field
            or has_model_attr
            or has_admin_attr
            or has_model_class_attr
        )

    @for_all_model_admins
    def test_specified_fields(self, model, model_admin):
        self.specified_fields_func(model, model_admin)

    def specified_fields_func(self, model, model_admin):
        attr_set = self.get_attr_set(model, model_admin)

        instance = model.objects.last()

        if not instance:
            warnings.warn(
                f"No {model_path(model)} data created to test fields on {model_admin}."
            )
            return

        for attr in attr_set:
            # for now we'll just check attributes, not strings
            if not isinstance(attr, str):
                continue

            # don't split attributes that start with underscores (such as
            # __str__)
            if attr[0] != "_":
                attr = attr.split("__")[0]

            attr_variants = [attr, f"{attr}_set"]
            self.assertTrue(
                any(
                    self.has_attr(instance, model, model_admin, att)
                    for att in attr_variants
                ),
                f"Field '{attr}' not found on {model_path(model)} ({model_admin})",
            )

    @for_all_model_admins
    def test_queryset(self, model, model_admin):
        self.queryset_func(model, model_admin)

    def queryset_func(self, model, model_admin):
        request = self.get_request(model, model_admin)

        # make sure no errors happen here
        if hasattr(model_admin, "get_queryset"):
            list(model_admin.get_queryset(request))

    @for_all_model_admins
    def test_get_absolute_url(self, model, model_admin):
        self.get_absolute_url_func(model, model_admin)

    def get_absolute_url_func(self, model, model_admin):
        if hasattr(model, "get_absolute_url"):
            # Use fixture data if it exists
            instance = model.objects.last()
            # Otherwise create a minimal instance
            if not instance:
                instance = model(pk=1)
            # make sure no errors happen here
            instance.get_absolute_url()

    @for_all_model_admins
    def test_changelist_view(self, model, model_admin):
        self.changelist_view_func(model, model_admin)

    def changelist_view_func(self, model, model_admin):
        """Run the changelist_view method on the model admin."""
        request = self.get_request(model, model_admin)

        if not hasattr(
            model_admin, "has_view_permission"  # Django <= 2.0
        ) or model_admin.has_view_permission(request):
            # make sure no errors happen here
            response = model_admin.changelist_view(request)

            if isinstance(response, django.template.response.TemplateResponse):
                response.render()
            self.assertIn(response.status_code, [200, 302])

    @for_all_model_admins
    def test_changelist_filters_view(self, model, model_admin):
        """Try to get various values for list_filter and call the view with them"""
        self.changelist_filters_view_func(model, model_admin)

    def changelist_filters_view_func(self, model, model_admin):
        request = self.get_request(model, model_admin)

        if not hasattr(
            model_admin, "has_view_permission"  # Django <= 2.0
        ) or model_admin.has_view_permission(request):
            for filter in model_admin.list_filter:
                if isinstance(filter, tuple):
                    filter = filter[0]
                if isinstance(filter, str):
                    key = filter
                    value = model.objects.values(filter).first()[filter]
                    filters = [(key, value)]
                elif issubclass(filter, SimpleListFilter):
                    filter_instance = filter(request, [], model, model_admin)
                    key = filter_instance.parameter_name
                    filters = [
                        (key, lookup[0]) for lookup in filter_instance.lookup_choices
                    ]
                for key, value in filters:
                    request = self.get_request(
                        model, model_admin, params=QueryDict(f"{key}={value}")
                    )
                    response = model_admin.changelist_view(request)
                    if isinstance(response, django.template.response.TemplateResponse):
                        response.render()
                    self.assertIn(response.status_code, [200, 302])

    @for_all_model_admins
    def test_changelist_view_search(self, model, model_admin):
        self.changelist_view_search_func(model, model_admin)

    def changelist_view_search_func(self, model, model_admin):
        request = self.get_request(model, model_admin, params=QueryDict("q=test"))

        if model_admin.has_change_permission(request):
            # make sure no errors happen here
            response = model_admin.changelist_view(request)
            if isinstance(response, django.template.response.TemplateResponse):
                response.render()
            self.assertIn(response.status_code, [200, 302])

    @for_all_model_admins
    def test_add_view(self, model, model_admin):
        self.add_view_func(model, model_admin)

    def add_view_func(self, model, model_admin):
        request = self.get_request(model, model_admin)

        if model_admin.has_add_permission(request):
            # make sure no errors happen here
            response = model_admin.add_view(request)
            if isinstance(response, django.template.response.TemplateResponse):
                response.render()
            self.assertIn(response.status_code, [200, 302])

    @for_all_model_admins
    def test_change_view(self, model, model_admin):
        self.change_view_func(model, model_admin)

    def change_view_func(self, model, model_admin):
        item = model.objects.last()
        if not item or model._meta.proxy:
            return
        pk = item.pk
        request = self.get_request(model, model_admin)

        if model_admin.has_change_permission(request):
            response = model_admin.change_view(request, object_id=str(pk))
            if isinstance(response, django.template.response.TemplateResponse):
                # make sure no errors happen here
                response.render()
            self.assertIn(response.status_code, [200, 302])

    @for_all_model_admins
    def test_change_post(self, model, model_admin):
        self.change_post_func(model, model_admin)

    def change_post_func(self, model, model_admin):
        item = model.objects.last()
        if not item:
            return
        if model._meta.proxy:
            return
        pk = item.pk

        # Get form and use it to create POST data
        request = self.post_request(model, model_admin)
        form = model_admin.get_form(request)
        request = self.post_request(model, model_admin, post_data=form_data(form, item))
        if model_admin.has_change_permission(request):
            response = model_admin.change_view(request, object_id=str(pk))
            if isinstance(response, django.template.response.TemplateResponse):
                response.render()
            self.assertIn(response.status_code, [200, 302])


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    pass
