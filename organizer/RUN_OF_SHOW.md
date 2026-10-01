# Run of Show — Final Day CTF (5:00 PM – 9:00 PM)

> Organizers only. This plan runs the CTF in **five themed rounds**. Everyone works on the same four challenges at the same time. When a round ends, it closes and the solutions are revealed together on the projector.

---

## Why Rounds?

- **One shared flow.** The whole room is working on the same challenges, and everyone gets the "aha" moment together at each reveal.
- **Learning is spread through the evening.** Each reveal teaches right after students have struggled with a problem, instead of in one long walkthrough at the end.
- **Everyone scores, and nobody sits idle.** Each round opens with easy challenges and ends with a harder "stretch" challenge that keeps fast teams busy.

---

## The Five Rounds

| Round | Theme                   | Challenges                                                                                                          | Points   |
| ----- | ----------------------- | ------------------------------------------------------------------------------------------------------------------- | -------- |
| 1     | Warm-up: Encoding & Web | 01 Inspect the Oasis (50) ⧉ · 02 Strange Letters (50) · 04 Ones and Zeros (100) · 21 Caravan Ledger (250) ⧉ · **19 Onion Layers (250)** | 700      |
| 2     | Ciphers                 | 03 Julius in the Desert (100) · 13 The Merchant's Letter (200) · 11 Sandstorm XOR (200) · 22 Sealed Scroll (400) ⧉ · **12 Close Primes (350)** | 1250     |
| 3     | Hidden in Files         | 06 Desert Picture (100) · 07 Not a PDF (150) · 18 Deleted but Not Forgotten (250) · 23 Desert Diagnostics (300) ⧉ · **16 Pixel Secrets (300)** | 1100     |
| 4     | Breaking Locks          | 05 Crack the Falcon (100) · 09 Password Checker (150) · 14 Locked Vault (200) · 24 Mirage Preview (350) ⧉ · **20 Token of Trust (350)** ⧉ | 1150     |
| 5     | The Investigation       | 08 Camel Caravan (150) · 10 Who Broke In? (200) · 15 Wiretap (200) · 25 Floodgate Override (400) ⧉ · **17 Floodgate (400)** | 1350     |
|       | **Total**               | 25 challenges | **5550** |

**Bold** = the round's stretch challenge. **⧉** = a live per-team instance: press **Launch an instance**, then open the link (challenge 25 is raw TCP — connect with `nc`).

> **Rounds 1 and 4 each have two live challenges.** A team can run only **one** live instance at a time — launching a second replaces the first, which comes back with a new flag. Tell teams to finish and submit one live challenge before launching the next in the same round; these exploits take seconds to re-run.

---

## Schedule

| Time        | Duration | What happens                                                                                    |
| ----------- | -------- | ----------------------------------------------------------------------------------------------- |
| 4:30 – 5:00 | 30 min   | Organizers arrive. Test Wi-Fi, platform, projector, timer. Round 1 challenges ready but hidden. |
| 5:00 – 5:15 | 15 min   | **Briefing** (see below)                                                                        |
| 5:15 – 5:40 | 25 min   | **Round 1:** Warm-up                                                                            |
| 5:40 – 5:45 | 5 min    | Round 1 reveal                                                                                  |
| 5:45 – 6:10 | 25 min   | **Round 2:** Ciphers                                                                            |
| 6:10 – 6:35 | 25 min   | **Maghrib break.** Platform paused.                                                             |
| 6:35 – 6:40 | 5 min    | Round 2 reveal (brings everyone back together)                                                  |
| 6:40 – 7:10 | 30 min   | **Round 3:** Hidden in Files                                                                    |
| 7:10 – 7:15 | 5 min    | Round 3 reveal                                                                                  |
| 7:15 – 7:45 | 30 min   | **Round 4:** Breaking Locks                                                                     |
| 7:45 – 7:55 | 10 min   | **Isha break.** Platform paused.                                                                |
| 7:55 – 8:00 | 5 min    | Round 4 reveal                                                                                  |
| 8:00 – 8:35 | 35 min   | **Round 5:** The Investigation (final). Scoreboard frozen from 8:20.                            |
| 8:35 – 8:50 | 15 min   | Round 5 reveal and unfreeze the scoreboard                                                      |
| 8:50 – 9:00 | 10 min   | Winners, prizes, closing words                                                                  |

Total playing time: **2 h 25 min**.

> **Prayer times:** Confirm the exact Maghrib and Isha times for the day. In Saudi Arabia, Isha is usually about 90 minutes after Maghrib. If the times differ, shift the breaks and shorten or lengthen Round 3 or 4 to fit.

---

## Roles

| Role                  | Who        | Job                                                                                                              |
| --------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------- |
| **Host**              | 1 person   | Runs the briefing, announces rounds, presents the reveals.                                                       |
| **Platform operator** | 1 person   | Opens and closes challenges, pauses the platform, watches the scoreboard, and tells the host about first bloods. |
| **Floor helpers**     | 1–2 people | Walk the room. Confirm files work and answer platform questions. **Never give solutions.**                       |

---

## Round Mechanics

### At the start of each round

