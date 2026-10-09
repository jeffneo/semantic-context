# syntax=docker/dockerfile:1
# The hosted demo: the built page and examples/fennmoor-bank/server.py in one image (plans/2026-10-08-cloud-deploy.md).
#
#   uv run examples/fennmoor-bank/generate/hosted_work.py            # first: the slice of work/ the page's questions read
#   docker build -f docker/demo/Dockerfile -t qlsc-demo .            # from the repository root
#
# What is not in it: any key. The server signs in to BigQuery as the service account it runs as (QLSC_OVERRIDES: warehouse.identity ambient), the model and
# embedding keys come in as environment variables, and the Virtual Graph's signing key is mounted at /secrets/passthrough/passthrough.key. Where the
# databases are comes in the same way, as an overrides file (docker/demo/overrides.compose.yaml is the one for this repository's compose).

# the page is plain files: built on the machine that builds, whatever it is, so an image for another architecture does not run npm under emulation
FROM --platform=$BUILDPLATFORM node:22-slim AS page
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
# the contact the page's header shows (ui/.env.local locally); the build writes ui/dist and dist/presets.json, the list of what a hosted server will run
ARG NEO4J_CONTACT_EMAIL=""
ENV NEO4J_CONTACT_EMAIL=$NEO4J_CONTACT_EMAIL
RUN npm run build

FROM python:3.12-slim AS app
COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY parser parser
COPY src src
RUN uv sync --frozen --no-dev --extra bigquery
COPY prompts prompts
COPY examples/fennmoor-bank/estate.yaml examples/fennmoor-bank/server.py examples/fennmoor-bank/demo.py examples/fennmoor-bank/
COPY examples/fennmoor-bank/conversations examples/fennmoor-bank/conversations
COPY examples/fennmoor-bank/designed examples/fennmoor-bank/designed
COPY examples/fennmoor-bank/build/hosted-work examples/fennmoor-bank/work
COPY --from=page /ui/dist ui/dist
RUN mkdir -p examples/fennmoor-bank/work/virtual /secrets/passthrough \
 && ln -s /secrets/passthrough/passthrough.key examples/fennmoor-bank/work/virtual/passthrough.key \
 && useradd --system --home /app app && chown -R app /app/examples/fennmoor-bank/work
USER app
ENV PATH="/app/.venv/bin:$PATH" QLSC_DEMO_HOSTED=1 QLSC_DEMO_HOST=0.0.0.0 PORT=8080
EXPOSE 8080
CMD ["python", "examples/fennmoor-bank/server.py"]
