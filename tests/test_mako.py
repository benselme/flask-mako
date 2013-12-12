# -*- coding: utf-8 -*-
import os, sys, tempfile

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from contextlib import contextmanager

import flask
from flask import Flask, Blueprint, g
from flask.ext.mako import (MakoTemplates, TemplateError, render_template,
                            render_template_string, render_template_def)

from mako.exceptions import CompileException

class MakoTestCase(unittest.TestCase):

    def setUp(self):
        app = Flask(__name__)
        app.debug = True
        mako = MakoTemplates(app)
        self.app = app
        self.mako = mako

        @app.before_request
        def setup_context():
            g.test_g = "test_g"

        @app.route('/context')
        def context():
            return render_template_string(u"${ g.test_g }")

        @app.route('/templatefile')
        def template_file():
            return render_template('template_file.html', result="succeeds")

        @app.route('/def_file')
        def def_file():
            return render_template_def('def_file.html', 'test_def',
                result="This")



    def tearDown(self):
        pass

    def testRenderTemplateFile(self):
        c = self.app.test_client()
        result = c.get('/templatefile')
        self.assertEqual(result.data, b'Test succeeds')

    def testFlaskContext(self):
        c = self.app.test_client()
        result = c.get('/context')
        self.assertEqual(result.data, b'test_g')

    def testRenderTemplateDef(self):
        c = self.app.test_client()
        result = c.get('/def_file')
        self.assertTrue(b'This is inside the def.' in result.data)
        self.assertFalse(b'This is above the def.' in result.data)
        self.assertFalse(b'That is inside the def.' in result.data)
        self.assertFalse(b'This is below the def.' in result.data)


class MakoMultipleDirectoriesTestCase(unittest.TestCase):

    def setUp(self):
        bp = Blueprint('bp', __name__, template_folder=['templates/bp', 'another_templates/another_bp'])

        @bp.route('/render_bp_from_templates')
        def render_bp_from_templates():
            return render_template('bp.html', result="succeeds")

        @bp.route('/render_bp_from_another_templates')
        def render_bp_from_another_templates():
            return render_template('another_bp.html', result="succeeds")

        app = Flask(__name__, template_folder=['templates', 'another_templates'])
        MakoTemplates(app)

        @app.route('/render_from_templates')
        def render_from_templates():
            return render_template('template_file.html', result="succeeds")

        @app.route('/render_from_another_templates')
        def render_from_another_templates():
            return render_template('another_template_file.html', result="succeeds")

        app.register_blueprint(bp)
        self.app = app
        self.client = app.test_client()

    def test_app_multiple_directories(self):
        result = self.client.get('/render_from_templates')
        self.assertEqual(result.data, b'Test succeeds')

        result = self.client.get('/render_from_another_templates')
        self.assertEqual(result.data, b'Another templates, test succeeds')

    def test_blueprint_multiple_directories(self):
        result = self.client.get('/render_bp_from_templates')
        self.assertEqual(result.data, b'Blueprint templates, test succeeds')

        result = self.client.get('/render_bp_from_another_templates')
        self.assertEqual(result.data, b'Blueprint another templates, test succeeds')


