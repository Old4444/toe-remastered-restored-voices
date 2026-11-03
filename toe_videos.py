# -*- coding: utf-8 -*-
"""toe_videos.py - replaces the SOUND of selected cutscene movies of Tales of Eternia Remastered
with the sound of the same movie from YOUR OWN PSP disc. The video is not touched and
nothing from the game or the PSP is redistributed: everything is built on your computer.

How it works (in-place, same file size, same layout):
  1. read the movie's .pmf from your PSP ISO/CSO (or from an already extracted folder),
     take its ATRAC3+ audio and decode it with an external ffmpeg;
  2. encode it to HCA with an external VGAudio at the same frame size as the game's audio;
  3. copy the game's movie file and overwrite only the audio chunks of the chosen track(s).

Usage:
  python toe_videos.py build  RECIPE.csv  GAME_MOVIE_DIR  OUT_DIR  --iso PSP.iso|.cso  --ffmpeg ffmpeg --vgaudio VGAudioCli.exe
  python toe_videos.py build  ... --psp-dir FOLDER_WITH_pmf_FILES      (instead of --iso)
  python toe_videos.py info   GAME_MOVIE_DIR                            (lists the audio tracks of each movie)
  python toe_videos.py selftest MOVIE.pmf.dat                           (checks the rewrite logic; writes nothing)
Recipe columns: movie_file,psp_movie,sha256,track0,track1[,warp]   (warp: adv=SECONDS;t1=;t3=;t2=)   (track = psp | psp50 (half volume) | mute | keep | -)
"""
import os, sys, struct, subprocess, shutil, csv, tempfile, wave, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
import hcadec

FS = 682            # HCA frame size used by the game's movie audio
SKIP_S = 0.06       # ATRAC3+ decoder delay (measured on 13 movies whose sound is the same in both versions)
GAIN = 1.0          # same movies measured at 1.00 +- 0.006 between PSP and PC

def log(*a): print(*a, flush=True)

# ---------------------------------------------------------------- HCA <-> USM audio
def _tables(key=0x71258D1CD37A52):
    def tbl(k):
        mul = ((k & 1) << 3) | 5; add = (k & 14) | 1; k >>= 4; r = []
        for i in range(16):
            k = (k * mul + add) & 0xF; r.append(k)
        return r
    kc0 = key - 1; kc = [(kc0 >> (8 * i)) & 0xFF for i in range(7)]
    seed = [kc[1], kc[1]^kc[6], kc[2]^kc[3], kc[2], kc[2]^kc[1], kc[3]^kc[4], kc[3], kc[3]^kc[2],
            kc[4]^kc[5], kc[4], kc[4]^kc[3], kc[5]^kc[6], kc[5], kc[5]^kc[4], kc[6]^kc[1], kc[6]]
    br = tbl(kc[0]); base = [0] * 256
    for r in range(16):
        bc = tbl(seed[r]); nb = br[r] << 4
        for c in range(16): base[r * 16 + c] = nb | bc[c]
    ct = [0] * 256; x = 0; pos = 1
    for i in range(256):
        x = (x + 17) & 0xFF
        if base[x] != 0 and base[x] != 0xFF: ct[pos] = base[x]; pos += 1
    ct[0] = 0; ct[255] = 255
    inv = [0] * 256
    for i in range(256): inv[ct[i]] = i
    return bytes(inv)
_INV = None

