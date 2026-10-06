# The hosted demo. The local backend runs the example pipelines inside this
# container, which costs nothing per run. For the Sandboxes backend, record
# runs ahead of time and serve them with --readonly so visits never spend credits.
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples
RUN pip install --no-cache-dir . && useradd --create-home demo && mkdir runs && chown demo runs
USER demo
ENV PORT=8000
EXPOSE 8000
CMD ["loadbearing", "serve", "--host", "0.0.0.0", "--targets", "examples", "--cache", "runs"]
