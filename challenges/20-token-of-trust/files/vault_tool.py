#!/usr/bin/env python3
# Oasis Portal - vault encryption tool (excerpt)
import hashlib
import os
import sys

# Same secret the portal uses to sign session tokens (HS256).
SECRET = os.environ["JWT_SECRET"]


def crypt(data: bytes) -> bytes:
    key = hashlib.sha256(SECRET.encode()).digest()
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, "rb") as f:
        data = f.read()
    with open(dst, "wb") as f:
        f.write(crypt(data))
