"""
flask-mako
----------

This extension for the `Flask <http://flask.pocoo.org/>`_ micro web framework
allows developers to use  `Mako Templates
<http://http://www.makotemplates.org/>`_ instead of the default Jinja2
templating engine.

"""
from setuptools import setup


setup(
    name='Flask-Mako',
    version='0.2',
    url='https://github.com/benselme/flask-mako',
    license='BSD',
    author='Beranger Enselme, Frank Murphy',
    author_email='benselme@gmail.com',
    description='Mako templating support for Flask applications.',
    long_description=__doc__,
    py_modules=['flask_mako', 'tests.test_mako'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'Mako'
    ],
    test_suite='tests.test_mako.suite',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

