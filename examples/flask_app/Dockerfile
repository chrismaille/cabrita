FROM python:latest

WORKDIR /opt/app
RUN pip install -U pip Flask
ADD . .

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]