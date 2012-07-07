# -*- coding: utf-8 -*-
"""
    flaskext.mako_templates
    ~~~~~~~~~~~~~~~~~~~~~~~

    Implements the bridge to Mako Templates with support for flask-babel

    :copyright: (c) 2012 by Béranger Enselme <benselme@gmail.com>
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
from flask.helpers import locked_cached_property
from flask.signals import template_rendered
from mako.lookup import TemplateLookup
from mako.template import Template
from mako import exceptions
from flask import _request_ctx_stack
import os

_BABEL_IMPORTS =  'from flaskext.babel import gettext as _, ngettext, ' \
                  'pgettext, npgettext'
_FLASK_IMPORTS =  'from flask.helpers import url_for, get_flashed_messages'


class MakoTemplates(object):
    """
    Main class for bridging mako and flask. We try to stay as close as possible
    to how Jinja2 is used in flask, while at the same time surfacing the useful
    stuff from Mako.

    Here's how to initialize the extension.

    ::

        app = Flask(__name__)
        mako = MakoTemplates(app)


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
        app.mako_instance = self
        self.app = app
        self.app.config.setdefault('MAKO_INPUT_ENCODING', 'utf-8')
        self.app.config.setdefault('MAKO_OUTPUT_ENCODING', 'utf-8')
        self.app.config.setdefault('MAKO_MODULE_DIRECTORY', None)
        self.app.config.setdefault('MAKO_COLLECTION_SIZE', -1)
        self.app.config.setdefault('MAKO_IMPORTS', None)
        self.app.config.setdefault('MAKO_FILESYSTEM_CHECKS', True)


    @locked_cached_property
    def template_lookup(self):
        """Returns a :class:`TemplateLookup <mako.lookup.TemplateLookup>`
        instance that looks for templates from the same places as Flask, ie.
        subfolders named 'templates' in both the app folder and its blueprints'
        folders.

        If flask-babel is installed it will add support for it in the templates
        by adding the appropriate imports clause.

        """
        imports = self.app.config['MAKO_IMPORTS'] or []
        imports.append(_FLASK_IMPORTS)

        if 'babel' in self.app.extensions:
            imports.append(_BABEL_IMPORTS)

        kw = {
            'input_encoding': self.app.config['MAKO_INPUT_ENCODING'],
            'output_encoding': self.app.config['MAKO_OUTPUT_ENCODING'],
            'module_directory': self.app.config['MAKO_MODULE_DIRECTORY'],
            'collection_size': self.app.config['MAKO_COLLECTION_SIZE'],
            'imports': imports,
            'filesystem_checks': self.app.config['MAKO_FILESYSTEM_CHECKS'],
        }
        path = os.path.join(self.app.root_path, self.app.template_folder)
        template_paths = [path]
        blueprints = getattr(self.app, 'blueprints', {})
        for name, blueprint in blueprints.iteritems():
            if blueprint.template_folder:
                blueprint_template_path = os.path.join(blueprint.root_path,
                    blueprint.template_folder)
                if os.path.isdir(blueprint_template_path):
                    template_paths.append(blueprint_template_path)
        return TemplateLookup(directories=template_paths, **kw)

    def get_template(self, template_name):
        return self.template_lookup.get_template(template_name)

    def from_string(self, source):
        return Template(source, lookup=self.template_lookup)


def _render(template, context, app):
    """Renders the template and fires the signal"""
    try:
        rv = template.render(**context)
        template_rendered.send(app, template=template, context=context)
        return rv
    except:
        print exceptions.text_error_template().render()
        raise


def render_template(template_name, **context):
    """Renders a template from the template folder with the given
    context.

    :param template_name: the name of the template to be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(ctx.app.mako_instance.get_template(template_name),
        context, ctx.app)


def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context.

    :param source: the sourcecode of the template to be
                          rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(ctx.app.mako_instance.from_string(source),
        context, ctx.app)


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
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(ctx.app.mako_instance.\
        get_template(template_name).get_def(def_name),
            context, ctx.app)
