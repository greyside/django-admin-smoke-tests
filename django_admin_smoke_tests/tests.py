from django.contrib import admin
from django.test import TestCase
from django.test.client import RequestFactory

class AdminSiteSmokeTest(TestCase):
    def setUp(self):
        super(AdminSiteSmokeTest, self).setUp()
        
        self.factory = RequestFactory()
        
        try:
            admin.autodiscover()
        except:
            pass
    
    def test__check_specified_fields(self):
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
        
        for model, model_admin in admin.site._registry.items():
            attr_set = []
            
            for attr in iter_attributes:
                attr_set += getattr(model_admin, attr)
            
            for attr in iter_or_falsy_attributes:
                attrs = getattr(model_admin, attr, None)
                
                if isinstance(attrs, list) or isinstance(attrs, tuple):
                    attr_set += attrs
            
            declared_fieldsets = model_admin.declared_fieldsets or []
            
            for fieldset in declared_fieldsets:
                for field in fieldset[1]['fields']:
                    if isinstance(field, list) or isinstance(field, tuple):
                        attr_set += field
                    else:
                        attr_set.append(field)
            
            attr_set = set(attr_set)
            
            for attr in single_attributes:
                val = getattr(model_admin, attr, None)
                if val:
                    attr_set.add(val)
            
            # FIXME: not all attributes can be used everywhere (e.g. you can't use
            # list_filter with a form field). This will have to be fixed later.
            model_field_names = frozenset(model._meta.get_all_field_names())
            form_field_names = frozenset(getattr(model_admin.form, 'base_fields', []))
            
            model_instance = model()
            
            for attr in attr_set:
                # for now we'll just check attributes, not strings
                if not isinstance(attr, basestring):
                    continue
                
                # dont' split attributes that start with underscores (such as __str__)
                if attr[0] != '_':
                    attrs = attr.split('__')
                    attr = attrs[0]
                else:
                    attrs = [attr]
                
                has_model_field = attr in model_field_names
                has_form_field = attr in form_field_names
                has_model_attr = hasattr(model_instance, attr)
                has_admin_attr = hasattr(model_admin, attr)
                has_field_or_attr = has_model_field or has_form_field or has_model_attr or has_admin_attr
                
                self.assertTrue(has_field_or_attr, '%s not found on %s (%s)' % (attr, model, model_admin,))
                
    
    def test__queryset(self):
        request = self.factory.get('/')
        
        #TODO: use model_mommy to generate a few instances to query against
        for model, model_admin in admin.site._registry.items():
            # make sure no errors happen here
            qs = list(model_admin.queryset(request))
        

