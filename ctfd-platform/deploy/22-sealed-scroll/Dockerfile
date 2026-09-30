# Challenge 22 — Sealed Scroll (deployable version).
# An AES-CBC session token with no integrity check: vulnerable to a bit-flip.
FROM python:3.12-alpine

RUN pip install --no-cache-dir flask==3.0.3 pycryptodome==3.20.0

WORKDIR /app
COPY app.py /app/

EXPOSE 80
ENV PORT=80
CMD ["python", "app.py"]
