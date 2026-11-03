"""Leitor/gravador de USM proprio (sem cricodecs). Mascara de video derivada empiricamente da chave do jogo."""
import struct, hashlib
MASK1 = bytes.fromhex('527ad3e88636d2ad4dcd2c8552659aa7a60b58f854232151d0290542956e1596')  # derivada da chave 0x71258D1CD37A52
MASK2 = bytes(v ^ 0xFF for v in MASK1)

def chunks(path):
    """Gera (sig, ptype, payload) de cada chunk do USM, na ordem do arquivo."""
    with open(path, 'rb') as f:
        while True:
            h = f.read(8)
            if len(h) < 8: return
            sig = h[:4]; size = struct.unpack('>I', h[4:])[0]; b = f.read(size)
            off = b[1]; pad = struct.unpack('>H', b[2:4])[0]
            yield sig, b[7] & 3, b[off:size - pad]

def video_decrypt(p):
    """Decifra um payload de video (mascara USM). Pacotes < 0x240 bytes nao sao mascarados."""
    if len(p) <= 0x240: return bytes(p)
    h, d = p[:0x40], bytearray(p[0x40:])
    m = bytearray(MASK2)
    for i in range(0x100, len(d)):
        d[i] ^= m[i & 31]; m[i & 31] = d[i] ^ MASK2[i & 31]
    m = bytearray(MASK1)
    for i in range(0x100):
        m[i & 31] ^= d[0x100 + i]; d[i] ^= m[i & 31]
    return bytes(h) + bytes(d)

def video_encrypt(p):
    if len(p) <= 0x240: return bytes(p)
    h, d = p[:0x40], bytearray(p[0x40:])
    m = bytearray(MASK1)
    for i in range(0x100):
        m[i & 31] ^= d[0x100 + i]; d[i] ^= m[i & 31]
    m = bytearray(MASK2)
    for i in range(0x100, len(d)):
        pt = d[i]; d[i] ^= m[i & 31]; m[i & 31] = pt ^ MASK2[i & 31]
    return bytes(h) + bytes(d)

if __name__ == '__main__':
    import sys
    sha = hashlib.sha256(); n = 0
    for sig, pt, pl in chunks(sys.argv[1]):
        if sig == b'@SFV' and pt == 0:
            dec = video_decrypt(pl); sha.update(dec); n += len(dec)
            assert video_encrypt(dec) == pl, 'cifrar(decifrar(x)) != x'
    print(n, sha.hexdigest())


