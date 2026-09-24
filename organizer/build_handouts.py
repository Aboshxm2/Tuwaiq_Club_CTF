#!/usr/bin/env python3
"""Regenerates every challenge handout file. Edit FLAGS below to change flags."""

import base64
import codecs
import datetime
import hashlib
import hmac
import io
import json
import math
import os
import random
import shutil
import struct
import subprocess
import tarfile
import tempfile
import urllib.parse
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "challenges"

FLAGS = {
    "web": ("TAIBAH{1nsp3ct_", "th3_", "s0urc3}"),
    "base64": "TAIBAH{b4s364_1s_n0t_3ncrypt10n}",
    "caesar": "TAIBAH{ju11us_w0uld_b3_pr0ud}",
    "binary": "TAIBAH{b1n4ry_1s_th3_l4ngu4g3}",
    "hash_word": "falcon",
    "strings": "TAIBAH{str1ngs_r3v34l_s3cr3ts}",
    "magic": "TAIBAH{m4g1c_byt3s_d0nt_l13}",
    "hidden": "TAIBAH{h1dd3n_f1l3s_4r3_n0t_s0_h1dd3n}",
    "reverse": "TAIBAH{r3v3rs1ng_1s_fun}",
    "log_ip": "203.0.113.66",
    "log_user": "webadmin",
    "xor": "TAIBAH{x0r_w1th_4_sh0rt_k3y_1s_w34k}",
    "xor_key": "DUNE5",
    "rsa": "TAIBAH{cl0s3_pr1m3s_f4ll_t0_f3rm4t}",
    "vigenere": "TAIBAH{v1g3n3r3_h1d3s_n0_s3cr3ts}",
    "vigenere_key": "MIRAGE",
    "zip": "TAIBAH{s1x_d1g1ts_4r3_n0t_3n0ugh}",
    "zip_pin": "739214",
    "pcap": "TAIBAH{cl34rt3xt_http_l34ks_cr3ds}",
    "lsb": "TAIBAH{l34st_s1gn1f1c4nt_s3cr3ts}",
    "elf": "TAIBAH{gh1dr4_s33s_thr0ugh_y0u}",
    "git": "TAIBAH{g1t_n3v3r_f0rg3ts_4_c0mm1t}",
    "onion": "TAIBAH{p33l1ng_th3_3nc0d1ng_0n10n}",
    "jwt": "TAIBAH{w34k_jwt_s3cr3ts_unl0ck_v4ults}",
    "jwt_secret": "mirage2025",
}


def out(challenge: str) -> Path:
    p = ROOT / challenge / "files"
    p.mkdir(parents=True, exist_ok=True)
    return p


def caesar(text: str, shift: int) -> str:
    res = []
    for c in text:
        if c.isupper():
            res.append(chr((ord(c) - 65 + shift) % 26 + 65))
        elif c.islower():
            res.append(chr((ord(c) - 97 + shift) % 26 + 97))
        else:
            res.append(c)
    return "".join(res)


