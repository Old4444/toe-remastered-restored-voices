# Status – what is confirmed and what needs testers

Version: **0.9.0**. "Confirmed" means heard in game by the maintainer on one PC; it is not a guarantee for every setup.

## Game version notice

Most of the changes in this patch were tested on game version **2.0.0**. After the game updated to **2.1.0** (2026-11-02), some changes were identified that **may alter how the patch behaves and have not been fully tested**:

- Battle voices still play after the update (checked by the maintainer on one PC). On a clean 2.1.0 install (game files verified in Steam on 2026-11-02), the original `Vo.acb`, `Vo.awb` and `toe_psp_se_bank_S00.acb` are byte-identical to the 2.0.0 ones (SHA-256 compared), so the voice part of the patch should not be affected.
- The title-logo texture files were renamed and changed by the update, so the logo step written for 2.0.0 no longer matched. It was adapted for 2.1.0 and works in the maintainer's tests.
- 2.1.0 adds an "Arte Shortcut" feature and fixes some battle effects. How they interact with the restored battle voices (for example the shortcut lines) is unknown.

If you notice anything different after the update, you can open an Issue to document it. I may use reports to guide future work as time and resources allow.

## Confirmed
- Story events and the original (hint) skits H001–H079 play the PSP English voice (including the skit "Joining Chat crew", which used to freeze the game and was fixed).
- Reid: techniques, normal attack, damage, victories. Keele and Meredy: normal attack, damage, Meredy's summons. Farah: normal attack and damage.
- Rassius (attack, damage, skills, death). Undine, Sylph and Efreet (summons).
- Shizel (lightning, cure, resurrection, raise dead).
- Craymel Express (2 lines). The title logo. The restored opening video.
- Install and restore cycles.

## NOT confirmed – help wanted
- **Reid – Omega Seal and Omega Demon Chaos (extended versions)**: not yet reached in game by the maintainer.
- **Rassius, 4 victory lines** (`rac_won00`–`03`): identified on the PSP Sound Test, not tested in game.
- **WHIS (cards, `vc_mg_*`)**: the 6 lines for Farah (1, 2, 3, 5, 7, 8) are best guesses; Max and Chat not tested.
- **Gnome**: `shout03` stays with the remaster voice. Some voice mappings (`grabi`, `grave`, `damage01`, `spell00`, `kee_gnome`, `mer_gnome`) remain technically uncertain, but no incorrect or noticeably mismatched lines have been identified during in-game testing.
- **Max (`vc_fog_*`, `vc_max_*`) and Chat**: Max sounds right in the maintainer's tests (see the Max section below); `vc_max_shout05` and `vc_vol_spell00` may still be wrong, and Chat was not tested.
- **Valkyrie (`vc_wal_*`)**: not reached yet; `vc_wal_strike` is a guess.
- **Nereid**: fixed by analysis, not confirmed in game.
- **Celsius**: see "Celsius – choices made" below.
- Not yet tested on other PCs, other disc dumps, or with other antivirus software.

### Reid – Aurora Sword/Wall call-outs (0.9.0, tester check pending)
- Aurora Sword is a 3-stage technique (only 2 stages in normal play). In the remaster, Reid gives a faint little shout at the Aurora Wall stage before the technique fires (not a spoken word; it is not one of the `SE_ACT_KYOKKO*` effects, which were listened to and ruled out).
- In the PSP version, he says "Now!" and then the Aurora Sword fires. That part is already corrected.
- Still unreplaced: the faint shout before Aurora Wall. Whether the PSP has a shout there at all is unverified (needs checking in the PSP game). No Vo cue for Aurora Wall was found. If the PSP has none, it may stay as is.
- Do not change anything until the PSP is checked. If you have information about this, you can share it in an Issue; it may help guide future investigation.

