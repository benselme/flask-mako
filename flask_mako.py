# -*- coding: utf-8 -*-
"""
    flask.ext.mako
    ~~~~~~~~~~~~~~~~~~~~~~~

    Extension implementing Mako Templates support in Flask with support for
    flask-babel

    :copyright: (c) 2012 by Béranger Enselme <benselme@gmail.com>
    :license: BSD, see LICENSE for more details.
"""
import os, sys

from flask.helpers import locked_cached_property
from flask.signals import template_rendered

# Find the context stack so we can resolve which application is calling this
# extension.  Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

from werkzeug.debug.tbtools import Traceback, Frame, Line

from mako.lookup import TemplateLookup
from mako.template import Template
from mako import exceptions
from mako.exceptions import RichTraceback, text_error_template


itervalues = getattr(dict, 'itervalues', dict.values)

_BABEL_IMPORTS =  'from flaskext.babel import gettext as _, ngettext, ' \
                  'pgettext, npgettext'
_FLASK_IMPORTS =  'from flask.helpers import url_for, get_flashed_messages'

class MakoFrame(Frame):
    """ A special `~werkzeug.debug.tbtools.Frame` object for Mako sources. """
    def __init__(self, exc_type, exc_value, tb, name, line):
        super(MakoFrame, self).__init__(exc_type, exc_value, tb)
        self.info = "(translated Mako exception)"
        self.filename = name
        self.lineno = line
        old_locals = self.locals
        self.locals = dict(tb.tb_frame.f_locals['context'].kwargs)
        self.locals['__mako_module_locals__'] = old_locals

    def get_annotated_lines(self):
        """
        Remove frame-finding code from `~werkzeug.debug.tbtools.Frame`. This
        code is actively dangerous when run on Mako templates because
        Werkzeug's parsing doesn't understand their syntax. Instead, just mark
        the current line.

        """
        lines = [Line(idx + 1, x) for idx, x in enumerate(self.sourcelines)]

        try:
            lines[self.lineno - 1].current = True
        except IndexError:
            pass

        return lines


class TemplateError(RichTraceback, RuntimeError):
    """ A template has thrown an error during rendering. """

    def werkzeug_debug_traceback(self, exc_type, exc_value, tb):
        """ Munge the default Werkzeug traceback to include Mako info. """

        orig_type, orig_value, orig_tb = self.einfo
        translated = Traceback(orig_type, orig_value, tb)

        # Drop the "raise" frame from the traceback.
        translated.frames.pop()

        def orig_frames():
            cur = orig_tb
            while cur:
                yield cur
                cur = cur.tb_next

        # Append our original frames, overwriting previous source information
        # with the translated Mako line locators.
        for tb, record in zip(orig_frames(), self.records):
            name, line = record[4:6]
            if name:
                new_frame = MakoFrame(orig_type, orig_value, tb, name, line)
            else:
                new_frame = Frame(orig_type, orig_value, tb)

            translated.frames.append(new_frame)

        return translated


    def __init__(self, template):
        super(TemplateError, self).__init__()
        self.einfo = sys.exc_info()
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
        self.app = None
        if app is not None:
            self.init_app(app)
        self.app = app


    def init_app(self, app):
        """
        Initialize a :class:`~flask.Flask` application
        for use with this extension. This method is useful for the factory
        pattern of extension initialization. Example::

            mako = MakoTemplates()

            app = Flask(__name__)
            mako.init_app(app)

        .. note::
            This call will fail if you called the :class:`MakoTemplates`
            constructor with an ``app`` argument.

        """
        if self.app:
            raise RuntimeError("Cannot call init_app when app argument was "
                               "provided to MakoTemplates constructor.")

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
        app.config.setdefault('MAKO_TRANSLATE_EXCEPTIONS', True)
        app.config.setdefault('MAKO_DEFAULT_FILTERS', None)
        app.config.setdefault('MAKO_PREPROCESSOR', None)


def _create_lookup(app):
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
        'default_filters': app.config['MAKO_DEFAULT_FILTERS'],
        'preprocessor': app.config['MAKO_PREPROCESSOR'],
    }
    path = os.path.join(app.root_path, app.template_folder)
    paths = [path]
    blueprints = getattr(app, 'blueprints', {})
    for blueprint in itervalues(blueprints):
        if blueprint.template_folder:
            blueprint_template_path = os.path.join(blueprint.root_path,
                blueprint.template_folder)
            if os.path.isdir(blueprint_template_path):
                paths.append(blueprint_template_path)
    return TemplateLookup(directories=paths, **kw)


def _lookup(app):
    if not app._mako_lookup:
        app._mako_lookup = _create_lookup(app)
    return app._mako_lookup


def _render(template, context, app):
    """Renders the template and fires the signal"""
    context.update(app.jinja_env.globals)
    app.update_template_context(context)
    try:
        rv = template.render(**context)
        template_rendered.send(app, template=template, context=context)
        return rv
    except:
        translate = app.config.get("MAKO_TRANSLATE_EXCEPTIONS")
        if translate:
            translated = TemplateError(template)
            raise translated
        else:
            raise


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
