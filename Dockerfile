FROM python:3.7.17-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Tehran

WORKDIR /event_capture_lib

ENV PYTHONPATH: "${PYTHONPATH}:/event_capture_lib"

COPY --link ./requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY --link ./event_capture_lib /event_capture_lib

WORKDIR /

ENTRYPOINT python3 -m event_capture_lib.tests