def hca_to_usm_audio(hca):
    """Plain HCA (VGAudio) -> masked header + frames encrypted with cipher type 56, as inside the game's USM."""
    global _INV
    if _INV is None: _INV = _tables()
    assert hca[:3] == b'HCA', 'not an HCA'
    hs = struct.unpack('>H', hca[6:8])[0]
    h = bytearray(hca[:hs]); p = 8; fs = None
    sizes = {b'fmt': 16, b'comp': 16, b'dec': 12, b'ciph': 6, b'ath': 6, b'loop': 16, b'vbr': 8, b'rva': 8, b'comm': 5, b'pad': 4}
    for i in range(3): h[i] |= 0x80
    while p < hs - 2:
        tag = bytes(h[p:p + 4]); name = bytes(x & 0x7f for x in tag).rstrip(b'\0')
        if name not in sizes: break
        if name == b'comp': fs = struct.unpack('>H', h[p + 4:p + 6])[0]
        if name == b'ciph': h[p + 4:p + 6] = struct.pack('>H', 56)
        for i in range(4):
            if i < 3 or name not in (b'fmt', b'pad', b'dec', b'ath', b'vbr', b'rva', b'comm'): h[p + i] |= 0x80
        p += sizes[name]
    h[hs - 2:hs] = struct.pack('>H', hcadec.crc16(bytes(h[:hs - 2])))
    frames = []
    for i in range(hs, len(hca) - fs + 1, fs):
        e = hca[i:i + fs - 2].translate(_INV)
        frames.append(e + struct.pack('>H', hcadec.crc16(e)))
    return bytes(h), frames, fs

def hca_info(hca):
    """(frame_count, frame_size, inserted, appended, channels, rate) of a plain or masked HCA."""
    hs = struct.unpack('>H', hca[6:8])[0]; p = 8; r = {}
    while p < hs - 2:
        name = bytes(x & 0x7f for x in hca[p:p + 4]).rstrip(b'\0')
        if name == b'fmt':
            r['ch'] = hca[p + 4]; r['rate'] = int.from_bytes(hca[p + 5:p + 8], 'big')
            r['frames'], r['ins'], r['app'] = struct.unpack('>IHH', hca[p + 8:p + 16]); p += 16
        elif name == b'comp': r['fs'] = struct.unpack('>H', hca[p + 4:p + 6])[0]; p += 16
        elif name == b'dec': p += 12
        elif name == b'ciph': p += 6
        elif name == b'ath': p += 6
        elif name == b'loop': p += 16
        elif name == b'vbr': p += 8
        elif name == b'rva': p += 8
        elif name == b'comm': p += 5
        else: break
    return r

def set_fmt_frames(hca_masked_hdr, frames):
    """Rewrites the frame count in the 'fmt' tag of a masked header and fixes its CRC."""
    h = bytearray(hca_masked_hdr); hs = struct.unpack('>H', h[6:8])[0]; p = 8
    while p < hs - 2:
        name = bytes(x & 0x7f for x in h[p:p + 4]).rstrip(b'\0')
        if name == b'fmt': h[p + 8:p + 12] = struct.pack('>I', frames); break
        p += {b'comp': 16, b'dec': 12, b'ciph': 6, b'ath': 6, b'loop': 16, b'vbr': 8, b'rva': 8, b'comm': 5}.get(name, 99)
    h[hs - 2:hs] = struct.pack('>H', hcadec.crc16(bytes(h[:hs - 2])))
    return bytes(h)

# ---------------------------------------------------------------- USM scan / patch
def scan(path):
    """List of audio chunks: {stream: {'hdr': (payload_off, len), 'frames': [(payload_off, len)...], 'tables': [(chunk_off, size)]}}"""
    streams = {}
    with open(path, 'rb') as f:
        pos = 0; end = os.path.getsize(path)
        while pos + 32 <= end:
            f.seek(pos); h = f.read(32)
            sig = h[:4]; size = struct.unpack('>I', h[4:8])[0]
            b = h[8:]
            off, pad = b[1], struct.unpack('>H', b[2:4])[0]
            if sig == b'@SFA':
                st = b[4]; pt = b[7] & 3; s = streams.setdefault(st, {'hdr': None, 'frames': [], 'tables': []})
                if pt == 0:
                    ent = (pos + 8 + off, size - off - pad)
                    if s['hdr'] is None: s['hdr'] = ent
                    else: s['frames'].append(ent)
                elif pt in (1, 3): s['tables'].append((pos + 8, size))
            pos += 8 + size
    return streams

def track_info(path):
    st = scan(path); out = {}
    with open(path, 'rb') as f:
        for k, s in sorted(st.items()):
            f.seek(s['hdr'][0]); hd = f.read(s['hdr'][1]); i = hca_info(hd)
            out[k] = dict(header_frames=i.get('frames'), slot_frames=len(s['frames']), fs=i.get('fs'), ch=i.get('ch'), rate=i.get('rate'), ins=i.get('ins'), app=i.get('app'))
    return out

