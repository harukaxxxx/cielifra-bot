FROM python:3.11.4-alpine

RUN apk update
RUN apk add --no-cache git zlib-dev jpeg-dev gcc musl-dev
RUN git clone https://github.com/harukaxxxx/cielifra-bot.git /app

WORKDIR /app
RUN pip install --no-cache-dir -r /app/requirements/prod.txt

CMD ["python", "-m", "bot"]
