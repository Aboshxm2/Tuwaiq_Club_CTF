"""Build a per-team copy of a challenge with that team's flag baked in.

The puzzle is the same for everyone. The flag string is not. A flag copied from
another team does not match this team's copy.
"""

import importlib.util
import os
import threading
import zipfile
from pathlib import Path

_LOCK = threading.Lock()
_BUILDER = None

FLAG_KEY = {
    "02-strange-letters": "base64",
    "03-julius-in-the-desert": "caesar",
    "04-ones-and-zeros": "binary",
    "06-desert-picture": "strings",
    "07-not-a-pdf": "magic",
    "08-camel-caravan": "hidden",
    "09-password-checker": "reverse",
    "11-sandstorm-xor": "xor",
    "12-close-primes": "rsa",
    "13-the-merchants-letter": "vigenere",
    "14-locked-vault": "zip",
    "15-wiretap": "pcap",
    "16-pixel-secrets": "lsb",
    "17-floodgate": "elf",
    "18-deleted-not-forgotten": "git",
    "19-onion-layers": "onion",
    "20-token-of-trust": "jwt",
}

README = (
    "These files were generated for your team.\n"
    "Recover the flag from them and submit it.\n"
    "A flag copied from another team will not score.\n"
)


def builder_path() -> Path:
    env = os.environ.get("CTF_REPO")
    if env:
        return Path(env) / "organizer" / "build_handouts.py"
    return Path(__file__).resolve().parents[3] / "organizer" / "build_handouts.py"


