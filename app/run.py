from os import environ

from app import app

app_var = app

port = int(environ.get("PORT", 5000))
app_var.run(debug=True, host='0.0.0.0', port=port)
