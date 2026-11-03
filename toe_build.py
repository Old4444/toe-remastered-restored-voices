# -*- coding: utf-8 -*-
"""toe_build.py - step 3: builds the test Vo.acb / Vo.awb / S00 from the ORIGINAL game files.
Replaces: (a) 900 battle/minigame cues (in-memory waveforms inside the .acb),
          (b) the 136 EM0200 event lines (streams in Vo.awb) and the .acb fields that depend on them,
          (c) 36 S00 sound-effect voices (normal hit / damage), written byte-for-byte at the original size.
Usage: python toe_build.py FOLDER_WITH_ORIGINAL_FILES OUTPUT [hca_battle] [hca_events] [recipe.csv]
Never modifies the input files.
"""
import sys, os, csv, hashlib, wave, collections
from toe_paths import RES, WORK
sys.path.insert(0, os.path.join(RES, 'lib'))
import utf, afs2, afs2b, enc_vga

ORIG = {'Vo.acb': '7c9b0d532912b31701b7a79c7e1ce25e23754120ad16d0d2b99f2b5ff5efffff',
        'Vo.awb': 'ae7d6d7c021362b3cb4825d7bc5cb688ee0cd2ce3879762e43504b6aa3e59de7',
        'toe_psp_se_bank_S00.acb': '4076f691fd3a565e1a4760383751b413eca08b583f98bf52519835d0cfc54c9d'}
S00 = 'toe_psp_se_bank_S00.acb'
sha = lambda b: hashlib.sha256(b).hexdigest()

def nsamples(wavp):
    with wave.open(wavp) as w:   # fecha o arquivo na hora (antes ficava aberto ate o coletor de lixo)
        assert w.getframerate() == 44100 and w.getnchannels() == 1
        return w.getnframes()

def _patch_campo(buf, t, row, nome, valor, base):
    """Writes a numeric field of a @UTF table row directly into the bytes (the file size does not change)."""
    import struct
    ver, rows_off, str_off, data_off, name_off, fc, rsz, rc = struct.unpack_from('>HHIIIHHI', buf, base + 8)
    off = 0
    for f in t.fields:
        if f['st'] != 0x50: continue
        fmt, n = utf.TYPES[f['ty']] if f['ty'] in utf.TYPES else (None, 4 if f['ty'] == 0xA else 8)
        if f['name'] == nome:
            assert fmt, 'non-numeric field: ' + nome
            struct.pack_into(fmt, buf, base + 8 + rows_off + row * rsz + off, valor); return
        off += n
    raise KeyError(nome)

def cortar_frames(clear, max_bytes):
    """Fallback: if the clear HCA does not fit its slot, drops frames from the end and fixes the header (fmt + CRC)."""
    import struct, hcadec
    hs = struct.unpack('>H', clear[6:8])[0]; h = bytearray(clear[:hs]); p = 8; fs = None; pf = None
    while p < hs - 2:
        t = bytes(h[p:p + 4]).rstrip(b'\0')
        if t == b'fmt': pf = p; p += 16
        elif t == b'comp': fs = struct.unpack('>H', h[p + 4:p + 6])[0]; p += 16
        elif t == b'dec': p += 12
        elif t == b'ciph': p += 6
        elif t == b'vbr': p += 8
        elif t == b'ath': p += 6
        elif t == b'loop': p += 16
        elif t == b'rva': p += 8
        elif t == b'comm': p += 5
        elif t == b'pad': break
        else: break
    assert fs and pf is not None, 'unexpected HCA'
    n = (max_bytes - hs) // fs
    h[pf + 8:pf + 12] = struct.pack('>I', n); h[hs - 2:hs] = struct.pack('>H', hcadec.crc16(bytes(h[:hs - 2])))
    return bytes(h) + clear[hs:hs + n * fs], n

