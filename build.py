'''
Author: Be1k0
URL: https://github.com/Be1k0/YuQue-BdT
'''

import os
import sys
import re
import shutil
import subprocess
import argparse

MAIN_FILE = "main.py"

def get_current_version():
    if not os.path.exists(MAIN_FILE):
        return "vUnknown"
    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^__version__\s*=\s*["\'](v[^"\']+)["\']', content, re.MULTILINE)
    return match.group(1) if match else "vUnknown"

def update_main_version(new_version):
    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    new_content = re.sub(
        r'^__version__\s*=\s*["\']v[^"\']+["\']',
        f'__version__ = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[OK] 已将 {MAIN_FILE} 的版本号更新为 Tag: {new_version}")

def get_windows_file_version(version_str):
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        return f"{match.group(1)}.{match.group(2)}.{match.group(3)}.0"
    return "1.0.0.0"

def do_build_nuitka(target_version):
    print("\n--- 开始执行 Nuitka 打包 ---")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
        
    file_version_str = get_windows_file_version(target_version)
    exe_name = f"YuQue-BdT {target_version}"
    
    command = [
        sys.executable, "-m", "nuitka",
        "--clean-cache=all",
        "--assume-yes-for-downloads",
        "--onefile",
        "--enable-plugin=pyqt6",
        "--output-dir=dist",
    ]

    if sys.platform == "win32":
        command.extend([
            "--windows-console-mode=disable",
            "--windows-icon-from-ico=logo.ico",
            f"--output-filename={exe_name}-Windows.exe",
            "--company-name=Be1k0",
            f"--product-name=YuQue-BdT {target_version}",
            f"--file-version={file_version_str}",
            f"--product-version={file_version_str}",
            "--copyright=Copyright (C) 2025-2026 By Be1k0",
        ])
    else:
        # Linux 平台的输出文件
        command.extend([
            f"--output-filename={exe_name}-Linux.bin",
        ])

    # 附加资源文件
    if os.path.exists("src/ui/themes"):
        command.append(f"--include-data-dir=src/ui/themes=src/ui/themes")
    if os.path.exists("favicon.ico"):
        command.append(f"--include-data-file=favicon.ico=favicon.ico")
    if os.path.exists("CHANGELOG.md"):
        command.append(f"--include-data-file=CHANGELOG.md=CHANGELOG.md")
    if os.path.exists("logo.ico"):
        command.append(f"--include-data-file=logo.ico=logo.ico")

    command.append(MAIN_FILE)
    print(f"执行命令: {' '.join(command)}")

    try:
        subprocess.check_call(command)
        print("\n[SUCCESS] Nuitka 构建成功! 可执行文件位于: dist/")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Nuitka 构建失败: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="GitHub Actions 构建脚本")
    parser.add_argument("--version", type=str, help="从 Actions 获取的 Tag，如 'v2.1.0'")
    
    args = parser.parse_args()
    
    if args.version:
        target_version = args.version if args.version.startswith('v') else f"v{args.version}"
        update_main_version(target_version)
    else:
        target_version = get_current_version()
        print(f"未传入版本号，使用当前代码版本: {target_version}")

    do_build_nuitka(target_version)
    
if __name__ == "__main__":
    main()