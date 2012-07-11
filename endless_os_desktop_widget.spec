# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support/_mountzlib.py'), os.path.join(HOMEPATH,'support/useUnicode.py'), '/home/dev1/checkout/eos-desktop/src/endless_os_desktop.py'],
             pathex=['/home/dev1/apps/pyinstaller-1.5.1'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'endless_os_desktop'),
          debug=False,
          strip=False,
          upx=True,
          console=1 )
