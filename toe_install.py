# -*- coding: utf-8 -*-
"""toe_install.py - step 4: installs/restores the test patch in the Steam game, with backup.
Usage: python toe_install.py install|restore|status [--game "game folder"] [--orig "folder with original Vo files (testing only)"]
Rules: only installs if Vo.acb, Vo.awb and the S00 bank are the ORIGINALS; never deletes an existing backup;
verifies hashes after copying.
"""
import sys, os, re, shutil, hashlib, subprocess, datetime
from toe_paths import RES, WORK
import toe_build as B
ORIG = B.ORIG
SUF = '.PRE_PATCH_TEST'
ARQS = ('Vo.acb', 'Vo.awb', 'toe_psp_se_bank_S00.acb')
GAME = 'Tales of Eternia Remastered'
REL = os.path.join(GAME + '_Data', 'StreamingAssets', 'Sound', 'en')

def sha_arq(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()

def achar_jogo():
    cands = []
    for r in (os.environ.get('ProgramFiles(x86)'), os.environ.get('ProgramFiles'), 'C:\\Program Files (x86)', 'C:\\Program Files'):
        if r: cands.append(os.path.join(r, 'Steam'))
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'), (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam')):
            try:
                with winreg.OpenKey(hive, key) as k:
                    for nome in ('SteamPath', 'InstallPath'):
                        try: cands.append(winreg.QueryValueEx(k, nome)[0])
                        except OSError: pass
            except OSError: pass
    except ImportError: pass
    libs = []
    for c in list(cands):
        v = os.path.join(c, 'steamapps', 'libraryfolders.vdf')
        if os.path.isfile(v):
            for m in re.findall(r'"path"\s+"([^"]+)"', open(v, encoding='utf-8', errors='ignore').read()):
                cands.append(m.replace('\\\\', '\\'))
    for c in cands:
        g = os.path.join(c, 'steamapps', 'common', GAME)
        if os.path.isdir(os.path.join(g, REL)): return g
    return None

def estado(snd):
    """Classifies the Vo.acb / Vo.awb / S00 set."""
    h = {x: sha_arq(os.path.join(snd, x)) for x in ARQS}
    if all(h[x] == ORIG[x] for x in ARQS): return 'ORIGINAL', h
    return 'MODIFIED/UNKNOWN', h

def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('install', 'restore', 'status'): print(__doc__); return 2
    cmd = args[0]; game = None; orig_dir = None
    if '--game' in args: game = args[args.index('--game') + 1].strip().strip('"')
    if '--orig' in args: orig_dir = args[args.index('--orig') + 1].strip().strip('"')
    if not game:
        game = achar_jogo()
        if not game:
            print('Could not find the game automatically.')
            game = input('Paste the game folder (the one that contains "%s_Data"): ' % GAME).strip().strip('"')
    snd = os.path.join(game, REL)
    falta = [x for x in ARQS if not os.path.isfile(os.path.join(snd, x))]
    if falta: print('ERROR: not found in %s: %s' % (snd, ', '.join(falta))); return 1
    print('Game: ' + game)
    est, hs = estado(snd)
    print('Current state of Vo.acb/Vo.awb/S00: ' + est)
    if cmd == 'status':
        for s in ARQS:
            print('  backup of %s: %s' % (s, 'exists' if os.path.isfile(os.path.join(snd, s + SUF)) else 'does not exist'))
        return 0
    if cmd == 'restore':
        ok = True
        for s in ARQS:
            bk = os.path.join(snd, s + SUF)
            if not os.path.isfile(bk):
                if sha_arq(os.path.join(snd, s)) == ORIG[s]: print(s + ': already original (no backup needed).'); continue
                print('No backup of ' + s + ' and the file is not the original. Use "Verify integrity of game files" in Steam.'); ok = False; continue
            if sha_arq(bk) != ORIG[s]: print('The backup of %s is not the original (not using it). Use "Verify integrity of game files" in Steam.' % s); ok = False; continue
            shutil.copy2(bk, os.path.join(snd, s + '.tmp')); os.replace(os.path.join(snd, s + '.tmp'), os.path.join(snd, s))
        est2 = estado(snd)[0]; print('After restoring: ' + est2)
        return 0 if ok and est2 == 'ORIGINAL' else 1
    # instalar
    if est != 'ORIGINAL':
        print('\nSTOPPED: your game\'s Vo.acb/Vo.awb/S00 are NOT the originals (modded or another version).')
        for x in ARQS: print('  %s: %s  (%s)' % (x, hs[x][:16], 'original' if hs[x] == ORIG[x] else 'DIFFERENT'))
        print('If this patch installed them, use option 2 (RESTORE) and run again. Otherwise restore the game with Steam (Properties > Installed Files > Verify integrity of game files).')
        print('If the game is unmodified and the error persists, send these lines to the author.'); return 1
    livre = shutil.disk_usage(snd).free
    if livre < 1 << 30: print('Not enough free disk space (~1 GB needed).'); return 1
    saida = os.path.join(WORK, 'output_patch')
    print('Building the banks (about 30 s)...')
    sys.argv = ['toe_build.py', orig_dir or snd, saida]
    if B.main() != 0: print('Build failed. The game was not changed.'); return 1
    for s in ARQS:
        bk = os.path.join(snd, s + SUF)
        if not os.path.isfile(bk): shutil.copy2(os.path.join(snd, s), bk)
        if sha_arq(bk) != ORIG[s]: print('Invalid backup of ' + s + '. Aborted without changing the game.'); return 1
    resultado = {}
    for s in ARQS:
        shutil.copy2(os.path.join(saida, s), os.path.join(snd, s + '.tmp')); os.replace(os.path.join(snd, s + '.tmp'), os.path.join(snd, s))
        resultado[s] = sha_arq(os.path.join(snd, s))
        if resultado[s] != sha_arq(os.path.join(saida, s)): print('Copy error in ' + s + '. Please restore.'); return 1
    rel = os.path.join(WORK, 'INSTALL_REPORT.txt')
    open(rel, 'w', encoding='utf-8').write('TOE test patch installed on %s\nGame: %s\n' % (
        datetime.datetime.now().isoformat(timespec='seconds'), game) + ''.join('%s original %s\n%s new %s\n' % (x, ORIG[x], x, resultado[x]) for x in ARQS))
    print('\nINSTALLED (Vo.acb, Vo.awb and S00). Backups ending in %s are in the game sound folder.' % SUF); print('Report: ' + rel)
    return 0

if __name__ == '__main__': sys.exit(main())
