import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# WARNING: YOU MUST INCLUDE 'idna' AS A DEPENDENCY
build_exe_options = {"packages": ['sqlalchemy', 'datetime', 'requests', 'lxml', 'tqdm', 'sys', 'string', 'pprint', 'selenium', 'urllib', 'time', 're', 'os', 'errno', 'traceback', 'random', 'urlparse', 'keyring', 'getpass', 'logging', 'idna', 'six', 'weakref'], "include_files": ['boxdriver', 'boxdriver.exe']}

base = None

# If it's a console application, you do NOT require base GUI below

# GUI applications require a different base on Windows (the default is for a
# console application).
# if sys.platform == "win32":
#     base = "Win32GUI"

setup(  name = "Blackbox",
        version = "1.0",
        description = "Dropbox for Blackboard",
        options = {"build_exe": build_exe_options},
        executables = [Executable("blackbox.py", base=base, icon="box.ico")])
