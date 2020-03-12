FROM python:3.7-slim-stretch as builder

RUN apt-get update \
  && apt-get -y --no-install-recommends install \
  g++ \
  gcc

ENV WORKDIR=/app
WORKDIR $WORKDIR

COPY LICENSE README.md $WORKDIR/
COPY setup.py $WORKDIR/

RUN pip install ".[all]"
RUN find /usr/local/lib/python3.7 \
  -name '*.pxd' -o \
  -name '*.pyd' -o \
  -name '*.pyc' -delete \
  && find /usr/local/lib/python3.7 \
  -path '*/tests/*' -delete \
  && find /usr/local/lib/python3.7 \
  -name '__pycache__' | xargs rm -r \
  && find /usr/local/lib/python3.7 \
  -name '*.so*' | xargs strip

COPY a2ml/ $WORKDIR/a2ml
COPY tests $WORKDIR/tests
RUN pip install -e .

FROM python:3.7-slim-stretch

ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1

ENV WORKDIR=/app
WORKDIR $WORKDIR

COPY --from=builder /usr/local/lib/python3.7 /usr/local/lib/python3.7
COPY --from=builder /usr/local/bin/celery /usr/local/bin/celery
COPY --from=builder /usr/local/bin/a2ml /usr/local/bin/a2ml
COPY --from=builder $WORKDIR $WORKDIR
COPY --from=builder /usr/local/bin/pytest /usr/local/bin/pytest
COPY --from=builder /usr/local/bin/tox /usr/local/bin/tox

#ENTRYPOINT /usr/local/bin/a2ml
