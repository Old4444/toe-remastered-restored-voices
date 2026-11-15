# -*- coding: utf-8 -*-
"""toe_voices090.py - regenera do zero (a partir do PSP do proprio usuario) as vozes de evento EM (1347), skits H (79),
batalha vc (946) e S00 (52): decodifica -> WAV -> VGAudio -> HCA. Nada de audio do jogo/PSP e distribuido: so receitas (numeros e hashes)."""
import os, io, csv, sys, wave, struct, hashlib, subprocess
from concurrent.futures import ThreadPoolExecutor
from toe_paths import RES, WORK
from psx_decode import decode_adpcm
RATE = 44100
sha = lambda b: hashlib.sha256(b).hexdigest()
UNMUTE = set()   # groups (cless, arche, sekundes, valkyrie) the user chose NOT to mute: their cues keep the remaster audio
GRUPOS = ('cless', 'arche', 'sekundes', 'valkyrie')
FAM = (('events', 1347), ('h', 79), ('battle', 946), ('s00', 52))

def _wav(path, pcm):
    b = io.BytesIO(); w = wave.open(b, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes(struct.pack('<%dh' % len(pcm), *pcm)); w.close(); data = b.getvalue()
    try:
        if os.path.isfile(path) and open(path, 'rb').read() == data: return data   # unchanged: keep the file (and its date) so the HCA is not re-encoded
    except OSError: pass
    open(path, 'wb').write(data); return data

def _csv(nome, enc='utf-8'): return list(csv.DictReader(open(os.path.join(RES, nome), encoding=enc)))

def aplicar(o, ganho, corte):
    if corte:
        seg, fade = corte.split(';'); n = int(round(float(seg) * RATE)); f = int(round(float(fade) * RATE / 1000))
        o = list(o[:n])
        for k in range(min(f, len(o))): o[len(o) - 1 - k] = o[len(o) - 1 - k] * k / f
    return [max(-32768, min(32767, int(round(x * ganho)))) for x in o]

def vag(ps, pasta, idx): return open(os.path.join(ps, pasta, '%s_%04d.vag' % (pasta, int(idx))), 'rb').read()

def prepare_wavs():
    ps = os.path.join(WORK, 'psp_streams'); avisos = 0
    for d in ('wav_events', 'wav_h', 'wav_battle', 'wav_s00'): os.makedirs(os.path.join(WORK, d), exist_ok=True)
    for r in _csv('RECEITA_EVENTOS.csv'):
        data = _wav(os.path.join(WORK, 'wav_events', r['evento_id'] + '.wav'), decode_adpcm(vag(ps, 's_us', r['indice_s_us'])[0x30:]))
        if sha(data) != r['wav_sha256']: avisos += 1
    for r in _csv('RECEITA_H.csv'):
        data = _wav(os.path.join(WORK, 'wav_h', r['cue'] + '.wav'), decode_adpcm(vag(ps, 'fc_us', r['indice_fc_us'])[0x30:])[:-28])
        if sha(data) != r['wav_sha256']: avisos += 1
    for r in _csv('RECEITA_BATALHA_090.csv'):
        if r['origem'] == 'mudo': o = [0] * 4096
        else:
            o = aplicar(decode_adpcm(vag(ps, r['origem'], r['indice'])[0x30:]), float(r['ganho'] or 1), r['corte'])
            o = o[int(r['recorte_ini']):len(o) - int(r['recorte_fim'])]
        _wav(os.path.join(WORK, 'wav_battle', r['cue'] + '.wav'), o)
        if len(o) != int(r['amostras_final']): avisos += 1
    import toe_audio
    toe_audio.s00(ps, os.path.join(RES, 'recipe_s00.csv'), os.path.join(WORK, 'wav_s00'))
    return avisos

def jobs():
    j = []
    for r in _csv('RECEITA_EVENTOS.csv'): j.append(('wav_events', 'hca_events', r['evento_id'], ['--no-loop', '--hcaquality', 'high']))
    for r in _csv('RECEITA_H.csv'): j.append(('wav_h', 'hca_h', r['cue'], ['--hcaquality', 'High']))
    for r in _csv('RECEITA_BATALHA_090.csv'): j.append(('wav_battle', 'hca_battle', r['cue'], ['--no-loop', '--hcaquality', 'High' if r['frame'] == '341' else 'Highest']))
    for f in sorted(os.listdir(os.path.join(WORK, 'wav_s00'))):
        if f.endswith('.wav'): j.append(('wav_s00', 'hca_s00', f[:-4], ['--hcaquality', 'Highest']))
    return j

def encode(vgaudio):
    J = jobs(); flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    for _, h, _, _ in J: os.makedirs(os.path.join(WORK, h), exist_ok=True)
    def one(j):
        src = os.path.join(WORK, j[0], j[2] + '.wav'); dst = os.path.join(WORK, j[1], j[2] + '.hca')
        if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): return True
        r = subprocess.run([vgaudio, '-i', src, '-o', dst, *j[3]], capture_output=True, creationflags=flags)
        return r.returncode == 0 and os.path.isfile(dst)
    print('Encoding %d files to HCA (several minutes)...' % len(J))
    with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as ex: res = list(ex.map(one, J))
    return len(res) - sum(res)

def counts():
    out = []
    for h, n in (('hca_events', 1347), ('hca_h', 79), ('hca_battle', 946), ('hca_s00', 52)):
        p = os.path.join(WORK, h); out.append((h, len([f for f in os.listdir(p) if f.endswith('.hca')]) if os.path.isdir(p) else 0, n))
    return out

def _skip(tipo):
    """IDs (cue names) of the optional-mute groups the user chose to leave in the remaster."""
    if not UNMUTE: return set()
    return {r['id'] for r in _csv('OPCOES_MUDOS.csv') if r['grupo'] in UNMUTE and r['tipo'] == tipo}

def s00_recipe():
    """recipe_s00.csv path; if some group stays unmuted, writes a filtered copy (those S00 slots keep the remaster audio)."""
    rec = os.path.join(RES, 'recipe_s00.csv'); sk = _skip('s00')
    if not sk: return rec
    rows = _csv('recipe_s00.csv', 'utf-8-sig'); keep = [r for r in rows if not (set(r['cues'].split(';')) & sk)]
    p = os.path.join(WORK, 'recipe_s00_efetivo.csv')
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(keep)
    return p

def items():
    it = []
    for r in _csv('RECEITA_EVENTOS.csv'): it.append((r['evento_id'], os.path.join(WORK, 'hca_events', r['evento_id'] + '.hca'), os.path.join(WORK, 'wav_events', r['evento_id'] + '.wav')))
    for r in _csv('RECEITA_H.csv'): it.append((r['cue'], os.path.join(WORK, 'hca_h', r['cue'] + '.hca'), os.path.join(WORK, 'wav_h', r['cue'] + '.wav')))
    sk = _skip('vo')
    for r in _csv('RECEITA_BATALHA_090.csv'):
        if r['cue'] in sk: continue
        it.append((r['cue'], os.path.join(WORK, 'hca_battle', r['cue'] + '.hca'), os.path.join(WORK, 'wav_battle', r['cue'] + '.wav')))
    return it
