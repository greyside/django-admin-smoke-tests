from fabric.api import task
from fabric.operations import local

import utils_plus


@task
def release():
    local('git push')
    local('git tag {}'.format(utils_plus.__version__))
    local('git push --tags')

    # dont forget to have this file
    # ~/.pypirc
    # [distutils]
    # index-servers =
    #  pypi

    # [pypi]
    # repository: https://upload.pypi.org/legacy/
    # username: jnoortheen
    # password: pwd
    local('python setup.py sdist upload')