def patch_usm(src, dst, replacements, progress=None):
    """replacements: {stream: (hdr96, [frames...])}. The frame list must have exactly slot_frames entries of the slot size."""
    st = scan(src)
    if os.path.abspath(src) != os.path.abspath(dst): shutil.copyfile(src, dst)
    with open(dst, 'r+b') as f:
        for k, (hdr, frames) in replacements.items():
            s = st[k]; assert len(frames) == len(s['frames']), 'stream %d: %d frames, slot has %d' % (k, len(frames), len(s['frames']))
            f.seek(s['hdr'][0]); old = f.read(s['hdr'][1]); assert len(hdr) == len(old) == 96, 'unexpected header size'
            for (o, ln), fr in zip(s['frames'], frames):
                assert len(fr) == ln, 'frame size %d != slot %d' % (len(fr), ln)
                f.seek(o); f.write(fr)
            f.seek(s['hdr'][0]); f.write(hdr)
            # the same header also lives inside the stream's info tables
            for (co, sz) in s['tables']:
                f.seek(co); blob = f.read(sz); j = blob.find(old)
                while j >= 0:
                    f.seek(co + j); f.write(hdr); j = blob.find(old, j + 1)
            if progress: progress(k)
    return True

# ---------------------------------------------------------------- PSP side
def psp_audio_es(d):
    pos = struct.unpack('>I', d[8:12])[0]; es = bytearray()
    while pos < len(d) - 6:
        if d[pos:pos + 3] == b'\x00\x00\x01':
            sid = d[pos + 3]
            if sid == 0xBA: pos += 14 + (d[pos + 13] & 7); continue
            if sid in (0xBB, 0xBE, 0xBD, 0xE0, 0xBF, 0xBC):
                ln = struct.unpack('>H', d[pos + 4:pos + 6])[0]
                if sid == 0xBD:
                    hl = d[pos + 8]; es += d[pos + 9 + hl:pos + 6 + ln][4:]
                pos += 6 + ln; continue
        pos += 1
    return bytes(es)

def pmf_to_oma(pmf_bytes, oma_path):
    es = psp_audio_es(pmf_bytes)
    assert es[:2] == b'\x0f\xd0', 'ATRAC3+ audio not found in the PSP movie'
    params = struct.unpack('>H', es[2:4])[0]; fsz = (params & 0x3FF) * 8 + 8; step = fsz + 8
    assert len(es) % step == 0, 'unexpected PSP audio size'
    frames = [es[i + 8:i + step] for i in range(0, len(es), step)]
    h = bytearray(96); h[:6] = b'EA3\x01\x00\x60'; h[6] = h[7] = 0xFF; h[32] = 1; h[33:36] = bytes([0, params >> 8, params & 255])
    open(oma_path, 'wb').write(b'ea3\x03\x00\x00\x00\x00\x00\x00' + bytes(h) + b''.join(frames))
    return len(frames)

def read_wav(p):
    w = wave.open(p, 'rb'); assert w.getnchannels() == 2 and w.getsampwidth() == 2 and w.getframerate() == 44100, 'unexpected wav'
    d = w.readframes(w.getnframes()); w.close(); return d

