import six
import warnings

from django.contrib import admin, auth
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.test import TestCase
from django.test.client import RequestFactory

class AdminSiteSmokeTest(TestCase):
    admin_sites = None
    
    def setUp(self):
        super(AdminSiteSmokeTest, self).setUp()
        
        self.superuser = auth.get_user_model().objects.create_superuser('testuser', 'testuser@example.com', 'foo')
        
        self.factory = RequestFactory()
        
        if not self.admin_sites:
            self.admin_sites = admin.site._registry.items()
        
        try:
            admin.autodiscover()
        except:
            pass
    
    def get_request(self):
        request = self.factory.get('/')
        request.user = self.superuser
        return request
    
    def test_specified_fields(self):
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
        
        def strip_minus(attr, val):
            if attr in strip_minus_attrs and val[0] == '-':
                val = val[1:]
            return val
        
        for model, model_admin in self.admin_sites:
            attr_set = []
            
            for attr in iter_attributes:
                attr_set += [strip_minus(attr, a) for a in getattr(model_admin, attr)]
            
            for attr in iter_or_falsy_attributes:
                attrs = getattr(model_admin, attr, None)
                
                if isinstance(attrs, list) or isinstance(attrs, tuple):
                    attr_set += [strip_minus(attr, a) for a in attrs]
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                declared_fieldsets = getattr(model_admin, 'declared_fieldsets', None)
            declared_fieldsets = declared_fieldsets or []
            
            for fieldset in declared_fieldsets:
                for attr in fieldset[1]['fields']:
                    if isinstance(attr, list) or isinstance(attr, tuple):
                        attr_set += [strip_minus(fieldset, a) for a in attr]
                    else:
                        attr_set.append(attr)
            
            attr_set = set(attr_set)
            
            for attr in single_attributes:
                val = getattr(model_admin, attr, None)
                
                if val:
                    attr_set.add(strip_minus(attr, val))
            
            # FIXME: not all attributes can be used everywhere (e.g. you can't use
            # list_filter with a form field). This will have to be fixed later.
            model_field_names = frozenset(model._meta.get_all_field_names())
            form_field_names = frozenset(getattr(model_admin.form, 'base_fields', []))
            
            model_instance = model()
            
            for attr in attr_set:
                # for now we'll just check attributes, not strings
                if not isinstance(attr, six.string_types):
                    continue
                
                # don't split attributes that start with underscores (such as __str__)
                if attr[0] != '_':
                    attrs = attr.split('__')
                    attr = attrs[0]
                else:
                    attrs = [attr]
                
                has_model_field = attr in model_field_names
                has_form_field = attr in form_field_names
                has_model_class_attr = hasattr(model_instance.__class__, attr)
                has_admin_attr = hasattr(model_admin, attr)
                
                try:
                    has_model_attr = hasattr(model_instance, attr)
                except (ValueError, ObjectDoesNotExist):
                    has_model_attr = attr in model_instance.__dict__
                
                has_field_or_attr = has_model_field or has_form_field or has_model_attr or has_admin_attr or has_model_class_attr
                
                self.assertTrue(has_field_or_attr, '%s not found on %s (%s)' % (attr, model, model_admin,))
    
    def test_queryset(self):
        request = self.get_request()
        
        #TODO: use model_mommy to generate a few instances to query against
        for model, model_admin in self.admin_sites:
            # make sure no errors happen here
            if hasattr(model_admin, 'queryset'):
                qs = list(model_admin.queryset(request))
            if hasattr(model_admin, 'get_queryset'):
                qs = list(model_admin.get_queryset(request))
    
    def test_get_absolute_url(self):
        for model, model_admin in self.admin_sites:
            # make sure no errors happen here
            if hasattr(model, 'get_absolute_url'):
                url = model(id=1).get_absolute_url()
    
    def test_changelist_view(self):
        request = self.get_request()
        
        for model, model_admin in self.admin_sites:
            # make sure no errors happen here
            model_admin.changelist_view(request)
    
    def test_add_view(self):
        request = self.get_request()
        
        for model, model_admin in self.admin_sites:
            # make sure no errors happen here
            try:
                model_admin.add_view(request)
            except PermissionDenied:
                # this error is commonly raised by ModelAdmins that don't allow adding.
                pass

