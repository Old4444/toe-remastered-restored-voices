# Status – what is confirmed and what needs testers

Version: **TEST 0.1**. "Confirmed" means heard in game by the maintainer on one PC; it is not a guarantee for every setup.

## Confirmed
- The 136 EM0200 event lines play the PSP English voice.
- Battle and minigame voices, as currently mapped, play correctly.
- Shizel's lines are fixed.
- Reid attack / damage voices (S00) after the in-place S00 fix.
- The title logo installs and displays.
- Install and restore cycles work (voices and logo), both from the Python version and from `ToePatcher.exe`.

## NOT confirmed – help wanted
- S00 mapping was done by duration and lineage, **without waveform correlation**. A PSP clip longer than the original remaster slot is cut to that slot
  length (20 of the 32 waveforms), because `S00` must keep its exact original size. Two Meredy clips are truncated.
- `rac_won00` – `rac_won03`: untested.
- WHIS, Gnome, Max / Chat, Valkyrie, Nereid, `max_shout05`, `vol_spell00`: not confirmed.
- `vc_arc_won00`, `vc_far_chiyukou`: left as the remaster voice (no safe PSP match).
- Celsius cuts (trimmed at PSP `b_us` 832 / 843): subjective.
- Not yet tested on other PCs, on other disc dumps, or with other antivirus software.

## Decisions
- 33 battle cues are **muted** by decision of the maintainer: the dual / combined-skill voices that have no PSP counterpart (Reid, Meredy, Keele, Farah, Celsius, Sylph; including `vc_mer_destiny`). The exact list is every row with status `mute` in `recipe_battle.csv`.
- `vc_kok` is untouched.
- HCA is encoded at `Highest` quality (the original events used `high`).

## NOT changed
- Events other than EM0200, camp skits, the intro video, menu and other sound-effect banks.
- Voices of battle NPCs (left as in the remaster).
