# Third-party notices

## In this repository
- **VGAudio / VGAudioCli v2.2.1** - MIT License, Copyright (c) 2016 (the upstream LICENSE leaves the holder name blank; text included verbatim). https://github.com/Thealexbarney/VGAudio . Included unmodified as `tools/VGAudioCli.exe` (SHA-256 0f3bda1bf2dc2421756a16c05769430e4881876deb4eab40ca47b31009173e2b). See `tools/LICENSE_VGAudio.txt`.
- **DejaVu Sans Bold** - Bitstream Vera / DejaVu license, `fonts/LICENSE_DejaVu.txt`.

## Inside `ToePatcher.exe` (Releases)
The .exe is built with PyInstaller and bundles the Python runtime (PSF License), the code of this repository, `VGAudioCli.exe` and the libraries used by the
title-logo option. Licenses as reported by the build environment (the full texts are in **`THIRD_PARTY_LICENSES.txt`**, attached to each Release):

| Package | License (as reported) |
|---|---|
| UnityPy 1.25.4, astc-encoder-py, etcpak, texture2ddecoder, tpk_ar, charset-normalizer, urllib3, brotli, attrs | MIT |
| numpy 2.5.4 | BSD-3-Clause and others (OpenBLAS, LAPACK, GCC runtime library – see the file) |
| Pillow 13.0.0 | MIT-CMU |
| fsspec, idna, lz4 | BSD |
| packaging | Apache-2.0 OR BSD-2-Clause |
| requests | Apache-2.0 |
| archspec | metadata says "Other"; the license text shipped with it is Apache-2.0 |
| certifi | MPL-2.0 (unmodified; source: https://github.com/certifi/python-certifi) |
| PyInstaller 6.22.3, pyinstaller-hooks-contrib | GPLv2 with the PyInstaller exception that allows bundling (and Apache-2.0 for the hooks) |

The list above is a superset of what the .exe really embeds (it was generated from the build environment).
This table is a convenience summary; `THIRD_PARTY_LICENSES.txt` is the authoritative text.

## Trademarks
*Tales of Eternia* and related material belong to their owners. This project is unofficial.
