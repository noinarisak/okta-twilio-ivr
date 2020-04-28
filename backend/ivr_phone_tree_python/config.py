import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


class DefaultConfig(object):
    DEBUG = False
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
    OKTA_API_TOKEN = os.getenv('OKTA_API_TOKEN')


class DevelopmentConfig(DefaultConfig):
    DEBUG = True


class TestConfig(DefaultConfig):
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False


config_env_files = {
    'test': 'ivr_phone_tree_python.config.TestConfig',
    'development': 'ivr_phone_tree_python.config.DevelopmentConfig',
}
