Flask Mako Templates
====================

Provides support for Mako Templates in Flask. Based on code from flask-mako,
flask-genshi and flask itself.

Installation
------------
    setup.py install

Usage
-----

*Configuration*

You can use the following parameters in your config to configure Mako's
TemplateLookup object, which simply map to that class's constructor
parameters of the same names:

- MAKO_INPUT_ENCODING
- MAKO_OUTPUT_ENCODING
- MAKO_MODULE_DIRECTORY
- MAKO_COLLECTION_SIZE
- MAKO_IMPORTS
- MAKO_FILESYSTEM_CHECKS

*Registration*
    
    from flask import Flask
    from flaskext.makotemplates import MakoTemplates
        
    app = Flask(__name__)
    mako = MakoTemplates(app)

*Rendering*

Rendering is done exactly the same way as with Jinja2 templates. The Mako
templates' context is enriched by the same mechanism as the Jinja2 templates,
meaning that the same flask variables are available throughout your Mako
templates, including g, session, etc.

    from flaskext.makotemplates import render_template

    def hello_mako():
        return render_template('hello.html', name='mako')

*Babel integration*

flask-makotemplates will detect flask-babel if it is used by the application
and will automatically add the appropriate imports when creating the
TemplateLookup object