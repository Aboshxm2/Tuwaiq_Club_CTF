# 22 — Sealed Scroll (deployable)

An AES-CBC bit-flipping challenge. Each team gets its own scroll archive.

- **Type:** `dynamic_docker` (ctfd-whale), HTTP redirect, port 80.
- **Flag:** injected by whale as the `FLAG` env var; returned by `/vault` to a
  scroll whose first block decrypts to `role=admin`.
- **Vulnerability:** the session "scroll" is `base64url(IV || AES-CBC(plaintext))`
  with **no MAC**. The AES key is random per container. The first plaintext block
  is `role=guest;xxxxx`, shown on the home page.
- **Intended solve (organizer note):** CBC decrypts block 0 as
  `P0 = D(C0) XOR IV`, so flipping `IV[i]` flips plaintext byte `i`. For the five
  bytes of `guest` (offsets 5..9), set
  `new_iv[i] = iv[i] ^ ord("guest"[i-5]) ^ ord("admin"[i-5])`, re-encode the
  scroll, and send it to `/vault`. Only the IV changes, so the PKCS7 pad block
  stays valid.

Because the key is random per container, a scroll forged for one team's instance
is meaningless against another's, and the flag is per-team.

## Local test

```sh
docker build -t taibah-ctf/22-sealed-scroll:latest .
docker run --rm -p 8022:80 -e FLAG='TAIBAH{test}' taibah-ctf/22-sealed-scroll:latest
# open http://localhost:8022/ , then flip IV bytes 5..9 and GET /vault?token=...
```
