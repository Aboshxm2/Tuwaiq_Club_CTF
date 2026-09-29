# Challenge 01 — Inspect the Oasis (deployable version).
# A tiny static site. The per-team flag arrives in the FLAG env var and is
# split across three files' comments when the container starts.
FROM nginx:1.27-alpine

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
