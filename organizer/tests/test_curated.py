"""Solve the new puzzles and exercise each web app without Docker/production."""
import base64
import importlib.util
import io
import json
import os
import re
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "organizer"))
from prepare_curated import load_modules

catalog, files, personal = load_modules()
web_path = ROOT / "ctfd-platform/deploy/curated-web/app.py"
web_spec = importlib.util.spec_from_file_location("curated_web", web_path)
web = importlib.util.module_from_spec(web_spec)
web_spec.loader.exec_module(web)
web.app.config["TESTING"] = True


def packets(path):
    data, offset = path.read_bytes(), 24
    while offset < len(data):
        _, _, length, original = struct.unpack_from("<IIII", data, offset)
        assert length == original
        offset += 16
        yield data[offset:offset + length]
        offset += length
    assert offset == len(data)


class FilePuzzles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def build(self, slug, token="abcd"):
        dest = self.root / (slug + "-" + token)
        flag = personal.generate("curated-" + slug, token, dest)
        self.assertTrue((dest / "bundle.zip").is_file())
        with zipfile.ZipFile(dest / "bundle.zip") as bundle:
            self.assertIsNone(bundle.testzip())
            self.assertNotIn("bundle.zip", bundle.namelist())
            self.assertFalse(any("SOLUTION" in name.upper() for name in bundle.namelist()))
        return dest, flag

    def test_two_team_flags_and_repeatability(self):
        for slug in sorted(files.SLUGS):
            with self.subTest(slug=slug):
                first, a = self.build(slug, "abcd")
                second, b = self.build(slug, "efgh")
                self.assertNotEqual(a, b)
                before = (first / "bundle.zip").read_bytes()
                self.build(slug, "abcd")
                self.assertEqual(before, (first / "bundle.zip").read_bytes())

    def test_telegram(self):
        d, flag = self.build("26-archive-telegram")
        self.assertEqual(base64.b64decode(bytes.fromhex((d / "telegram.txt").read_text())).decode(), flag)

    def test_report_signature_and_hidden_file(self):
        d, flag = self.build("27-two-faced-report")
        self.assertTrue((d / "annual-report.pdf").read_bytes().startswith(b"PK"))
        with zipfile.ZipFile(d / "annual-report.pdf") as bundle:
            self.assertEqual(bundle.read("report/.review/handover.txt").decode().strip(), flag)

    def test_photo_metadata(self):
        d, flag = self.build("28-photo-remembers")
        with Image.open(d / "field-survey.png") as image:
            self.assertIn(flag, image.info["Comment"])

    def test_transparency_preserves_ink(self):
        d, flag = self.build("29-invisible-ink")
        with Image.open(d / "sheet-07.png") as image:
            rgba = image.convert("RGBA")
            visible = Image.new("RGBA", rgba.size, "white")
            visible.alpha_composite(rgba)
            # Hidden ink exists in RGB at alpha zero, but cannot be seen when
            # correctly composited. Save the recovered view for visual review.
            ink = [(r, g, b, a) for r, g, b, a in rgba.crop((30,150,1170,365)).get_flattened_data() if a == 0 and r < 50]
            self.assertGreater(len(ink), 100)
            self.assertTrue(all(p[:3] == (255,255,255) for p in visible.crop((30,150,1170,365)).get_flattened_data()))

    def test_appended_archive(self):
        d, flag = self.build("33-image-luggage")
        with Image.open(d / "postcard.png") as image:
            image.verify()
        with zipfile.ZipFile(d / "postcard.png") as bundle:
            self.assertEqual(bundle.read("luggage/handover.txt").decode().strip(), flag)

    def test_document_comment(self):
        d, flag = self.build("32-editors-note")
        with zipfile.ZipFile(d / "handover.docx") as doc:
            for name in doc.namelist():
                ElementTree.fromstring(doc.read(name))
            self.assertIn(flag, doc.read("word/comments.xml").decode())
            self.assertNotIn(flag, doc.read("word/document.xml").decode())

    def test_dns_source(self):
        d, flag = self.build("31-who-asked")
        frames = list(packets(d / "dns.pcap"))
        matches = [p for p in frames if b"\x07updates\x05oasis\x07example" in p]
        self.assertEqual(len(matches), 1)
        ip = ".".join(str(b) for b in matches[0][26:30])
        self.assertEqual(flag, "TAIBAH{" + ip + "_abcd}")
        for p in frames:
            self.assertEqual(personal.load_builder().inet_checksum(p[14:34]), 0)

    def test_pcap_reassemble_and_extract(self):
        d, flag = self.build("30-final-parcel")
        streams = {}
        for frame in packets(d / "dispatch.pcap"):
            ip = frame[14:]
            ip_length = (ip[0] & 15) * 4
            self.assertEqual(personal.load_builder().inet_checksum(ip[:ip_length]), 0)
            tcp = ip[ip_length:]
            offset = (tcp[12] >> 4) * 4
            if tcp[offset:] and struct.unpack_from("!H", tcp)[0] == 80:
                dest_port = struct.unpack_from("!H", tcp, 2)[0]
                streams.setdefault(dest_port, bytearray()).extend(tcp[offset:])
        images = []
        for data in streams.values():
            if b"Content-Type: image/png" in data:
                images.append(bytes(data).split(b"\r\n\r\n", 1)[1])
        self.assertEqual(len(images), 2)
        self.assertNotIn(flag.encode(), (d / "dispatch.pcap").read_bytes())
        for blob in images:
            with Image.open(io.BytesIO(blob)) as image:
                image.verify()
        self.assertIn(b"302 Found", (d / "dispatch.pcap").read_bytes())

    def test_osint_note_contains_no_answer_key(self):
        files.osint_handout(self.root)
        with Image.open(self.root / "found-note.png") as image:
            self.assertEqual(image.size, (1050,650))
            self.assertNotIn("Comment", image.info)