1. The platform operator makes the round's 4 challenges **visible**.
2. The host reads the round's chapter intro (see [Story](#story-operation-sandstorm)) and starts a **big countdown timer** on the projector.
3. The projector shows the timer and the live scoreboard side by side.

### At the end of each round

1. The host gives a 5-minute warning, then a 1-minute warning.
2. When the timer hits zero, the platform operator presses **End** on the Rounds page. That hides the round's challenges. Points already earned stay on the scoreboard.
3. Reveal (5 min), then press **Start** on the next round.

### Reveal format (5 minutes)

1. **Celebrate first (1 min):** the round leader, plus the **first blood** (first team to solve) on each challenge.
2. **Easy challenges (2 min):** solve them live, about 1 minute each.
3. **Stretch challenge (2 min):** explain the key idea and show the result. Skip the full walkthrough.
4. End with the one-sentence **Lesson** from `SOLUTIONS.md`.

The final reveal after Round 5 gets 15 minutes: the full Round 5 reveal, then **unfreeze the scoreboard** for the final standings.

### On the platform

The site is in `ctfd-platform/`. The **Rounds** item in the admin navbar is the clock.

- **Start** opens that round and hides every other challenge.
- **Freeze** pauses the clock and rejects submissions. Use it for Maghrib and Isha. **Resume** continues the same round.
- **End** closes the round. Scores stay. Ending does not wipe points from earlier rounds.
- Do not use CTFd's global pause or its scoreboard-freeze time for the rounds. Those are separate from this clock.

Players register, create a team of 1 to 3 (change the limit on the Rounds page), and press **Launch instance** on each challenge. The download is unique to that team.

---

## Briefing Script (15 min)

1. **Welcome (2 min):** Five days of learning, and today you use it all.
2. **How it works (5 min):**
   - Teams of 1 to 3. Playing alone means a team with one member.
   - 5 rounds, 4 challenges per round, about 30 minutes each.
   - **When a round ends, its challenges close.** Solve what you can before time runs out.
   - Flag format: `TAIBAH{...}`, case-sensitive.
   - There are no hints.
3. **Rules (3 min):** Don't attack the platform or other teams. Don't share flags between teams. No brute-forcing the submission form.
4. **Demo (3 min):** Show how to open a challenge, download files, and submit a flag. Use a dummy flag, not a real challenge.
5. **Questions (2 min)**, then start Round 1.

---

## Story: Operation Sandstorm

Read one short chapter intro at the start of each round to turn the 25 challenges into one mission.

**Prologue (at the briefing)**

> A smuggling network led by someone called **Sandstorm** is operating around the Oasis. Tonight, you are the cyber unit tasked with stopping them. Every flag you capture is a piece of evidence.

**Round 1: Warm-up**

> Our first lead: Sandstorm's gang uses a travel agency website as a front. Inspect everything they left behind: pages, messages, and strange encoded notes.

**Round 2: Ciphers**

> We intercepted Sandstorm's messages. Some use ancient ciphers, one uses XOR, and one uses a "secure" bank key. Read them all.

**Round 3: Hidden in Files**

> We seized the gang's files: a photo, a "report", and a code repository. They swear there's nothing inside. Prove them wrong.

**Round 4: Breaking Locks**

> We found their vault, a password checker, and their web portal. Everything is locked. Break every lock.

**Round 5: The Investigation**

> Final chapter. The gang broke into a server, sniffed passwords on the office network, and planned to open the dam's floodgates. Find out who did it and stop the floodgates.

**Closing (at the awards)**

> Operation Sandstorm is complete. Every flag you captured tonight is a real technique that real attackers use and real defenders detect. Well done.

---

## Distributing Files

With rounds, students should **not** receive the whole `challenges/` folder at the start, because that would give away future rounds.

- Upload each challenge's files to the platform, attached to that challenge, so they appear only when the round opens.
- **Wi-Fi backup:** prepare one ZIP per round (`round1.zip` … `round5.zip`) on a USB stick. Share each one only when its round opens.
- Share the full `challenges/` folder and the solutions **after** the event.

---

## Pre-Event Checklist

**The day before**

- [ ] All 25 challenges created on the platform, grouped by round, all **hidden**
- [ ] Teams registered (so the briefing isn't spent creating accounts)
- [ ] Hide, pause, and freeze behaviour tested with a test team
- [ ] Ran `python3 organizer/verify_solutions.py`, all PASS
- [ ] Built the deployable images on every challenge node (`ctfd-platform/deploy/build.sh`) and ran `whale_selftest.py`, all 7 live challenges PASS
- [ ] Checked that students have Linux (Kali, WSL, or a VM) for the reverse-engineering and pwn challenges (17 Floodgate, 25 Floodgate Override)
- [ ] Per-round ZIPs on a USB stick (file challenges only; the seven live challenges need the platform)
- [ ] Prizes ready

**On the day**

- [ ] Projector shows the countdown timer and scoreboard
- [ ] Roles assigned (host, platform operator, floor helpers)
- [ ] Prayer times confirmed and breaks adjusted
- [ ] `SOLUTIONS.md` open on the host's laptop for the reveals
