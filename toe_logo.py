# -*- coding: utf-8 -*-
"""toe_logo.py - title-screen logo: RESTORED + "TEST" instead of the version text, compass ball at 75 percent.
Usage: python toe_logo.py generate|install|restore [--game "folder"]
Needs: pip install numpy UnityPy pillow (on your computer only; nothing is distributed).
Reads the ORIGINAL textures from your own game bundles; no game image is included in this package.
"""
import os, sys, glob, hashlib, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from toe_paths import RES, WORK
sys.path.insert(0, os.path.join(RES, 'lib'))
from seyfert import transform as bola
TEXTO = 'TEST'
IDS = ['0x0801004f', '0x08010050', '0x08010051', '0x08010052', '0x08010053', '0x08010054', '0x08010057']
ID_BOLA = '0x08010058'
ORIG = {'0x0801004f': 'eda769d6ba278fe54a6e90893b2f07f39035536643dfdc053981ce67f02670b3', '0x08010050': '132beafa709464b8baae69001f77fb1095f2b7bda2e5f44501ca21e94a6131ed', '0x08010051': '3afcc5967b20c83bbe42843eda7ab6ef6b2297ba6b77076844072fc817e7fbed', '0x08010052': 'd02a439dca3adde0680deaa50eec9abdf38f57f5629b02b0dad0da61744527db', '0x08010053': 'cfac4216d180098d3868ae04c38552cd1cfbdbb3f3308ab8c4768730cff6613f', '0x08010054': '3c8bfd9719e9a0bb4456a8981ed0d90b8f3737df16fe5440089639af628daa48', '0x08010057': 'dcb19384e146d3a7a8a9cb8e84ded345d0ce7dd89aab96a1b9fabd71d6f4aceb', '0x08010058': '91a4facf91da583b83a1b492e4d9eb3d991b01be50aa2e09724e2ce271bb53ac'}
AA = os.path.join('Tales of Eternia Remastered_Data', 'StreamingAssets', 'aa', 'StandaloneWindows64')
BK = os.path.join(WORK, 'backup_logo'); OUT = os.path.join(WORK, 'output_logo')

