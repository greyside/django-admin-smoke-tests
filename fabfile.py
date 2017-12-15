from fabric.api import task
from fabric.operations import local

import django_admin_smoke_tests


@task
def release():
    local('git push')
    local('git tag {}'.format(django_admin_smoke_tests.__version__))
    local('git push --tags')

    local('python setup.py sdist upload')
