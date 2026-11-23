# ---------- base: runtime dependencies only ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- test: adds pytest/flake8 and the test suite ----------
FROM base AS test
COPY requirements-dev.txt .flake8 ./
RUN pip install -r requirements-dev.txt
COPY VERSION ACEest_Fitness.py ./
COPY aceest/ aceest/
COPY tests/ tests/
CMD ["pytest", "-v"]

# ---------- runtime: small, non-root production image ----------
FROM base AS runtime
ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="aceest-fitness" \
      org.opencontainers.image.version="${APP_VERSION}"
RUN useradd --create-home --uid 10001 aceest \
    && mkdir /data && chown aceest /data
COPY --chown=aceest VERSION ACEest_Fitness.py ./
COPY --chown=aceest aceest/ aceest/
USER aceest
ENV ACEEST_DB=/data/aceest_fitness.db PORT=5000
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "ACEest_Fitness:app"]
