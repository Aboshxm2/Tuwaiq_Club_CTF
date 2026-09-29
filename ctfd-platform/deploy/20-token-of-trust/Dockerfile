# Challenge 20 — Token of Trust (deployable version).
# A staff portal that signs guest JWTs with a weak secret from a leaked wordlist.
FROM python:3.12-alpine

RUN pip install --no-cache-dir flask==3.0.3

WORKDIR /app
COPY app.py wordlist.txt /app/

EXPOSE 80
ENV PORT=80
CMD ["python", "app.py"]
