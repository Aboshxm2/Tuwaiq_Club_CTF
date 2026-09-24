#!/usr/bin/env python3
"""Solves challenges 11-20 using only the handout files and checks the results against FLAGS.

Run after build_handouts.py to confirm every challenge is still solvable:
    python3 organizer/verify_solutions.py
"""

import base64
import codecs
import hashlib
import hmac
import importlib.util
import json
import math
import re
import struct
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "challenges"
FLAG_RE = re.compile(rb"TAIBAH\{[ -|~]+?\}")

spec = importlib.util.spec_from_file_location("build_handouts", HERE / "build_handouts.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
FLAGS = build.FLAGS


def files(challenge: str) -> Path:
    return ROOT / challenge / "files"


def find_flag(data: bytes) -> str:
    m = FLAG_RE.search(data)
    if not m:
        raise ValueError("no flag found")
    return m.group().decode()


def solve_xor():
    ct = bytes.fromhex((files("11-sandstorm-xor") / "cipher.hex").read_text().strip())
    known = b"TAIBAH{"
    for length in range(1, len(known) + 1):
        key = bytes(ct[i] ^ known[i] for i in range(length))
        pt = bytes(b ^ key[i % length] for i, b in enumerate(ct))
        if all(32 <= b < 127 for b in pt):
            return find_flag(pt)
    raise ValueError("key not recovered")


def solve_rsa():
    values = dict(line.split(" = ") for line in (files("12-close-primes") / "public.txt").read_text().splitlines())
    n, e, c = (int(values[k]) for k in ("n", "e", "c"))
    a = math.isqrt(n)
    if a * a < n:
        a += 1
    while True:
        b2 = a * a - n
        b = math.isqrt(b2)
        if b * b == b2:
            break
        a += 1
    p, q = a - b, a + b
    assert p * q == n
    m = pow(c, pow(e, -1, (p - 1) * (q - 1)), n)
    return find_flag(m.to_bytes((m.bit_length() + 7) // 8, "big"))


ENGLISH = [8.2, 1.5, 2.8, 4.3, 12.7, 2.2, 2.0, 6.1, 7.0, 0.15, 0.77, 4.0, 2.4,
           6.7, 7.5, 1.9, 0.095, 6.0, 6.3, 9.1, 2.8, 0.98, 2.4, 0.15, 2.0, 0.074]


def solve_vigenere():
    text = (files("13-the-merchants-letter") / "letter.txt").read_text()
    letters = [ord(c.upper()) - 65 for c in text if c.isascii() and c.isalpha()]

    def ic(col):
        n = len(col)
        return sum(col.count(i) * (col.count(i) - 1) for i in range(26)) / (n * (n - 1))

    length = next(k for k in range(1, 20)
                  if sum(ic(letters[i::k]) for i in range(k)) / k > 0.065)
    key = ""
    for i in range(length):
        col = letters[i::length]

        def chi(shift):
            counts = [0] * 26
            for v in col:
                counts[(v - shift) % 26] += 1
            return sum((counts[j] - len(col) * ENGLISH[j] / 100) ** 2 / (len(col) * ENGLISH[j] / 100)
                       for j in range(26))

        key += chr(65 + min(range(26), key=chi))
    return find_flag(build.vigenere(text, key, sign=-1).encode())


def solve_zip():
    with zipfile.ZipFile(files("14-locked-vault") / "vault.zip") as zf:
        for pin in range(1_000_000):
            pwd = f"{pin:06d}".encode()
            try:
                data = zf.read("flag.txt", pwd=pwd)
            except Exception:
                continue
            return find_flag(data)
    raise ValueError("PIN not found")


def inet_ok(data: bytes) -> bool:
    return build.inet_checksum(data) == 0


def solve_pcap():
    raw = (files("15-wiretap") / "capture.pcap").read_bytes()
    assert struct.unpack("<I", raw[:4])[0] == 0xA1B2C3D4
    off, streams = 24, {}
    while off < len(raw):
        _, _, incl, _ = struct.unpack("<IIII", raw[off:off + 16])
        frame = raw[off + 16:off + 16 + incl]
        off += 16 + incl
        ip = frame[14:]
        ihl = (ip[0] & 0x0F) * 4
        assert inet_ok(ip[:ihl]), "bad IP checksum"
        seg = ip[ihl:struct.unpack("!H", ip[2:4])[0]]
        pseudo = ip[12:20] + struct.pack("!BBH", 0, 6, len(seg))
        assert inet_ok(pseudo + seg), "bad TCP checksum"
        sport, dport = struct.unpack("!HH", seg[:4])
        payload = seg[(seg[12] >> 4) * 4:]
        key = (min(sport, dport), max(sport, dport))
        streams.setdefault(key, {"c": b"", "s": b""})["s" if sport == 80 else "c"] += payload
    for s in streams.values():
        if s["c"].startswith(b"POST /login") and s["s"].startswith(b"HTTP/1.1 302"):
            body = s["c"].split(b"\r\n\r\n", 1)[1].decode()
            return urllib.parse.parse_qs(body)["password"][0]
    raise ValueError("successful login not found")


def solve_lsb():
    data = (files("16-pixel-secrets") / "dunes.png").read_bytes()
    off, idat, w, h = 8, b"", 0, 0
    while off < len(data):
        length, kind = struct.unpack(">I4s", data[off:off + 8])
        body = data[off + 8:off + 8 + length]
        if kind == b"IHDR":
            w, h = struct.unpack(">II", body[:8])
        elif kind == b"IDAT":
            idat += body
        off += 12 + length
    raw = zlib.decompress(idat)
    stride = w * 3 + 1
    pixels = bytearray()
    for y in range(h):
        assert raw[y * stride] == 0, "only filter type 0 is handled"
        pixels += raw[y * stride + 1:(y + 1) * stride]
    bits = "".join(str(b & 1) for b in pixels)
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = int(bits[i:i + 8], 2)
        if byte == 0:
            break
        out.append(byte)
    return find_flag(bytes(out))


def solve_elf():
    binary = files("17-floodgate") / "floodgate"
    blob = binary.read_bytes()
    for start in range(len(blob) - 8):
        st, out = build.ELF_SEED, bytearray()
        for i in range(min(128, len(blob) - start)):
            st = (st * 37 + 11) & 0xFF
            c = ((blob[start + i] - 3 * i) & 0xFF) ^ st
            out.append(c)
            if i < 7 and out != b"TAIBAH{"[:i + 1]:
                break
            if c == ord("}"):
                candidate = out.decode()
                result = subprocess.run([str(binary)], input=candidate + "\n",
                                        capture_output=True, text=True, timeout=5)
                assert "OVERRIDE ACCEPTED" in result.stdout, result.stdout
                return candidate
    raise ValueError("encoded flag not found")


def solve_git():
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(files("18-deleted-not-forgotten") / "oasis-portal.tar.gz") as tar:
            tar.extractall(tmp, filter="data")
        repo = Path(tmp) / "oasis-portal"
        head = subprocess.run(["git", "grep", "TAIBAH", "HEAD"], cwd=repo, capture_output=True)
        assert head.returncode == 1, "flag should not be in the latest commit"
        log = subprocess.run(["git", "log", "-p", "--all"], cwd=repo, capture_output=True, check=True)
        return find_flag(log.stdout)


def solve_onion():
    data = (files("19-onion-layers") / "layers.txt").read_text().strip()
    data = base64.b64decode(data)
    data = bytes.fromhex(data.decode())
    data = base64.b32decode(data)
    data = zlib.decompress(data)
    return codecs.decode(data.decode(), "rot13")


def solve_jwt():
    d = files("20-token-of-trust")
    header, payload, sig = (d / "token.txt").read_text().strip().split(".")
    assert json.loads(base64.urlsafe_b64decode(header + "=="))["alg"] == "HS256"
    want = base64.urlsafe_b64decode(sig + "==")
    for word in (d / "wordlist.txt").read_text().split():
        if hmac.compare_digest(hmac.new(word.encode(), f"{header}.{payload}".encode(),
                                        hashlib.sha256).digest(), want):
            key = hashlib.sha256(word.encode()).digest()
            vault = (d / "vault.enc").read_bytes()
            return find_flag(bytes(b ^ key[i % 32] for i, b in enumerate(vault)))
    raise ValueError("secret not in wordlist")


CHECKS = [
    ("11 Sandstorm XOR", solve_xor, "xor"),
    ("12 Close Primes", solve_rsa, "rsa"),
    ("13 The Merchant's Letter", solve_vigenere, "vigenere"),
    ("14 Locked Vault", solve_zip, "zip"),
    ("15 Wiretap", solve_pcap, "pcap"),
    ("16 Pixel Secrets", solve_lsb, "lsb"),
    ("17 Floodgate", solve_elf, "elf"),
    ("18 Deleted but Not Forgotten", solve_git, "git"),
    ("19 Onion Layers", solve_onion, "onion"),
    ("20 Token of Trust", solve_jwt, "jwt"),
]

if __name__ == "__main__":
    failed = 0
    for name, solver, key in CHECKS:
        try:
            got = solver()
            ok = got == FLAGS[key]
        except Exception as exc:
            got, ok = f"error: {exc}", False
        failed += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {got}")
    sys.exit(1 if failed else 0)
