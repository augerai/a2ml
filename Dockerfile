FROM python:3.7-slim-stretch as base

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

COPY LICENSE README.md setup.py $WORKDIR/
# unused version so we get dependencies installed
RUN mkdir -p $WORKDIR/a2ml && \
  echo "__version__ = '99.99.99'" > $WORKDIR/a2ml/__init__.py

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
  -name '*.so*' | grep -v libgfortran | xargs strip

FROM base as runtime

ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1

ENV WORKDIR=/app
WORKDIR $WORKDIR

COPY --from=builder /usr/local/lib/python3.7 /usr/local/lib/python3.7
COPY --from=builder /usr/local/bin/celery /usr/local/bin/celery

COPY LICENSE README.md setup.py setup.cfg $WORKDIR/
COPY a2ml $WORKDIR/a2ml
COPY tests $WORKDIR/tests
RUN python setup.py bdist_wheel && \
  pip install -U --force-reinstall --no-cache-dir --no-deps dist/*

CMD /usr/local/bin/a2ml
