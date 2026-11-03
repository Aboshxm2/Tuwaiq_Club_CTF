"""File puzzle builders for the curated English pack.

No answer keys are written into player bundles. All builders accept the final
per-team flag from personalize.generate; the OSINT puzzle is the documented
exception because a public business has one public telephone number.
"""
import base64
import datetime
import hashlib
import io
import random
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

SLUGS = {
    "26-archive-telegram", "27-two-faced-report", "28-photo-remembers",
    "29-invisible-ink", "30-final-parcel", "31-who-asked",
    "32-editors-note", "33-image-luggage",
}


def font(size):
    # Pillow ships a scalable default font; no host font dependency.
    return ImageFont.load_default(size=size)


def document_png(text):
    image = Image.new("RGB", (1100, 360), "#f8f4e9")
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 1076, 336), outline="#b4a68a", width=2)
    draw.text((55, 50), "OASIS ARCHIVE / HANDOVER NOTE", font=font(24), fill="#324e62")
    # Fixed-size line wrapping keeps the random per-team suffix on the image.
    for i in range(0, len(text), 48):
        draw.text((55, 122 + (i // 48) * 46), text[i:i+48], font=font(25), fill="#253b4b")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def archive_telegram(flag, dest):
    value = base64.b64encode(flag.encode()).hex()
    (dest / "telegram.txt").write_text(value + "\n", encoding="ascii")
    (dest / "EXPORT.txt").write_text("Archive export: octets are printed as pairs. The original transport payload was text-safe.\n", encoding="ascii")


def two_faced_report(flag, dest):
    with zipfile.ZipFile(dest / "annual-report.pdf", "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("report/summary.txt", "Annual report draft. The handover note is kept with the hidden review material.\n")
        bundle.writestr("report/.review/handover.txt", flag + "\n")
        bundle.writestr("report/expenses.csv", "item,cost\nPrinting,45\nTransport,80\n")


def photo_remembers(flag, dest):
    image = Image.new("RGB", (1000, 600), "#cddce5")
    draw = ImageDraw.Draw(image)
    draw.polygon([(0, 380), (220, 170), (470, 400), (660, 240), (1000, 400), (1000, 600), (0, 600)], fill="#9b9478")
    draw.polygon([(0, 450), (430, 330), (1000, 510), (1000, 600), (0, 600)], fill="#ceaf77")
    draw.ellipse((780, 55, 875, 150), fill="#f9d77d")
    info = PngImagePlugin.PngInfo()
    info.add_text("Title", "Field survey / Oasis Ridge")
    info.add_text("Comment", "The caption was removed from the post. Original handover: " + flag)
    image.save(dest / "field-survey.png", pnginfo=info)


def invisible_ink(flag, dest):
    image = Image.new("RGBA", (1200, 400), (239, 244, 247, 255))
    draw = ImageDraw.Draw(image)
    draw.text((40, 35), "CONSERVATION RECORD / SHEET 07", font=font(23), fill=(39, 65, 82, 255))
    draw.text((40, 88), "The scan looks empty. The colour channels kept more than the preview.", font=font(17), fill=(85, 104, 117, 255))
    # Fully transparent region with a meaningful RGB layer, preserved by PNG.
    draw.rectangle((30, 150, 1170, 365), fill=(255, 255, 255, 0))
    for i in range(0, len(flag), 48):
        draw.text((50, 180 + (i // 48) * 48), flag[i:i+48], font=font(28), fill=(20, 45, 70, 0))
    image.save(dest / "sheet-07.png")


def image_luggage(flag, dest):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("luggage/handover.txt", flag + "\n")
    # Actual PNG, followed by an extractable ZIP. No plain answer after IEND.
    (dest / "postcard.png").write_bytes(document_png("Nothing unusual to declare.") + data.getvalue())


def editors_note(flag, dest):
    # Minimal valid WordprocessingML package with a real comment anchor.
    with zipfile.ZipFile(dest / "handover.docx", "w", zipfile.ZIP_DEFLATED) as doc:
        doc.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>')
        doc.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        doc.writestr("word/_rels/document.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdComments" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>')
        doc.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Oasis Services / Final handover</w:t></w:r></w:p><w:p><w:commentRangeStart w:id="0"/><w:r><w:t>The public version is ready for release.</w:t></w:r><w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p><w:sectPr/></w:body></w:document>')
        doc.writestr("word/comments.xml", '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:comment w:id="0" w:author="Oasis Editor" w:date="2026-01-01T10:00:00Z"><w:p><w:r><w:t>Remove this review note before publication: ' + flag + '</w:t></w:r></w:p></w:comment></w:comments>')


def final_parcel(flag, dest, legacy):
    writer = legacy.PcapWriter(datetime.datetime(2026, 1, 1, 9, tzinfo=datetime.timezone.utc).timestamp())
    rng = random.Random(3030)
    client, server = "10.23.0.12", "10.23.0.80"
    wrong = document_png("Public timetable / no handover record")
    final = document_png(flag)
    events = [
        ("10.23.0.44", legacy.http_request("GET", "/public/timetable.png"), legacy.http_response("200 OK", wrong, "image/png")),
        (client, legacy.http_request("POST", "/login", b"username=operator&password=welcome"), legacy.http_response("401 Unauthorized", b"Invalid credentials")),
        (client, legacy.http_request("POST", "/login", b"username=operator&password=Archive%402026"), legacy.http_response("302 Found", extra="Location: /dispatch\r\nSet-Cookie: session=dispatch-7; HttpOnly\r\n")),
        (client, legacy.http_request("GET", "/dispatch", extra="Cookie: session=dispatch-7\r\n"), legacy.http_response("200 OK", b'<a href="/exports/dispatch-07.png">Download dispatch record</a>')),
        (client, legacy.http_request("GET", "/exports/dispatch-07.png", extra="Cookie: session=dispatch-7\r\n"), legacy.http_response("200 OK", final, "image/png")),
    ]
    for index, (source, req, res) in enumerate(events):
        writer.http_exchange(rng, source, server, 49200 + index, req, res, gap=1.2)
    (dest / "dispatch.pcap").write_bytes(writer.data)


def who_asked(flag, dest, legacy):
    # UDP/DNS packets in an Ethernet PCAP. The token is disclosed as case-id,
    # while the source IP must be recovered from the matching DNS request.
    token = flag.removesuffix("}").rsplit("_", 1)[-1]
    target = "updates.oasis.example"
    packets = [("10.44.0.12", "news.oasis.example"), ("10.44.0.31", target), ("10.44.0.15", "mail.oasis.example")]
    data = bytearray(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for index, (src, domain) in enumerate(packets):
        dns = struct.pack("!HHHHHH", 100 + index, 0x0100, 1, 0, 0, 0)
        dns += b"".join(bytes([len(label)]) + label.encode() for label in domain.split(".")) + b"\x00\x00\x01\x00\x01"
        udp = struct.pack("!HHHH", 51000 + index, 53, 8 + len(dns), 0) + dns
        s, d = bytes(map(int, src.split("."))), bytes([10, 44, 0, 53])
        ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(udp), index + 1, 0, 64, 17, 0, s, d)
        ip = ip[:10] + struct.pack("!H", legacy.inet_checksum(ip)) + ip[12:]
        frame = b"\x02\x00" + d + b"\x02\x00" + s + b"\x08\x00" + ip + udp
        data += struct.pack("<IIII", 1767258000 + index, 0, len(frame), len(frame)) + frame
    (dest / "dns.pcap").write_bytes(data)
    (dest / "CASE.txt").write_text(f"Case-id: {token}\nFind the IPv4 source that requested {target}.\nSubmit TAIBAH{{<source_ip>_{token}}}.\n", encoding="ascii")


def generate(slug, flag, dest, legacy):
    builders = {
        "26-archive-telegram": archive_telegram, "27-two-faced-report": two_faced_report,
        "28-photo-remembers": photo_remembers, "29-invisible-ink": invisible_ink,
        "32-editors-note": editors_note, "33-image-luggage": image_luggage,
    }
    if slug == "30-final-parcel":
        final_parcel(flag, dest, legacy)
    elif slug == "31-who-asked":
        who_asked(flag, dest, legacy)
    else:
        builders[slug](flag, dest)


def osint_handout(dest):
    """Only the coordinates and a clue; business identity/phone stay private."""
    dest.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1050, 650), "#253747")
    draw = ImageDraw.Draw(image)
    draw.polygon([(95, 80), (935, 60), (970, 560), (120, 590)], fill="#f3ead4")
    draw.text((170, 145), "CALL ME IF YOU CAN", font=font(42), fill="#273c4b")
    draw.text((170, 270), "57.4125041, -6.1949942", font=font(34), fill="#273c4b")
    draw.text((170, 400), "One more slice before we leave the island.", font=font(24), fill="#735543")
    image.save(dest / "found-note.png")
