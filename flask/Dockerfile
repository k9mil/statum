FROM python:3.10

WORKDIR /statum

ADD . /statum

RUN pip install -r requirements.txt

CMD ["uwsgi", "statum.ini"]
