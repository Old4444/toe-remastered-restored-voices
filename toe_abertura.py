# -*- coding: utf-8 -*-
"""toe_abertura.py - PROTOTIPO do modulo "abertura restaurada" (video HD do PC na ordem do PSP + musica do PSP).
Tudo e montado na maquina do usuario a partir do op.pmf.dat do PROPRIO jogo e do op.pmf do PROPRIO disco PSP.
NAO distribui nenhum arquivo do jogo/PSP; so a receita (edl_final.json). NAO mexe no jogo: grava so em --work.
Passos: pcvideo (extrai VP9/IVF do op.pmf.dat, sem cricodecs) | audio (demux ATRAC3+ do op.pmf PSP -> WAV com ganho -> HCA via VGAudioCli)
        | video (remonta o IVF na ordem do PSP, ffmpeg+libvpx) | mux (empacota op.pmf.dat, sem cricodecs)."""
import os, sys, json, struct, subprocess, shutil, argparse, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
KEY = 0x71258D1CD37A52
FPS = 30000 / 1001; TB = 1001 / 30000
GAIN = 1.4758            # ganho PSP -> nivel do PC (medido; o final aprovado usa ~1.4758)
NFRAMES = 3951           # quadros do video final (131,83 s)
PC_FRAMES = 3860         # quadros do video do PC
ENC = ['-c:v','libvpx-vp9','-crf','14','-b:v','0','-g','60','-auto-alt-ref','0','-lag-in-frames','0','-row-mt','1','-tile-columns','2',
       '-cpu-used','4','-deadline','good','-pix_fmt','yuv420p','-color_primaries','smpte170m','-colorspace','smpte170m','-color_trc','smpte170m',
       '-r','30000/1001','-video_track_timescale','30000','-f','ivf']

def log(*a): print(*a, flush=True)

# ---------------- PSP: demux do audio ATRAC3+ do op.pmf ----------------
def psp_audio_es(pmf_bytes):
    """Junta o payload dos pacotes private_stream_1 (0xBD). Cada quadro ATRAC3+ vem com 8 bytes de cabecalho '0F D0 xx xx 00 00 00 00'."""
    d = pmf_bytes; pos = struct.unpack('>I', d[8:12])[0]; es = bytearray()
    while pos < len(d) - 6:
        if d[pos:pos+3] == b'\x00\x00\x01':
            sid = d[pos+3]
            if sid == 0xBA: pos += 14 + (d[pos+13] & 7); continue
            if sid in (0xBB, 0xBE, 0xBD, 0xE0, 0xBF, 0xBC):
                ln = struct.unpack('>H', d[pos+4:pos+6])[0]
                if sid == 0xBD:
                    hl = d[pos+8]; es += d[pos+9+hl:pos+6+ln][4:]
                pos += 6 + ln; continue
        pos += 1
    return bytes(es)

def psp_audio_to_oma(pmf_path, oma_path):
    es = psp_audio_es(open(pmf_path, 'rb').read())
    assert es[:2] == b'\x0f\xd0', 'audio ATRAC3+ nao encontrado no op.pmf'
    params = struct.unpack('>H', es[2:4])[0]; fsz = (params & 0x3FF) * 8 + 8
    step = fsz + 8; assert len(es) % step == 0, 'tamanho do audio inesperado'
    frames = [es[i+8:i+step] for i in range(0, len(es), step)]
    assert all(es[i:i+2] == b'\x0f\xd0' for i in range(0, len(es), step)), 'cabecalho de quadro invalido'
    h = bytearray(96); h[:6] = b'EA3\x01\x00\x60'; h[6] = h[7] = 0xFF; h[32] = 1; h[33:36] = bytes([0, params >> 8, params & 255])
    open(oma_path, 'wb').write(b'ea3\x03\x00\x00\x00\x00\x00\x00' + bytes(h) + b''.join(frames))
    return len(frames)

def step_audio(a):
    os.makedirs(a.work, exist_ok=True); oma = os.path.join(a.work, 'op_psp.oma'); wav = os.path.join(a.work, 'OP_PSP_final.wav')
    n = psp_audio_to_oma(a.psp_pmf, oma); log('audio PSP: %d quadros ATRAC3+' % n)
    subprocess.run([a.ffmpeg, '-v', 'error', '-y', '-i', oma, '-af', 'volume=%.4f' % GAIN, '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', wav], check=True)
    log('WAV com ganho:', wav, os.path.getsize(wav))
    hca = os.path.join(a.work, 'OP_PSP_final.hca')
    if a.vgaudio:
        subprocess.run([a.vgaudio, '-i', wav, '-o', hca, '--bitrate', '235000'], check=True, stdout=subprocess.DEVNULL); log('HCA:', hca, os.path.getsize(hca))
    else: log('(sem --vgaudio: HCA nao gerado)')

