import os
import sys
from setuptools import setup
from sitetree import VERSION

f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = f.read()
f.close()

PYTEST_RUNNER = ['pytest-runner'] if 'test' in sys.argv else []

setup(
    name='django-sitetree',
    version='.'.join(map(str, VERSION)),
    url='http://github.com/idlesign/django-sitetree',

    description='This reusable Django app introduces site tree, menu and breadcrumbs navigation elements',
    long_description=readme,
    license='BSD 3-Clause License',

    author='Igor `idle sign` Starikov',
    author_email='idlesign@yandex.ru',

    packages=['sitetree'],
    include_package_data=True,
    zip_safe=False,

    setup_requires=[] + PYTEST_RUNNER,
    tests_require=[
        'pytest',
        'pytest-djangoapp>=0.13.0',
    ],

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
