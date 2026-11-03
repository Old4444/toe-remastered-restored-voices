# -*- coding: utf-8 -*-
"""toe_extras.py - extra steps of the single patcher: mute the remaster-only skits, cutscene-movie audio, restored opening.
Everything is generated on YOUR computer from YOUR game and YOUR PSP disc. Nothing from the game/PSP is distributed."""
import os, sys, re, csv, struct, hashlib, shutil, subprocess, tempfile, types, wave
from toe_paths import RES, WORK
sys.path.insert(0, os.path.join(RES, 'lib')); sys.path.insert(0, RES)

GAME = 'Tales of Eternia Remastered'
MOVIE_REL = os.path.join(GAME + '_Data', 'StreamingAssets', 'Movie', 'vp9')
ORIG_OP_SHA = 'a802aa8d104ceb3954d74d483519fe3c79362462f4943218eebdf73c344e54ad'
SUF_VID, SUF_OP = '.PRE_VID', '.PRE_OP'
sha = lambda b: hashlib.sha256(b).hexdigest()

def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()

# ------------------------------------------------------------ mute the remaster-only skits (N/C/S families of Vo.acb)
def mute_skits(out_dir, vgaudio):
    """Replaces every N###/C###/S### cue (skits that exist only in the remaster; streaming, mono 44.1 kHz) by silence of the SAME
    length, in the freshly built Vo.acb/Vo.awb inside out_dir. Updates the AWB hash and header stored in the ACB."""
    import utf, afs2, afs2b, enc_vga
    acb_p, awb_p = os.path.join(out_dir, 'Vo.acb'), os.path.join(out_dir, 'Vo.awb')
    acb = open(acb_p, 'rb').read(); awb = open(awb_p, 'rb').read()
    a = afs2.parse_afs2(awb); pl = [awb[s:e] for s, e in a['ents']]
    assert afs2b.build_afs2(a, pl) == awb, 'mute: AWB re-pack check failed'
    t = utf.parse(acb); R = t.rows[0]
    assert hashlib.md5(awb).digest() == utf.parse(R['StreamAwbHash'][1]).rows[0]['Hash'][1], 'mute: AWB hash does not match the ACB'
    wt = utf.parse(R['WaveformTable'][1]); ct = utf.parse(R['CueTable'][1]); cn = utf.parse(R['CueNameTable'][1])
    n2c = {utf.sget(cn, r['CueName']): r['CueIndex'] for r in cn.rows}
    sel = sorted(c for c in n2c if re.match(r'^(N|C|S)\d{3}$', c))
    def frames_of(p):
        assert p[8:11] == bytes([0x66 | 0x80, 0x6d | 0x80, 0x74 | 0x80]), 'mute: unexpected HCA header'
        return struct.unpack('>I', p[16:20])[0], p[12], struct.unpack('>I', b'\0' + p[13:16])[0]
    rows = []; seen = set()
    for c in sel:
        cr = ct.rows[n2c[c]]; w = wt.rows[cr['ReferenceIndex']]
        if cr['ReferenceType'] != 3 or w['Streaming'] != 1 or w['NumChannels'] != 1 or w['SamplingRate'] != 44100: continue
        sid = w['StreamAwbId']
        if sid in seen: continue
        seen.add(sid); fr, ch, sr = frames_of(pl[sid])
        if ch == 1 and sr == 44100: rows.append((c, sid, fr))
    if not rows: print('  mute: no new-skit cues found (different game version?). Skipped.'); return 0
    maxfr = max(r[2] for r in rows)
    tmp = tempfile.mkdtemp(prefix='toemute_')
    try:
        wp = os.path.join(tmp, 'sil.wav'); hp = os.path.join(tmp, 'sil.hca')
        w_ = wave.open(wp, 'wb'); w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(44100); w_.writeframes(b'\0\0' * ((maxfr + 4) * 1024)); w_.close()
        subprocess.run([vgaudio, '-i', wp, '-o', hp, '--hcaquality', 'Lowest'], check=True, stdout=subprocess.DEVNULL)
        clear = open(hp, 'rb').read()
    finally: shutil.rmtree(tmp, ignore_errors=True)
    assert clear[:3] == b'HCA'
    hs = struct.unpack('>H', clear[6:8])[0]; assert clear[8:12] == b'fmt\0' and clear[24:28] == b'comp'
    fs = struct.unpack('>H', clear[28:30])[0]; assert (len(clear) - hs) % fs == 0
    frames = [clear[hs + i * fs: hs + (i + 1) * fs] for i in range((len(clear) - hs) // fs)]; assert len(frames) >= maxfr + 2
    fr0 = frames[len(frames) // 2]; newpl = list(pl)
    for c, sid, fr in rows:
        h = bytearray(clear[:hs]); h[16:20] = struct.pack('>I', fr)
        f_ = enc_vga.enc(bytes(h) + fr0 * fr, 49920)
        assert f_[:4] == bytes.fromhex('c8c3c100') and frames_of(f_)[0] == fr
        newpl[sid] = f_
    newawb = afs2b.build_afs2(a, newpl); a2 = afs2.parse_afs2(newawb)
    assert a2['ids'] == a['ids'] and a2['hdr_end'] == a['hdr_end']
    ht = utf.parse(R['StreamAwbHash'][1]); ht.rows[0]['Hash'] = ('D', hashlib.md5(newawb).digest(), ht.rows[0]['Hash'][2])
    R['StreamAwbHash'] = ('D', utf.build(ht), R['StreamAwbHash'][2])
    hd = utf.parse(R['StreamAwbAfs2Header'][1]); hl = len(hd.rows[0]['Header'][1])
    hd.rows[0]['Header'] = ('D', newawb[:hl], hd.rows[0]['Header'][2]); R['StreamAwbAfs2Header'] = ('D', utf.build(hd), R['StreamAwbAfs2Header'][2])
    new_acb = utf.build(t)
    r2 = utf.parse(new_acb).rows[0]
    assert utf.parse(r2['StreamAwbHash'][1]).rows[0]['Hash'][1] == hashlib.md5(newawb).digest()
    open(awb_p, 'wb').write(newawb); open(acb_p, 'wb').write(new_acb)
    print('  muted %d remaster-only skit lines (same lengths).' % len(rows)); return 0

# ------------------------------------------------------------ ffmpeg
def find_ffmpeg(ask=True):
    """Looks for ffmpeg (LGPL build is enough): TOE_FFMPEG, next to the program, PATH. Otherwise asks once."""
    c = []
    if os.environ.get('TOE_FFMPEG'): c.append(os.environ['TOE_FFMPEG'])
    for d in (WORK, os.path.join(WORK, 'ffmpeg'), os.path.join(WORK, 'ffmpeg', 'bin'), os.path.join(WORK, 'tools')):
        c.append(os.path.join(d, 'ffmpeg.exe'))
    w = shutil.which('ffmpeg')
    if w: c.append(w)
    try:
        for n in os.listdir(WORK):
            p = os.path.join(WORK, n, 'bin', 'ffmpeg.exe')
            if os.path.isdir(os.path.join(WORK, n)): c.append(p)
    except OSError: pass
    for p in c:
        if p and os.path.isfile(p): return p
    if not ask: return None
    print('\nThis step needs ffmpeg (a free program; the "LGPL" build is enough). It is NOT included in this download.')
    print('Get it from https://github.com/BtbN/FFmpeg-Builds/releases/latest (file ffmpeg-n*-win64-lgpl-*.zip - NOT "winarm64"), unzip it anywhere, and select ffmpeg.exe (inside its "bin" folder).')
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk(); root.withdraw(); root.attributes('-topmost', True)
        p = filedialog.askopenfilename(title='Select ffmpeg.exe (leave empty to skip)', filetypes=[('ffmpeg', 'ffmpeg.exe'), ('All files', '*.*')]); root.destroy()
    except Exception:
        p = input('Path to ffmpeg.exe (empty = skip): ').strip().strip('"')
    return p if p and os.path.isfile(p) else None

# ------------------------------------------------------------ cutscene movies (audio replaced by the PSP English audio)
def movie_dir(game): return os.path.join(game, MOVIE_REL)

def install_movies(game, disc, ffmpeg, vgaudio):
    import toe_videos
    md = movie_dir(game)
    if not os.path.isdir(md): print('Movie folder not found: ' + md); return 1
    out = os.path.join(WORK, 'output_movies'); shutil.rmtree(out, ignore_errors=True)
    ns = types.SimpleNamespace(recipe=os.path.join(RES, 'RECEITA_VIDEOS_090.csv'), game_dir=md, out=out, iso=disc, psp_dir=None, ffmpeg=ffmpeg, vgaudio=vgaudio)
    toe_videos.build(ns)
    n = 0
    for fn in sorted(os.listdir(out)) if os.path.isdir(out) else []:
        dst = os.path.join(md, fn); bk = dst + SUF_VID
        if not os.path.exists(bk): shutil.copy2(dst, bk)
        shutil.copy2(os.path.join(out, fn), dst + '.tmp'); os.replace(dst + '.tmp', dst); n += 1
    shutil.rmtree(out, ignore_errors=True)
    print('Cutscene movies updated: %d file(s). Backups end in %s.' % (n, SUF_VID)); return 0 if n else 1

def restore_movies(game):
    md = movie_dir(game); n = 0
    if os.path.isdir(md):
        for fn in os.listdir(md):
            if fn.endswith(SUF_VID):
                shutil.copy2(os.path.join(md, fn), os.path.join(md, fn[:-len(SUF_VID)] + '.tmp')); os.replace(os.path.join(md, fn[:-len(SUF_VID)] + '.tmp'), os.path.join(md, fn[:-len(SUF_VID)])); n += 1
    print('Cutscene movies restored: %d file(s).' % n); return 0

# ------------------------------------------------------------ restored opening
def install_opening(game, disc, ffmpeg, vgaudio, jobs=2):
    import toe_abertura as A, toe_videos
    md = movie_dir(game); gp = os.path.join(md, 'op.pmf.dat'); bk = gp + SUF_OP
    src = bk if os.path.exists(bk) else gp
    if not os.path.isfile(src): print('op.pmf.dat not found.'); return 1
    work = os.path.join(WORK, 'work_opening'); os.makedirs(work, exist_ok=True)
    get = toe_videos.open_psp(types.SimpleNamespace(iso=disc, psp_dir=None))
    psp = os.path.join(work, 'op_psp.pmf'); open(psp, 'wb').write(get('op'))
    a = types.SimpleNamespace(work=work, game_pmf=src, psp_pmf=psp, pc_ivf=None, edl=os.path.join(RES, 'edl_final.json'), ffmpeg=ffmpeg, vgaudio=vgaudio, jobs=jobs)
    for step in (A.step_pcvideo, A.step_audio, A.step_video, A.step_mux): step(a)
    out = os.path.join(work, 'op.pmf.dat')
    if not os.path.exists(bk): shutil.copy2(gp, bk)
    if sha_file(bk) != ORIG_OP_SHA: print('The backup of op.pmf.dat is not the original; aborted.'); return 1
    shutil.copy2(out, gp + '.tmp'); os.replace(gp + '.tmp', gp)
    shutil.rmtree(work, ignore_errors=True)
    print('Restored opening installed. Backup: op.pmf.dat' + SUF_OP); return 0

def restore_opening(game):
    gp = os.path.join(movie_dir(game), 'op.pmf.dat'); bk = gp + SUF_OP
    if not os.path.exists(bk): print('Opening: no backup (it was not changed by this tool).'); return 0
    if sha_file(bk) != ORIG_OP_SHA: print('Opening backup is not the original; use Steam "Verify integrity of game files".'); return 1
    shutil.copy2(bk, gp + '.tmp'); os.replace(gp + '.tmp', gp); print('Opening restored.'); return 0
