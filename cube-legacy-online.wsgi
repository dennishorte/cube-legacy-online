import os
import sys
sys.path.insert(0, '/var/www/html/clo-v2')

def application(environ, start_response):
    ENVIRONMENT_VARIABLES = [
        'FLASK_ENV',
        'FLASK_SECRET_KEY',
        'DB_USER',
        'DB_PASS',
        'DB_HOST',
        'DB_NAME',
	'SLACK_BOT_TOKEN',
    ]

    for key in ENVIRONMENT_VARIABLES:
        os.environ[key] = environ.get(key)

    from app import app

    return app(environ, start_response)
