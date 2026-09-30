# Challenge 25 — Floodgate Override (deployable, raw TCP / pwn).
# A ret2win binary served over TCP with socat. The build image is pinned so the
# compiled binary (and therefore win()'s address) is deterministic on every node.
FROM alpine:3.20 AS build
RUN apk add --no-cache build-base
WORKDIR /src
COPY floodgate.c /src/
# -no-pie + -fno-stack-protector: fixed win() address, no canary.
RUN gcc -fno-stack-protector -no-pie -O0 -w -o floodgate2 floodgate.c \
    && base64 floodgate2 > floodgate2.b64

FROM alpine:3.20
RUN apk add --no-cache socat
WORKDIR /app
COPY --from=build /src/floodgate2 /src/floodgate2.b64 /app/
COPY serve.sh /app/
RUN chmod +x /app/serve.sh /app/floodgate2

EXPOSE 9999
# fork: one binary per connection. -T60: drop idle connections after 60s.
CMD ["socat", "-T60", "TCP-LISTEN:9999,reuseaddr,fork", "EXEC:/app/serve.sh"]
