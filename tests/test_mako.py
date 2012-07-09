# -*- coding: utf-8 -*-
import os, sys, unittest, tempfile
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
        self.assertEqual(result.data, 'Test succeeds')

    def testFlaskContext(self):
        c = self.app.test_client()
        result = c.get('/context')
        self.assertEqual(result.data, 'test_g')

    def testRenderTemplateDef(self):
        c = self.app.test_client()
        result = c.get('/def_file')
        self.assertTrue('This is inside the def.' in result.data)
        self.assertFalse('This is above the def.' in result.data)
        self.assertFalse('That is inside the def.' in result.data)
        self.assertFalse('This is below the def.' in result.data)

class MakoDetailedTestCase(unittest.TestCase):
    """ Tests the `flask_mako` templating extension. """

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def _add_template(self, name, text, d="templates"):
        template_dir = os.path.join(self.root, d)
        if not os.path.exists(template_dir):
            os.mkdir(template_dir)

        with open(os.path.join(template_dir, name), 'w') as f:
            f.write(text.encode('utf8'))

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
        self.assertEqual(e.exception.tb.errorname, "UnicodeEncodeError")

    def test_basic_template(self):
        """ Tests that the application can render a template. """
        self._add_template("basic", """
        % for arg in arguments:
            ${arg}
        % endfor
        """)
        with self.test_renderer() as (_, mako):
            result = render_template('basic', arguments=['testing', '123'])
            self.assertTrue('testing' in result)
            self.assertTrue('123' in result)

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
            self.assertEqual(render_template("imports"), ascii_letters)

    if flask.signals_available:
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

        with self.test_renderer() as (app, _):
            app.template_folder = alt1_dir
            self.assertEqual(render_template('app'), 'test 1')
            with self.test_renderer(MAKO_CACHE_DIR=None) as (app, _):
                app.template_folder = alt2_dir
                self.assertEqual(render_template('app'), 'test 2')

    def test_blueprints(self):
        """ Tests that the plugin properly pulls templates from blueprints. """
        self._add_template("blue", "blueprint", "blueprint_templates")
        blue_dir = os.path.join(self.root, "blueprint_templates")

        test = Blueprint('blue', __name__, template_folder=blue_dir)

        with self.test_renderer() as (app, mako):
            app.register_blueprint(test, url_prefix="blue")

            self.assertEqual(render_template("blue"), "blueprint")

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
    suite.addTest(unittest.makeSuite(MakoDetailedTestCase))
    if MakoBabelTestCase:
        suite.addTest(unittest.makeSuite(MakoBabelTestCase))
    return suite

if __name__ == '__main__':
    unittest.main()
