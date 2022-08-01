FROM python:3.10.5-slim

ADD migrations /migrations
COPY dist/mrmat_python_api_flask-*.whl /
RUN \
    groupadd -g 1000 flask \
    && useradd -u 1000 -g 1000 -c "Flask User" -M flask \
    && mkdir -p /app/instance \
    && chown -R 1000:1000 /app /app/instance

USER 1000:1000

ENV FLASK_APP=mrmat_python_api_flask
RUN \
    python -mvenv /app/venv \
    && . /app/venv/bin/activate \
    && python -m pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --no-cache-dir gunicorn \
    && pip install --no-cache-dir /mrmat_python_api_flask-*.whl \
    && flask db upgrade

USER 0:0
RUN \
    rm -rf /mrmat_python_api_flask-*.whl /migrations

EXPOSE 8080
USER 1000:1000
ENTRYPOINT /app/venv/bin/gunicorn -w 4 -b 0.0.0.0:8080 --error-logfile /app/instance/error.log --access-logfile /app/instance/access.log 'mrmat_python_api_flask:create_app()'
