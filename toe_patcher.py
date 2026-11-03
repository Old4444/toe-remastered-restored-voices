# -*- coding: utf-8 -*-
"""toe_patcher.py - single entry point of the Tales of Eternia Remastered "Restored English Voices" patcher.
Run it with Python (python toe_patcher.py) or as the compiled ToePatcher.exe. It only uses YOUR files:
your Steam game and your own PSP disc image. Nothing is uploaded; nothing is distributed.
Command line (optional):  toe_patcher.py install [--no-mute] [--opening] [--no-movies] [--disc FILE] [--ffmpeg FILE] [--game FOLDER] | restore | status | prepare "game.iso" | install-voices | logo-install | logo-restore | clean
"""
import os, sys, shutil, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
from toe_paths import RES, WORK
sys.path.insert(0, RES)

VGAUDIO_SHA = '0f3bda1bf2dc2421756a16c05769430e4881876deb4eab40ca47b31009173e2b'
import toe_voices090 as V090
TEMP_DIRS = ('output_movies', 'work_opening', 'psp_streams', 'wav_battle', 'wav_events', 'wav_h', 'wav_s00', 'hca_battle', 'hca_events', 'hca_h', 'hca_s00', 'output_patch', 'output_logo')

def call(fn, *args):
    """Runs a module's main() with the given command-line arguments."""
    old = sys.argv; sys.argv = ['toe'] + list(args)
    try: r = fn()
    except SystemExit as e: r = e.code
    finally: sys.argv = old
    return 0 if r in (None, 0, False) else (r if isinstance(r, int) else 1)

DISC = None
FFMPEG = None

def pick_disc():
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk(); root.withdraw(); root.attributes('-topmost', True)
        p = filedialog.askopenfilename(title='Select your PSP disc image (Tales of Eternia, European release)',
                                       filetypes=[('PSP disc image', '*.iso *.cso'), ('All files', '*.*')])
        root.destroy()
        if p: return p
    except Exception:
        pass
    return input('Type or drag your PSP .iso/.cso file here and press Enter: ').strip().strip('"')

def get_disc(d=None):
    global DISC
    if d: DISC = d.strip().strip('"')
    if not DISC: DISC = pick_disc().strip().strip('"')
    return DISC

def vgaudio():
    p = os.environ.get('TOE_VGAUDIO') or os.path.join(RES, 'tools', 'VGAudioCli.exe')
    if not os.path.isfile(p): print('ERROR: tools\\VGAudioCli.exe not found.'); return None
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    print('VGAudioCli SHA-256: ' + h)
    if h != VGAUDIO_SHA and not os.environ.get('TOE_VGAUDIO'): print('WARNING: hash differs from the official v2.2.1 release.')
    return p

def encode_all():
    v = vgaudio()
    if not v: return False
    bad = V090.encode(v)
    if bad: print('ERROR: %d files failed to encode (VGAudioCli needs .NET Framework 4.5.1+ on Windows).' % bad); return False
    return True

def counts():
    return V090.counts()

def prepared():
    return all(c == n for _, c, n in counts())

def prepare(disc=None):
    import toe_psp, toe_audio
    if prepared():
        a = input('A previous preparation was found. Reuse it? [Y/n] ').strip().lower()
        if a in ('', 'y', 'yes'): return True
    disc = get_disc(disc)
    if not disc or not os.path.isfile(disc): print('ERROR: file not found: ' + disc); return False
    print('\nSTEP 1/3 - extracting the voices from your disc image')
    if call(toe_psp.main, disc, os.path.join(WORK, 'psp_streams')): print('Stopped.'); return False
    print('\nSTEP 2/3 - decoding and applying the recipes')
    av = V090.prepare_wavs()
    if av: print('  note: %d decoded files differ from the reference fingerprints (different disc dump?). Continuing.' % av)
    print('\nSTEP 3/3 - encoding')
    if not encode_all(): return False
    for h, c, n in counts(): print('  %-11s %4d files (expected %d)%s' % (h, c, n, '' if c == n else '  <-- MISMATCH'))
    return prepared()


def build_only(iso, orig_dir, out):
    """Test helper: prepare + build the banks into OUT without touching the game."""
    import toe_build
    if not prepare(iso): return 1
    return call(toe_build.main, orig_dir, out)

def install(*extra):
    import toe_install
    if not prepare(): return 1
    return call(toe_install.main, 'install', *extra)

def simple(modname, *args):
    mod = __import__(modname)
    return call(mod.main, *args)

