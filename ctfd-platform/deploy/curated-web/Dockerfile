FROM python:3.12-alpine
RUN pip install --no-cache-dir flask==3.0.3
WORKDIR /app
COPY app.py /app/app.py
ARG CHALLENGE=last-edit
ENV CHALLENGE=${CHALLENGE} PORT=8080 PYTHONDONTWRITEBYTECODE=1
RUN adduser -D -u 10001 challenge
USER challenge
EXPOSE 8080
CMD ["python", "app.py"]
