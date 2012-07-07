Flask-MakoTemplates
===================

The **Flask-MakoTemplates** extension provides
`Mako Templates <http://www.makotemplates.org/>`_ support for `Flask <http://flask.pocoo.org/>`_.

Based on code from flask-mako, flask-genshi and flask itself, it allows for templates
written in Mako to be used just like Jinja2 templates: it will look for templates
in the same directories, provides the same API and integrates with Flask-Babel for
internationalization.

Installation
------------
::

    pip install Flask-MakoTemplates

Usage
-----

Configuration
`````````````

You can use the following parameters in your config to configure Mako's
:class:`TemplateLookup <mako.lookup.TemplateLookup>` object, which simply map
to that class's constructor
parameters of the same names:

- MAKO_INPUT_ENCODING
- MAKO_OUTPUT_ENCODING
- MAKO_MODULE_DIRECTORY
- MAKO_COLLECTION_SIZE
- MAKO_IMPORTS
- MAKO_FILESYSTEM_CHECKS

Registration
````````````
The two registration methods are supported::

        from flask import Flask
        from flaskext.makotemplates import MakoTemplates

        app = Flask(__name__)
        mako = MakoTemplates(app)

Or, you can use the :meth:`~.MakoTemplates.init_app` method.

Rendering
`````````

Rendering is done exactly the same way as with Jinja2 templates. The Mako
templates' context is enriched by the same mechanism as the Jinja2 templates,
meaning that the same flask variables are available throughout your Mako
templates, including g, session, etc.

::

    from flaskext.makotemplates import render_template

    def hello_mako():
        return render_template('hello.html', name='mako')

Babel integration
`````````````````

Flask-MakoTemplates will detect `Flask-Babel <http://packages.python.org/Flask-Babel/>`_
if it is used by the application and will automatically add the appropriate
imports when creating the TemplateLookup object


API
````
.. automodule:: makotemplates
    :members:
