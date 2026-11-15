# Status – what is confirmed and what needs testers

Version: **1.0** (final version). "Confirmed" means heard in game by the maintainer on one PC; it is not a guarantee for every setup.
The maintainer finished the game with this version and tested everything he came across; what he could not check one by one is listed under "NOT confirmed".

## Game version notice

Most of the changes in this patch were tested on game version **2.0.0**. After the game updated to **2.1.0** (2026-11-02), some changes were identified that **may alter how the patch behaves and have not been fully tested**:

- Battle voices still play after the update (checked by the maintainer on one PC). On a clean 2.1.0 install (game files verified in Steam on 2026-11-02), the original `Vo.acb`, `Vo.awb` and `toe_psp_se_bank_S00.acb` are byte-identical to the 2.0.0 ones (SHA-256 compared), so the voice part of the patch should not be affected.
- The title-logo texture files were renamed and changed by the update, so the logo step written for 2.0.0 no longer matched. It was adapted for 2.1.0 and works in the maintainer's tests.
- 2.1.0 adds an "Arte Shortcut" feature and fixes some battle effects. How they interact with the restored battle voices (for example the shortcut lines) is unknown.

If you notice anything different after the update, you can open an Issue to document it. I may use reports to guide future work as time and resources allow.

## Confirmed
- Story events and the original (hint) skits H001–H079 play the PSP English voice (including the skit "Joining Chat crew", which used to freeze the game and was fixed).
- Reid: techniques (including the extended Omega Seal), normal attack, damage, victories. Keele and Meredy: normal attack, damage, Meredy's summons. Farah: normal attack and damage.
- Rassius (attack, damage, skills, death). Undine, Sylph and Efreet (summons).
- Shizel (lightning, cure, resurrection, raise dead).
- Craymel Express (2 lines). The title logo. The restored opening video.
- Reid: the Final Dragon Fang ("Dragon Demon Chaos", PSP voice) and his muted extra call-outs; Farah: Lion's Howl ("Chi!"); Valkyrie: hit and damage sounds.
- Cutscene movie `24` (the last movie, which the maintainer calls the credits movie): the PSP sound was checked after finishing the game and sounds right.
- Install and restore cycles.

## NOT confirmed – help wanted
- **Reid – Omega Demon Chaos (extended version)**: not yet reached in game by the maintainer.
- **Rassius, 4 victory lines** (`rac_won00`–`03`): identified on the PSP Sound Test, not tested in game.
- **WHIS (cards, `vc_mg_*`)**: the 6 lines for Farah (1, 2, 3, 5, 7, 8) are best guesses; Max and Chat not tested.
- **Gnome**: `shout03` stays with the remaster voice. Some voice mappings (`grabi`, `grave`, `damage01`, `spell00`, `kee_gnome`, `mer_gnome`) remain technically uncertain, but no incorrect or noticeably mismatched lines have been identified during in-game testing.
- **Max (`vc_fog_*`, `vc_max_*`) and Chat**: Max sounds right in the maintainer's tests (see the Max section below); `vc_max_shout05` and `vc_vol_spell00` may still be wrong, and Chat was not tested.
- **Nereid**: see the Nereid note under "Changes in 1.0" (his attack names are not spoken in the final battle; left as is).
- **Cless, Arche, Sekundes**: muted by default because the PSP has no match; this was verified from gameplay videos and the PlayStation 1 version, not from a PSP save.
- **Celsius**: see "Celsius – choices made" below.
- Not yet tested on other PCs, other disc dumps, or with other antivirus software.

### Reid – Aurora Sword/Wall call-outs (tester check pending)
- Aurora Sword is a 3-stage technique (only 2 stages in normal play). In the remaster, Reid gives a faint little shout at the Aurora Wall stage before the technique fires (not a spoken word; it is not one of the `SE_ACT_KYOKKO*` effects, which were listened to and ruled out).
- In the PSP version, he says "Now!" and then the Aurora Sword fires. That part is already corrected.
- Still unreplaced: the faint shout before Aurora Wall. Whether the PSP has a shout there at all is unverified (needs checking in the PSP game). No Vo cue for Aurora Wall was found. If the PSP has none, it may stay as is.
- It was left as it is. If you have information about this, you can share it in an Issue; it may help guide future investigation.

