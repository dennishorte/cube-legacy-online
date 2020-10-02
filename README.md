Build the image using the following command

```bash
$ docker build -t skeleton-dock-python-flask:latest .
```

Run the Docker container using the command shown below.

```bash
$ docker run -d -p 5000:5000 skeleton-dock-python-flask
```

The application will be accessible at http:127.0.0.1:5000.
