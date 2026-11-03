#!/usr/bin/env python3
"""Build review copies and an English catalog. Does not contact production."""
import importlib
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "ctfd-platform/plugins/ctfd-rounds"


def load_modules():
    # Loading the package's __init__ would boot CTFd. Pure builder modules do
    # not need a database, so give them a lightweight package namespace.
    package = types.ModuleType("curated_build")
    package.__path__ = [str(PLUGIN)]
    sys.modules["curated_build"] = package
    return tuple(importlib.import_module("curated_build." + name)
                 for name in ("curated_catalog", "curated_files", "personalize"))


def main():
    catalog, files, personal = load_modules()
    output = ROOT / "curated-output"
    output.mkdir(exist_ok=True)
    (output / "catalog.json").write_text(json.dumps(catalog.CHALLENGES, indent=2), encoding="utf-8")
    for item in catalog.CHALLENGES:
        folder = output / item["key"]
        folder.mkdir(exist_ok=True)
        (folder / "PLAYER.md").write_text("# " + item["name"] + "\n\n" + item["description"] + "\n", encoding="utf-8")
        if item["kind"] == "file":
            personal.generate(item["slug"], "demo", folder / "preview-only")
        elif item["kind"] == "shared":
            files.osint_handout(folder / "player-files")
    print(f"Prepared {len(catalog.CHALLENGES)} catalog entries; demo bundles are for review, not upload as unique team files.")
    print(output)


if __name__ == "__main__":
    main()
