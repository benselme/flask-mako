# -*- coding: utf-8 -*-
"""
    flask.ext.mako
    ~~~~~~~~~~~~~~~~~~~~~~~

    Extension implementing Mako Templates support in Flask with support for
    flask-babel

    :copyright: (c) 2012 by Béranger Enselme <benselme@gmail.com>
    :license: BSD, see LICENSE for more details.
"""
import os

from flask.helpers import locked_cached_property
from flask.signals import template_rendered
from flask import _request_ctx_stack

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

from mako.lookup import TemplateLookup
from mako.template import Template
from mako import exceptions
from mako.exceptions import RichTraceback, text_error_template


_BABEL_IMPORTS =  'from flaskext.babel import gettext as _, ngettext, ' \
                  'pgettext, npgettext'
_FLASK_IMPORTS =  'from flask.helpers import url_for, get_flashed_messages'


class TemplateError(RuntimeError):
    """ A template has thrown an error during rendering. """
    def __init__(self, template):
        self.tb = RichTraceback()
        self.text = text_error_template().render()
        msg = "Error occurred while rendering template '{0}'"
        msg = msg.format(template.uri)
        super(TemplateError, self).__init__(msg)


class MakoTemplates(object):
    """
    Main class for bridging mako and flask. We try to stay as close as possible
    to how Jinja2 is used in Flask, while at the same time surfacing the useful
    stuff from Mako.

    """

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)


    def init_app(self, app):
        """
        Initialize a :class:`~flask.Flask` application
        for use with this extension. Useful for the factory pattern but
        not needed if you passed your application to the :class:`MakoTemplates`
        constructor.

        ::

            mako = MakoTemplates()

            app = Flask(__name__)
            mako.init_app(app)

        """
        if not hasattr(app, 'extensions'):
            app.extensions = {}

        app.extensions['mako'] = self
        app._mako_lookup = None

        app.config.setdefault('MAKO_INPUT_ENCODING', 'utf-8')
        app.config.setdefault('MAKO_OUTPUT_ENCODING', 'utf-8')
        app.config.setdefault('MAKO_MODULE_DIRECTORY', None)
        app.config.setdefault('MAKO_COLLECTION_SIZE', -1)
        app.config.setdefault('MAKO_IMPORTS', None)
        app.config.setdefault('MAKO_FILESYSTEM_CHECKS', True)


    @staticmethod
    def create_lookup(app):
        """Returns a :class:`TemplateLookup <mako.lookup.TemplateLookup>`
        instance that looks for templates from the same places as Flask, ie.
        subfolders named 'templates' in both the app folder and its blueprints'
        folders.

        If flask-babel is installed it will add support for it in the templates
        by adding the appropriate imports clause.

        """
        imports = app.config['MAKO_IMPORTS'] or []
        imports.append(_FLASK_IMPORTS)

        if 'babel' in app.extensions:
            imports.append(_BABEL_IMPORTS)

        kw = {
            'input_encoding': app.config['MAKO_INPUT_ENCODING'],
            'output_encoding': app.config['MAKO_OUTPUT_ENCODING'],
            'module_directory': app.config['MAKO_MODULE_DIRECTORY'],
            'collection_size': app.config['MAKO_COLLECTION_SIZE'],
            'imports': imports,
            'filesystem_checks': app.config['MAKO_FILESYSTEM_CHECKS'],
        }
        path = os.path.join(app.root_path, app.template_folder)
        paths = [path]
        blueprints = getattr(app, 'blueprints', {})
        for name, blueprint in blueprints.iteritems():
            if blueprint.template_folder:
                blueprint_template_path = os.path.join(blueprint.root_path,
                    blueprint.template_folder)
                if os.path.isdir(blueprint_template_path):
                    paths.append(blueprint_template_path)
        return TemplateLookup(directories=paths, **kw)


def _lookup(app):
    if not app._mako_lookup:
        app._mako_lookup = MakoTemplates.create_lookup(app)
    return app._mako_lookup


def _render(template, context, app):
    """Renders the template and fires the signal"""
    app.update_template_context(context)
    try:
        rv = template.render(**context)
        template_rendered.send(app, template=template, context=context)
        return rv
    except:
        translated = TemplateError(template)
        raise translated


def render_template(template_name, **context):
    """Renders a template from the template folder with the given
    context.

    :param template_name: the name of the template to be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = stack.top
    return _render(_lookup(ctx.app).get_template(template_name),
                   context, ctx.app)


def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context.

    :param source: the sourcecode of the template to be
                          rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = stack.top
    template = Template(source, lookup=_lookup(ctx.app))
    return _render(template, context, ctx.app)


def render_template_def(template_name, def_name, **context):
    """Renders a specific def from a given
    template from the template folder with the given
    context. Useful for implementing this AJAX pattern:

    http://techspot.zzzeek.org/2008/09/01/ajax-the-mako-way

    :param template_name: the name of the template file containing the def
                    to be rendered
    :param def_name: the name of the def to be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = stack.top
    template = _lookup(ctx.app).get_template(template_name)
    return _render(template.get_def(def_name), context, ctx.app)
