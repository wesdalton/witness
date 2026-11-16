# Sandbox image for the evidence-access benchmark (witness.evidence_access.execution.IMAGE).
# Build it under the name the runners expect:
#   docker build -t sandbox-default:latest docker/
# Workspaces are bind-mounted read-only at run time; the image itself is generic.
FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==8.4.1

WORKDIR /workspace
CMD ["tail", "-f", "/dev/null"]