def build_s00(src, out, hca_dir, wav_dir, rec):
    """S00 (battle sound effects): 36 normal-hit/damage waveforms; replaces in-memory payloads (subkey 60381)."""
    acb = open(os.path.join(src, S00), 'rb').read()
    if sha(acb) != ORIG[S00]: print('ERROR: the input S00 is not the ORIGINAL.'); return 1
    t = utf.parse(acb); R = t.rows[0]
    wt = utf.parse(R['WaveformTable'][1]); ct = utf.parse(R['CueTable'][1]); cn = utf.parse(R['CueNameTable'][1])
    n2c = {utf.sget(cn, r['CueName']): r['CueIndex'] for r in cn.rows}
    mem = afs2.parse_afs2(R['AwbFile'][1]); mpl = [R['AwbFile'][1][a:b] for a, b in mem['ents']]
    log = []
    for r in csv.DictReader(open(rec, encoding='utf-8-sig')):
        aid, wi = int(r['awb_id']), int(r['waveform']); w = wt.rows[wi]
        assert w['MemoryAwbId'] == aid and w['Streaming'] == 0, 'S00: unexpected waveform %s' % r['awb_id']
        hf = os.path.join(hca_dir, 'S00_%d.hca' % aid)
        if not os.path.exists(hf): print('ERROR: missing ' + hf); return 1
        ns = nsamples(os.path.join(wav_dir, 'S00_%d.wav' % aid))
        assert abs(ns - int(r['expected_samples'])) <= 28, 'S00 %d: duration %d differs from expected %s' % (aid, ns, r['expected_samples'])
        slot = len(mpl[aid]); clear = open(hf, 'rb').read(); hca = enc_vga.enc(clear, 60381)
        if len(hca) > slot:   # does not fit in the original slot: drop trailing frames (the S00 must keep its original size)
            clear, nfr = cortar_frames(clear, slot); hca = enc_vga.enc(clear, 60381); ns = min(ns, nfr * 1024)
            print('  note: S00 %d - the PSP clip is longer than the original slot; trimmed to %d frames (expected)' % (aid, nfr))
        assert len(hca) <= slot, 'S00 %d: payload larger than its slot' % aid
        hca = hca + b'\0' * (slot - len(hca)); mpl[aid] = hca; w['NumSamples'] = ns
        for c in r['cues'].split(';'): ct.rows[n2c[c]]['Length'] = int(ns * 1000 / 44100)
        log.append((r['cues'], 's00', wi, aid, len(hca), sha(hca)))
    # S00: write DIRECTLY into the original bytes (utf.build would rewrite the file and change its size; the game freezes on the title screen otherwise)
    import struct
    pool0 = 8 + struct.unpack_from('>HHIIIHHI', acb, 8)[3]
    ab = lambda k: pool0 + R[k][2]
    for k in ('AwbFile', 'WaveformTable', 'CueTable'): assert acb[ab(k):ab(k) + len(R[k][1])] == R[k][1], 'S00: position of ' + k
    new = bytearray(acb); awb_new = afs2b.build_afs2(mem, mpl)
    assert len(awb_new) == len(R['AwbFile'][1]), 'S00: AWB changed size'
    new[ab('AwbFile'):ab('AwbFile') + len(awb_new)] = awb_new
    for r in csv.DictReader(open(rec, encoding='utf-8-sig')):
        wi = int(r['waveform']); ns = wt.rows[wi]['NumSamples']
        _patch_campo(new, wt, wi, 'NumSamples', ns, ab('WaveformTable'))
        for c in r['cues'].split(';'): _patch_campo(new, ct, n2c[c], 'Length', ct.rows[n2c[c]]['Length'], ab('CueTable'))
    new = bytes(new)
    assert len(new) == len(acb), 'S00: final size differs from the original'
    t2 = utf.parse(new); w2 = utf.parse(t2.rows[0]['WaveformTable'][1]); c2 = utf.parse(t2.rows[0]['CueTable'][1])
    assert [r['NumSamples'] for r in w2.rows] == [r['NumSamples'] for r in wt.rows] and [r['Length'] for r in c2.rows] == [r['Length'] for r in ct.rows], 'S00: re-read mismatch'
    os.makedirs(out, exist_ok=True); open(os.path.join(out, S00), 'wb').write(new)
    with open(os.path.join(out, 'BUILD_REPORT.csv'), 'a', newline='', encoding='utf-8-sig') as f: csv.writer(f).writerows(log)
    print('OK S00: %d voices, %d B (sha %s...)' % (len(log), len(new), sha(new)[:12]))
    return 0

def main():
    """0.9.0: Vo.acb/Vo.awb (events EM, H skits, battle vc) + S00. Usage: toe_build.py FOLDER_WITH_ORIGINAL_FILES OUTPUT"""
    if len(sys.argv) < 3: print(__doc__); return 2
    src, out = sys.argv[1], sys.argv[2]
    import build090, toe_voices090 as V
    err = build090.build_vo(src, out, V.items())
    if err: print(err); return 1
    if os.path.exists(os.path.join(src, S00)):
        return build_s00(src, out, os.path.join(WORK, 'hca_s00'), os.path.join(WORK, 'wav_s00'), os.path.join(RES, 'recipe_s00.csv'))
    print('Warning: S00 not found in ' + src + '; only Vo was built.'); return 0

if __name__ == '__main__': sys.exit(main())