def write_wav(p, data, rate=44100):
    w = wave.open(p, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(rate); w.writeframes(data); w.close()

def parse_warp(txt):
    """'adv=0.96;t1=33.0;t3=57.0;t2=87.0' -> dict (seconds). Empty -> None."""
    if not txt or not txt.strip() or txt.strip() == '-': return None
    d = dict(kv.split('=') for kv in txt.strip().split(';') if kv)
    w = {k: float(v) for k, v in d.items()}
    if 'gap' in w: assert w['t1'] < w['t2'] and w['adv'] > 0, 'invalid warp'; w['t3'] = None
    else: assert w['t1'] < w['t3'] < w['t2'] and w['adv'] > 0, 'invalid warp'
    return w

def psp_wav(pmf_bytes, ffmpeg, work, name, n_samples, rate=44100, gain=1.0, warp=None):
    """PSP movie audio -> stereo 16-bit wav at `rate`, decoder delay removed, padded/cut to exactly n_samples.
    warp (optional): the sound is moved EARLIER by `adv` seconds from t1 on (a cut of `adv` seconds of the PSP sound at t1)
    and brought back to normal timing by t2 by playing t3..t2 slightly slower (pitch is kept), so nothing is repeated."""
    oma = os.path.join(work, name + '.oma'); wav = os.path.join(work, name + '_raw.wav')
    pmf_to_oma(pmf_bytes, oma)
    base = 'atrim=start=%.4f,asetpts=PTS-STARTPTS,volume=%.4f,aresample=%d' % (SKIP_S, GAIN * gain, rate)
    if warp and warp.get('t3') is None:
        # gap mode: moved earlier by `adv` from t1; at t2 a silence of `adv` seconds is inserted (choose t2 so that
        # t2+adv falls in a pause between two lines) and the sound is back to normal timing, nothing repeated or lost.
        a, t1, t2 = warp['adv'], warp['t1'], warp['t2']; f = 0.015
        parts = ['[0:a]%s,asplit=3[x0][x1][x3]' % base,
                 '[x0]atrim=0:%.4f,asetpts=PTS-STARTPTS,afade=t=out:st=%.4f:d=%.3f[y0]' % (t1, t1 - f, f),
                 '[x1]atrim=%.4f:%.4f,asetpts=PTS-STARTPTS,afade=t=in:d=%.3f,afade=t=out:st=%.4f:d=%.3f[y1]' % (t1 + a, t2 + a, f, (t2 - t1) - f, f),
                 'anullsrc=channel_layout=stereo:sample_rate=%d,atrim=0:%.4f,asetpts=PTS-STARTPTS[y2]' % (rate, a),
                 '[x3]atrim=start=%.4f,asetpts=PTS-STARTPTS,afade=t=in:d=%.3f[y3]' % (t2 + a, f),
                 '[y0][y1][y2][y3]concat=n=4:v=0:a=1[out]']
        cmd = [ffmpeg, '-v', 'error', '-y', '-i', oma, '-filter_complex', ';'.join(parts), '-map', '[out]', '-ar', str(rate), '-ac', '2', '-c:a', 'pcm_s16le', wav]
    elif warp:
        a, t1, t3, t2 = warp['adv'], warp['t1'], warp['t3'], warp['t2']; f = 0.015
        tempo = ((t2 - (t3 + a)) / (t2 - t3))
        segs = [('atrim=0:%.4f' % t1, t1),
                ('atrim=%.4f:%.4f' % (t1 + a, t3 + a), t3 - t1),
                ('atrim=%.4f:%.4f,asetpts=PTS-STARTPTS,atempo=%.6f' % (t3 + a, t2, tempo), t2 - t3),
                ('atrim=start=%.4f' % t2, None)]
        parts = ['[0:a]%s,asplit=4[x0][x1][x2][x3]' % base]
        for i, (flt, dur) in enumerate(segs):
            fx = (',' + 'afade=t=in:d=%.3f' % f if i > 0 else '') + ((',afade=t=out:st=%.4f:d=%.3f' % (dur - f, f)) if dur else '')
            parts.append('[x%d]%s,asetpts=PTS-STARTPTS%s[y%d]' % (i, flt, fx, i))
        parts.append('[y0][y1][y2][y3]concat=n=4:v=0:a=1[out]')
        cmd = [ffmpeg, '-v', 'error', '-y', '-i', oma, '-filter_complex', ';'.join(parts), '-map', '[out]', '-ar', str(rate), '-ac', '2', '-c:a', 'pcm_s16le', wav]
    else:
        cmd = [ffmpeg, '-v', 'error', '-y', '-i', oma, '-af', base, '-ac', '2', '-c:a', 'pcm_s16le', wav]
    subprocess.run(cmd, check=True)
    w = wave.open(wav, 'rb'); d = w.readframes(w.getnframes()); w.close()
    need = n_samples * 4
    d = d[:need] + b'\0' * max(0, need - len(d))
    out = os.path.join(work, name + '.wav'); write_wav(out, d, rate); return out

def silence_wav(work, name, n_samples, rate):
    out = os.path.join(work, name + '.wav'); write_wav(out, b'\0' * (n_samples * 4), rate); return out

def encode_hca(vgaudio, wav, hca, rate=44100):
    """CBR-encodes with VGAudio looking for the bitrate that gives the game's 682-byte frames."""
    target = FS * 8 * rate / 1024.0
    for delta in (0, 1, 2, 5, 20, 100, -1, -2, -5, -20, -100, 300, -300):
        b = int(round(target + delta))
        subprocess.run([vgaudio, '-i', wav, '-o', hca, '--bitrate', str(b)], check=True, stdout=subprocess.DEVNULL)
        data = open(hca, 'rb').read()
        if hca_info(data).get('fs') == FS: return data
    raise SystemExit('VGAudio did not produce %d-byte frames at %d Hz' % (FS, rate))

def fit_stream(plain_hca, header_frames, slot_frames, silence_frame):
    """Plain HCA -> (hdr96, frames) with exactly slot_frames frames and header frame count = header_frames."""
    hdr, frames, fs = hca_to_usm_audio(plain_hca)
    assert fs == FS, 'encoded HCA frame size is %d, the game uses %d' % (fs, FS)
    frames = frames[:slot_frames] + [silence_frame] * max(0, slot_frames - len(frames))
    hdr = set_fmt_frames(hdr, header_frames)
    return hdr, frames

# ---------------------------------------------------------------- build
def open_psp(a):
    if a.psp_dir:
        return lambda n: open(os.path.join(a.psp_dir, n + '.pmf'), 'rb').read()
    import toe_psp
    c = toe_psp.abrir(a.iso); files = toe_psp.listar(c)
    def get(n):
        key = [k for k in files if k.replace('\\', '/').lower().endswith('usrdir/movie/%s.pmf' % n.lower())]
        assert key, 'movie %s.pmf not found in the PSP disc' % n
        lb, sz = files[key[0]]; return toe_psp.ler_arquivo(c, lb, sz)
    return get

def sha256(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()

def build(a):
    rows = list(csv.DictReader(open(a.recipe, encoding='utf-8')))
    get = open_psp(a); os.makedirs(a.out, exist_ok=True); work = tempfile.mkdtemp(prefix='toevid_')
    for r in rows:
        mv = r['movie_file']; dst = os.path.join(a.out, mv); t0 = time.time()
        src = None
        for cand in (os.path.join(a.game_dir, mv + '.PRE_VID'), os.path.join(a.game_dir, mv)):   # prefer the backup of the original
            if os.path.exists(cand) and (not r.get('sha256') or sha256(cand) == r['sha256'].strip().lower()): src = cand; break
        if src is None:
            log('SKIP %s: not found, or it is not the original file of the game (restore the game files with Steam first).' % mv); continue
        ti = track_info(src); log('%s: tracks %s' % (mv, {k: (v['header_frames'], v['slot_frames']) for k, v in ti.items()}))
        pmf = get(r['psp_movie']); rep = {}
        for k in sorted(ti):
            act = (r.get('track%d' % k) or '-').strip().lower()
            if act in ('-', 'keep', ''): continue
            hf, sf, rate = ti[k]['header_frames'], ti[k]['slot_frames'], ti[k]['rate']
            tag = '%s_t%d' % (r['psp_movie'], k)
            if act == 'mute': wav = silence_wav(work, tag, hf * 1024, rate)
            elif act == 'psp': wav = psp_wav(pmf, a.ffmpeg, work, tag, hf * 1024, rate, 1.0, parse_warp(r.get('warp')))
            elif act == 'psp50': wav = psp_wav(pmf, a.ffmpeg, work, tag, hf * 1024, rate, 0.5, parse_warp(r.get('warp')))
            else: raise SystemExit('invalid action %r in the recipe' % act)
            hca = encode_hca(a.vgaudio, wav, os.path.join(work, tag + '.hca'), rate)
            sw = silence_wav(work, tag + '_sil', 44100, rate)
            sf_hca = encode_hca(a.vgaudio, sw, os.path.join(work, tag + '_sil.hca'), rate)
            _, sfr, _ = hca_to_usm_audio(sf_hca)
            rep[k] = fit_stream(hca, hf, sf, sfr[len(sfr) // 2])
            log('  track %d (%d Hz): %s' % (k, rate, act))
        patch_usm(src, dst, rep)
        log('  OK %s (%.0f s): tracks changed %s' % (mv, time.time() - t0, sorted(rep)))
    shutil.rmtree(work, ignore_errors=True)
    log('Done. Output:', a.out)

def selftest(path):
    """Takes each audio track of the movie, converts it to plain HCA, wraps it again with hca_to_usm_audio
    and checks that the frames are byte-identical to the game's. Nothing is written."""
    import struct as S
    ti = track_info(path); st = scan(path); ok = True
    with open(path, 'rb') as f:
        for k, s in st.items():
            f.seek(s['hdr'][0]); hd = f.read(s['hdr'][1])
            # unmask header tags
            h = bytearray(hd); hs = S.unpack('>H', h[6:8])[0]; p = 8
            while p < hs - 2:
                name = bytes(x & 0x7f for x in h[p:p + 4]).rstrip(b'\0')
                if name == b'pad':
                    for q in range(3): h[p + q] &= 0x7f
                    break
                n = {b'fmt': 16, b'comp': 16, b'dec': 12, b'ciph': 6, b'loop': 16, b'vbr': 8, b'ath': 6, b'rva': 8, b'comm': 5}.get(name)
                if n is None: break
                for q in range(len(name)): h[p + q] &= 0x7f
                p += n
            h[0:3] = b'HCA'; h[hs - 2:hs] = S.pack('>H', hcadec.crc16(bytes(h[:hs - 2])))
            fr_plain = []
            ct, inv = hcadec.mk(0x71258D1CD37A52, 0)
            for (o, ln) in s['frames'][:200]:
                f.seek(o); fr = bytearray(f.read(ln))
                for j in range(ln - 2): fr[j] = ct[fr[j]]
                fr[ln - 2:ln] = S.pack('>H', hcadec.crc16(bytes(fr[:ln - 2]))); fr_plain.append(bytes(fr))
            # plain hca with header ciph=0
            hp = bytearray(h); q = bytes(hp).find(b'ciph')
            if q > 0: hp[q + 4:q + 6] = b'\0\0'
            hp[hs - 2:hs] = S.pack('>H', hcadec.crc16(bytes(hp[:hs - 2])))
            nh, nfr, fs = hca_to_usm_audio(bytes(hp) + b''.join(fr_plain))
            same_f = all(nfr[i] == (lambda o, ln: (f.seek(o), f.read(ln))[1])(*s['frames'][i]) for i in range(len(nfr)))
            same_h = nh == hd
            log('stream %d: frames re-wrapped identical=%s, header identical=%s (info %s)' % (k, same_f, same_h, ti[k]))
            ok = ok and same_f
    return ok

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['build', 'info', 'selftest']); ap.add_argument('args', nargs='*')
    ap.add_argument('--iso'); ap.add_argument('--psp-dir'); ap.add_argument('--ffmpeg', default='ffmpeg'); ap.add_argument('--vgaudio')
    a = ap.parse_args()
    if a.cmd == 'info':
        for fn in sorted(os.listdir(a.args[0])):
            if fn.endswith('.pmf.dat'): log(fn, track_info(os.path.join(a.args[0], fn)))
    elif a.cmd == 'selftest':
        return 0 if selftest(a.args[0]) else 1
    else:
        a.recipe, a.game_dir, a.out = a.args[:3]
        if not (a.iso or a.psp_dir) or not a.vgaudio: raise SystemExit('need --iso (or --psp-dir) and --vgaudio')
        build(a)
    return 0

if __name__ == '__main__':
    sys.exit(main())
