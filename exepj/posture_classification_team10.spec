# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\logo_page.ico", '.'),
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\logo_page.png", '.'),
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\su_final.png", '.'),
]
a = Analysis(
    ['posture_classification_team10.py'],
    pathex=[
        'C:\\Users\\user\\anaconda3\\envs\\ss\\Lib\\site-packages',
        'C:\\Users\\user\\aivle\\bp\\winexe\\exepj',
        'C:\\Users\\user\\aivle\\bp\\winexe\\dll',
        'C:\\Users\\user\\anaconda3\\envs\\ss\\Lib\\site-packages\\xgboost',
    ],
    binaries=[
        ("C:\\Users\\user\\anaconda3\\envs\\ss\\Lib\\site-packages\\cv2\\opencv_videoio_ffmpeg490_64.dll", '.\\cv2'),
        ('C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\xgboost\\xgboost.dll','.\\xgboost'), 
        ('C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\xgboost\\VERSION', '.\\xgboost')
    ],
    datas=[
        ("./pose_classification_model.pkl", '.'),
    ],
    hiddenimports=[
        "cv2.config",
        "cv2.config-3",
        "cv2.cv2",
        "cv2.data",
        "cv2.gapi",
        "cv2.load_config_py3",
        "cv2.mat_wrapper",
        "cv2.misc",
        "cv2.misc.version",
        "cv2.typing",
        "cv2.utils",
        "cv2.version",
        "cv2.cv2",
        "pandas",
        "numpy",
        'scipy.special._ufuncs_cxx',
        'scipy.linalg.cython_blas',
        'scipy.linalg.cython_lapack',
        'scipy.integrate',
        'scipy.integrate.quadrature',
        'scipy.integrate.odepack',
        'scipy.integrate._odepack',
        'scipy.integrate.quadpack',
        'scipy.integrate._quadpack',
        'scipy.integrate._ode',
        'scipy.integrate.vode',
        'scipy.integrate._dop',
        'scipy.integrate.lsoda',
        'joblib',
        'sklearn',
        'scipy',
        'xgboost',
        "sklearn.neighbors._typedefs",
        "sklearn.neighbors.quad_tree",
        "sklearn.tree._utils",
        "sklearn.utils._typedefs",
        "sklearn.neighbors._partition_nodes"
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='posture_classification_team10',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon='./logo_page.ico',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='posture_classification',
)