# ---------------- PC: extrair video do op.pmf.dat ----------------
ORIG_OP_SHA256 = 'a802aa8d104ceb3954d74d483519fe3c79362462f4943218eebdf73c344e54ad'   # op.pmf.dat ORIGINAL da Steam
def sha256_file(p):
    import hashlib; h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 22), b''): h.update(blk)
    return h.hexdigest()

def step_pcvideo(a):
    import usm_own
    log('conferindo se o op.pmf.dat de entrada e o ORIGINAL da Steam (le 400 MB)...')
    if sha256_file(a.game_pmf) != ORIG_OP_SHA256:
        sys.exit('ERRO: %s nao e o op.pmf.dat original da Steam (hash diferente). Restaure o jogo/abertura e tente de novo. Nada foi gravado.' % a.game_pmf)
    out = os.path.join(a.work, 'op_pc_video.ivf'); os.makedirs(a.work, exist_ok=True)
    n = usm_own.extract_video(a.game_pmf, out)      # leitor/decifrador de USM proprio (sem cricodecs)
    log('video do PC extraido:', out, n)

# ---------------- remontar o video ----------------
def ivf_index(path):
    f = open(path, 'rb'); hdr = f.read(32); sz = f.seek(0, 2); pos = 32; idx = []
    while pos + 12 <= sz:
        f.seek(pos); s = struct.unpack('<I', f.read(4))[0]; f.seek(pos + 12); b = f.read(1)[0]
        idx.append((pos + 12, s, ((b >> 2) & 1) == 0 and (b >> 6) == 2 and ((b >> 3) & 1) == 0)); pos += 12 + s
    return hdr, idx

def make_plan(edl, idx):
    frames = [round((pb - pa) * FPS) for pa, pb, _, _, _ in edl]; frames[-1] += round(131.83 * FPS) - sum(frames); assert sum(frames) == NFRAMES
    keys = [i for i, x in enumerate(idx) if x[2]]
    def nextkey(i):
        for k in keys:
            if k >= i: return k
        return 10**9
    plan = []
    for (pa, pb, c0, c1, t), n in zip(edl, frames):
        if t == 'psp': plan.append(('enc_psp', min(round(pa * FPS), NFRAMES - n), n)); continue
        ci = round(c0 * FPS); avail = round((c1 - c0) * FPS); ratio = (pb - pa) / (c1 - c0)
        if abs(ratio - 1) > 0.02: plan.append(('enc_pcs', ci, avail, n)); continue
        take = min(n, avail); cj = ci + take; K = nextkey(ci)
        if K >= cj: plan.append(('enc_pc', ci, take))
        else:
            if K > ci: plan.append(('enc_pc', ci, K - ci))
            plan.append(('copy', K, cj))
        if n > take: plan.append(('dup', cj - 1, n - take))
    cnt = lambda p: p[2] - p[1] if p[0] == 'copy' else (p[3] if p[0] == 'enc_pcs' else p[2])
    assert sum(cnt(p) for p in plan) == NFRAMES
    return plan, cnt

def ivf_frames(path):
    d = open(path, 'rb').read(); pos = 32; out = []
    while pos + 12 <= len(d):
        s = struct.unpack('<I', d[pos:pos+4])[0]; out.append(d[pos+12:pos+12+s]); pos += 12 + s
    return out

