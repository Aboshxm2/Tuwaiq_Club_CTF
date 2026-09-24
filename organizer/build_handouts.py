#!/usr/bin/env python3
"""Regenerates every challenge handout file. Edit FLAGS below to change flags."""

import base64
import hashlib
import io
import random
import struct
import tarfile
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


if __name__ == "__main__":
    build_web()
    build_strings()
    build_magic()
    build_hidden()
    build_reverse()
    build_logs()
    print("base64 :", build_base64())
    print("caesar :", build_caesar())
    print("binary :", build_binary())
    print("md5    :", build_hash())
