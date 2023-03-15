from cx_Freeze import setup, Executable

setup(
    name="your_app_name",
    version="1.0",
    description="Your application description",
    executables=[Executable("IronLogic.py")],
    options={
        "build_exe": {
            "includes": ["aiohttp","aiosignal","async-timeout","attrs","charset-normalizer","frozenlist","idna","multidict","yarl"],
            "include_files": ["ControllerIronLogic.dll", "ZGuard.dll"]
        }
    }
)
