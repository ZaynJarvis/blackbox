import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# WARNING: YOU MUST INCLUDE 'idna' AS A DEPENDENCY
<<<<<<< HEAD
build_exe_options = {"packages": ['backports.weakref', 'sqlalchemy', 'datetime', 'requests', 'lxml', 'tqdm', 'sys', 'string', 'pprint', 'selenium', 'urllib', 'time', 're', 'os', 'errno', 'traceback', 'random', 'keyring', 'getpass', 'logging', 'idna', 'six', 'weakref'], "include_files": ['boxdriver', 'boxdriver.exe']}
=======
build_exe_options = {"packages": ['backports.weakref', 'sqlalchemy', 'datetime', 'requests', 'lxml', 'tqdm', 'sys', 'string', 'pprint', 'selenium', 'urllib', 'time', 're', 'os', 'errno', 'traceback', 'random', 'urlparse', 'keyring', 'getpass', 'logging', 'idna', 'six', 'weakref'], "include_files": ['boxdriver', 'boxdriver.exe']}
>>>>>>> c6175d4053124c39bfa8342b33601b835a6cedb5

base = None

setup(  name = "Blackbox",
        version = "1.0",
        description = "Dropbox for Blackboard",
        options = {"build_exe": build_exe_options},
        executables = [Executable("blackbox.py", base=base, icon="box.ico")])
