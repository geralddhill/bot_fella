FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get update
RUN apt-get install -y ffmpeg

CMD [ "python", "./bot_fella.py" ]
