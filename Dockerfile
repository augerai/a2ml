FROM python:3.8.5-slim-stretch as base

RUN apt-get update \
  && apt-get -y --no-install-recommends install \
    gcc \
    g++ \
    libgomp1 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

FROM base as builder

ENV WORKDIR=/app
WORKDIR $WORKDIR

COPY LICENSE README.md $WORKDIR/
COPY setup.py $WORKDIR/

RUN pip install ".[testing,server,azure,google]"
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

FROM base

ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1

ENV WORKDIR=/app
WORKDIR $WORKDIR

COPY --from=builder /usr/local/lib/python3.7 /usr/local/lib/python3.7
COPY --from=builder /usr/local/bin/celery /usr/local/bin/celery
COPY --from=builder /usr/local/bin/pytest /usr/local/bin/pytest
COPY --from=builder /usr/local/bin/tox /usr/local/bin/tox

COPY LICENSE README.md setup.py tox.ini $WORKDIR/
COPY a2ml $WORKDIR/a2ml
COPY tests $WORKDIR/tests
RUN python setup.py bdist_wheel && \
  pip install -U --no-deps dist/*

CMD /usr/local/bin/a2ml