class WebPuzzles(unittest.TestCase):
    def setUp(self):
        web.FLAG = "TAIBAH{test_team_a}"
        self.client = web.app.test_client()

    def mode(self, mode):
        web.MODE = mode

    def test_last_edit_parts(self):
        self.mode("last-edit")
        chunks = []
        for url in ("/", "/style.css", "/site.js"):
            text = self.client.get(url).get_data(as_text=True)
            chunks.append(re.search(r"Build note [123]/3: ([^\n]*?)(?: -->| \*/|\n|$)", text).group(1))
        self.assertEqual("".join(chunks), web.FLAG)

    def test_robots_to_backup(self):
        self.mode("forgotten-route")
        self.assertIn(b"/retired-archive/", self.client.get("/robots.txt").data)
        self.assertIn(b"portal-backup.zip", self.client.get("/retired-archive/").data)
        with zipfile.ZipFile(io.BytesIO(self.client.get("/retired-archive/portal-backup.zip").data)) as archive:
            self.assertIn(web.FLAG.encode(), archive.read("settings.ini"))

    def test_frontend_state(self):
        self.mode("frontend-pass")
        self.assertNotIn(web.FLAG.encode(), self.client.get("/").data)
        self.assertEqual(self.client.get("/preview").status_code, 403)
        self.client.set_cookie("preview_state", base64.b64encode(b'{"view":"staff"}').decode())
        self.assertIn(web.FLAG.encode(), self.client.get("/preview").data)
        for invalid in ("!", "bnVsbA==", "W10="):
            self.client.set_cookie("preview_state", invalid)
            self.assertEqual(self.client.get("/preview").status_code, 403)

    def test_login_injection(self):
        self.mode("trial-login")
        self.assertEqual(self.client.post("/login", data={"username":"wrong","password":"wrong"}).status_code, 403)
        solved = self.client.post("/login", data={"username":"' OR 1=1 -- ","password":"x"})
        self.assertIn(web.FLAG.encode(), solved.data)

    def test_refund_requires_target_and_action(self):
        self.mode("refund-desk")
        self.assertNotIn(web.FLAG.encode(), self.client.get("/api/requests/108").data)
        self.assertNotIn(web.FLAG.encode(), self.client.post("/api/requests/104", json={"action":"approve"}).data)
        self.assertEqual(self.client.post("/api/requests/108", json={"action":"deny"}).status_code, 400)
        self.assertEqual(self.client.post("/api/requests/108", json={"action":"approve"}).json["audit_code"], web.FLAG)

    def test_ledger_schema_then_secret(self):
        self.mode("caravan-ledger")
        self.assertNotIn(web.FLAG.encode(), self.client.get("/", query_string={"q":"Route"}).data)
        schema = self.client.get("/", query_string={"q":"' UNION SELECT name,sql FROM sqlite_master -- "})
        self.assertIn(b"audit_records", schema.data)
        solved = self.client.get("/", query_string={"q":"' UNION SELECT label,secret FROM audit_records -- "})
        self.assertIn(web.FLAG.encode(), solved.data)
        error = self.client.get("/", query_string={"q":"'"})
        self.assertNotIn(b"SELECT name,cargo", error.data)

    def test_template_expression_and_context(self):
        self.mode("template-studio")
        self.assertNotIn(web.FLAG.encode(), self.client.get("/").data)
        self.assertIn(b"49", self.client.post("/render", data={"template":"{{ 50-1 }}"}).data)
        self.assertIn(web.FLAG.encode(), self.client.post("/render", data={"template":"{{ config.AUDIT_CODE }}"}).data)
        self.assertNotIn(b"__mro__", self.client.post("/render", data={"template":"{{ ''.__class__.__mro__ }}"}).data)
        self.assertEqual(self.client.post("/render", data={"template":"{% for i in range(10) %}x{% endfor %}"}).status_code, 400)

    def test_mode_isolation_and_team_flags(self):
        for mode in web.ALLOWED:
            self.mode(mode)
            home = self.client.get("/")
            self.assertEqual(home.status_code, 200)
            self.assertIn(b'lang="en"', home.data)
            self.assertNotIn(web.FLAG.encode(), home.data)
            if mode != "refund-desk":
                self.assertEqual(self.client.get("/api/requests/108").status_code, 404)
            if mode != "forgotten-route":
                self.assertEqual(self.client.get("/retired-archive/portal-backup.zip").status_code, 404)
        self.mode("refund-desk")
        web.FLAG = "TAIBAH{test_team_b}"
        self.assertEqual(self.client.post("/api/requests/108", json={"action":"approve"}).json["audit_code"], web.FLAG)


if __name__ == "__main__":
    unittest.main()
