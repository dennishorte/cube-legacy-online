from os import environ

from app import app

DO_PROFILING = False

if DO_PROFILING:
    from werkzeug.middleware.profiler import ProfilerMiddleware
    app.config['PROFILE'] = True
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

if __name__ == "__main__":
    port = int(environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
