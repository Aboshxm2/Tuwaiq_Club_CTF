# 15 — Wiretap

| Category          | Points | Difficulty |
|-------------------|--------|------------|
| Network Forensics | 200    | Medium     |

## Description

The Oasis Travel intranet still runs over plain **HTTP**. An auditor plugged a laptop into the office network and recorded traffic from an employee's computer for a few seconds.

During the capture, the administrator logged into the intranet. Find the password that **successfully** logged in.

## Files

- [`files/capture.pcap`](files/capture.pcap)

## Hints

<details>
<summary>Hint 1 (free)</summary>

Open the file in [Wireshark](https://www.wireshark.org/). Login forms usually send data with an HTTP **POST** request. Try the display filter:

```
http.request.method == "POST"
```
</details>

<details>
<summary>Hint 2 (-40 points)</summary>

There is more than one login attempt. Right-click each request → **Follow** → **HTTP Stream** and check the server's reply. `401 Unauthorized` means the attempt failed, and a `302` redirect to the dashboard means it worked.
</details>

<details>
<summary>Hint 3 (-40 points)</summary>

Form data is **URL-encoded**. For example, `%7B` is `{` and `%40` is `@`. Decode it with CyberChef → **URL Decode**.
</details>

## Flag Format

`TAIBAH{...}`

## Discussion (after the CTF)

Why is HTTPS (TLS) essential for login pages, even on an internal network?
