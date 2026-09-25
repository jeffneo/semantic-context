# qlsc-parse: stateless SQL parse service. The same image runs under docker-compose,
# Cloud Run (service or job) and AWS Lambda (via the Lambda Web Adapter extension).
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY qlsc_parse ./qlsc_parse
# sqlglot[c] ships mypyc-compiled modules inside the sqlglot package (~2.3x faster)
RUN pip install --no-cache-dir ".[serve]" && python -c "import qlsc_parse as q; print(q.PARSER_ID, 'compiled' if q.COMPILED else 'pure-python')"

ENV CATALOG_PATH=/catalog/catalog.json PORT=8080 WEB_CONCURRENCY=4
EXPOSE 8080
# One process per core; the catalog is loaded per worker on first request.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY} --timeout 120 qlsc_parse.service:app"]
