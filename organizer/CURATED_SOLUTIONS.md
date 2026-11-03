# Organizer solution paths — not player attachments

These notes describe methods, not production flags. Generated flags depend on
the team's instance; live flags come from Whale. Keep this file out of bundles.

| Key | Intended path |
|---|---|
| W1 | Read HTML source, linked CSS and JavaScript; concatenate numbered build notes. |
| W2 | Read /robots.txt, follow /retired-archive/, download the linked ZIP, inspect settings.ini. |
| W3 | Inspect/enable the preview button, decode preview_state as Base64 JSON, change view from guest to staff, load /preview. |
| W4 | Send a boolean SQL-injection username to the fictional legacy login. No password list is needed. |
| W5 | Inspect /api/requests/104, find attachment 108, POST JSON action=approve to /api/requests/108 despite the interface ownership restriction. |
| W6 | Discover two-column UNION shape, enumerate sqlite_master, query label and secret from audit_records. |
| W7 | Confirm template evaluation with {{ 50-1 }}, then inspect the exposed config object or render {{ config.AUDIT_CODE }}. |
| E1 | Hex to bytes, then Base64 decode. |
| E2 | Convert each eight-bit group to an ASCII character. |
| C1 | Recover the Caesar shift using known flag prefix; undo it for letters only. |
| C2 | XOR ciphertext against the known prefix; test repeating short keys and recover plaintext. |
| C3 | Fermat-factor n with integer square roots; compute private exponent and decrypt c. |
| F1 | Read PNG Comment metadata or printable strings from the original PNG. |
| F2 | Identify PK/ZIP signature despite .pdf; extract report/.review/handover.txt. |
| F3 | Detect ZIP appended after PNG; extract luggage/handover.txt. |
| F4 | Open document comments or unzip DOCX and inspect word/comments.xml. |
| F5 | Remove/ignore alpha rather than compositing onto white; read the preserved RGB text. Pillow Image.open(...).convert('RGB') reveals it. |
| N1 | Identify the successful login and its session cookie; follow /dispatch then export dispatch-07.png from HTTP. Read the flag visually from the recovered PNG. |
| N2 | Filter the DNS question in CASE.txt; read the IPv4 source and combine with the case-id exactly as instructed. |
| B1 | Find repeated SSH failures, link their source to Accepted password, submit IP_username_case-id. |
| O1 | Recognize coordinates, find the pizza takeaway at that location, follow its official branch contact page, normalize its number to international digits. |

For the full pack, use the release plan in CURATED_CHALLENGES.md. Reserves are
not prerequisites. The tests reconstruct the new file puzzles and exercise
each web solve and several incorrect paths; manual visual checks complement
the generated-image tests.
