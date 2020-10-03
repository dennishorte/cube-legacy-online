import os

basedir = os.path.abspath(os.path.dirname(__file__))


if os.environ.get('FLASK_ENV') == 'development':
    db_uri ="sqlite:///" + basedir + "/app.db"
else:
    PROD_DB_URI_STRING = "{driver}://{user}:{pw}@{host}:{port}/{db_name}"
    db_uri = PROD_DB_URI_STRING.format(
        driver="mysql+pymysql",
        user=os.environ["DB_USER"],
        pw=os.environ["DB_PASS"],
        host=os.environ["DB_HOST"].split(':')[0],
        port=os.environ["DB_HOST"].split(':')[1],
        db_name=os.environ["DB_NAME"],
    )
    
class Config(object):
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = db_uri
