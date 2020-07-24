from ivr_phone_tree_python import app, configure_app
from flask.ext.testing import TestCase

# *** WARNING ***: Testing will now work.
# Really embarrassing but there is no testing. The original Twilio codes sample is pretty outdated
# using Nose 1.3.7 and Flask-Testing 0.4.2 from 2014 with Python 2.7.x (deprecated)! A lot has change (its 2020!),
# except time to covert the testing to use pytest and the latest Flask-Testing 0.8.0. =(
# *** WARNING ***


class BaseTestCase(TestCase):
    render_templates = False

    def create_app(self):
        configure_app(app, 'test')
        return app
