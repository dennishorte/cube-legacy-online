import os
import sys
sys.path.insert(0, '/var/www/html/cube-legacy-online')

def application(environ, start_response):
    ENVIRONMENT_VARIABLES = [
        'FLASK_ENV',
        'FLASK_SECRET_KEY',
        'DB_USER',
        'DB_PASS',
        'DB_HOST',
        'DB_NAME',
    ]

    for key in ENVIRONMENT_VARIABLES:
        os.environ[key] = environ.get(key)

    from app import app

    return app(environ, start_response)