class MakoDetailedTestCase(unittest.TestCase):
    """ Tests the `flask_mako` templating extension. """

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def _add_template(self, name, text, d="templates"):
        template_dir = os.path.join(self.root, d)
        if not os.path.exists(template_dir):
            os.mkdir(template_dir)

        if not isinstance(text, bytes):
            text = text.encode('utf-8')

        with open(os.path.join(template_dir, name), 'wb') as f:
            f.write(text)

    @contextmanager
    def test_renderer(self, **kwargs):
        app = Flask(__name__)
        app.template_folder = os.path.join(self.root, "templates")
        app.config.update(
            MAKO_CACHE_DIR=os.path.join(self.root, "cache"),
            MAKO_CACHE_SIZE=10
        )
        app.config.update(kwargs)
        with app.test_request_context():
            yield app, MakoTemplates(app)

    def test_encoding(self):
        """ Tests that the Mako templates properly handle Unicode. """
        utf = u'\xA2'
        self._add_template("unicode", utf + u'${arg}')

        with self.test_renderer() as (_, mako):
            result = render_template('unicode', arg=utf)
            self.assertEqual(utf * 2, result.decode("utf8"))

        with self.assertRaises(CompileException):
            with self.test_renderer(MAKO_INPUT_ENCODING="ascii",
                                    MAKO_CACHE_DIR=None) as (_, mako):
                render_template("unicode", arg="test")

        with self.assertRaises(TemplateError) as e:
            with self.test_renderer(MAKO_OUTPUT_ENCODING="ascii",
                                    MAKO_CACHE_DIR=None) as (_, mako):
                render_template('unicode', arg='test')
        self.assertEqual(e.exception.einfo[0].__name__, "UnicodeEncodeError")

    def test_basic_template(self):
        """ Tests that the application can render a template. """
        self._add_template("basic", """
        % for arg in arguments:
            ${arg}
        % endfor
        """)
        with self.test_renderer() as (_, mako):
            result = render_template('basic', arguments=['testing', '123'])
            self.assertTrue(b'testing' in result)
            self.assertTrue(b'123' in result)

    def test_standard_variables(self):
        """
        Tests that the variables generally available to Flask Jinja
        templates are also available to Mako templates.

        """
        self._add_template("vars", """
        ${config['MAKO_INPUT_ENCODING']}
        ${request.args}
        ${session.new}
        ${url_for('test')}
        ${get_flashed_messages()}

        ${injected()}
        """)

        with self.test_renderer() as (app, mako):

            @app.route('/test')
            def test(): return "test"

            @app.context_processor
            def inject(): return {"injected": lambda: "injected"}

            result = render_template("vars")

    def test_imports(self):
        """ Tests that the extension properly sets Mako imports. """
        from string import ascii_letters
        self._add_template("imports", "${ascii_letters}")

        imports = ["from string import ascii_letters"]
        with self.test_renderer(MAKO_IMPORTS=imports) as (_, mako):
            self.assertEqual(render_template("imports"), ascii_letters.encode())

    @unittest.skipIf(not flask.signals_available,
                     "This test requires Flask signaling support.")
    def test_signals(self):
        """ Tests that template rendering fires the right signal. """
        from flask.signals import template_rendered

        self._add_template("signal", "signal template")
        with self.test_renderer() as (app, mako):

            log = []
            def record(*args, **extra):
                log.append(args)
            template_rendered.connect(record, app)

            result = render_template('signal')

            self.assertEqual(len(log), 1)

    def test_multiple_apps(self):
        """ Tests that the Mako plugin works with multiple Flask apps. """
        self._add_template("app", "test 1", "alt1")
        self._add_template("app", "test 2", "alt2")
        alt1_dir = os.path.join(self.root, "alt1")
        alt2_dir = os.path.join(self.root, "alt2")

        with self.test_renderer() as (app, mako):
            app.template_folder = alt1_dir
            self.assertEqual(render_template('app'), b'test 1')
            with self.test_renderer(MAKO_CACHE_DIR=None) as (app, _):
                app.template_folder = alt2_dir
                self.assertEqual(render_template('app'), b'test 2')


            with self.assertRaises(RuntimeError):
                mako.init_app(Flask(__name__))

    def test_blueprints(self):
        """ Tests that the plugin properly pulls templates from blueprints. """
        self._add_template("blue", "blueprint", "blueprint_templates")
        blue_dir = os.path.join(self.root, "blueprint_templates")

        test = Blueprint('blue', __name__, template_folder=blue_dir)

        with self.test_renderer() as (app, mako):
            app.register_blueprint(test, url_prefix="blue")

            self.assertEqual(render_template("blue"), b"blueprint")

    def test_error(self):
        """ Tests that template errors are properly handled. """
        self._add_template("error_template", """
        % for arg in arguments:
            ${error}
        % endfor
        """)

        with self.test_renderer() as (app, mako):
            with self.assertRaises(TemplateError) as error:
                render_template('error_template', arguments=['x'])

            e = error.exception
            self.assertTrue('error_template' in e.message)
            self.assertTrue('error_template' in e.text)
            self.assertTrue('line 3' in e.text)

        with self.test_renderer(MAKO_TRANSLATE_EXCEPTIONS=False) as _:
            with self.assertRaises(NameError):
                render_template('error_template', arguments=['y'])

try:
    from flaskext import babel
    from flaskext.babel import Babel

    class MakoBabelTestCase(unittest.TestCase):
        def setUp(self):
            app = Flask(__name__)
            app.debug = True
            babel = Babel(app)
            mako = MakoTemplates(app)
            self.app = app
            self.mako = mako
            self.babel = babel

            @app.route('/')
            def babel_page():
                return render_template('babel_template.html')

            @babel.localeselector
            def get_locale():
                return self.locale

        def testTranslation(self):
            self.locale = "en"
            c = self.app.test_client()
            result = c.get('/')
            self.assertEqual(result.data, u"Something")
            self.locale = "fr"
            result = c.get('/')
            self.assertEqual(result.data, u"Quelque chose")

except ImportError:
    MakoBabelTestCase = None

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MakoTestCase))
    suite.addTest(unittest.makeSuite(MakoMultipleDirectoriesTestCase))
    suite.addTest(unittest.makeSuite(MakoDetailedTestCase))
    if MakoBabelTestCase:
        suite.addTest(unittest.makeSuite(MakoBabelTestCase))
    return suite

if __name__ == '__main__':
    unittest.main()