### Other items left as the remaster voice (0.9.0) (tester check pending)
- **"Summon demon" skill** (`vc_shi_summondemon` and any other character that uses it, e.g. Shizel and Shadow; the full list of users is not verified): every instance keeps the remaster audio, because no equivalent was found in the PSP version (not fully verified). The decision applies to all characters. In play it did not break immersion in the fights against Shizel and Shadow.
- **Reid's line after destroying a ship in the naval battle minigame** (`vc_mg_rid_*`): still the remaster line; the matching cue and PSP line were not identified, so it does not match the energy of the old dub.
- **Max**: `vc_fog_order13` stays as the remaster voice. Sound effects `SE_BTV_022`, `023`, `029`–`037`, `044` and `049`–`116` in the S00 bank were not touched (044 is probably Nereid's damage sound, unconfirmed).
- **Reid's muted techniques**: eight cues stay silent on purpose (`vc_rid_1dankuuken`, `1gurenken`, `dankuuken`, `gurenken`, `hiouzetsuenshou` [Rising/Burning Phoenix], `kyokkouken`, `ryuukometsugazan`, `senkuusenresuha`). Two PSP lines are not used by any cue: `b_us` 131 (heard as "Neo Spiral Swarm", probably `senkuusenresuha`) and `b_us` 139 ("Dragon Demon Chaos", owner unknown). Both are only guesses and are not applied. The maintainer's playthrough found no problem with the other Reid techniques, which match their skill names.

### Cutscene movies (0.9.0, tester check pending)
- Only the **sound** of a movie is replaced, with the sound of the same movie from your own PSP disc. The video is never touched. It is rebuilt on your computer; no movie or sound is distributed.
- Method: the PSP audio of every movie was listened to and compared with the PC audio. A movie was chosen for replacement only when a different dub was noticed while listening, or when the comparison suggested it (by estimate). Movies whose sound is the same in both versions were left alone.
- **Replaced (3):** `01` (opening cutscene, English version; it has spoken lines and also the Melnics language that Meredy speaks), `15` and `24`.
- **Not replaced:** `02`, `03`, `04`, `06`, `07`, `09`, `12`, `19`, `20`, `21`, `22`, `23` (the sound is the same as the PSP; this was checked by comparing the volume curve of both and by listening), `25` (credits) and `op` (the opening, restored separately by the "complete" install). `01jp` (Japanese version) is also left alone.
- Movie numbers `05`, `08`, `10`, `11`, `13`, `14` and `16`–`18` exist neither in the game nor on the PSP disc: both have the same 17 movies. Why those numbers are skipped was not investigated.
- `01` (English) and `15` carry **two audio tracks** (44.1 kHz and 48 kHz). Tests in the game showed that the game plays track 1 (the 48 kHz one) in both: replacing track 0 changed nothing in `01` (English) or `15`. Track 0 is probably the Japanese audio. So the PSP sound goes into track 1 and track 0 is left untouched. This was just changed after those tests and is still to be confirmed in the game. `15` was checked in the game by the maintainer and sounds right (no problem noticed). `24` has not been reached in the game yet. **`01` (English) was timing-adjusted by hand-picked offsets**: the PSP sound is moved about 1 s earlier from 33 s to 87 s (a 1 s pause is inserted at 87.25 s to return to normal timing), because the new PC dub places its lines differently from the PSP. The maintainer checked it in the game and it sounds right; **one line may still be about half a second late**, which is barely noticeable.
- Unknown: whether `24` has a Japanese track that this replaces (it has a single audio track).
- If a movie sounds wrong, out of sync, or too loud/quiet, please open an Issue with the movie number.

## Decisions
- The project only restores voices; the remaster's text and script are not touched. A restored line may differ slightly from the on-screen text.
- `vc_mer_destiny` is **muted** (no line in the PSP). Double strikes (unison) are **muted** (also silent on PSP/PS1).
- Skits that exist only in the remaster (new in the remaster, 295 cues) have no English PSP voice; there is an **option to mute them** (on by default). Side effect: in those skits the characters' mouths stay closed and some expressions may look odd; answer "no" to the question during installation to keep the remaster voice.
- `vc_shi_delay` stays with the remaster voice (no equivalent PSP line).
- 33 battle cues remain intentionally muted (see `RECEITA_BATALHA_090.csv`, rows with `origem` = `mudo`); if you know the original PSP voice for any, you can share it in an Issue; it may help guide future investigation.
- HCA frames are kept at 512 bytes or less everywhere (original skits at 341 bytes, as in the PSP). Larger frames (up to 1486 bytes) froze one skit during testing.

## Celsius – choices made
Chosen by the maintainer for this version; the voice may still change later.
- `vc_cel_fenrir` is **muted** (no matching line found in the PSP). Tested in game: it sounds fine that way.
- `vc_cel_blizzard` and `vc_cel_koore` are **cuts of PSP clips**, a subjective choice: `blizzard` uses only the first 0.81 s of the clip it shares with `spell00` (50 ms fade-out); `koore` uses the first 0.55 s of the clip it shares with `freezelancer` (30 ms fade-out).
- **19 Celsius cues keep the remaster voice**: `iceneedle`, `shishisenkou`, `shouteiha`, `shou`, `soudoushouteiha`, `soudou`, `sazanka`, `seiseiseiya`, `sankamoushuukyaku`, `rengadan`, `hachiyourenga`, `hienrenkyaku`, `hienrentenkyaku`, `garyoukuuha`, `yousoushuugeki`, `yousourakubakushuu`, `ikkatsu`, `tenketsubakutai`, `hiyouhonpo`.
- One PSP Celsius line (`celcius_09`, b_us index 846) is not used by any cue; it is not known which attack it belongs to, so it is left unused for now.
- If you remember a PSP line that should replace one of these, you can share it in an Issue; it may help guide future investigation.
## Hyades – damage voices (0.9.0, confirmed by the maintainer)
- `vc_hia_damage00` (PSP `b_us` 707) and `vc_hia_dead00` (PSP `b_us` 706, "Gah!") are Hyades' two ordinary hit grunts. `vc_hia_dead00` used to use `b_us` 708 ("Not possible!"), which sounded wrong for an ordinary hit; it was changed to 706.
- The "Impossible" line is now heard only on very strong hits (a critical or a heavy blow). That is `vc_hia_dead01`, which was **not replaced** and keeps the remaster voice. In play this fits the moment well.
- Not replaced and left as the remaster voice: `vc_hia_dead01`, `vc_hia_shout01`, `vc_hia_stragnation`. His defeat plays `vc_hia_won00` (PSP voice).
- PSP `b_us` 708 ("Not possible!") is currently unused; it could be a candidate for `vc_hia_dead01`, but this is only a guess and is not applied.

## Max – battle voices, tester check pending
- One tester described Max's battle voices as sounding "strange" (not like wrong words or pain instead of an attack, more like "not how it should be"). It may be volume or sound-effect balance rather than the wrong line.
- Internal check of the build recipe: all 39 Max (`vc_fog_*`) cues point to PSP `b_us` 497-535, matching the Sound Test mapping, with no gain change applied. This was checked against the recipe, not by comparing the installed game files.
- `vc_fog_shortcut00` was built from `b_us` 530 ("Yeah!", the victory line), while the Sound Test mapping lists `b_us` 521 ("Right.") for it. It now uses 521. Every PSP Max line (`b_us` 497-535) is now used by exactly one cue.
- `vc_fog_order13` has no matching PSP line left and stays as in the remaster.
- Testers: if Max sounds wrong in battle, please tell us which action (attack, shortcut command, damage, victory) so it can be traced to a cue.
- Update: Max's normal-attack and damage effects play from the S00 bank (`SE_BTV_025` to `SE_BTV_028`, a block of 4 like every other character), which was still the remaster voice. They now use PSP `b_us` 512-515 (labelled "normal attack" in the PSP Sound Test). After this change the odd-sounding damage/attack seems to be fixed (first impression of the maintainer; more testing is welcome). Checked again on game version 2.1.0 with the final build: Max still sounds right.
- Not changed: `SE_BTV_022`, `023` (Chat), `029`-`037`, `044` (probably Nereid's 4th slot, unconfirmed) and `049`-`116` remain the remaster voice.

## NOT changed
- `vc_kok_*` (Quickie), `vc_kom_*`, `vc_kum_*`, `vc_man_*`, `vc_wom_*`, `vc_old_*`: left as in the remaster.
- Text, menu and other sound-effect banks.
