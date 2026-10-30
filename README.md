# Tales of Eternia Remastered – Restored English Voices (TEST patcher)

**Status: public test. Not a finished release.** Goal: put the original PSP English dub back into
*Tales of Eternia Remastered* (Steam, AppID 3470960), and find out which lines still need work.
**Testers wanted** – every doubtful item is listed below.

## What this test patch changes
| Area | What |
|---|---|
| Events | Only **EM0200** (136 event lines) |
| Battle / minigame voices | All cues used by the game's `Vo.acb` (900 cues, in-memory waveforms) |
| Battle sound-effect voices | 32 waveforms in `S00` (normal hit / damage) |
| Title logo (optional) | "RESTORED" logo with **TEST** instead of the version text |
| Intro video | **Not included** (later, in the full version) |

Everything is built **on your PC** from **your own** Steam game and **your own** PSP disc image.
This repository contains only scripts, tables (cue names, indexes, gains) and hashes.
No game, PSP, audio, video or image file is distributed. (I am not a lawyer.)

## Requirements
- Windows, the Steam game *Tales of Eternia Remastered* (unmodified: use "Verify integrity" first).
- Your own dump of the **European PSP release (ULES-00176)**, `.iso` or `.cso`. The patcher checks it against a hash list and refuses anything else. Please do not ask for, or post, links to dumps here.
- [Python 3.10+](https://python.org) (tick "Add python.exe to PATH"). The logo option also installs `numpy`, `UnityPy`, `pillow` via pip.
- ~1 GB free disk space (temporary files).
- `tools/VGAudioCli.exe` is included (official v2.2.1, MIT; may need .NET Framework 4.5.1+ – *inference, not verified on every PC*).

## Usage
Two ways, same result. Everything runs on your PC and uses a menu.

**A) Python version (readable source, recommended if you want to audit what runs)**
Double-click `RUN_PATCHER.bat` (it only runs `python toe_patcher.py`), or run `python toe_patcher.py` yourself.

**B) `ToePatcher.exe`** (from the Releases page, if published)
The exe is just the same Python code packed with PyInstaller. It is unsigned, so Windows SmartScreen and some antivirus programs may warn about it. Compare its SHA-256 with the one published on the release page, or build it yourself from this source with `BUILD_EXE.bat` (add `lite` to leave out the logo option).

In the menu choose **1 - INSTALL everything**: it asks for your PSP `.iso`/`.cso` (a file window opens), checks it, extracts the voices, encodes them (2-3 minutes, expected 900 / 136 / 32 files), installs voices **and** the "TEST" title logo, with backups. If the logo step fails the voices stay installed.
**2 - RESTORE everything** puts voices and logo back. Other options: status, voices only, logo only, and **delete temporary files** (removes the extracted PSP audio when you are done).

Backups are named `*.PRE_PATCH_TEST` next to the game files. Restore always works, and Steam's
"Verify integrity" also reverts everything. **Never delete the backups before restoring.**

## Status
### Confirmed (heard in game by the maintainer)
- The 136 EM0200 event lines play the PSP English voice.
- Battle and minigame voices, as currently mapped, play correctly (restore/install cycles tested).
- Shizel's lines are fixed.
- Reid attack / damage voices (S00) after the in-place S00 fix.
- Logo installs and displays.

### NOT confirmed – help wanted
- S00 mapping was done by duration + lineage, **without waveform correlation**. Two Meredy clips are truncated to fit their slot. In general, a PSP clip longer than the original remaster slot is cut to that slot length (20 of the 32 waveforms were cut; S00 must keep its exact original size).
- `rac_won00`–`03`: untested.
- WHIS, Gnome, Max / Chat, Valkyrie, Nereid, `max_shout05`, `vol_spell00`: not confirmed.
- `vc_arc_won00`, `vc_far_chiyukou`: left as the remaster voice (no safe PSP match).
- Celsius cuts (trimmed at PSP b_us 832 / 843): subjective.
- Untested on third-party PCs and on other disc dumps.

### Decisions
- `vc_mer_destiny` is muted. `vc_kok` is untouched.
- HCA is encoded at `Highest` quality (the original events used `high`).

### NOT changed
- Other events (only EM0200), skits, the intro video, menu/other SE banks.

## How to report
Open an Issue with: what you played (scene / battle / character), what you heard, and the
`INSTALL_REPORT`/console output if something failed. Short audio clips of *your own recording* are fine; please do not upload extracted game audio.

## Safety (repo hygiene)
Uploaded by browser only, no tokens, 2FA on, GitHub Actions disabled. If you fork, read every script first.

## License
Own code (scripts, tables, docs): MIT, see `LICENSE`. This license does **not** cover any game, PSP or third-party material. Third-party components: see `THIRD_PARTY_NOTICES.md`.