def stub_audio_libs():
    """UnityPy imports an audio library (fmod) and an ASTC texture encoder only for formats this tool never uses (the logo is RGBA32).
    In the packed .exe its DLL may be missing, so if it cannot be imported we replace it with an inert stub."""
    import types
    class Stub(types.ModuleType):
        def __getattr__(self, n):
            if n.startswith('__'): raise AttributeError(n)
            def f(*a, **k): raise RuntimeError('audio support is not available in this build')
            return f
    for n in ('fmod_toolkit', 'pyfmodex', 'astc_encoder'):
        try: __import__(n)
        except Exception:
            for k in [k for k in sys.modules if k == n or k.startswith(n + '.')]: del sys.modules[k]
            sys.modules[n] = Stub(n)

def logo(cmd, *extra):
    stub_audio_libs()
    try: import toe_logo
    except ImportError as e:
        print('The logo option is not available in this build (%s).\nUse the Python version: pip install numpy UnityPy pillow' % e); return 1
    return call(toe_logo.main, cmd, *extra)

def clean():
    print('This deletes ONLY the temporary folders created by this tool next to it (extracted PSP audio, WAV/HCA files, build output):')
    found = [d for d in TEMP_DIRS if os.path.isdir(os.path.join(WORK, d))]
    for d in found: print('  ' + os.path.join(WORK, d))
    if not found: print('  (nothing to delete)'); return 0
    print('Your game files, the backups (*.PRE_PATCH_TEST, backup_logo) and your disc image are NOT touched.')
    if input('Delete them? [y/N] ').strip().lower() not in ('y', 'yes'): return 0
    for d in found: shutil.rmtree(os.path.join(WORK, d), ignore_errors=True)
    print('Done.'); return 0

def logo_safe(cmd, *extra):
    try: return logo(cmd, *extra)
    except Exception as e: print('Logo step failed: %s' % e); return 1

def parse_opts(args):
    o = {'mute': True, 'opening': False, 'movies': True, 'disc': None, 'ffmpeg': None}; rest = []; it = iter(args)
    for x in it:
        if x == '--no-mute': o['mute'] = False
        elif x == '--opening': o['opening'] = True
        elif x == '--no-movies': o['movies'] = False
        elif x == '--disc': o['disc'] = next(it)
        elif x == '--ffmpeg': o['ffmpeg'] = next(it)
        else: rest.append(x)
    return o, rest

def pick_game():
    """Asks for the game folder (window; falls back to typing) until it contains the game's sound folder."""
    import toe_install
    ok = lambda g: bool(g) and os.path.isdir(os.path.join(g, toe_install.REL))
    while True:
        print('\nCould not find the game automatically. Select the game folder (the one named "%s" that contains "%s_Data").' % (toe_install.GAME, toe_install.GAME))
        g = ''
        try:
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk(); root.withdraw(); root.attributes('-topmost', True)
            g = filedialog.askdirectory(title='Select the Tales of Eternia Remastered game folder'); root.destroy()
        except Exception:
            g = input('Paste the game folder path: ').strip().strip('"')
        g = os.path.normpath(g) if g else ''
        if ok(g): return g
        if not g: g = input('Paste the game folder path (empty = cancel): ').strip().strip('"')
        if not g: raise SystemExit('Cancelled: game folder not selected.')
        if ok(g): return g
        print('That folder does not contain %s. Try again.' % toe_install.REL)

def resolve_game(rest):
    import toe_install
    if '--game' in rest: return rest[rest.index('--game') + 1].strip().strip('"'), rest
    g = toe_install.achar_jogo() or pick_game()
    return g, rest + ['--game', g]

def install_all(*args):
    import toe_install, toe_extras
    o, rest = parse_opts(list(args)); game, rest = resolve_game(rest)
    v = vgaudio()
    if not v: return 1
    if o['disc']: get_disc(o['disc'])
    ff = None
    if o['movies'] or o['opening']:
        ff = o['ffmpeg'] or toe_extras.find_ffmpeg()
        if not ff:
            print('\nffmpeg was not provided, so NOTHING was installed. Place the ffmpeg folder next to this program and run again, or choose "INSTALL without videos" in the menu.'); return 1
    toe_install.MUTE = o['mute']; toe_install.VGAUDIO = v
    print('\nOptions: mute remaster-only skits = %s | cutscene movie audio = %s | restored opening = %s | title-logo change = always' % tuple('ON' if x else 'off' for x in (o['mute'], o['movies'], o['opening'])))
    print('\n--- Voices ---')
    rv = install(*rest)
    if rv: print('\nThe voices were NOT installed, so the other steps were skipped.'); return rv
    print('\n--- Title logo ---')
    rl = logo_safe('install', *rest)
    rm = ro = None
    if ff and o['movies']:
        print('\n--- Cutscene movie audio (01, 15, 24) ---')
        try: rm = toe_extras.install_movies(game, get_disc(), ff, v)
        except Exception as e: print('Movie step failed: %s' % e); rm = 1
    if ff and o['opening']:
        print('\n--- Restored opening (takes several minutes) ---')
        try: ro = toe_extras.install_opening(game, get_disc(), ff, v)
        except Exception as e: print('Opening step failed: %s' % e); ro = 1
    st = lambda r, name: '%s %s' % (name, 'skipped' if r is None else ('OK' if r == 0 else 'FAILED (see above)'))
    print('\nSUMMARY:  voices OK | %s | %s | %s | %s' % ('skits muted' if o['mute'] else 'skits kept', st(rl, 'logo'), st(rm, 'movies'), st(ro, 'opening')))
    return 0

