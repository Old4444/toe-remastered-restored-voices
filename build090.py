# -*- coding: utf-8 -*-
"""build090.py - monta Vo.acb / Vo.awb (eventos EM, skits H, batalha vc) a partir dos ORIGINAIS do jogo e de uma lista de itens.
items: lista de (cue, arquivo_hca_claro, arquivo_wav). Troca o payload (cifra 56), NumSamples, SamplingRate, NumChannels e Length.
Nunca altera os arquivos de entrada."""
import sys, os, hashlib, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(0, os.path.join(here, 'lib'))
import utf, afs2, afs2b, enc_vga
import toe_build as B
sha = B.sha

def build_vo(src, out, items, quiet=False):
    acb = open(os.path.join(src, 'Vo.acb'), 'rb').read(); awb = open(os.path.join(src, 'Vo.awb'), 'rb').read()
    if sha(acb) != B.ORIG['Vo.acb'] or sha(awb) != B.ORIG['Vo.awb']:
        return 'ERRO: Vo.acb/Vo.awb de entrada nao sao os ORIGINAIS do jogo.'
    t = utf.parse(acb); R = t.rows[0]
    wt = utf.parse(R['WaveformTable'][1]); ct = utf.parse(R['CueTable'][1]); cn = utf.parse(R['CueNameTable'][1])
    n2c = {utf.sget(cn, r['CueName']): r['CueIndex'] for r in cn.rows}
    mem = afs2.parse_afs2(R['AwbFile'][1]); mpl = [R['AwbFile'][1][s:e] for s, e in mem['ents']]
    st = afs2.parse_afs2(awb); spl = [awb[s:e] for s, e in st['ents']]
    erros = []; usados = {}; log = []
    for cue, hcaf, wavf in items:
        if cue not in n2c: erros.append('cue inexistente: ' + cue); continue
        cr = ct.rows[n2c[cue]]; wi = cr['ReferenceIndex']; w = wt.rows[wi]
        if cr['ReferenceType'] != 3: erros.append('%s: ReferenceType %s' % (cue, cr['ReferenceType'])); continue
        if wi in usados and usados[wi][0] != hcaf: erros.append('%s: waveform %d dividido com %s com audio diferente' % (cue, wi, usados[wi][1])); continue
        usados[wi] = (hcaf, cue)
        raw = open(hcaf, 'rb').read(); hca = enc_vga.enc(raw)  # raw ja cifrado so ocorre nos testes com arquivos conhecidos
        ns = B.nsamples(wavf)
        if w['Streaming'] == 0: mpl[w['MemoryAwbId']] = hca; aid = w['MemoryAwbId']; tipo = 'mem'
        else: aid = w['StreamAwbId']; spl[st['ids'].index(aid)] = hca; tipo = 'stream'
        w['NumSamples'] = ns; w['SamplingRate'] = 44100; w['NumChannels'] = 1; cr['Length'] = int(ns * 1000 / 44100)
        log.append((cue, tipo, wi, aid, len(hca), sha(hca)))
    if erros: return 'ERROS (nada gravado):\n' + '\n'.join(' - ' + e for e in erros[:30])
    R['WaveformTable'] = ('D', utf.build(wt), R['WaveformTable'][2]); R['CueTable'] = ('D', utf.build(ct), R['CueTable'][2])
    R['AwbFile'] = ('D', afs2b.build_afs2(mem, mpl), R['AwbFile'][2])
    new_awb = afs2b.build_afs2(st, spl)
    h = utf.parse(R['StreamAwbHash'][1]); h.rows[0]['Hash'] = ('D', hashlib.md5(new_awb).digest(), h.rows[0]['Hash'][2]); R['StreamAwbHash'] = ('D', utf.build(h), R['StreamAwbHash'][2])
    hh = utf.parse(R['StreamAwbAfs2Header'][1]); n = len(hh.rows[0]['Header'][1]); assert n >= st['hdr_end']
    hh.rows[0]['Header'] = ('D', new_awb[:n], hh.rows[0]['Header'][2]); R['StreamAwbAfs2Header'] = ('D', utf.build(hh), R['StreamAwbAfs2Header'][2])
    new_acb = utf.build(t)
    os.makedirs(out, exist_ok=True); open(os.path.join(out, 'Vo.acb'), 'wb').write(new_acb); open(os.path.join(out, 'Vo.awb'), 'wb').write(new_awb)
    if not quiet: print('OK: %d cues (%d mem, %d stream). Vo.acb %d B, Vo.awb %d B' % (len(log), sum(1 for l in log if l[1] == 'mem'), sum(1 for l in log if l[1] == 'stream'), len(new_acb), len(new_awb)))
    return None