def load_builder():
    global _BUILDER
    if _BUILDER is None:
        path = builder_path()
        spec = importlib.util.spec_from_file_location("taibah_build_handouts", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load challenge builder at {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _BUILDER = module
    return _BUILDER


def split3(flag: str):
    first = len(flag) // 3
    second = 2 * len(flag) // 3
    return flag[:first], flag[first:second], flag[second:]


def stamp(flag: str, token: str, replace: bool = False) -> str:
    if not flag.endswith("}"):
        raise ValueError(f"flag must end with }}: {flag}")
    if replace:
        return flag[: -1 - len(token)] + token + "}"
    return flag[:-1] + "_" + token + "}"


def canonical_flag(mod, slug: str) -> str:
    if slug == "01-inspect-the-oasis":
        joined = "".join(mod.FLAGS["web"])
        return joined if joined.endswith("}") else joined + "}"
    if slug == "05-crack-the-falcon":
        return "TAIBAH{" + mod.FLAGS["hash_word"] + "}"
    if slug == "10-who-broke-in":
        return "TAIBAH{" + mod.FLAGS["log_ip"] + "_" + mod.FLAGS["log_user"] + "}"
    return mod.FLAGS[FLAG_KEY[slug]]


def elf_bytes(flag: str) -> bytes:
    state = 0x5C
    encoded = []
    for index, char in enumerate(flag.encode()):
        state = (state * 37 + 11) & 0xFF
        encoded.append(((char ^ state) + 3 * index) & 0xFF)
    return bytes(encoded)


def _write(dest: Path, name: str, text: str):
    (dest / name).write_text(text if text.endswith("\n") else text + "\n")


def _build_into(mod, slug: str, flag: str, token: str, dest: Path):
    if slug == "01-inspect-the-oasis":
        mod.FLAGS["web"] = split3(flag)
        mod.build_web()
    elif slug == "02-strange-letters":
        mod.FLAGS["base64"] = flag
        _write(dest, "message.txt", mod.build_base64())
    elif slug == "03-julius-in-the-desert":
        mod.FLAGS["caesar"] = flag
        _write(dest, "message.txt", mod.build_caesar())
    elif slug == "04-ones-and-zeros":
        mod.FLAGS["binary"] = flag
        _write(dest, "bits.txt", mod.build_binary())
    elif slug == "05-crack-the-falcon":
        _write(dest, "hash.txt", mod.build_hash())
        _write(dest, "CASE.txt", token)
        _write(
            dest,
            "INSTRUCTIONS.txt",
            "Crack the password in hash.txt.\n"
            "Your case-id is in CASE.txt.\n"
            "Submit TAIBAH{<password>_<case-id>}.\n",
        )
    elif slug == "06-desert-picture":
        mod.FLAGS["strings"] = flag
        mod.build_strings()
    elif slug == "07-not-a-pdf":
        mod.FLAGS["magic"] = flag
        mod.build_magic()
    elif slug == "08-camel-caravan":
        mod.FLAGS["hidden"] = flag
        mod.build_hidden()
    elif slug == "09-password-checker":
        mod.FLAGS["reverse"] = flag
        mod.build_reverse()
    elif slug == "10-who-broke-in":
        mod.build_logs()
        log = dest / "auth.log"
        log.write_text(f"# case-id: {token}\n" + log.read_text())
        _write(
            dest,
            "INSTRUCTIONS.txt",
            "Find the attacker IP and the username they logged into.\n"
            "Your case-id is on the first line of auth.log.\n"
            "Submit TAIBAH{<ip>_<username>_<case-id>}.\n",
        )
    elif slug == "11-sandstorm-xor":
        mod.FLAGS["xor"] = flag
        mod.build_xor()
    elif slug == "12-close-primes":
        mod.FLAGS["rsa"] = flag
        mod.build_rsa()
    elif slug == "13-the-merchants-letter":
        mod.FLAGS["vigenere"] = flag
        mod.build_vigenere()
    elif slug == "14-locked-vault":
        mod.FLAGS["zip"] = flag
        mod.build_zip()
    elif slug == "15-wiretap":
        mod.FLAGS["pcap"] = flag
        mod.build_pcap()
    elif slug == "16-pixel-secrets":
        mod.FLAGS["lsb"] = flag
        mod.build_lsb()
    elif slug == "17-floodgate":
        _patch_elf(mod, flag, dest)
    elif slug == "18-deleted-not-forgotten":
        mod.FLAGS["git"] = flag
        mod.build_git()
    elif slug == "19-onion-layers":
        mod.FLAGS["onion"] = flag
        mod.build_onion()
    elif slug == "20-token-of-trust":
        mod.FLAGS["jwt"] = flag
        mod.build_jwt()
    else:
        raise KeyError(slug)


def _patch_elf(mod, flag: str, dest: Path):
    source = builder_path().parent.parent / "challenges" / "17-floodgate" / "files" / "floodgate"
    original = canonical_flag(mod, "17-floodgate")
    blob = source.read_bytes()
    old = elf_bytes(original)
    new = elf_bytes(flag)
    if len(old) != len(new):
        raise RuntimeError("Floodgate flag length changed; the binary cannot be patched")
    found = blob.count(old)
    if found != 1:
        raise RuntimeError(f"Floodgate ciphertext pattern found {found} times")
    target = dest / "floodgate"
    target.write_bytes(blob.replace(old, new))
    target.chmod(0o755)


def _zip_dir(src: Path, dest_zip: Path):
    with zipfile.ZipFile(dest_zip, "w") as archive:
        for path in sorted(src.rglob("*")):
            if not path.is_file() or path == dest_zip:
                continue
            info = zipfile.ZipInfo(path.relative_to(src).as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (path.stat().st_mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def generate(slug: str, token: str, dest: Path) -> str:
    """Write the team's files into dest and return the flag that scores."""
    dest.mkdir(parents=True, exist_ok=True)
    mod = load_builder()
    flag = stamp(canonical_flag(mod, slug), token, replace=(slug == "17-floodgate"))
    if slug == "05-crack-the-falcon":
        flag = "TAIBAH{" + mod.FLAGS["hash_word"] + "_" + token + "}"
    elif slug == "10-who-broke-in":
        flag = "TAIBAH{" + mod.FLAGS["log_ip"] + "_" + mod.FLAGS["log_user"] + "_" + token + "}"

    with _LOCK:
        saved = dict(mod.FLAGS)
        saved_web = mod.FLAGS["web"]
        old_out = mod.out

        def out(_challenge, dest=dest):
            dest.mkdir(parents=True, exist_ok=True)
            return dest

        mod.out = out
        try:
            _build_into(mod, slug, flag, token, dest)
        finally:
            mod.FLAGS.clear()
            mod.FLAGS.update(saved)
            mod.FLAGS["web"] = saved_web
            mod.out = old_out

    _write(dest, "README.txt", README)
    zip_path = dest / "bundle.zip"
    _zip_dir(dest, zip_path)
    # The zip is the download. Leave the loose files too so a failed zip is obvious.
    return flag


def reset_builder():
    """Drop the cached generator."""
    global _BUILDER
    _BUILDER = None