# ---------------------------------------------------------------------------
# Cifra de video rapida (inteiros grandes, sem laco por byte) e montador de USM
# ---------------------------------------------------------------------------
def _rep(m, n):
    return (m * (n // 32 + 1))[:n]

def video_encrypt_fast(p):
    if len(p) <= 0x240: return bytes(p)
    head, d = bytes(p[:0x40]), p[0x40:]
    L = len(d)
    R2 = int.from_bytes(d[0x100:], 'little'); n2 = L - 0x100
    c2 = R2 ^ ((R2 << 256) & ((1 << (8 * n2)) - 1)) ^ int.from_bytes(_rep(MASK2, n2), 'little')
    out2 = c2.to_bytes(n2, 'little')
    acc = bytearray(MASK1); c1 = bytearray()
    for k in range(8):
        blk = d[0x100 + 32 * k: 0x100 + 32 * k + 32]
        acc = bytearray(a ^ b for a, b in zip(acc, blk))
        c1 += bytes(a ^ b for a, b in zip(d[32 * k:32 * k + 32], acc))
    return head + bytes(c1) + out2

def _crc16(b):
    t = []
    for i in range(256):
        c = i << 8
        for _ in range(8): c = ((c << 1) ^ 0x8005) if c & 0x8000 else c << 1
        t.append(c & 0xFFFF)
    c = 0
    for x in b: c = ((c << 8) & 0xFFFF) ^ t[(c >> 8) ^ x]
    return c
_CRCT = None
def crc16(b):
    global _CRCT
    if _CRCT is None:
        _CRCT = []
        for i in range(256):
            c = i << 8
            for _ in range(8): c = ((c << 1) ^ 0x8005) if c & 0x8000 else c << 1
            _CRCT.append(c & 0xFFFF)
    c = 0
    for x in b: c = ((c << 8) & 0xFFFF) ^ _CRCT[(c >> 8) ^ x]
    return c

def _hca_tables(key=0x71258D1CD37A52):
    def tbl(k):
        mul = ((k & 1) << 3) | 5; add = (k & 14) | 1; k >>= 4; r = []
        for i in range(16):
            k = (k * mul + add) & 0xF; r.append(k)
        return r
    kc0 = key - 1
    kc = [(kc0 >> (8 * i)) & 0xFF for i in range(7)]
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

def hca_to_usm_audio(hca):
    """HCA sem cifra (VGAudio) -> cabecalho mascarado + quadros cifrados (tipo 56) como no USM. Retorna (header96, [quadros])."""
    assert hca[:3] == b'HCA'
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
    h[hs - 2:hs] = struct.pack('>H', crc16(bytes(h[:hs - 2])))
    inv = _hca_tables(); trans = bytes(inv)
    frames = []
    for i in range(hs, len(hca) - fs + 1, fs):
        e = hca[i:i + fs - 2].translate(trans)
        frames.append(e + struct.pack('>H', crc16(e)))
    return bytes(h), frames


# ---------------------------------------------------------------------------
# Montador do USM (layout identico ao gerado pelo cricodecs e aceito pelo jogo)
# ---------------------------------------------------------------------------
def _a32(n): return (n + 31) // 32 * 32

def _chunk(sig, ptype, payload, ft=0, rate=30, pad_to=None, nopad=None):
    if nopad is not None:
        size = 24 + len(payload); pad = len(payload) - nopad
        return (sig + struct.pack('>I', size) + bytes([0, 24]) + struct.pack('>H', pad) + bytes([0, 0, 0, ptype]) + struct.pack('>II', ft, rate) + b'\0' * 8 + payload)
    if pad_to is None: pl = _a32(len(payload))
    else: pl = pad_to - 24
    pad = pl - len(payload)
    size = 24 + pl
    return (sig + struct.pack('>I', size) + bytes([0, 24]) + struct.pack('>H', pad) +
            bytes([0, 0, 0, ptype]) + struct.pack('>II', ft, rate) + b'\0' * 8 + payload + b'\0' * pad)

def _is_key(frame_payload):
    b0 = frame_payload[12]          # primeiro byte do quadro VP9 (depois do cabecalho de 12 bytes do IVF)
    return ((b0 >> 3) & 1) == 0 and ((b0 >> 2) & 1) == 0

def load_templates(path):
    """Le as 9 tabelas de cabecalho de um USM gerado com este layout (ver embutir_modelos)."""
    import utf
    out = []; f = open(path, 'rb')
    for _ in range(9):
        h = f.read(8); size = struct.unpack('>I', h[4:])[0]; b = f.read(size)
        off = b[1]; pad = struct.unpack('>H', b[2:4])[0]; out.append((h[:4], b[7] & 3, b[off:size - pad]))
    return out

def build_usm(ivf_path, hca_path, out_path, templates=None, name_usm='op.pmf.dat', progress=None):
    import utf
    if templates is None:
        import usm_templates; templates = usm_templates.templates()
    ivf = open(ivf_path, 'rb').read(); hca = open(hca_path, 'rb').read()
    frames = []; pos = 32
    while pos < len(ivf):
        sz = struct.unpack('<I', ivf[pos:pos + 4])[0]; frames.append(ivf[pos:pos + 12 + sz]); pos += 12 + sz
    nf = len(frames); frames[0] = ivf[:32] + frames[0]
    keys = [i for i in range(nf) if _is_key(frames[i] if i else frames[0][32:])]
    hdr96, afr = hca_to_usm_audio(hca)
    na = len(afr)
    T = {t[0] + bytes([t[1]]): t for t in templates}
    tpl = [parse_t(t[2]) for t in templates[:3]]
    # ---------------- tabelas ----------------
    crid, vh, ah = tpl
    maxfs = max(len(x) for x in frames)
    vmin = _a32(maxfs) + 32
    seek = utf.parse(templates[5][2]); base_row = seek.rows[0]
    seek.rows = [dict(base_row, ofs_byte=0, ofs_frmid=k) for k in keys]
    seek_payload_len = len(utf.build(seek)); seek_chunk = 24 + _a32(seek_payload_len)
    ahdr = utf.parse(templates[6][2]); ahdr.rows[0]['hca_header'] = ('D', hdr96, ahdr.rows[0]['hca_header'][2])
    ah_chunk = 24 + _a32(len(utf.build(ahdr)))
    vh.rows[0].update(total_frames=nf, metadata_size=seek_chunk + 8, ixsize=vmin)
    fc, ins, app = struct.unpack('>IHH', hca[16:24]); tsamp = na * 1024 - ins - app
    ah.rows[0].update(total_samples=tsamp, metadata_size=ah_chunk + 8)
    vh_b, ah_b = utf.build(vh), utf.build(ah)
    head_len = 2048 + (24 + _a32(len(vh_b)) + 8) + (24 + _a32(len(ah_b)) + 8) + 2 * (56 + 8) + (seek_chunk + 8) + (ah_chunk + 8) + 2 * (56 + 8)
    # ---------------- sequencia de dados ----------------
    FR = 2997
    seq = [('V', i * 100, i) for i in range(nf)] + [('A', 0, -1)] + [('A', round(n * 1024 * FR / 44100), n) for n in range(na)]
    seq.sort(key=lambda x: (x[1], 0 if x[0] == 'V' else 1))
    pos = head_len; offs = {}; total = head_len
    for kind, ft, idx in seq:
        ln = len(frames[idx]) if kind == 'V' else (96 if idx < 0 else 682)
        if kind == 'V' and idx in keys: offs[idx] = total
        total += 8 + 24 + _a32(ln)
    total += 2 * (56 + 8)
    seek.rows = [dict(base_row, ofs_byte=offs[k], ofs_frmid=k) for k in keys]
    seek_b = utf.build(seek); ahdr_b = utf.build(ahdr)
    vavg = round(len(ivf) * 8 / (nf * 1001 / 30000)); aavg = round(len(hca) * 8 / (tsamp / 44100))
    r0, r1, r2 = crid.rows
    r0.update(filesize=total, minbuf=vmin + 27864 - 0, avbps=vavg + aavg)
    r1.update(filesize=len(ivf), minbuf=vmin, avbps=vavg); r2.update(filesize=len(hca), avbps=aavg)
    crid_b = utf.build(crid)
    HE = b'#HEADER END     ==============\0\0'; ME = b'#METADATA END   ==============\0\0'; CE = b'#CONTENTS END   ==============\0\0'
    with open(out_path, 'wb') as o:
        o.write(_chunk(b'CRID', 1, crid_b, pad_to=2040))
        o.write(_chunk(b'@SFV', 1, vh_b)); o.write(_chunk(b'@SFA', 1, ah_b))
        o.write(_chunk(b'@SFV', 2, HE)); o.write(_chunk(b'@SFA', 2, HE))
        o.write(_chunk(b'@SFV', 3, seek_b)); o.write(_chunk(b'@SFA', 3, ahdr_b))
        o.write(_chunk(b'@SFV', 2, ME)); o.write(_chunk(b'@SFA', 2, ME))
        for i, (kind, ft, idx) in enumerate(seq):
            if kind == 'V': o.write(_chunk(b'@SFV', 0, video_encrypt_fast(frames[idx] + b'\0' * (_a32(len(frames[idx])) - len(frames[idx]))), ft, FR, nopad=len(frames[idx])))
            elif idx < 0: o.write(_chunk(b'@SFA', 0, hdr96, ft, FR))
            else: o.write(_chunk(b'@SFA', 0, afr[idx], ft, FR))
            if progress and i % 2000 == 0: progress(i, len(seq))
        o.write(_chunk(b'@SFV', 2, CE)); o.write(_chunk(b'@SFA', 2, CE))
    return total

def parse_t(b):
    import utf
    return utf.parse(b)


def video_decrypt_fast(p):
    """Inverso rapido de video_encrypt_fast (prefixo-XOR por faixa de 32 bytes com inteiros grandes)."""
    if len(p) <= 0x240: return bytes(p)
    head, d = bytes(p[:0x40]), p[0x40:]
    L = len(d); n2 = L - 0x100
    q = int.from_bytes(d[0x100:], 'little') ^ int.from_bytes(_rep(MASK2, n2), 'little')
    mask = (1 << (8 * n2)) - 1; sh = 256
    while sh < 8 * n2:
        q ^= (q << sh) & mask; sh <<= 1
    plain2 = q.to_bytes(n2, 'little')
    acc = bytearray(MASK1); p1 = bytearray()
    for k in range(8):
        blk = plain2[32 * k:32 * k + 32]
        acc = bytearray(a ^ b for a, b in zip(acc, blk))
        p1 += bytes(a ^ b for a, b in zip(d[32 * k:32 * k + 32], acc))
    return head + bytes(p1) + plain2

def extract_video(usm_path, out_ivf):
    """Extrai o video (IVF) de um USM do jogo, ja decifrado. Retorna o tamanho."""
    n = 0
    with open(out_ivf, 'wb') as o:
        for sig, pt, pl in chunks(usm_path):
            if sig == b'@SFV' and pt == 0:
                dec = video_decrypt_fast(pl); o.write(dec); n += len(dec)
    return n
