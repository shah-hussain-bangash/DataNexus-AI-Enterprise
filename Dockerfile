FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY datanexus ./datanexus
COPY tests/fixtures ./tests/fixtures
RUN pip install --no-cache-dir ".[kafka]"
RUN useradd -r -u 10001 datanexus && mkdir -p /app/data/dev && chown -R datanexus:datanexus /app
USER datanexus
CMD ["python", "-m", "datanexus.cli", "--help"]
