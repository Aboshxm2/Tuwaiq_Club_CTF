# Challenge 21 — Caravan Ledger (deployable version).
# A caravan-manifest search page with a SQL-injectable search box (SQLite).
FROM python:3.12-alpine

RUN pip install --no-cache-dir flask==3.0.3

WORKDIR /app
COPY app.py /app/

EXPOSE 80
ENV PORT=80
CMD ["python", "app.py"]
