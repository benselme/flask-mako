"""
flask-makotemplates
----------

Mako templates support for Flask applications.

Links
`````

* `on github
<https://github.com/benselme/flask-makotemplates>`_

.. _Mako: http://www.makotemplates.org/

"""
from setuptools import setup


setup(
    name='Flask-MakoTemplates',
    version='0.1',
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

