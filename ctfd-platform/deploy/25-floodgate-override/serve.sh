#!/bin/sh
# One connection: hand the player the control program (so they can analyse it),
# then run it with stdin/stdout wired to the socket for the actual exploit.
# The binary does not contain the flag; whale passes the flag in FLAG at runtime.
printf '%s\n' '--- BEGIN floodgate (base64) ---'
cat /app/floodgate2.b64
printf '%s\n' '--- END floodgate (base64) ---'
exec /app/floodgate2
