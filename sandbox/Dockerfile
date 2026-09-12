FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==8.4.1

# Files for the task are copied in by Inspect per-sample (see Sample.files);
# the image itself is deliberately generic.
WORKDIR /workspace
CMD ["tail", "-f", "/dev/null"]
