# Tales of Eternia Remastered – Restored English Voices

Puts the original **PSP English voice acting** back into *Tales of Eternia Remastered* (Steam).
The patcher builds everything on **your PC**, from **your own** Steam game and **your own** European PSP disc image –
no game, PSP, audio, video or image file is distributed here.

**Current version:** TEST 0.1 – see [Releases](https://github.com/Old4444/toe-remastered-restored-voices/releases) for downloads and per-version notes, and
[STATUS.md](https://github.com/Old4444/toe-remastered-restored-voices/blob/main/STATUS.md) for what is confirmed and what still needs testers.

## What it restores

| Included | Not included |
|---|---|
| Story events of the **opening of the game, from the start to a little after the first boss** (**EM0200**, 136 lines) | The rest of the game's events, camp skits, the intro video |
| All **battle and minigame voices** used by the game's `Vo.acb` (900 cues) | Voices of battle NPCs (left as in the remaster) |
| Battle sound-effect voices in `S00` (normal hit / damage, 32 waveforms) | Menu and other sound-effect banks |
| Title logo: "RESTORED" with the word **TEST** (installed together with the voices) | |

## Install

1. Download `ToePatcher.exe` from [Releases](https://github.com/Old4444/toe-remastered-restored-voices/releases) and put it in **its own folder** (it uses ~1 GB of temporary space).
2. Run it and choose **1 – INSTALL everything**. A window asks for your PSP `.iso` / `.cso` (European release, ULES-00176).
   The patcher checks the disc against a hash list, extracts the voices, encodes them (2–3 minutes) and installs voices **and** the title logo.
   Backups of the original files are made first.
3. Start the game.

To undo: run the patcher again and choose **2 – RESTORE everything**. Steam's *Verify integrity of game files* also reverts the game.
Menu option 6 deletes the temporary files (the extracted PSP audio) when you are done.

## Requirements

- Windows and the Steam game *Tales of Eternia Remastered* (unmodified – use *Verify integrity* first).
- Your own dump of the **European PSP release (ULES-00176)**. Please do not ask for, or post, links to dumps here.
- `ToePatcher.exe` needs **nothing else installed**. (`VGAudioCli`, included, may need .NET Framework 4.5.1+ – *inference, not verified on every PC*.)
- To run from the readable source instead (no Git needed): *Code → Download ZIP*, extract, install Python 3.10+ (tick "Add python.exe to PATH"), then double-click `RUN_PATCHER.bat`. On first run it installs the logo libraries (`numpy`, `UnityPy`, `pillow`) with pip.

## Trust and safety

- The `.exe` is **not code-signed**, so Windows SmartScreen or your antivirus may warn about it. Compare its SHA-256 with the one on the Release page
  (`certutil -hashfile ToePatcher.exe SHA256`), or use the Python version, or build it yourself with `BUILD_EXE.bat` (`BUILD_EXE.bat lite` leaves out the logo).
- All source is in this repository and readable. The patcher only reads your files, writes next to itself and in the game's sound/logo folders (with backups), and uploads nothing.
- This repository is uploaded by browser only, with no tokens and no GitHub Actions workflows. If you fork it, read every script first.

## Help testing

Open an **Issue** with: what you played (scene / battle / character), what you heard, and the console output if something failed.
Short recordings of *your own* are fine; please do not upload extracted game audio.

## Legal

Unofficial fan project, not affiliated with the rights holders. *Tales of Eternia* and related material belong to their owners.
This repository contains only scripts, tables (cue names, indexes, gains) and hashes. I am not a lawyer.

## License

Own code (scripts, tables, docs): MIT, see [LICENSE](LICENSE). This license does **not** cover any game, PSP or third-party material.
Third-party components (including [VGAudio](https://github.com/Thealexbarney/VGAudio), MIT): see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