### Other items left as the remaster voice (tester check pending)
- **"Summon demon" skill** (`vc_shi_summondemon` and any other character that uses it, e.g. Shizel and Shadow; the full list of users is not verified): every instance keeps the remaster audio, because no equivalent was found in the PSP version (not fully verified). The decision applies to all characters. In play it did not break immersion in the fights against Shizel and Shadow.
- **Reid's line after destroying a ship in the naval battle minigame** (`vc_mg_rid_*`): still the remaster line; the matching cue and PSP line were not identified, so it does not match the energy of the old dub.
- **Max**: `vc_fog_order13` stays as the remaster voice. Sound effects `SE_BTV_022`, `023`, `029`–`037`, `044` and `049`–`104` (except `085`–`088`, see Valkyrie) in the S00 bank were not touched (044 is probably Nereid's damage sound, unconfirmed). `105`–`116` are the silent slots of Arche, Cless and Sekundes.
- **Reid's muted techniques**: seven cues stay silent on purpose (`vc_rid_1dankuuken`, `1gurenken`, `dankuuken`, `gurenken`, `hiouzetsuenshou` [Rising/Burning Phoenix], `kyokkouken` [Aurora Sword], `senkuusenresuha`). One PSP line is not used by any cue: `b_us` 131 (heard as "Neo Spiral Swarm", probably `senkuusenresuha`); it is only a guess and is not applied. (`ryuukometsugazan`, the Final Dragon Fang, now plays the PSP "Dragon Demon Chaos", `b_us` 139 – see "Changes in 1.0".) The maintainer's playthrough found no problem with the other Reid techniques, which match their skill names.

### Cutscene movies (tester check pending)
- Only the **sound** of a movie is replaced, with the sound of the same movie from your own PSP disc. The video is never touched. It is rebuilt on your computer; no movie or sound is distributed.
- Method: the PSP audio of every movie was listened to and compared with the PC audio. A movie was chosen for replacement only when a different dub was noticed while listening, or when the comparison suggested it (by estimate). Movies whose sound is the same in both versions were left alone.
- **Replaced (3):** `01` (opening cutscene, English version; it has spoken lines and also the Melnics language that Meredy speaks), `15` and `24`.
- **Not replaced:** `02`, `03`, `04`, `06`, `07`, `09`, `12`, `19`, `20`, `21`, `22`, `23` (the sound is the same as the PSP; this was checked by comparing the volume curve of both and by listening), `25` (credits) and `op` (the opening, restored separately by the "complete" install). `01jp` (Japanese version) is also left alone.
- Movie numbers `05`, `08`, `10`, `11`, `13`, `14` and `16`–`18` exist neither in the game nor on the PSP disc: both have the same 17 movies. Why those numbers are skipped was not investigated.
- `01` (English) and `15` carry **two audio tracks** (44.1 kHz and 48 kHz). Tests in the game showed that the game plays track 1 (the 48 kHz one) in both: replacing track 0 changed nothing in `01` (English) or `15`. Track 0 is probably the Japanese audio. So the PSP sound goes into track 1 and track 0 is left untouched. This was just changed after those tests and is still to be confirmed in the game. `15` was checked in the game by the maintainer and sounds right (no problem noticed). `24` was checked in the game by the maintainer after finishing it and sounds right. **`01` (English) was timing-adjusted by hand-picked offsets**: the PSP sound is moved about 1 s earlier from 33 s to 87 s (a 1 s pause is inserted at 87.25 s to return to normal timing), because the new PC dub places its lines differently from the PSP. The maintainer checked it in the game and it sounds right; **one line may still be about half a second late**, which is barely noticeable.
- Unknown: whether `24` has a Japanese track that this replaces (it has a single audio track).
- If a movie sounds wrong, out of sync, or too loud/quiet, please open an Issue with the movie number.

## Decisions
- The project only restores voices; the remaster's text and script are not touched. A restored line may differ slightly from the on-screen text.
- `vc_mer_destiny` is **muted** (no line in the PSP). Double strikes (unison) are **muted** (also silent on PSP/PS1).
- Skits that exist only in the remaster (new in the remaster, 295 cues) have no English PSP voice; there is an **option to mute them** (on by default). Side effect: in those skits the characters' mouths stay closed and some expressions may look odd; answer "no" to the question during installation to keep the remaster voice.
- `vc_shi_delay` stays with the remaster voice (no equivalent PSP line).
- 78 battle cues are muted on purpose (see `RECEITA_BATALHA_090.csv`, rows with `origem` = `mudo`): 35 of them for every user, plus 43 that belong to Cless, Arche, Sekundes and Valkyrie, which the installer lets you keep muted (default) or leave with the remaster voice; if you know the original PSP voice for any, you can share it in an Issue; it may help guide future investigation.
- HCA frames are kept at 512 bytes or less everywhere (original skits at 341 bytes, as in the PSP). Larger frames (up to 1486 bytes) froze one skit during testing.

## Celsius – choices made
Chosen by the maintainer for this version; the voice may still change later.
- `vc_cel_fenrir` is **muted** (no matching line found in the PSP). Tested in game: it sounds fine that way.
- `vc_cel_blizzard` and `vc_cel_koore` are **cuts of PSP clips**, a subjective choice: `blizzard` uses only the first 0.81 s of the clip it shares with `spell00` (50 ms fade-out); `koore` uses the first 0.55 s of the clip it shares with `freezelancer` (30 ms fade-out).
- **19 Celsius cues keep the remaster voice**: `iceneedle`, `shishisenkou`, `shouteiha`, `shou`, `soudoushouteiha`, `soudou`, `sazanka`, `seiseiseiya`, `sankamoushuukyaku`, `rengadan`, `hachiyourenga`, `hienrenkyaku`, `hienrentenkyaku`, `garyoukuuha`, `yousoushuugeki`, `yousourakubakushuu`, `ikkatsu`, `tenketsubakutai`, `hiyouhonpo`.
- One PSP Celsius line (`celcius_09`, b_us index 846) is not used by any cue; it is not known which attack it belongs to, so it is left unused for now.
- If you remember a PSP line that should replace one of these, you can share it in an Issue; it may help guide future investigation.
## Hyades – damage voices (confirmed by the maintainer)
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
- Not changed: `SE_BTV_022`, `023` (Chat), `029`-`037`, `044` (probably Nereid's 4th slot, unconfirmed) and `049`-`104` (except `085`-`088`) remain the remaster voice.

## Changes in 1.0 (since 0.9.0)
- **Reid – Final Dragon Fang ("Dragon Demon Chaos" in the PSP):** `vc_rid_ryuukometsugazan` now plays the PSP voice (`b_us` 139; confirmed in game). The remaster extra call-outs `vc_rid_65` ("Sacred skill!"), `vc_rid_58` ("This will do it!") and `vc_rid_66` ("Right there!") are muted. Sometimes Reid also says "I'm not done yet" (PSP voice, `b_us` 110, ear-checked by the maintainer); the technique can also play with only its name. This variation between attempts is normal and was checked by the maintainer.
- **Story event `EM9000_030_10` (Reid: "Ultus Veigh is entrusted to you now"):** now uses the PSP audio (`s_us` 1080, internal name `EM9000_030_10a`), which 0.9.0 missed because of the trailing "a". Events: 1,346 -> 1,347.
- **Hyades (`vc_hia_dead00`):** uses the "Gah!" (PSP 706). In 0.9.0 an old preparation could keep 708; the installer now detects changed recipes and prepares again.
- **Rem – Shining Flare (`vc_ask_shainingflare`):** muted (no equivalent line in the PSP).
- **Farah – Lion's Howl (`vc_far_shishisenkou`):** now the PSP "Chi!" (`b_us` 212), ear-checked by the maintainer (it was muted).
- **Cless and Arche (arena cameo bosses) – muted:** all of Cless's voice cues (`vc_cle_*`, 14) and Arche's spell/attack cues (`vc_arc_*`, 8; her victory line keeps the PSP clip it already used) are muted, plus their hit/damage sound-effect slots in the S00 bank. Reason: no match was found in the PSP database, and in a test battle on the PlayStation 1 version Cless is silent.
- **Sekundes (final boss, internal `vc_dha_*`, 15 cues) – all muted:** in the video check the boss makes no sound at all, so every voice cue is muted, and so are his S00 slots (empty in the PSP).
- **Valkyrie:** her voice cues (`vc_wal_*`, 6) are muted. Her hit and damage sounds (S00 `SE_BTV_085`–`088`) exist only in the PSP `S00.see` file and now come from the PSP (confirmed in game).
- **New installer option – mute or keep Cless, Arche, Sekundes and Valkyrie:** four questions at the start (default: muted, like the PSP). Answering *no* leaves that character's voices and hit/damage sounds as in the remaster, because some players find the silent versions dull.
- **How the Cless, Sekundes and Valkyrie checks were made:** from YouTube gameplay videos of the original game, because the maintainer had no PSP save file to confirm 100%. The decisions rest on those videos plus the absence of any match in the PSP database.
- **Nereid:** his cues use the PSP voice (including Dark Force and Thunder Blade). In the final battle (Shizel's Nereid) he uses the attacks without saying their names, but speaks other lines that fit the character and the attack; left as is. The other fight, the optional boss Regulus (a historical hero of Inferia, possessed by Nereid) on the last level of the EX Dungeon (the Labyrinth of Nereid), was not changed.
- **Destiny (Meredy's summon):** her summon stays silent like the original; the summoned heroes (`vc_des_*`) keep their remaster lines, which the maintainer preferred.
- **Logo:** shows "v1.0.0".
- **S00 bank:** 52 hit/damage slots (36 from `b_us`, 4 from the PSP `S00.see`, 12 silent).
- **Installer:** reuses a previous preparation only if it was made with the same recipes.

### Known limitations in 1.0
- **Attack and damage voices of Max, Chat and a few bosses** may not play, or play differently from the PSP. Likely cause: how the audio was encoded or how the game's sound database had to be edited. It cannot be fixed from our side and does not hurt the game experience.
- **Reid – faint "ahh" before Aurora Wall** (see above): still the remaster sound; no Vo cue for it was found, so it was not replaced.
- Some cues were matched by position and duration rather than by text (for example `vc_rid_57`, now the PSP "You're mine!").

## NOT changed
- `vc_kok_*` (Quickie), `vc_kom_*`, `vc_kum_*`, `vc_man_*`, `vc_wom_*`, `vc_old_*`: left as in the remaster.
- Text, menu and other sound-effect banks.
