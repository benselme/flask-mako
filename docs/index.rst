Flask-Mako
==========
The **Flask-Mako** extension provides `Mako Templating
<http://www.makotemplates.org/>`_ support for `Flask
<http://flask.pocoo.org/>`_.

Based on code from flask-mako, flask-genshi and flask itself, it allows for
templates written in Mako to be used just like Jinja2 templates. It will look
for templates in the same directories, provide the same API and integrate
with Flask-Babel for internationalization.

Installation
------------

This extension is available on PyPI::

    pip install Flask-Mako

Usage
-----

Configuration
`````````````

You can use the following parameters in your config to configure Mako's
:class:`~mako.lookup.TemplateLookup` object:

=======================     =====================
Configuration Parameter     :class:`~mako.lookup.TemplateLookup` parameter
=======================     =====================
MAKO_INPUT_ENCODING         input_encoding
MAKO_OUTPUT_ENCODING        output_encoding
MAKO_MODULE_DIRECTORY       module_directory
MAKO_COLLECTION_SIZE        collection_size
MAKO_IMPORTS                imports
MAKO_FILESYSTEM_CHECKS      filesystem_checks
=======================     =====================

Registration
````````````
Applications can be registered directly in the extension constructor::

    from flask import Flask
    from flask.ext.mako import MakoTemplates

    app = Flask(__name__)
    mako = MakoTemplates(app)

Or, you can use the :meth:`~.MakoTemplates.init_app` method to initialize
multiple applications::

    # ... in content.py ...
    mako = MakoTemplates(app)

    # ... in app1.py ...
    app = Flask(__name__)
    app.template_folder = "templates"
    content.mako.init_app(app)

    # ... in app1.py ...
    app = Flask(__name__)
    app.template_folder = "templates"
    content.mako.init_app(app)


Multiple Template Directories
`````````````````````````````

If the code within those templates tries to locate another template
resource, it will need some way to find them. `Using TemplateLookup
<http://docs.makotemplates.org/en/latest/usage.html#using-templatelookup>`_
in Flask::

    # ... in app ...
    app = Flask(__name__)
    app.template_folder = ['templates', 'another_templates']

    # or
    app = Flask(__name__, template_folder=['templates', 'another_templates'])

    # ... in blueprint ...
    bp = Blueprint('bp', __name__)
    bp.template_folder = ['templates', 'another_templates']

    # or
    bp = Blueprint('bp', __name__, template_folder=['templates', 'another_templates'])


Rendering
`````````

Rendering Mako templates sends the same :data:`~flask.template_rendered` signal
as Jinja2 templates. Additionally, Mako templates receive the same context as
Jinja2 templates. This allows you to use the same variables as you normally
would (``g``, ``session``, ``url_for``, etc)::

    from flask.ext.mako import render_template

    def hello_mako():
        return render_template('hello.html', name='mako')

Finally, the render context is populated with the same utility function as
Jinja templates (:meth:`~flask.Flask.update_template_context`). This allows you
to use the :meth:`@app.context_processor <flask.Flask.context_processor>`
decorator to add context processors to your :class:`~flask.Flask` application.

.. note::

    Unicode rendering in Mako is complicated by the non-ideal representation of
    unicode in Python 2. In particular, even if ``MAKO_OUTPUT_ENCODING`` is
    defined as UTF-8, all strings are passed through the :func:`unicode`
    built-in. This means that any :func:`str` instances rendered in Mako will
    potentially run into locale-specific encoding issues.

    The best way to mitigate this is to always return :func:`unicode` objects
    in rendered expressions. For more information, see the Mako :ref:`chapter
    <mako:unicode_toplevel>` on this subject.

Error Handling
``````````````

Mako template errors are tricky to debug; they contain tracebacks to the
compiled python module code instead of the template that caused the error.  To
help debug these errors, Flask-Mako will translate any error raised during
template error handling into a :class:`~.TemplateError` object and then
re-raise it.

Babel integration
`````````````````

Flask-Mako will detect `Flask-Babel
<http://packages.python.org/Flask-Babel/>`_ if it is used by the application
and will automatically add the appropriate imports when creating the
:class:`TemplateLookup <mako.lookup.TemplateLookup>` object. For this to 
work, the Flask-Babel extension must be initialized *before* the Flask-Mako
extension.


API
````
.. module:: flask_mako

.. autoclass:: MakoTemplates
    :members:

.. autoclass:: TemplateError
    :members:

    .. attribute:: tb

        A :class:`RichTraceback <mako.exceptions.RichTraceback>` object
        generated from the exception.

    .. attribute:: text

        The exception information, generated with :func:`text_error_template
        <mako.exceptions.text_error_template>`.

.. autofunction:: render_template

.. autofunction:: render_template_string

.. autofunction:: render_template_def
