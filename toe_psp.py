# -*- coding: utf-8 -*-
"""toe_psp.py - step 1 of the test patcher (Tales of Eternia Remastered, PSP voices).
Opens a PSP ISO or CSO, validates it against the hash list (toe_verify.py), and extracts the
VAG streams of b_us.v, s_us.v and fc_us.v into a TEMPORARY folder on your own computer.
Nothing is sent over the internet. No game/PSP file is redistributed: you use your own copy.
Usage: python toe_psp.py "game.iso|.cso" "output_folder"
"""
import sys, os, struct, hashlib, csv, time
import toe_verify as V

BANCOS = {  # arquivo no disco -> (pasta/prefixo, quantidade esperada de streams)
    'PSP_GAME/USRDIR/dat/b_us.v': ('b_us', 1100),
    'PSP_GAME/USRDIR/dat/s_us.v': ('s_us', 1347),
    'PSP_GAME/USRDIR/dat/fc_us.v': ('fc_us', 79),
}

def abrir(p):
    with open(p, 'rb') as f: magic = f.read(4)
    return V.CSO(p) if magic == b'CISO' else V.RAW(p)

def listar(c):
    pvd = c.read(16 * V.S, V.S)
    root = struct.unpack('<I', pvd[158:162])[0]; rlen = struct.unpack('<I', pvd[166:170])[0]
    return {n: (lb, sz) for n, lb, sz in V.walk(c, root, rlen)}

def ler_arquivo(c, lb, sz):
    out = bytearray(); off = lb * V.S; left = sz
    while left > 0:
        d = c.read(off, min(left, 1 << 20))
        if not d: break
        out += d; off += len(d); left -= len(d)
    return bytes(out)

def cortar_vags(data):
    """Scans the bank for 'VAGp' (0x30-byte header; big-endian size at +12)."""
    pos = 0; idx = 0; res = []
    while True:
        pos = data.find(b'VAGp', pos)
        if pos < 0 or pos + 0x30 > len(data): break
        ver = struct.unpack('>I', data[pos + 4:pos + 8])[0]
        n = struct.unpack('>I', data[pos + 12:pos + 16])[0]
        rate = struct.unpack('>I', data[pos + 16:pos + 20])[0]
        end = pos + 0x30 + n
        if end > len(data): res.append(('ERRO', idx, pos)); break
        nome = data[pos + 0x20:pos + 0x30].split(b'\0')[0].decode('latin1')
        res.append((idx, pos, end, ver, rate, nome)); idx += 1; pos = end
    return res

def main():
    if len(sys.argv) < 3:
        print(__doc__); return 2
    iso, saida = sys.argv[1].strip().strip('"'), sys.argv[2].strip().strip('"')
    print('1/3 Verifying the disc (may take a few seconds)...')
    ok, msgs = V.verificar(iso)
    print('\n'.join(msgs))
    if not ok:
        print('\nDISC REJECTED. Nothing was extracted.'); return 1
    print('\nDISC ACCEPTED.\n2/3 Extracting streams...')
    c = abrir(iso); files = listar(c); t0 = time.time(); problemas = []
    for arq, (pref, esperado) in BANCOS.items():
        if arq not in files: problemas.append('missing ' + arq); continue
        data = ler_arquivo(c, *files[arq])
        vs = cortar_vags(data)
        pasta = os.path.join(saida, pref); os.makedirs(pasta, exist_ok=True)
        linhas = []
        for r in vs:
            if r[0] == 'ERRO': problemas.append('%s: stream %d truncated' % (pref, r[1])); continue
            i, a, b, ver, rate, nome = r
            blob = data[a:b]
            open(os.path.join(pasta, '%s_%04d.vag' % (pref, i)), 'wb').write(blob)
            linhas.append((i, a, b - a, ver, rate, nome, hashlib.sha256(blob).hexdigest()))
        with open(os.path.join(saida, pref + '_manifest.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['index', 'offset', 'bytes', 'vag_version', 'rate_hz', 'name', 'sha256']); w.writerows(linhas)
        marca = 'OK' if len(linhas) == esperado else 'MISMATCH (expected %d)' % esperado
        v4 = sum(1 for l in linhas if l[3] == 4)
        print('  %-6s %4d streams  VAG v4: %4d  %s' % (pref, len(linhas), v4, marca))
        if len(linhas) != esperado: problemas.append('%s: %d streams (expected %d)' % (pref, len(linhas), esperado))
    print('3/3 Done in %.1f s. Folder: %s' % (time.time() - t0, saida))
    if problemas:
        print('\nPROBLEMS:'); print('\n'.join(' - ' + p for p in problemas)); return 1
    print('\nRESULT: all good.'); return 0

if __name__ == '__main__':
    sys.exit(main())
