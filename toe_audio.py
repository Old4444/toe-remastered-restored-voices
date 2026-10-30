# -*- coding: utf-8 -*-
"""toe_audio.py - step 2: decodes the extracted VAG streams (psp_streams/) and applies the recipes
(gain, mute, cut with fade). Produces 44.1 kHz mono 16-bit WAVs in wav_battle/, wav_s00/ and wav_events/
(temporary folders on your computer).
Usage: python toe_audio.py [psp_streams_folder] [recipe.csv] [wav_output_folder]
"""
import os, sys, csv, struct, wave
from toe_paths import RES, WORK
F = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]
RATE = 44100
MUDO_AMOSTRAS = 4096

def adpcm(d):
    s1 = s2 = 0; o = []
    for i in range(0, len(d) - 15, 16):
        sh = d[i] & 15; pr = min(d[i] >> 4, 4); f0, f1 = F[pr]
        for b in d[i + 2:i + 16]:
            for n in (b & 15, b >> 4):
                v = (n - 16 if n > 7 else n) << 12
                s = (v >> sh) + ((s1 * f0 + s2 * f1 + 32) >> 6)
                s = max(-32768, min(32767, s)); o.append(s); s2 = s1; s1 = s
    return o

def decodificar(vag):
    """v4 = always MONO, skip the 1st block and drop the last one; others: everything from 0x30."""
    ver = struct.unpack('>I', vag[4:8])[0]
    if ver == 4: return adpcm(vag[0x40:len(vag) - 16])
    return adpcm(vag[0x30:])

def gravar(p, o):
    w = wave.open(p, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes(struct.pack('<%dh' % len(o), *o)); w.close()

def aplicar(o, ganho, corte):
    if corte:
        seg, fade = corte.split(';'); n = int(round(float(seg) * RATE)); f = int(round(float(fade) * RATE / 1000))
        o = list(o[:n])
        for k in range(min(f, len(o))): o[len(o) - 1 - k] = o[len(o) - 1 - k] * k / f
    return [max(-32768, min(32767, int(round(x * ganho)))) for x in o]

def eventos(ps, out):
    """Decodes the 136 EM0200 event lines from s_us (stream name = event name on PC)."""
    os.makedirs(out, exist_ok=True); n = 0
    for r in csv.DictReader(open(os.path.join(ps, 's_us_manifest.csv'), encoding='utf-8')):
        nome = r['name'].split('.')[0]
        if not nome.startswith('EM0200'): continue
        vag = open(os.path.join(ps, 's_us', 's_us_%04d.vag' % int(r['index'])), 'rb').read()
        gravar(os.path.join(out, nome + '.wav'), aplicar(decodificar(vag), 1.0, '')); n += 1
    return n

def s00(ps, rec, out):
    """32 S00 waveforms (normal hit / damage) from b_us."""
    os.makedirs(out, exist_ok=True); n = 0
    for r in csv.DictReader(open(rec, encoding='utf-8-sig')):
        vag = open(os.path.join(ps, 'b_us', 'b_us_%04d.vag' % int(r['index'])), 'rb').read()
        o = aplicar(decodificar(vag), float(r['gain']), ''); esp = int(r['expected_samples'])
        if len(o) > esp + 28: o = o[:esp]   # same as the previously tested S00: tail cut (multiples of 1024 samples) to fit the original slot
        gravar(os.path.join(out, 'S00_%s.wav' % r['awb_id']), o); n += 1
    return n

def main():
    ps = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, 'psp_streams')
    rec = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RES, 'recipe_battle.csv')
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(WORK, 'wav_battle')
    os.makedirs(out, exist_ok=True); n = {'b_us': 0, 'mute': 0}; pend = []
    for r in csv.DictReader(open(rec, encoding='utf-8-sig')):
        cue = r['cue']
        if r['bank'] == 'b_us':
            vag = open(os.path.join(ps, 'b_us', 'b_us_%04d.vag' % int(r['index'])), 'rb').read()
            gravar(os.path.join(out, cue + '.wav'), aplicar(decodificar(vag), float(r['gain']), r['cut'])); n['b_us'] += 1
        elif r['bank'] == 'mute':
            gravar(os.path.join(out, cue + '.wav'), [0] * MUDO_AMOSTRAS); n['mute'] += 1
        else: pend.append(cue)
    rs = os.path.join(RES, 'recipe_s00.csv')
    print('S00 WAVs: %d' % s00(ps, rs, os.path.join(WORK, 'wav_s00')))
    ne = eventos(ps, os.path.join(WORK, 'wav_events'))
    print('EM0200 event WAVs: %d' % ne)
    print('WAVs generated: %d from the PSP, %d muted. Pending (keep the remaster voice): %s' % (n['b_us'], n['mute'], ', '.join(pend) or 'none'))

if __name__ == '__main__':
    main()
