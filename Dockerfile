FROM python:3.6-buster

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY . /app
WORKDIR /app/

RUN apt-get update
RUN apt-get install -y gettext
RUN msgfmt locale/ko_KR/LC_MESSAGES/bot.po -o locale/ko_KR/LC_MESSAGES/bot.mo

CMD python bot.py
