FROM python:latest

WORKDIR /opt/app
RUN pip install -U pip
RUN pip install -U Flask
ADD . .

CMD ['flask', 'run']