FROM --platform=linux/amd64 registry.apps.lab.andersentech.net/genai-spot-pod/rss-spot-pod-base:latest
LABEL maintainer="samstext@gmail.com"

RUN mkdir -p /tmp/app
WORKDIR /tmp/app

ADD ./dist/*.tar.gz /tmp

CMD ["sh","-c", "/opt/venv/bin/python3 /tmp/app/wsgi.py"]