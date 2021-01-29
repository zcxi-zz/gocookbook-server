FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python3-pip python-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt

ADD . /app
EXPOSE 5001

CMD ["python3", "manage.py", "runserver", "-h", "0.0.0.0", "-p", "5001"]
