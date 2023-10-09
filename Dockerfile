FROM python:3.11.4-alpine as base
FROM base as builder

RUN apk --no-cache add \
  libjpeg-turbo-dev \
  zlib-dev \
  freetype-dev \
  lcms2-dev \
  openjpeg-dev \
  tiff-dev \
  tk-dev \
  tcl-dev

COPY requirements/prod.txt /requirements.txt
RUN pip install --user -r /requirements.txt

FROM base
WORKDIR /base

COPY --from=builder /root/.local /root/.local
COPY ./bot ./bot

ENV PATH=/root/.local:$PATH

CMD ["python", "-m", "bot"]
