import six

from django.contrib import admin, auth
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.test import TestCase
from django.test.client import RequestFactory
import sys


def for_all_model_admins(fn):
    def test_deco(self):
        for model, model_admin in self.modeladmins:
            if model._meta.app_label in self.exclude_apps:
                continue
            try:
                fn(self, model, model_admin)
            except Exception:
                msg = ("Above exception occured while running test "
                       "'%s' on modeladmin %s (%s)" %
                       (fn.__name__, model_admin, model.__name__))
                if hasattr(Exception, 'with_traceback'):  # Python 3.x only
                    raise Exception(msg).with_traceback(sys.exc_info()[2])
                else:
                    print msg
                    raise
    return test_deco


class AdminSiteSmokeTestMixin(object):
    modeladmins = None
    exclude_apps = []
    fixtures = ['django_admin_smoke_tests']

    single_attributes = ['date_hierarchy']
    iter_attributes = [
        'filter_horizontal',
        'filter_vertical',
        'list_display',
        'list_display_links',
        'list_editable',
        'list_filter',
        'readonly_fields',
        'search_fields',
    ]
    iter_or_falsy_attributes = [
        'exclude',
        'fields',
        'ordering',
    ]

    strip_minus_attrs = ('ordering',)

    def setUp(self):
        super(AdminSiteSmokeTestMixin, self).setUp()

        self.superuser = auth.get_user_model().objects.create_superuser(
            'testuser', 'testuser@example.com', 'foo')

        self.factory = RequestFactory()

        if not self.modeladmins:
            self.modeladmins = admin.site._registry.items()

        try:
            admin.autodiscover()
        except:
            pass

    def get_request(self):
        request = self.factory.get('/')
        request.user = self.superuser
        return request

    def strip_minus(self, attr, val):
        if attr in self.strip_minus_attrs and val[0] == '-':
            val = val[1:]
        return val

    def get_fieldsets(self, model, model_admin):
        request = self.get_request()
        try:
            return model_admin.get_fieldsets(request, obj=model())
        except AttributeError:
            return model_admin.declared_fieldsets

    def get_attr_set(self, model, model_admin):
        attr_set = []

        for attr in self.iter_attributes:
            attr_set += [
                self.strip_minus(attr, a)
                for a in getattr(model_admin, attr)
            ]

        for attr in self.iter_or_falsy_attributes:
            attrs = getattr(model_admin, attr, None)

            if isinstance(attrs, list) or isinstance(attrs, tuple):
                attr_set += [self.strip_minus(attr, a) for a in attrs]

        for fieldset in self.get_fieldsets(model, model_admin):
            for attr in fieldset[1]['fields']:
                if isinstance(attr, list) or isinstance(attr, tuple):
                    attr_set += [self.strip_minus(fieldset, a)
                        for a in attr]
                else:
                    attr_set.append(attr)

        attr_set = set(attr_set)

        for attr in self.single_attributes:
            val = getattr(model_admin, attr, None)

            if val:
                attr_set.add(self.strip_minus(attr, val))

        return attr_set

    @for_all_model_admins
    def test_specified_fields(self, model, model_admin):
        attr_set = self.get_attr_set(model, model_admin)

        # FIXME: not all attributes can be used everywhere (e.g. you can't
        # use list_filter with a form field). This will have to be fixed
        # later.
        try:
            model_field_names = frozenset(model._meta.get_fields())
        except AttributeError:  # Django<1.10
            model_field_names = frozenset(
                model._meta.get_all_field_names()
            )
        form_field_names = frozenset(getattr(model_admin.form,
            'base_fields', []))

        model_instance = model()

        for attr in attr_set:
            # for now we'll just check attributes, not strings
            if not isinstance(attr, six.string_types):
                continue

            # don't split attributes that start with underscores (such as
            # __str__)
            if attr[0] != '_':
                attr = attr.split('__')[0]

            has_model_field = attr in model_field_names
            has_form_field = attr in form_field_names
            has_model_class_attr = hasattr(model_instance.__class__, attr)
            has_admin_attr = hasattr(model_admin, attr)

            try:
                has_model_attr = hasattr(model_instance, attr)
            except (ValueError, ObjectDoesNotExist):
                has_model_attr = attr in model_instance.__dict__

            has_field_or_attr = has_model_field or has_form_field or\
                has_model_attr or has_admin_attr or has_model_class_attr

            self.assertTrue(has_field_or_attr, '%s not found on %s (%s)' %
                (attr, model, model_admin,))

    @for_all_model_admins
    def test_queryset(self, model, model_admin):
        request = self.get_request()

        # TODO: use model_mommy to generate a few instances to query against
        # make sure no errors happen here
        if hasattr(model_admin, 'queryset'):
            list(model_admin.queryset(request))
        if hasattr(model_admin, 'get_queryset'):
            list(model_admin.get_queryset(request))

    @for_all_model_admins
    def test_get_absolute_url(self, model, model_admin):
        if hasattr(model, 'get_absolute_url'):
            # Use fixture data if it exists
            instance = model.objects.first()
            # Otherwise create a minimal instance
            if not instance:
                instance = model(pk=1)
            # make sure no errors happen here
            instance.get_absolute_url()

    @for_all_model_admins
    def test_changelist_view(self, model, model_admin):
        request = self.get_request()

        # make sure no errors happen here
        response = model_admin.changelist_view(request)
        self.assertEqual(response.status_code, 200)

    @for_all_model_admins
    def test_add_view(self, model, model_admin):
        request = self.get_request()

        # make sure no errors happen here
        try:
            response = model_admin.add_view(request)
            self.assertEqual(response.status_code, 200)
        except PermissionDenied:
            # this error is commonly raised by ModelAdmins that don't allow
            # adding.
            pass


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    pass
