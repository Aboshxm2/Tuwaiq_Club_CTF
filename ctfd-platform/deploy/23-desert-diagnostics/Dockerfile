# Challenge 23 — Desert Diagnostics (deployable version).
# A "ping" diagnostics page that shells out with the host field unsanitised.
FROM python:3.12-alpine

RUN pip install --no-cache-dir flask==3.0.3

WORKDIR /app
COPY app.py /app/

EXPOSE 80
ENV PORT=80
CMD ["python", "app.py"]
