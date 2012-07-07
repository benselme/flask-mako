"""
flask-makotemplates
-------------------

This extension for the `Flask <http://flask.pocoo.org/>`_ micro web framework
allows for `Mako Templates <http://http://www.makotemplates.org/>`_ to be used
instead of the default Jinja2 templating engine.

"""
from setuptools import setup


setup(
    name='Flask-MakoTemplates',
    version='0.2',
    url='https://github.com/benselme/flask-makotemplates',
    license='BSD',
    author='Beranger Enselme',
    author_email='benselme@gmail.com',
    description='Mako templates support for Flask applications.',
    long_description=__doc__,
    packages=['flaskext'],
    namespace_packages=['flaskext'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'Mako'
    ],
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

