# -*- coding: utf-8 -*-
import sys

import unittest
from flask import Flask, g
from flaskext.makotemplates import MakoTemplates, render_template, \
    render_template_string, render_template_def

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
        self.assertIn('This is inside the def.', result.data)
        self.assertNotIn('This is above the def.', result.data)
        self.assertNotIn('That is inside the def.', result.data)
        self.assertNotIn('This is below the def.', result.data)

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
    pass



if __name__ == '__main__':
    unittest.main()
