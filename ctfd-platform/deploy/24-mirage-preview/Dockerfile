# Challenge 24 — Mirage Preview (deployable version).
# A URL "link preview" service that is vulnerable to SSRF; the flag lives on a
# loopback-only admin service in the same container.
FROM python:3.12-alpine

RUN pip install --no-cache-dir flask==3.0.3

WORKDIR /app
COPY app.py /app/

EXPOSE 80
ENV PORT=80
CMD ["python", "app.py"]
