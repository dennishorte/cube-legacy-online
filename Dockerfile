FROM python:3.6-slim
MAINTAINER Dennis Horte "dennis.horte@gmail.com"

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Set up secret key for flask-login
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN pip install -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

# In case I want to use docker locally
# ENV FLASK_SECRET_KEY $FLASK_SECRET_KEY
# ENTRYPOINT ["python"]
# CMD ["src/app.py"]