def run_piece(a, pc, psp, i, p, out):
    tmp = out + '.tmp'; ff = [a.ffmpeg, '-v', 'error', '-y']
    if p[0] == 'enc_pc': cmd = ff + ['-ss', '%.6f' % ((p[1]-0.5)*TB), '-i', pc, '-frames:v', str(p[2])] + ENC + [tmp]
    elif p[0] == 'enc_pcs':
        r = p[3] / p[2]; cmd = ff + ['-ss', '%.6f' % ((p[1]-0.5)*TB), '-t', '%.4f' % ((p[2]+2)*TB), '-i', pc, '-vf', 'setpts=(PTS-STARTPTS)*%.6f,fps=30000/1001' % r, '-frames:v', str(p[3])] + ENC + [tmp]
    elif p[0] == 'enc_psp': cmd = ff + ['-i', psp, '-vf', 'trim=start_frame=%d:end_frame=%d,setpts=N/(30000/1001)/TB,scale=1920:1080:flags=lanczos,setsar=1,fps=30000/1001' % (p[1], p[1]+p[2]), '-frames:v', str(p[2])] + ENC + [tmp]
    elif p[0] == 'dup': cmd = ff + ['-ss', '%.6f' % ((p[1]-0.5)*TB), '-i', pc, '-frames:v', '1', '-vf', 'loop=loop=%d:size=1:start=0,setpts=N/(30000/1001)/TB' % p[2], '-frames:v', str(p[2])] + ENC + [tmp]
    subprocess.run(cmd, check=True); os.replace(tmp, out)

def step_video(a):
    pc = a.pc_ivf or os.path.join(a.work, 'op_pc_video.ivf'); pieces = os.path.join(a.work, 'pecas'); os.makedirs(pieces, exist_ok=True)
    edl = json.load(open(a.edl)); hdr, idx = ivf_index(pc); assert len(idx) == PC_FRAMES, 'video do PC inesperado: %d quadros' % len(idx)
    plan, cnt = make_plan(edl, idx); name = lambda i, p: os.path.join(pieces, 'p%02d_%s.ivf' % (i, p[0]))
    todo = [(i, p) for i, p in enumerate(plan) if p[0] != 'copy' and not os.path.exists(name(i, p))]
    log('%d pecas, %d a codificar, %d quadros copiados sem recodificar' % (len(plan), len(todo), sum(cnt(p) for p in plan if p[0] == 'copy')))
    t0 = time.time()
    def job(x):
        i, p = x; run_piece(a, pc, a.psp_pmf, i, p, name(i, p)); log('peca %d %s ok (%.0fs)' % (i, p[0], time.time() - t0))
    with ThreadPoolExecutor(max_workers=a.jobs) as ex: list(ex.map(job, todo))
    out = bytearray(hdr); out[24:28] = struct.pack('<I', NFRAMES); n = 0; src = open(pc, 'rb')
    def add(b):
        nonlocal n; out.extend(struct.pack('<IQ', len(b), n)); out.extend(b); n += 1
    for i, p in enumerate(plan):
        if p[0] == 'copy':
            for k in range(p[1], p[2]): src.seek(idx[k][0]); add(src.read(idx[k][1]))
        else:
            fr = ivf_frames(name(i, p)); assert len(fr) == cnt(p), (i, p, len(fr)); [add(b) for b in fr]
    assert n == NFRAMES; dst = os.path.join(a.work, 'op_final.ivf'); open(dst, 'wb').write(out); log('video final:', dst, len(out), n, 'quadros')

# ---------------- empacotar op.pmf.dat ----------------
def step_mux(a):
    import usm_own
    V = os.path.join(a.work, 'op_final.ivf'); A = os.path.join(a.work, 'OP_PSP_final.hca'); O = os.path.join(a.work, 'op.pmf.dat')
    for f in (V, A): assert os.path.exists(f), 'falta ' + f
    usm_own.build_usm(V, A, O); log('gravado', O, os.path.getsize(O))
    chk = os.path.join(a.work, '_verif.ivf'); usm_own.extract_video(O, chk)
    ok = sha256_file(chk) == sha256_file(V); os.remove(chk); log('video identico ao ivf:', ok)
    if not ok: sys.exit('ERRO: verificacao do video falhou')

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('steps', help='lista separada por virgula: pcvideo,audio,video,mux')
    ap.add_argument('--work', required=True); ap.add_argument('--game-pmf'); ap.add_argument('--psp-pmf')
    ap.add_argument('--pc-ivf'); ap.add_argument('--edl', default=os.path.join(HERE, 'edl_final.json'))
    ap.add_argument('--ffmpeg', default='ffmpeg'); ap.add_argument('--vgaudio'); ap.add_argument('--jobs', type=int, default=2)
    a = ap.parse_args()
    for s in a.steps.split(','): {'pcvideo': step_pcvideo, 'audio': step_audio, 'video': step_video, 'mux': step_mux}[s.strip()](a)
if __name__ == '__main__': main()
