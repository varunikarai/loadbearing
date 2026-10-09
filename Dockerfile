# The hosted demo. Free targets (no keys, local backend, no model calls) run on
# demand inside this container: the examples and every benchmark case. Targets
# that would spend credits on Sandboxes or Nemotron are served from their runs
# recorded in demo/runs/, so a visit never costs anything.
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples
COPY bench/cases ./bench/cases
COPY demo/runs ./runs
RUN pip install --no-cache-dir . && useradd --create-home demo && chown -R demo runs
USER demo
ENV PORT=8000
EXPOSE 8000
CMD ["loadbearing", "serve", "--host", "0.0.0.0", "--readonly", \
     "--targets", "examples", "--targets", "bench/cases", "--cache", "runs"]
