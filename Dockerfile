FROM python:3.11.4-alpine as base
FROM base as builder

RUN apk --no-cache add \
  freetype-dev \
  fribidi-dev \
  harfbuzz-dev \
  jpeg-dev \
  lcms2-dev \
  libimagequant-dev \
  openjpeg-dev \
  tcl-dev \
  tiff-dev \
  tk-dev \
  zlib-dev

COPY requirements/prod.txt /requirements.txt
RUN pip install --user -r /requirements.txt

FROM base
WORKDIR /base

COPY --from=builder /root/.local /root/.local
COPY ./bot ./bot

ENV PATH=/root/.local:$PATH

CMD ["python", "-m", "bot"]
