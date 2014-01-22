#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import django_admin_smoke_tests

package_name = 'django_admin_smoke_tests'

setup(name='django-admin-smoke-tests',
    version=django_admin_smoke_tests.__version__,
    description="Runs some quick tests on your admin site objects to make sure there aren't non-existant fields listed, etc.",
    author='Seán Hayes',
    author_email='sean@seanhayes.name',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    keywords='django admin smoke test',
    url='https://github.com/SeanHayes/django-admin-smoke-tests',
    download_url='https://github.com/SeanHayes/django-admin-smoke-tests',
    license='BSD',
    install_requires=[
        'django>=1.6',
    ],
    packages=[
        package_name,
    ],
    include_package_data=True,
)