def restore_all(*args):
    import toe_install, toe_extras
    o, rest = parse_opts(list(args)); game, rest = resolve_game(rest)
    rv = call(toe_install.main, 'restore', *rest)
    print('\n--- Title logo ---')
    if os.path.isdir(os.path.join(WORK, 'backup_logo')): rl = logo_safe('restore', *rest)
    else: print('No logo backup found next to this program; the logo was left as it is.'); rl = 0
    print('\n--- Cutscene movies and opening ---')
    rm = toe_extras.restore_movies(game); ro = toe_extras.restore_opening(game)
    print('\nSUMMARY:  voices %s | logo %s | movies %s | opening %s' % tuple('RESTORED' if r == 0 else 'NOT restored (see above)' for r in (rv, rl, rm, ro)))
    return rv or rl or rm or ro

def status(*extra):
    import toe_install, toe_extras
    rv = call(toe_install.main, 'status', *extra)
    print('  title logo backup: ' + ('exists (logo was installed by this tool)' if os.path.isdir(os.path.join(WORK, 'backup_logo')) else 'none'))
    try:
        md = toe_extras.movie_dir(resolve_game(list(extra))[0]); fl = os.listdir(md)
        print('  movie backups: ' + (', '.join(sorted(f[:-8] for f in fl if f.endswith(toe_extras.SUF_VID))) or 'none') + ' | opening backup: ' + ('exists' if 'op.pmf.dat' + toe_extras.SUF_OP in fl else 'none'))
    except Exception: pass
    return rv

MENU = '''
 TALES OF ETERNIA REMASTERED - RESTORED ENGLISH VOICES
 -----------------------------------------------------
  1  INSTALL - complete: voices + title logo + cutscene movies + original opening
            (needs ffmpeg and takes several minutes)
  2  INSTALL - without videos: voices + title logo only (no ffmpeg needed)
  3  RESTORE everything to the originals
  4  Status
  5  Delete temporary files (extracted PSP audio, WAV/HCA)
  0  Exit
'''

def ask_yn(q, default):
    r = input('%s [%s] ' % (q, 'Y/n' if default else 'y/N')).strip().lower()
    return default if not r else r in ('y', 'yes', 's', 'sim')

def main():
    a = sys.argv[1:]
    if a:
        c, rest = a[0], a[1:]
        if c == 'prepare': return 0 if prepare(rest[0] if rest else None) else 1
        if c == 'build': return build_only(*rest)
        if c == 'install': return install_all(*rest)
        if c == 'install-voices': return install(*rest)
        if c == 'restore': return restore_all(*rest)
        if c == 'status': return status(*rest)
        if c == 'logo-install': return logo('install', *rest)
        if c == 'logo-restore': return logo('restore', *rest)
        if c == 'clean': return clean()
        print(__doc__); return 2
    while True:
        print(MENU)
        k = input('Choose: ').strip()
        if k in ('1', '2'):
            extra = []
            if not ask_yn('Mute the new skits that only exist in the remaster (they have no English PSP voice)?', True): extra.append('--no-mute')
            extra += ['--opening'] if k == '1' else ['--no-movies']
            install_all(*extra)
        elif k == '3': restore_all()
        elif k == '4': status()
        elif k == '5': clean()
        elif k == '0': return 0
        input('\nPress Enter to continue...')

if __name__ == '__main__':
    try: rc = main()
    except KeyboardInterrupt: rc = 130
    except Exception as e:
        import traceback; traceback.print_exc(); print('\nUnexpected error: %s\nPlease send the text above to the author.' % e); rc = 1
    if getattr(sys, 'frozen', False) and len(sys.argv) == 1: input('\nPress Enter to close...')
    sys.exit(rc)
