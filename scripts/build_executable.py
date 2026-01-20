import argparse
import os
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Build SlideMob executable")
    parser.add_argument("--platform", choices=["win", "mac"], required=True, help="Target platform")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec_file = os.path.join(project_root, "pyinstaller.spec")

    if not os.path.exists(spec_file):
        print(f"Error: Spec file not found at {spec_file}")
        sys.exit(1)

    print(f"Starting build for {args.platform}...")

    # Build command
    # Use sys.executable to run PyInstaller module directly from the current environment
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", spec_file]

    try:
        subprocess.run(cmd, cwd=project_root, check=True)
        print(f"Build successful! Executable can be found in the 'dist/' folder.")

        if args.platform == "mac":
            print("Creating DMG...")
            dmg_settings = os.path.join(project_root, "dmg_settings.py")
            dmg_name = "SlideMob.dmg"
            dmg_path = os.path.join(project_root, "dist", dmg_name)

            # Ensure any existing DMG is removed
            if os.path.exists(dmg_path):
                os.remove(dmg_path)

            dmg_cmd = [
                sys.executable,
                "-m",
                "dmgbuild",
                "-s",
                dmg_settings,
                "SlideMob",
                dmg_path,
            ]
            subprocess.run(dmg_cmd, cwd=project_root, check=True)
            print(f"DMG created successfully: {dmg_path}")

    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
