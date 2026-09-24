# 16 — Pixel Secrets

| Category      | Points | Difficulty |
|---------------|--------|------------|
| Steganography | 300    | Hard       |

## Description

A photo of the dunes was posted on a forum known to be used by smugglers. It looks completely normal, and `strings` and `exiftool` show nothing useful this time.

But our analysts believe a message is hidden **inside the pixels themselves**.

## Files

- [`files/dunes.png`](files/dunes.png)

## Hints

<details>
<summary>Hint 1 (free)</summary>

Each pixel has a red, green, and blue value from 0 to 255. Changing the **lowest bit** of each value (for example 200 → 201) is invisible to the human eye, but it can store 3 bits of data per pixel.

This technique is called **LSB (Least Significant Bit) steganography**.
</details>

<details>
<summary>Hint 2 (-60 points)</summary>

Tools that detect LSB data automatically:

```bash
gem install zsteg
zsteg dunes.png
```

Or upload it to an online tool like [Aperi'Solve](https://www.aperisolve.com/), or open it in **StegSolve**.
</details>

<details>
<summary>Hint 3 (-60 points)</summary>

Extract it yourself with Python (`pip install pillow`):

```python
from PIL import Image
img = Image.open("dunes.png").convert("RGB")
bits = "".join(str(v & 1) for v in img.tobytes())
data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
print(data[:100])
```

Bits are read left to right, top to bottom, in R, G, B order. Each group of 8 bits is one byte, most significant bit first.
</details>

## Flag Format

`TAIBAH{...}`
