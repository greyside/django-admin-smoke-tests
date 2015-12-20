========================
django-admin-smoke-tests
========================

.. image:: https://travis-ci.org/greyside/django-admin-smoke-tests.svg?branch=master
    :target: https://travis-ci.org/greyside/django-admin-smoke-tests
.. image:: https://coveralls.io/repos/greyside/django-admin-smoke-tests/badge.png?branch=master
    :target: https://coveralls.io/r/greyside/django-admin-smoke-tests?branch=master

Run with ``./manage.py test django_admin_smoke_tests.tests``.

You don't have to add anything ``INSTALLED_APPS``

Usage in your tests
-------------------

If you want to use admin smoke tests as part of your tests with data from fixtures,
you can do following::

    from django_admin_smoke_tests import tests
    class AdminTest(tests.AdminSiteSmokeTest):
        fixtures = ['data']
