from cx_Freeze import setup, Executable
import os

# Dependencies are automatically detected, but it might need fine tuning.
# build_exe_options = {"packages": ["os"], "excludes": [
#     "tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
# if sys.platform == "win32":
#     base = "Win32GUI"

setup(name="ЭмуляторСетевыхКонтролеров IronLogic",
      version="0.1",
      description="ЭмуляторСетевыхКонтролеров IronLogic",
    #   options={"build_exe": build_exe_options},
      executables=[Executable("IronLogic.py", base=base)])
