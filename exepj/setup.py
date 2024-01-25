from cx_Freeze import setup, Executable

buildOptions = {
	"packages":[
    	"matplotlib","scipy","numpy","os", "cv2", "sys", "threading", "PyQt5",
     "sqlite3", "mediapipe", "joblib", "pandas", "preprocessing", "win10toast", "time",
     "xgboost", 'sklearn', 'openpyxl', 'xlsxwriter'
    ],
    "excludes":[
        # "bs4", "google_auth_oauthlib", "oauthlib", "requests"
    ],
    'include_files':[
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\logo_page.ico", './imgs/logo_page.ico'),
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\logo_page.png", './imgs/logo_page.png'),
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\su_final.png", './imgs/su_final.png'),
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\pose_classification_model.pkl", 'pose_classification_model.pkl'),
    ("C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\preprocessing.py", 'preprocessing.py'),
    ("C:\\Users\\user\\anaconda3\\envs\\ss\\Lib\\site-packages\\sklearn\\.libs\\msvcp140.dll", 'msvcp140.dll'),
    ("C:\\Users\\user\\anaconda3\\envs\\ss\\Lib\\site-packages\\sklearn\\.libs\\vcomp140.dll", 'vcomp140.dll'),
    ("C:\\Users\\user\\anaconda3\\envs\\ss\\Lib\\site-packages\\cv2\\opencv_videoio_ffmpeg490_64.dll", './lib/cv2/opencv_videoio_ffmpeg490_64.dll'),
    ],
    "include_msvcr": True   #skip error msvcr100.dll missing
}

# packages = [
#     	"matplotlib","scipy","numpy","os", "cv2", "sys", "threading", "PyQt5",
#      "sqlite3", "mediapipe", "joblib", "pandas", "preprocessing", "win10toast", "time"
#     ]
 
# '''include the file of the package from python/anaconda installation '''
# include_files = ['C:\\Users\\user\\anaconda3\\envs\\ss\\Lib\\site-packages\\matplotlib']

# build_exe_options = {'includes':includes,
#                      'packages':packages, 'excludes':excludes, 'include_files':includefiles}
 
exe = [Executable('posture_saver.py', base='Win32GUI', icon="C:\\Users\\user\\aivle\\bp\\winexe\\exepj\\logo_page.ico")]
 
setup(
    name='posture_saver',
    version='3.0',
    author='team10_CSB',
    options = dict(build_exe = buildOptions),
    executables = exe
)