def build_web():
    d = out("01-inspect-the-oasis")
    p1, p2, p3 = FLAGS["web"]
    (d / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Oasis Travel Agency</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header>
    <h1>Oasis Travel Agency</h1>
    <p>Your journey through the desert starts here.</p>
  </header>
  <main>
    <h2>Our Tours</h2>
    <ul>
      <li>Desert camping under the stars</li>
      <li>Date farm visits</li>
      <li>Historic Hejaz railway tour</li>
    </ul>
    <!-- Developer note: remove before going live! Part 1/3 of the flag: {p1} -->
    <button onclick="bookNow()">Book Now</button>
  </main>
  <script src="script.js"></script>
</body>
</html>
""")
    (d / "style.css").write_text(f"""body {{
  font-family: Arial, sans-serif;
  background-color: #f4e4c1;
  color: #4a3b2a;
  margin: 0;
  padding: 0;
}}

header {{
  background-color: #c2a36b;
  padding: 20px;
  text-align: center;
}}

/* Part 2/3 of the flag: {p2} */

main {{
  padding: 20px;
}}

button {{
  background-color: #8b5e3c;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}}
""")
    (d / "script.js").write_text(f"""function bookNow() {{
  alert("Sorry, all tours are fully booked this week!");
}}

// Part 3/3 of the flag: {p3}
""")


def build_base64():
    return base64.b64encode(FLAGS["base64"].encode()).decode()


def build_caesar():
    return caesar(FLAGS["caesar"], 3)


def build_binary():
    return " ".join(format(ord(c), "08b") for c in FLAGS["binary"])


def build_hash():
    return hashlib.md5(FLAGS["hash_word"].encode()).hexdigest()


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def build_strings():
    d = out("06-desert-picture")
    w, h = 64, 64
    raw = b"".join(b"\x00" + bytes([0xE6, 0xC2, 0x8A]) * w for _ in range(h))
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += png_chunk(b"tEXt", b"Comment\x00Photo taken near the oasis. " + FLAGS["strings"].encode())
    png += png_chunk(b"IDAT", zlib.compress(raw, 9))
    png += png_chunk(b"IEND", b"")
    (d / "desert.png").write_bytes(png)


def build_magic():
    d = out("07-not-a-pdf")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("report/flag.txt", f"Well done! Here is your flag:\n{FLAGS['magic']}\n")
        z.writestr("report/notes.txt", "Quarterly report draft. Nothing to see here.\n" * 5)
    (d / "report.pdf").write_bytes(buf.getvalue())


def build_hidden():
    d = out("08-camel-caravan")
    files = {
        "caravan/README.txt": "Welcome to the caravan. The flag is hiding somewhere in here.\n",
        "caravan/day1/supplies.txt": "Water: 20 litres\nDates: 5 kg\nBread: 10 loaves\n",
        "caravan/day1/route.txt": "Start at the oasis, head north towards the mountains.\n",
        "caravan/day2/camels.txt": "Camels: Sahab, Barq, Najm, Reem\n",
        "caravan/day2/flag.txt": "Nope, not this one. Keep looking!\n",
        "caravan/day3/tent/notes.txt": "Some things are only visible if you know how to look...\n",
        "caravan/day3/tent/.secret/.flag.txt": FLAGS["hidden"] + "\n",
        "caravan/day4/weather.txt": "Sunny, 42C. Sandstorm expected in the evening.\n",
    }
    tar_path = d / "caravan.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        dirs = sorted({str(Path(f).parent) for f in files} | {"caravan"})
        all_dirs = set()
        for dd in dirs:
            parts = Path(dd).parts
            for i in range(1, len(parts) + 1):
                all_dirs.add(str(Path(*parts[:i])))
        for dd in sorted(all_dirs):
            info = tarfile.TarInfo(dd)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            tar.addfile(info)
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))


def build_reverse():
    d = out("09-password-checker")
    key = 0x2A
    encoded = [ord(c) ^ key for c in FLAGS["reverse"]]
    (d / "checker.py").write_text(f"""#!/usr/bin/env python3
# Oasis Vault - Password Checker v1.0

SECRET = {encoded}
KEY = {key}


def check(password):
    if len(password) != len(SECRET):
        return False
    for i in range(len(password)):
        if ord(password[i]) ^ KEY != SECRET[i]:
            return False
    return True


def main():
    print("=== Oasis Vault ===")
    password = input("Enter the password: ")
    if check(password):
        print("Access granted! The password is the flag.")
    else:
        print("Access denied.")


if __name__ == "__main__":
    main()
""")


def build_logs():
    d = out("10-who-broke-in")
    rng = random.Random(1445)
    users = ["ahmed", "sara", "omar", "noura", "faisal", "reem"]
    legit_ips = ["10.0.0.12", "10.0.0.15", "10.0.0.23", "10.0.0.31", "10.0.0.44"]
    noise_ips = ["198.51.100.7", "198.51.100.23", "192.0.2.14", "192.0.2.88"]
    attacker = FLAGS["log_ip"]
    target = FLAGS["log_user"]

    events = []
    t = 8 * 3600
    for _ in range(400):
        t += rng.randint(5, 60)
        r = rng.random()
        if r < 0.75:
            u, ip = rng.choice(users), rng.choice(legit_ips)
            events.append((t, f"Accepted password for {u} from {ip} port {rng.randint(40000, 65000)} ssh2"))
        elif r < 0.9:
            u, ip = rng.choice(users), rng.choice(legit_ips)
            events.append((t, f"Failed password for {u} from {ip} port {rng.randint(40000, 65000)} ssh2"))
        else:
            ip = rng.choice(noise_ips)
            u = rng.choice(["root", "test", "guest"])
            events.append((t, f"Failed password for invalid user {u} from {ip} port {rng.randint(40000, 65000)} ssh2"))

    attack_start = 8 * 3600 + 3 * 3600
    at = attack_start
    for _ in range(312):
        at += rng.randint(1, 3)
        events.append((at, f"Failed password for {target} from {attacker} port {rng.randint(40000, 65000)} ssh2"))
    at += 2
    events.append((at, f"Accepted password for {target} from {attacker} port {rng.randint(40000, 65000)} ssh2"))
    events.sort(key=lambda e: e[0])

    lines = []
    for ts, msg in events:
        hh, mm, ss = ts // 3600 % 24, ts // 60 % 60, ts % 60
        pid = rng.randint(1000, 9999)
        lines.append(f"Sep 24 {hh:02d}:{mm:02d}:{ss:02d} taibah-srv sshd[{pid}]: {msg}")
    (d / "auth.log").write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Medium / advanced challenges (11-20)
# ---------------------------------------------------------------------------

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def build_xor():
    d = out("11-sandstorm-xor")
    msg = f"{FLAGS['xor']} -- Meet me at the old well after sunset. Come alone."
    ct = xor_bytes(msg.encode(), FLAGS["xor_key"].encode())
    (d / "cipher.hex").write_text(ct.hex() + "\n")


def is_probable_prime(n: int) -> bool:
    if n < 2:
        return False
    bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)
    for p in bases:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in bases:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def next_prime(n: int) -> int:
    n |= 1
    while not is_probable_prime(n):
        n += 2
    return n


def build_rsa():
    d = out("12-close-primes")
    rng = random.Random(2026)
    e = 65537
    while True:
        p = next_prime(rng.getrandbits(512) | (1 << 511))
        q = next_prime(p + rng.randint(10**6, 10**7))
        if math.gcd(e, (p - 1) * (q - 1)) == 1:
            break
    n = p * q
    c = pow(int.from_bytes(FLAGS["rsa"].encode(), "big"), e, n)
    (d / "public.txt").write_text(f"n = {n}\ne = {e}\nc = {c}\n")


VIGENERE_LETTER = """Dear brother Saleh,

Our caravan reached the oasis of Khaybar after nine long days in the open desert.
The camels are tired but healthy, and the traders here paid a fair price for the
dates and the woven carpets. Tomorrow we travel north along the old pilgrim road
towards the mountains, where the nights are cold and the wells are few.

Do not trust the messenger who carries this letter. He talks too much in the
markets and I believe he reads everything he carries. That is why I have written
this letter in our family cipher, the same one our grandfather taught us when we
were children sitting around the fire.

The storehouse behind the old mosque is locked. The password to open it is
written below, exactly as you must say it to the guard at the gate:

{flag}

Burn this letter after you read it. May God keep you safe until we meet again in
Madinah before the end of the month.

Your brother,
Faisal
"""


def vigenere(text: str, key: str, sign: int = 1) -> str:
    res, i = [], 0
    for c in text:
        if c.isalpha() and c.isascii():
            base = 65 if c.isupper() else 97
            k = ord(key[i % len(key)].upper()) - 65
            res.append(chr((ord(c) - base + sign * k) % 26 + base))
            i += 1
        else:
            res.append(c)
    return "".join(res)


def build_vigenere():
    d = out("13-the-merchants-letter")
    letter = VIGENERE_LETTER.format(flag=FLAGS["vigenere"])
    (d / "letter.txt").write_text(vigenere(letter, FLAGS["vigenere_key"]))


def build_zip():
    d = out("14-locked-vault")
    target = d / "vault.zip"
    target.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "flag.txt").write_text(f"Vault opened. Your flag:\n{FLAGS['zip']}\n")
        (tmp / "inventory.csv").write_text(
            "item,quantity\ngold coins,1200\nsilver rings,85\nsaffron (kg),14\nincense (kg),40\n")
        subprocess.run(["zip", "-q", "-j", "-X", "-P", FLAGS["zip_pin"], str(target),
                        str(tmp / "flag.txt"), str(tmp / "inventory.csv")], check=True)


def inet_checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


SYN, FIN, PSH, ACK = 0x02, 0x01, 0x08, 0x10


class PcapWriter:
    def __init__(self, start: float):
        self.t = start
        self.ip_id = 0x1000
        self.data = bytearray(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))

    def tcp(self, src, dst, sport, dport, seq, ack, flags, payload=b"", dt=0.001):
        s, t = bytes(map(int, src.split("."))), bytes(map(int, dst.split(".")))
        hdr = struct.pack("!HHIIBBHHH", sport, dport, seq & 0xFFFFFFFF, ack & 0xFFFFFFFF,
                          5 << 4, flags, 64240, 0, 0)
        pseudo = s + t + struct.pack("!BBH", 0, 6, len(hdr) + len(payload))
        seg = hdr[:16] + struct.pack("!H", inet_checksum(pseudo + hdr + payload)) + hdr[18:] + payload
        self.ip_id += 1
        ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(seg), self.ip_id, 0x4000, 64, 6, 0, s, t)
        ip = ip[:10] + struct.pack("!H", inet_checksum(ip)) + ip[12:]
        frame = b"\x02\x00" + t + b"\x02\x00" + s + b"\x08\x00" + ip + seg
        self.t += dt
        sec = int(self.t)
        usec = min(int((self.t - sec) * 1_000_000), 999_999)
        self.data += struct.pack("<IIII", sec, usec, len(frame), len(frame)) + frame

    def http_exchange(self, rng, client, server, sport, request: bytes, response: bytes, gap: float):
        cseq, sseq = rng.getrandbits(32), rng.getrandbits(32)
        self.tcp(client, server, sport, 80, cseq, 0, SYN, dt=gap)
        cseq += 1
        self.tcp(server, client, 80, sport, sseq, cseq, SYN | ACK, dt=0.0004)
        sseq += 1
        self.tcp(client, server, sport, 80, cseq, sseq, ACK, dt=0.0001)
        self.tcp(client, server, sport, 80, cseq, sseq, PSH | ACK, request, dt=0.0002)
        cseq += len(request)
        self.tcp(server, client, 80, sport, sseq, cseq, ACK, dt=0.0003)
        for i in range(0, len(response), 1400):
            chunk = response[i:i + 1400]
            self.tcp(server, client, 80, sport, sseq, cseq, PSH | ACK, chunk, dt=0.002)
            sseq += len(chunk)
        self.tcp(client, server, sport, 80, cseq, sseq, ACK, dt=0.0002)
        self.tcp(server, client, 80, sport, sseq, cseq, FIN | ACK, dt=0.0002)
        sseq += 1
        self.tcp(client, server, sport, 80, cseq, sseq, FIN | ACK, dt=0.0002)
        cseq += 1
        self.tcp(server, client, 80, sport, sseq, cseq, ACK, dt=0.0002)


def http_request(method, path, body=b"", extra=""):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
    head = (f"{method} {path} HTTP/1.1\r\nHost: intranet.oasis.local\r\nUser-Agent: {ua}\r\n"
            f"Accept: */*\r\nConnection: close\r\n{extra}")
    if body:
        head += f"Content-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(body)}\r\n"
    return head.encode() + b"\r\n" + body


def http_response(status, body=b"", ctype="text/html", extra=""):
    return (f"HTTP/1.1 {status}\r\nServer: nginx/1.24.0\r\nContent-Type: {ctype}\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n{extra}\r\n").encode() + body


def build_pcap():
    d = out("15-wiretap")
    rng = random.Random(1515)
    start = datetime.datetime(2026, 9, 24, 9, 15, tzinfo=datetime.timezone.utc).timestamp()
    pcap = PcapWriter(start)
    client, server = "10.0.0.23", "10.0.0.80"

    home = b"<html><head><title>Oasis Intranet</title><link rel='stylesheet' href='/style.css'></head>" \
           b"<body><h1>Oasis Travel Intranet</h1><a href='/login'>Staff login</a></body></html>"
    css = b"body { font-family: sans-serif; background: #f4e4c1; }\nh1 { color: #8b5e3c; }\n"
    form = b"<html><body><h2>Staff Login</h2><form method='POST' action='/login'>" \
           b"<input name='username'><input name='password' type='password'>" \
           b"<button>Login</button></form></body></html>"
    fail = b"<html><body><p>Invalid username or password.</p></body></html>"
    dash = b"<html><body><h2>Welcome back, admin</h2><p>3 new bookings today.</p></body></html>"

    good = urllib.parse.urlencode({"username": "admin", "password": FLAGS["pcap"]}).encode()
    exchanges = [
        (http_request("GET", "/"), http_response("200 OK", home)),
        (http_request("GET", "/style.css"), http_response("200 OK", css, "text/css")),
        (http_request("GET", "/favicon.ico"), http_response("404 Not Found", b"Not Found", "text/plain")),
        (http_request("GET", "/login"), http_response("200 OK", form)),
        (http_request("POST", "/login", b"username=admin&password=Oasis%402025"),
         http_response("401 Unauthorized", fail)),
        (http_request("POST", "/login", b"username=admin&password=admin123"),
         http_response("401 Unauthorized", fail)),
        (http_request("POST", "/login", good),
         http_response("302 Found", b"", extra="Location: /dashboard\r\n"
                       "Set-Cookie: session=6f1c2a9e4b; HttpOnly\r\n")),
        (http_request("GET", "/dashboard", extra="Cookie: session=6f1c2a9e4b\r\n"),
         http_response("200 OK", dash)),
    ]
    sport = 49712
    for req, resp in exchanges:
        sport += rng.randint(1, 4)
        pcap.http_exchange(rng, client, server, sport, req, resp, gap=rng.uniform(0.3, 4.0))
    (d / "capture.pcap").write_bytes(bytes(pcap.data))


def build_lsb():
    d = out("16-pixel-secrets")
    w, h = 160, 120
    bits = "".join(format(b, "08b") for b in FLAGS["lsb"].encode() + b"\x00")
    idx = 0
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            horizon = 70 + 10 * math.sin(x / 17) + 4 * math.sin(x / 5)
            if y < horizon:
                px = [min(255, 110 + y), min(255, 170 + y // 2), 235]
            else:
                shade = int(18 * math.sin((x + y * 2) / 9))
                px = [215 + shade // 2, 175 + shade, 110 + shade]
            for i in range(3):
                if idx < len(bits):
                    px[i] = (px[i] & 0xFE) | int(bits[idx])
                    idx += 1
            raw += bytes(max(0, min(255, v)) for v in px)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += png_chunk(b"tEXt", b"Comment\x00Nice try! The flag is not in the metadata this time.")
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    (d / "dunes.png").write_bytes(png)


ELF_SOURCE = r"""
#include <stdio.h>
#include <string.h>
#include <sys/ptrace.h>

static const unsigned char ENC[] = { @ENC@ };

static int check(const char *s)
{
    size_t n = sizeof(ENC);
    unsigned char st = @SEED@, diff = 0;
    if (strlen(s) != n)
        return 0;
    for (size_t i = 0; i < n; i++) {
        st = (unsigned char)(st * 37 + 11);
        diff |= (unsigned char)((unsigned char)(((unsigned char)s[i] ^ st) + 3 * i) ^ ENC[i]);
    }
    return diff == 0;
}

int main(void)
{
    char buf[128];
    if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1) {
        puts("Debugger detected. Floodgates locked.");
        return 1;
    }
    puts("=== Oasis Dam Control Panel ===");
    printf("Enter the override code: ");
    fflush(stdout);
    if (!fgets(buf, sizeof(buf), stdin))
        return 1;
    buf[strcspn(buf, "\n")] = '\0';
    if (check(buf))
        puts("OVERRIDE ACCEPTED. The override code is the flag.");
    else
        puts("ACCESS DENIED.");
    return 0;
}
"""

ELF_SEED = 0x5C


def build_elf():
    d = out("17-floodgate")
    if not shutil.which("gcc"):
        print("warning: gcc not found, skipping 17-floodgate (existing binary kept)")
        return
    st, enc = ELF_SEED, []
    for i, c in enumerate(FLAGS["elf"].encode()):
        st = (st * 37 + 11) & 0xFF
        enc.append(((c ^ st) + 3 * i) & 0xFF)
    src = ELF_SOURCE.replace("@ENC@", ", ".join(f"0x{b:02x}" for b in enc)).replace("@SEED@", hex(ELF_SEED))
    with tempfile.TemporaryDirectory() as tmp:
        c_file = Path(tmp) / "floodgate.c"
        c_file.write_text(src)
        subprocess.run(["gcc", "-O1", "-s", "-o", str(d / "floodgate"), str(c_file)], check=True)
    (d / "floodgate").chmod(0o755)


def build_git():
    d = out("18-deleted-not-forgotten")
    commits = [
        ("2026-08-02T10:14:00+03:00", "Initial commit", {
            "README.md": "# Oasis Portal\n\nInternal booking portal for Oasis Travel Agency.\n",
            "app.py": "from flask import Flask\n\napp = Flask(__name__)\n\n\n@app.route('/')\n"
                      "def index():\n    return 'Oasis Portal'\n",
        }),
        ("2026-08-09T16:40:00+03:00", "Add payment gateway integration", {
            "config.py": "# Payment gateway settings\nPAYMENT_API_URL = \"https://pay.oasis.example/v1\"\n"
                         f"PAYMENT_API_KEY = \"{FLAGS['git']}\"\n",
        }),
        ("2026-08-10T09:05:00+03:00", "Move secrets to environment variables", {
            "config.py": "import os\n\n# Payment gateway settings\n"
                         "PAYMENT_API_URL = \"https://pay.oasis.example/v1\"\n"
                         "PAYMENT_API_KEY = os.environ[\"PAYMENT_API_KEY\"]\n",
            ".gitignore": ".env\n__pycache__/\n",
        }),
        ("2026-08-21T13:22:00+03:00", "Add health check endpoint", {
            "app.py": "from flask import Flask\n\napp = Flask(__name__)\n\n\n@app.route('/')\n"
                      "def index():\n    return 'Oasis Portal'\n\n\n@app.route('/health')\n"
                      "def health():\n    return {'status': 'ok'}\n",
        }),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "oasis-portal"
        repo.mkdir()
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
               "GIT_AUTHOR_NAME": "Khalid", "GIT_AUTHOR_EMAIL": "khalid@oasis.example",
               "GIT_COMMITTER_NAME": "Khalid", "GIT_COMMITTER_EMAIL": "khalid@oasis.example"}

        def git(*args, date=None):
            e = env if date is None else {**env, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
            subprocess.run(["git", *args], cwd=repo, env=e, check=True, capture_output=True)

        git("init", "-q", "-b", "main")
        for date, message, files in commits:
            for name, content in files.items():
                (repo / name).write_text(content)
            git("add", "-A")
            git("commit", "-q", "-m", message, date=date)
        git("gc", "-q")
        with tarfile.open(d / "oasis-portal.tar.gz", "w:gz") as tar:
            tar.add(repo, arcname="oasis-portal")


def build_onion():
    d = out("19-onion-layers")
    data = codecs.encode(FLAGS["onion"], "rot13").encode()
    data = zlib.compress(data, 9)
    data = base64.b32encode(data)
    data = data.hex().encode()
    data = base64.b64encode(data)
    (d / "layers.txt").write_text(data.decode() + "\n")


JWT_WORDS = [
    "123456", "password", "12345678", "qwerty", "123456789", "12345", "1234", "111111", "1234567",
    "dragon", "123123", "baseball", "abc123", "football", "monkey", "letmein", "shadow", "master",
    "666666", "qwertyuiop", "123321", "mustang", "1234567890", "michael", "654321", "superman",
    "1qaz2wsx", "7777777", "121212", "000000", "qazwsx", "123qwe", "killer", "trustno1", "jordan",
    "jennifer", "zxcvbnm", "asdfgh", "hunter", "buster", "soccer", "harley", "batman", "andrew",
    "tigger", "sunshine", "iloveyou", "charlie", "robert", "thomas", "hockey", "ranger", "daniel",
    "starwars", "112233", "george", "computer", "michelle", "jessica", "pepper", "zxcvbn", "555555",
    "11111111", "131313", "freedom", "777777", "pass", "maggie", "159753", "aaaaaa", "ginger",
    "princess", "joshua", "cheese", "amanda", "summer", "love", "ashley", "nicole", "chelsea",
    "matthew", "access", "yankees", "987654321", "dallas", "austin", "thunder", "taylor", "matrix",
    "secret", "admin", "welcome", "changeme", "jwtsecret", "supersecret", "s3cr3t", "secretkey",
]
JWT_THEMED = ["oasis", "desert", "falcon", "camel", "madinah", "taibah", "mirage", "sandstorm",
              "caravan", "palmtree"]

VAULT_TOOL = '''#!/usr/bin/env python3
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
'''


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def build_jwt():
    d = out("20-token-of-trust")
    secret = FLAGS["jwt_secret"]
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = b64url(json.dumps({"sub": "s441907", "name": "Guest Student", "role": "guest",
                                 "iat": 1790240000}, separators=(",", ":")).encode())
    sig = b64url(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    (d / "token.txt").write_text(f"{header}.{payload}.{sig}\n")

    words = list(JWT_WORDS)
    for w in JWT_THEMED:
        words += [w, w.capitalize() + "123", w + "!"] + [f"{w}{y}" for y in range(2019, 2027)]
    if secret not in words:
        words.append(secret)
    random.Random(2020).shuffle(words)
    (d / "wordlist.txt").write_text("\n".join(words) + "\n")

    key = hashlib.sha256(secret.encode()).digest()
    (d / "vault.enc").write_bytes(xor_bytes(f"Vault unlocked.\n{FLAGS['jwt']}\n".encode(), key))
    (d / "vault_tool.py").write_text(VAULT_TOOL)


if __name__ == "__main__":
    build_web()
    build_strings()
    build_magic()
    build_hidden()
    build_reverse()
    build_logs()
    build_xor()
    build_rsa()
    build_vigenere()
    build_zip()
    build_pcap()
    build_lsb()
    build_elf()
    build_git()
    build_onion()
    build_jwt()
    print("base64 :", build_base64())
    print("caesar :", build_caesar())
    print("binary :", build_binary())
    print("md5    :", build_hash())
