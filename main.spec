import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(['main.py'],
             pathex=['.'],
             binaries=None,
             datas=[('exercises', 'exercises')],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='app',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='assets\\icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='ActiveBreaks')

app = BUNDLE(coll,
             name='ActiveBreaks.app',
             icon='assets/icon.icns',
             bundle_identifier='com.github.namuan.activebreaks',
             info_plist={
                'CFBundleName': 'ActiveBreaks',
                'CFBundleVersion': '1.0.0',
                'CFBundleShortVersionString': '1.0.0',
                'NSPrincipalClass': 'NSApplication',
                'NSHighResolutionCapable': 'True'
                }
             )
