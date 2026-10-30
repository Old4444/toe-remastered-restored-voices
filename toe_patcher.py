# -*- coding: utf-8 -*-
"""toe_patcher.py - single entry point of the Tales of Eternia Remastered "Restored English Voices" TEST patcher.
Run it with Python (python toe_patcher.py) or as the compiled ToePatcher.exe. It only uses YOUR files:
your Steam game and your own PSP disc image. Nothing is uploaded; nothing is distributed.
Command line (optional):  toe_patcher.py prepare "game.iso" | install | install-voices | restore | status | logo-install | logo-restore | clean
"""
import os, sys, shutil, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
from toe_paths import RES, WORK
sys.path.insert(0, RES)

VGAUDIO_SHA = '0f3bda1bf2dc2421756a16c05769430e4881876deb4eab40ca47b31009173e2b'
EXPECTED = (('wav_battle', 'hca_battle', 900), ('wav_events', 'hca_events', 136), ('wav_s00', 'hca_s00', 32))
TEMP_DIRS = ('psp_streams', 'wav_battle', 'wav_events', 'wav_s00', 'hca_battle', 'hca_events', 'hca_s00', 'output_patch', 'output_logo')

def call(fn, *args):
    """Runs a module's main() with the given command-line arguments."""
    old = sys.argv; sys.argv = ['toe'] + list(args)
    try: r = fn()
    except SystemExit as e: r = e.code
    finally: sys.argv = old
    return 0 if r in (None, 0, False) else (r if isinstance(r, int) else 1)

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
    jobs = []
    for w, h, _ in EXPECTED:
        os.makedirs(os.path.join(WORK, h), exist_ok=True)
        for f in sorted(os.listdir(os.path.join(WORK, w))):
            if f.lower().endswith('.wav'): jobs.append((os.path.join(WORK, w, f), os.path.join(WORK, h, f[:-4] + '.hca')))
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    def one(j):
        r = subprocess.run([v, '-i', j[0], '-o', j[1], '--hcaquality', 'Highest'], capture_output=True, creationflags=flags)
        return r.returncode == 0 and os.path.isfile(j[1])
    print('Encoding %d files to HCA (a few minutes)...' % len(jobs))
    with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as ex: res = list(ex.map(one, jobs))
    bad = len(res) - sum(res)
    if bad: print('ERROR: %d files failed to encode (VGAudioCli needs .NET Framework 4.5.1+ on Windows).' % bad); return False
    return True

def counts():
    return [(h, len([f for f in os.listdir(os.path.join(WORK, h)) if f.endswith('.hca')]) if os.path.isdir(os.path.join(WORK, h)) else 0, n) for _, h, n in EXPECTED]

def prepared():
    return all(c == n for _, c, n in counts())

def prepare(disc=None):
    import toe_psp, toe_audio
    if prepared():
        a = input('A previous preparation was found. Reuse it? [Y/n] ').strip().lower()
        if a in ('', 'y', 'yes'): return True
    disc = (disc or pick_disc()).strip().strip('"')
    if not disc or not os.path.isfile(disc): print('ERROR: file not found: ' + disc); return False
    print('\nSTEP 1/3 - extracting the voices from your disc image')
    if call(toe_psp.main, disc, os.path.join(WORK, 'psp_streams')): print('Stopped.'); return False
    print('\nSTEP 2/3 - decoding and applying the recipes')
    if call(toe_audio.main): print('Stopped.'); return False
    print('\nSTEP 3/3 - encoding')
    if not encode_all(): return False
    for h, c, n in counts(): print('  %-11s %4d files (expected %d)%s' % (h, c, n, '' if c == n else '  <-- MISMATCH'))
    return prepared()


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

def install_all(*extra):
    rv = install(*extra)
    if rv: print('\nThe voices were NOT installed, so the logo step was skipped.'); return rv
    print('\n--- Title logo ---')
    rl = logo_safe('install', *extra)
    print('\nSUMMARY:  voices INSTALLED  |  logo %s' % ('INSTALLED' if rl == 0 else 'NOT installed (see the message above; the voices are fine)'))
    return 0

def restore_all(*extra):
    import toe_install
    rv = call(toe_install.main, 'restore', *extra)
    print('\n--- Title logo ---')
    if os.path.isdir(os.path.join(WORK, 'backup_logo')): rl = logo_safe('restore', *extra)
    else: print('No logo backup found next to this program; the logo was left as it is.'); rl = 0
    print('\nSUMMARY:  voices %s  |  logo %s' % ('RESTORED' if rv == 0 else 'NOT restored (see above)', 'RESTORED / untouched' if rl == 0 else 'NOT restored (see above)'))
    return rv or rl

def status(*extra):
    import toe_install
    rv = call(toe_install.main, 'status', *extra)
    print('  title logo backup: ' + ('exists (logo was installed by this tool)' if os.path.isdir(os.path.join(WORK, 'backup_logo')) else 'none'))
    return rv

MENU = '''
 TALES OF ETERNIA REMASTERED - RESTORED VOICES (TEST)
 ---------------------------------------------------
  1  INSTALL everything: voices + title logo "TEST"   (recommended; backups first)
  2  RESTORE everything (voices + logo) to the originals
  3  Status
  4  Install the voices only
  5  Install the title logo only
  6  Delete temporary files (extracted PSP audio, WAV/HCA)
  0  Exit
'''

def main():
    a = sys.argv[1:]
    if a:
        c, rest = a[0], a[1:]
        if c == 'prepare': return 0 if prepare(rest[0] if rest else None) else 1
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
        if k == '1': install_all()
        elif k == '2': restore_all()
        elif k == '3': status()
        elif k == '4': install()
        elif k == '5': logo_safe('install')
        elif k == '6': clean()
        elif k == '0': return 0
        input('\nPress Enter to continue...')

if __name__ == '__main__':
    try: rc = main()
    except KeyboardInterrupt: rc = 130
    except Exception as e:
        import traceback; traceback.print_exc(); print('\nUnexpected error: %s\nPlease send the text above to the author.' % e); rc = 1
    if getattr(sys, 'frozen', False) and len(sys.argv) == 1: input('\nPress Enter to close...')
    sys.exit(rc)