def sha_arq(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def prem_resize(img, size):
    a = np.array(img).astype(np.float32); al = a[..., 3:4] / 255; a[..., :3] *= al
    r = np.stack([np.array(Image.fromarray(a[..., i]).resize(size, Image.LANCZOS)) for i in range(4)], -1).astype(np.float32)
    al2 = np.clip(r[..., 3:4] / 255, 1e-4, 1); r[..., :3] = np.clip(r[..., :3] / al2, 0, 255)
    return Image.fromarray(r.astype(np.uint8), 'RGBA')

def compor(im, texto=TEXTO):
    """Builds the RESTORED logo from the letters of the REMASTERED word in your own original logo (2048x512)."""
    im = im.convert('RGBA')
    crop = lambda x0, x1, y0=399, y1=512: im.crop((x0, y0, x1, y1))
    RE = crop(1215, 1310); ST = crop(1431, 1529); RED = crop(1573, 1716); D = crop(1670, 1716)
    w = D.size[0]; half = w // 2; Dm = D.transpose(Image.FLIP_LEFT_RIGHT)
    O = Image.new('RGBA', (half * 2 - 2, D.size[1]), (0, 0, 0, 0))
    O.alpha_composite(Dm.crop((0, 0, half, D.size[1])), (0, 0)); O.alpha_composite(D.crop((half, 0, w, D.size[1])), (half - 2, 0))
    gap = -3; parts = [RE, ST, O, RED]
    W = sum(p.size[0] for p in parts) + gap * 3; H = RE.size[1]
    RS = Image.new('RGBA', (W, H), (0, 0, 0, 0)); x = 0
    for p in parts: RS.alpha_composite(p, (x, 0)); x += p.size[0] + gap
    s = 0.76; bb = im.getbbox(); core = im.crop(bb)
    sc = prem_resize(core, (int(core.size[0] * s), int(core.size[1] * s))); rs = prem_resize(RS, (int(W * s), int(H * s)))
    canvas = Image.new('RGBA', (2048, 512), (0, 0, 0, 0)); cx = 1037; x0 = cx - sc.size[0] // 2; y0 = 6
    canvas.alpha_composite(sc, (x0, y0))
    rem_bottom = y0 + int((475 - bb[1]) * s); rem_cx = int((1215 + 1716) / 2 - bb[0]) * s + x0
    rx = int(rem_cx - rs.size[0] / 2); ry = rem_bottom - 1
    canvas.alpha_composite(rs, (rx, ry))
    font = ImageFont.truetype(os.path.join(RES, 'fonts', 'DejaVuSans-Bold.ttf'), 26)
    tw = int(font.getlength(texto)) + 16; th = 48
    L = Image.new('RGBA', (tw + 20, th + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.text((10, 10), texto, font=font, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(20, 12, 8, 255))
    mask = Image.new('L', L.size, 0); ImageDraw.Draw(mask).text((10, 10), texto, font=font, fill=255)
    g = Image.new('RGBA', L.size, (0, 0, 0, 0)); gp = g.load()
    for yy in range(L.size[1]):
        t = min(1, max(0, (yy - 10) / th)); col = (245, int(150 + 90 * t), int(70 + 150 * t), 255)
        for xx in range(L.size[0]): gp[xx, yy] = col
    L2 = L.copy(); L2.paste(Image.composite(g, L, mask), (0, 0), mask)
    glow = Image.new('RGBA', L.size, (40, 200, 110, 0)); glow.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(4)))
    V = Image.new('RGBA', L.size, (0, 0, 0, 0)); V.alpha_composite(glow); V.alpha_composite(L2)
    vx = int(rx + rs.size[0] / 2 - V.size[0] / 2); vy = ry + rs.size[1] - 18
    canvas.alpha_composite(V, (vx, vy))
    return canvas

def achar_pacote(aa, i):
    fs = glob.glob(os.path.join(aa, 'group_residenttexture_texture_assets_%s_*.bundle' % i))
    return fs[0] if len(fs) == 1 else None

def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('generate', 'install', 'restore', 'preview'): print(__doc__); return 2
    cmd = args[0]
    if cmd == 'preview':   # only to check the artwork: needs the original logo PNG (2048x512)
        compor(Image.open(args[1])).save(args[2]); print('preview written'); return 0
    import toe_install as I
    game = args[args.index('--game') + 1].strip().strip('"') if '--game' in args else I.achar_jogo()
    if not game: game = input('Paste the game folder: ').strip().strip('"')
    aa = os.path.join(game, AA)
    if not os.path.isdir(aa): print('ERROR: not found: ' + aa); return 1
    print('Game: ' + game)
    if cmd == 'restore':
        n = 0
        for i in IDS + [ID_BOLA]:
            fs = glob.glob(os.path.join(BK, 'group_residenttexture_texture_assets_%s_*.bundle' % i))
            if len(fs) == 1 and sha_arq(fs[0]) == ORIG[i]:
                shutil.copy2(fs[0], os.path.join(aa, os.path.basename(fs[0]))); n += 1
        print('Bundles restored from backup: %d of 8.' % n); return 0 if n else 1
    fontes = {}
    for i in IDS + [ID_BOLA]:
        p = achar_pacote(aa, i)
        if not p: print('ERROR: bundle %s not found (different game version?).' % i); return 1
        if sha_arq(p) != ORIG[i]:
            print('STOPPED: bundle %s is not the original (logo already changed or another game version).' % i)
            print('If this patch did it, use "restore". Otherwise verify the game files in Steam and try again.'); return 1
        fontes[i] = p
    import UnityPy
    from UnityPy.enums import TextureFormat
    os.makedirs(OUT, exist_ok=True)
    def textura(env, nome):
        for o in env.objects:
            if o.type.name == 'Texture2D':
                d = o.read()
                if d.m_Name == nome: return d
    envs = {i: UnityPy.load(fontes[i]) for i in IDS}
    NEW = compor(textura(envs[IDS[0]], 'ToE_logo').image)
    ok = 0
    for i in IDS:
        d = textura(envs[i], 'ToE_logo'); assert (d.m_Width, d.m_Height) == NEW.size
        d.set_image(NEW, target_format=TextureFormat.RGBA32, mipmap_count=1); d.save()
        dados = envs[i].file.save(packer='lz4'); p = os.path.join(OUT, os.path.basename(fontes[i])); open(p, 'wb').write(dados)
        for o in UnityPy.load(p).objects:
            if o.type.name == 'Texture2D': ok += int(np.abs(np.array(o.read().image.convert('RGBA')).astype(int) - np.array(NEW).astype(int)).max() <= 2)
    e = UnityPy.load(fontes[ID_BOLA]); d = textura(e, 'ToE_logo_seyfert'); nova = bola(d.image, 0.75, -50)
    d.set_image(nova, target_format=TextureFormat.RGBA32, mipmap_count=1); d.save()
    dados = e.file.save(packer='lz4'); p = os.path.join(OUT, os.path.basename(fontes[ID_BOLA])); open(p, 'wb').write(dados)
    for o in UnityPy.load(p).objects:
        if o.type.name == 'Texture2D': ok += int(np.abs(np.array(o.read().image.convert('RGBA')).astype(int) - np.array(nova).astype(int)).max() <= 2)
    print('Bundles generated and verified: %d of 8.' % ok)
    if ok != 8: print('Verification FAILED. Nothing was installed.'); return 1
    if cmd == 'generate': print('Generated in ' + OUT + ' (game not changed).'); return 0
    os.makedirs(BK, exist_ok=True)
    for i in IDS + [ID_BOLA]:
        b = os.path.join(BK, os.path.basename(fontes[i]))
        if not os.path.exists(b): shutil.copy2(fontes[i], b)
        if sha_arq(b) != ORIG[i]: print('Invalid backup; aborted.'); return 1
    for i in IDS + [ID_BOLA]:
        shutil.copy2(os.path.join(OUT, os.path.basename(fontes[i])), fontes[i])
    print('LOGO INSTALLED (8 bundles). Backups in ' + BK + '. Restart the game to see it.'); return 0

if __name__ == '__main__': sys.exit(main())
