# 17 — Floodgate

| Category            | Points | Difficulty |
|---------------------|--------|------------|
| Reverse Engineering | 400    | Hard       |

## Description

The Oasis Dam control panel asks for an **override code** before it opens the floodgates. We recovered the control program, but its source code is gone and the binary is **stripped**.

The override code is the flag. `strings` won't help you this time, because the code is never stored in plain text.

## Files

- [`files/floodgate`](files/floodgate) — Linux x86-64 ELF executable

```bash
chmod +x floodgate
./floodgate
```

## Hints

<details>
<summary>Hint 1 (free)</summary>

Use a decompiler such as [Ghidra](https://ghidra-sre.org/) (free, by the NSA), [Binary Ninja Cloud](https://cloud.binary.ninja/), or [Dogbolt](https://dogbolt.org/) (online, compares several decompilers).

Find where `ACCESS DENIED` is used. In Ghidra: **Search → For Strings**, then double-click the string and follow its reference. The code just before it is the input check.
</details>

<details>
<summary>Hint 2 (-80 points)</summary>

The check loops over each input character. It updates a one-byte `state` variable, mixes it with your character, and compares the result with a byte from a constant array in `.rodata`.

You don't have to guess the input. Rewrite the loop backwards in Python: for each position, undo the `+` and the `^`.
</details>

<details>
<summary>Hint 3 (-80 points)</summary>

If you try to run the program under `gdb`, `strace`, or `ltrace`, it refuses to work. Look for a call to `ptrace` in `main`. This is a common **anti-debugging** trick. You can patch the jump after it, or just solve the challenge statically.

All arithmetic is on `unsigned char`, so remember `& 0xFF` in Python.
</details>

## Flag Format

`TAIBAH{...}`
