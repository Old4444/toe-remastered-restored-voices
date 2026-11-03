"""Decodificador PSX ADPCM (VAG) bit-exato com os WAV_Convertidos de referencia.
Validado: 1347/1347 streams de s_us.v identicos (amostra a amostra).
Regras: filtros padrao PSX, (s1*f0+s2*f1)>>6 (floor, sem arredondamento), clamp 16 bits,
bloco com flag 7 (fim) vira 28 zeros. Entrada = dados ADPCM (sem cabecalho de 0x30 bytes)."""
F = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]

def decode_adpcm(d):
    s1 = s2 = 0
    o = []
    for i in range(0, len(d) - 15, 16):
        if d[i + 1] == 7:
            o += [0] * 28
            continue
        sh = d[i] & 15
        f0, f1 = F[min(d[i] >> 4, 4)]
        for b in d[i + 2:i + 16]:
            for n in (b & 15, b >> 4):
                v = (n - 16 if n > 7 else n) << 12
                s = (v >> sh) + ((s1 * f0 + s2 * f1) >> 6)
                s = max(-32768, min(32767, s))
                o.append(s)
                s2 = s1
                s1 = s
    return o
