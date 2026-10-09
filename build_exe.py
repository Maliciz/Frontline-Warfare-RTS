"""
Build Script for compiling Frontline: Steel Vanguard RTS into a standalone Windows .exe
"""
import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("=== Compiling Frontline: Steel Vanguard RTS with PyInstaller ===")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=FrontlineWarfare",
        "--onefile",
        "--windowed",
        "--clean",
        f"--icon={os.path.join(BASE_DIR, 'icon.ico')}",
        "--hidden-import=pygame",
        "--hidden-import=numpy",
        "--hidden-import=engine",
        "--hidden-import=engine.config",
        "--hidden-import=engine.sound",
        "--hidden-import=engine.camera",
        "--hidden-import=engine.fog_of_war",
        "--hidden-import=engine.map_grid",
        "--hidden-import=engine.effects",
        "--hidden-import=engine.combat",
        "--hidden-import=engine.buildings",
        "--hidden-import=engine.units",
        "--hidden-import=engine.ai",
        "--hidden-import=engine.ui",
        "--hidden-import=engine.game_state",
        os.path.join(BASE_DIR, "main.py")
    ]

    print("Executing command:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=BASE_DIR)

    if res.returncode == 0:
        exe_src = os.path.join(BASE_DIR, "dist", "FrontlineWarfare.exe")
        exe_dest = os.path.join(BASE_DIR, "FrontlineWarfare.exe")
        shutil.copyfile(exe_src, exe_dest)
        print(f"\n[SUCCESS] Standalone executable created at:\n{exe_dest}")
        print(f"File size: {os.path.getsize(exe_dest) / (1024 * 1024):.2f} MB")
        return exe_dest
    else:
        print("[ERROR] PyInstaller compilation failed!")
        sys.exit(1)

if __name__ == "__main__":
    build()
