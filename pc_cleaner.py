#!/usr/bin/env python3
"""
██████╗  ██████╗    ██████╗██╗     ███████╗ █████╗ ███╗   ██╗
██╔══██╗██╔════╝   ██╔════╝██║     ██╔════╝██╔══██╗████╗  ██║
██████╔╝██║        ██║     ██║     █████╗  ███████║██╔██╗ ██║
██╔═══╝ ██║        ██║     ██║     ██╔══╝  ██╔══██║██║╚██╗██║
██║     ╚██████╗   ╚██████╗███████╗███████╗██║  ██║██║ ╚████║
╚═╝      ╚═════╝    ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝
                    PC Maintenance Utility v1.0
                    Windows All-in-One Cleaner
"""

import os
import sys
import time
import shutil
import ctypes
import winreg
import hashlib
import fnmatch
import platform
import tempfile
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta

# ─── Color palette ───────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[38;5;196m"
    GREEN  = "\033[38;5;82m"
    YELLOW = "\033[38;5;220m"
    CYAN   = "\033[38;5;51m"
    WHITE  = "\033[38;5;255m"
    GRAY   = "\033[38;5;240m"
    ORANGE = "\033[38;5;214m"
    PURPLE = "\033[38;5;135m"
    BG_RED = "\033[48;5;52m"

# Enable ANSI on Windows
os.system("color")
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

# ─── Helpers ─────────────────────────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def rerun_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

def fmt_bytes(num):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"

def run_cmd(cmd, capture=True):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture,
            text=True, timeout=60
        )
        return result.stdout.strip() if capture else None
    except Exception:
        return ""

def delete_path(path):
    """Delete file or directory, return size freed."""
    freed = 0
    try:
        p = Path(path)
        if p.is_file() or p.is_symlink():
            freed = p.stat().st_size
            p.unlink(missing_ok=True)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    try:
                        freed += f.stat().st_size
                    except:
                        pass
            shutil.rmtree(p, ignore_errors=True)
    except Exception:
        pass
    return freed

def spinner(stop_event, msg=""):
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    while not stop_event.is_set():
        print(f"\r  {C.CYAN}{chars[i % len(chars)]}{C.RESET}  {msg}", end="", flush=True)
        i += 1
        time.sleep(0.08)
    print("\r" + " " * (len(msg) + 10) + "\r", end="")

def with_spinner(fn, msg):
    stop = threading.Event()
    t = threading.Thread(target=spinner, args=(stop, msg), daemon=True)
    t.start()
    result = fn()
    stop.set()
    t.join()
    return result

# ─── UI elements ─────────────────────────────────────────────────────────────
def header():
    clear()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════════╗
║{C.WHITE}{C.BOLD}   AECLEANER  //  Windows Maintenance Utility v1.0        {C.RESET}{C.CYAN}║
║{C.GRAY}   {platform.node():<20}  {platform.win32_ver()[0]} {platform.win32_ver()[1]:<16}{C.CYAN}║
╚══════════════════════════════════════════════════════════╝{C.RESET}
""")

def section(title):
    print(f"\n{C.CYAN}┌─ {C.WHITE}{C.BOLD}{title}{C.RESET}")

def line(label, value, color=C.GREEN, warn=False):
    c = C.YELLOW if warn else color
    print(f"{C.CYAN}│{C.RESET}  {C.GRAY}{label:<30}{C.RESET}{c}{value}{C.RESET}")

def ok(msg):    print(f"  {C.GREEN}✓{C.RESET}  {msg}")
def info(msg):  print(f"  {C.CYAN}·{C.RESET}  {msg}")
def warn(msg):  print(f"  {C.YELLOW}!{C.RESET}  {msg}")
def err(msg):   print(f"  {C.RED}✗{C.RESET}  {msg}")
def sep():      print(f"  {C.GRAY}{'─'*54}{C.RESET}")

def menu(options, title=""):
    if title:
        print(f"\n  {C.WHITE}{C.BOLD}{title}{C.RESET}")
    print()
    for i, opt in enumerate(options, 1):
        icon, label = opt
        print(f"  {C.CYAN}[{C.WHITE}{i}{C.CYAN}]{C.RESET}  {icon}  {label}")
    print(f"\n  {C.CYAN}[{C.WHITE}0{C.CYAN}]{C.RESET}  ←  Back / Exit")
    print()
    choice = input(f"  {C.GRAY}›{C.RESET} ").strip()
    return choice

def confirm(msg):
    r = input(f"  {C.YELLOW}?{C.RESET}  {msg} {C.GRAY}[y/N]{C.RESET} ").strip().lower()
    return r == "y"

def press_enter():
    input(f"\n  {C.GRAY}[Enter to continue]{C.RESET}")

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — SYSTEM INFO
# ═══════════════════════════════════════════════════════════════════════════════
def module_sysinfo():
    header()
    section("System Overview")

    # CPU
    cpu_name = run_cmd("wmic cpu get Name /value").replace("Name=", "").strip()
    cpu_load = run_cmd("wmic cpu get LoadPercentage /value").replace("LoadPercentage=", "").strip()

    # RAM
    total_mem = run_cmd("wmic ComputerSystem get TotalPhysicalMemory /value").replace("TotalPhysicalMemory=", "").strip()
    avail_mem = run_cmd("wmic OS get FreePhysicalMemory /value").replace("FreePhysicalMemory=", "").strip()
    try:
        total_mb = int(total_mem) / 1024 / 1024
        avail_mb = int(avail_mem) / 1024
        used_mb = total_mb - avail_mb
        ram_pct = used_mb / total_mb * 100
    except:
        total_mb = avail_mb = used_mb = ram_pct = 0

    # Disk
    disk = shutil.disk_usage("C:\\")
    disk_pct = disk.used / disk.total * 100

    # OS
    os_caption = run_cmd("wmic os get Caption /value").replace("Caption=", "").strip()
    os_build   = run_cmd("wmic os get BuildNumber /value").replace("BuildNumber=", "").strip()
    uptime_sec = int(run_cmd("wmic os get LastBootUpTime /value").replace("LastBootUpTime=", "").strip()[:14] or 0)

    # Uptime
    boot_raw = run_cmd("wmic os get LastBootUpTime /value").replace("LastBootUpTime=", "").strip()
    try:
        boot_dt = datetime.strptime(boot_raw[:14], "%Y%m%d%H%M%S")
        uptime  = datetime.now() - boot_dt
        up_str  = str(uptime).split(".")[0]
    except:
        up_str = "N/A"

    line("OS", os_caption)
    line("Build", os_build)
    line("CPU", cpu_name[:40])
    line("CPU Load", f"{cpu_load}%", warn=int(cpu_load or 0) > 80)
    line("RAM Used", f"{fmt_bytes(used_mb*1024*1024)} / {fmt_bytes(total_mb*1024*1024)}  ({ram_pct:.0f}%)", warn=ram_pct > 85)
    line("Disk C:", f"{fmt_bytes(disk.used)} / {fmt_bytes(disk.total)}  ({disk_pct:.0f}%)", warn=disk_pct > 85)
    line("Uptime", up_str)
    line("Admin", "YES" if is_admin() else "NO — some features limited", warn=not is_admin())

    # GPU
    gpu = run_cmd("wmic path win32_VideoController get Name /value").replace("Name=", "").strip().split("\n")[0]
    if gpu:
        line("GPU", gpu[:40])

    section("Network")
    ip = run_cmd("powershell (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | Select-Object -First 1).IPAddress")
    mac = run_cmd("getmac /fo csv /nh").split(",")[0].strip('"')
    dns = run_cmd("powershell (Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object {$_.ServerAddresses -ne $null} | Select-Object -First 1).ServerAddresses")
    line("IP", ip or "N/A")
    line("MAC", mac or "N/A")
    line("DNS", dns or "N/A")

    press_enter()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — DISK CLEANER
# ═══════════════════════════════════════════════════════════════════════════════
CLEAN_TARGETS = {
    "Windows Temp":        os.path.expandvars(r"%WINDIR%\Temp"),
    "User Temp":           os.path.expandvars(r"%TEMP%"),
    "Prefetch":            r"C:\Windows\Prefetch",
    "Recent Files":        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent"),
    "Recycle Bin":         r"C:\$Recycle.Bin",
    "IE Cache":            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INetCache"),
    "Edge Cache":          os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache"),
    "Chrome Cache":        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"),
    "Firefox Cache":       os.path.expandvars(r"%LOCALAPPDATA%\Mozilla\Firefox\Profiles"),
    "Windows Update Cache":r"C:\Windows\SoftwareDistribution\Download",
    "Crash Dumps":         os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps"),
    "Thumbnail Cache":     os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Explorer"),
    "DirectX Shader Cache":os.path.expandvars(r"%LOCALAPPDATA%\D3DSCache"),
    "Log Files (Windows)": r"C:\Windows\Logs",
}

def scan_targets():
    results = {}
    for name, path in CLEAN_TARGETS.items():
        size = 0
        p = Path(path)
        if p.exists():
            try:
                for f in p.rglob("*"):
                    if f.is_file():
                        try:
                            size += f.stat().st_size
                        except:
                            pass
            except:
                pass
        results[name] = (path, size)
    return results

def module_cleaner():
    header()
    section("Disk Cleaner — Scanning...")

    results = with_spinner(scan_targets, "Scanning disk for junk files...")

    total = sum(s for _, s in results.values())
    print()
    for name, (path, size) in results.items():
        exists = Path(path).exists()
        col = C.YELLOW if size > 0 and exists else C.GRAY
        flag = " ◀" if size > 100 * 1024 * 1024 else ""
        print(f"  {col}{name:<30}{C.RESET}  {fmt_bytes(size)}{C.ORANGE}{flag}{C.RESET}")

    sep()
    print(f"  {C.WHITE}Total reclaimable:{C.RESET}  {C.GREEN}{C.BOLD}{fmt_bytes(total)}{C.RESET}")
    print()

    if not confirm("Proceed with cleaning all targets?"):
        return

    freed = 0
    for name, (path, size) in results.items():
        if Path(path).exists():
            f = with_spinner(lambda p=path: delete_path(p), f"Cleaning {name}...")
            freed += f
            ok(f"{name} → freed {fmt_bytes(f)}")

    # Also run built-in cleanmgr silently if admin
    if is_admin():
        info("Running Windows Disk Cleanup (background)...")
        subprocess.Popen("cleanmgr /sagerun:1", shell=True)

    sep()
    print(f"\n  {C.GREEN}{C.BOLD}Cleaned! Total freed: {fmt_bytes(freed)}{C.RESET}")
    press_enter()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — VIRUS / MALWARE SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

# Known malicious file name patterns (lightweight heuristics)
SUSPECT_NAMES = [
    "*.exe.exe", "*.pdf.exe", "*.jpg.exe", "*.docx.exe",
    "autorun.inf", "*.bat.exe", "desktop_.ini", "*.scr",
]

# Locations commonly abused by malware
SCAN_LOCATIONS = [
    os.path.expandvars(r"%TEMP%"),
    os.path.expandvars(r"%APPDATA%\Roaming"),
    os.path.expandvars(r"%LOCALAPPDATA%"),
    r"C:\Users\Public",
    r"C:\Windows\Temp",
    r"C:\ProgramData",
]

SUSPICIOUS_REG_KEYS = [
    (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
]

def scan_files():
    hits = []
    for loc in SCAN_LOCATIONS:
        p = Path(loc)
        if not p.exists():
            continue
        try:
            for f in p.rglob("*"):
                if not f.is_file():
                    continue
                for pat in SUSPECT_NAMES:
                    if fnmatch.fnmatch(f.name.lower(), pat.lower()):
                        hits.append(("FILE", str(f), f"Suspicious name pattern: {pat}"))
                        break
                # Hidden exe in temp
                if f.suffix.lower() == ".exe" and "temp" in str(f).lower():
                    try:
                        attrs = f.stat().st_file_attributes
                        if attrs & 2:  # FILE_ATTRIBUTE_HIDDEN
                            hits.append(("FILE", str(f), "Hidden executable in Temp"))
                    except:
                        pass
        except PermissionError:
            pass
    return hits

def scan_registry():
    hits = []
    for hive, key_path in SUSPICIOUS_REG_KEYS:
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    val_lower = str(value).lower()
                    # Flag entries pointing to temp/appdata
                    if any(s in val_lower for s in [r"\temp\\", r"\appdata\roaming\\", r"\users\public\\"]):
                        hits.append(("REG", f"{key_path} → {name}", f"Value: {value[:80]}"))
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass
    return hits

def scan_hosts():
    hits = []
    hosts_file = r"C:\Windows\System32\drivers\etc\hosts"
    try:
        with open(hosts_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if not line.startswith(("127.0.0.1", "::1", "0.0.0.0")):
                        hits.append(("HOSTS", hosts_file, f"Unusual entry: {line}"))
    except:
        pass
    return hits

def scan_processes():
    hits = []
    out = run_cmd("tasklist /fo csv /nh")
    suspicious_procs = [
        "miner", "coinhive", "xmrig", "cryptonight",
        "keylog", "rat.exe", "njrat", "nanocore",
    ]
    for line_txt in out.splitlines():
        parts = line_txt.split(",")
        if parts:
            proc_name = parts[0].strip('"').lower()
            for s in suspicious_procs:
                if s in proc_name:
                    hits.append(("PROC", proc_name, f"Suspicious process name: {s}"))
    return hits

def run_windows_defender():
    info("Triggering Windows Defender Quick Scan...")
    if is_admin():
        run_cmd(r'"C:\Program Files\Windows Defender\MpCmdRun.exe" -Scan -ScanType 1', capture=False)
        ok("Defender scan triggered — check Security Center for results")
    else:
        warn("Need admin to trigger Defender scan")

def module_scanner():
    header()
    section("Malware & Threat Scanner")
    info("This performs heuristic local scanning + Windows Defender trigger")
    info("It does NOT replace a full AV suite\n")

    all_hits = []

    print(f"  {C.GRAY}Scanning files...{C.RESET}")
    file_hits = with_spinner(scan_files, "Scanning file system for suspicious files...")
    all_hits += file_hits

    print(f"  {C.GRAY}Scanning registry...{C.RESET}")
    reg_hits = with_spinner(scan_registry, "Scanning startup registry keys...")
    all_hits += reg_hits

    print(f"  {C.GRAY}Scanning hosts file...{C.RESET}")
    hosts_hits = scan_hosts()
    all_hits += hosts_hits

    print(f"  {C.GRAY}Scanning running processes...{C.RESET}")
    proc_hits = scan_processes()
    all_hits += proc_hits

    sep()
    if not all_hits:
        ok("No obvious threats detected")
    else:
        print(f"  {C.RED}{C.BOLD}Found {len(all_hits)} suspicious item(s):{C.RESET}\n")
        for kind, location, reason in all_hits:
            col = C.RED if kind == "FILE" else C.YELLOW
            print(f"  {col}[{kind}]{C.RESET}  {location[:60]}")
            print(f"  {C.GRAY}       └─ {reason}{C.RESET}")
            print()

    sep()
    if confirm("Trigger Windows Defender Quick Scan?"):
        run_windows_defender()

    press_enter()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 4 — STARTUP MANAGER
# ═══════════════════════════════════════════════════════════════════════════════
def get_startup_items():
    items = []
    for hive, key_path in [
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    ]:
        hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    items.append((hive_name, hive, key_path, name, value))
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except:
            pass
    return items

def module_startup():
    header()
    section("Startup Manager")

    items = get_startup_items()
    if not items:
        info("No startup items found (may need admin)")
        press_enter()
        return

    for idx, (hive_name, _, _, name, value) in enumerate(items, 1):
        print(f"  {C.CYAN}[{idx:02d}]{C.RESET}  {C.WHITE}{name:<30}{C.RESET}  {C.GRAY}{hive_name}{C.RESET}")
        print(f"        {C.DIM}{value[:65]}{C.RESET}")

    sep()
    print(f"  {C.YELLOW}Enter number to DISABLE a startup entry, or 0 to go back:{C.RESET} ", end="")
    choice = input().strip()
    if choice == "0" or not choice.isdigit():
        return

    idx = int(choice) - 1
    if 0 <= idx < len(items):
        _, hive, key_path, name, value = items[idx]
        if confirm(f"Disable '{name}' from startup?"):
            try:
                key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
                ok(f"Removed '{name}' from startup")
            except Exception as e:
                err(f"Failed: {e}")

    press_enter()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 5 — NETWORK TOOLS
# ═══════════════════════════════════════════════════════════════════════════════
def module_network():
    header()
    section("Network Tools")
    opts = [
        ("📡", "Flush DNS Cache"),
        ("🔌", "Reset Winsock & TCP/IP"),
        ("🌐", "Show Active Connections"),
        ("📶", "Wi-Fi Saved Passwords"),
        ("🔍", "Ping Test (8.8.8.8)"),
        ("🚫", "Show / Edit Hosts File"),
    ]
    choice = menu(opts, "Network Utilities")

    if choice == "1":
        run_cmd("ipconfig /flushdns")
        ok("DNS cache flushed")

    elif choice == "2":
        if not is_admin():
            err("Requires administrator")
        else:
            run_cmd("netsh winsock reset")
            run_cmd("netsh int ip reset")
            ok("Winsock & TCP/IP reset — please reboot")

    elif choice == "3":
        out = run_cmd("netstat -ano")
        print(f"\n{C.GRAY}{out[:3000]}{C.RESET}")

    elif choice == "4":
        profiles = run_cmd("netsh wlan show profiles")
        names = [l.split(":")[1].strip() for l in profiles.splitlines() if "All User Profile" in l]
        for n in names:
            pwd = run_cmd(f'netsh wlan show profile name="{n}" key=clear')
            for line_txt in pwd.splitlines():
                if "Key Content" in line_txt:
                    key = line_txt.split(":")[1].strip()
                    print(f"  {C.WHITE}{n:<30}{C.RESET}  {C.GREEN}{key}{C.RESET}")
                    break
            else:
                print(f"  {C.WHITE}{n:<30}{C.RESET}  {C.GRAY}(no password / open){C.RESET}")

    elif choice == "5":
        out = run_cmd("ping -n 4 8.8.8.8")
        print(f"\n{C.GRAY}{out}{C.RESET}")

    elif choice == "6":
        hosts = r"C:\Windows\System32\drivers\etc\hosts"
        with open(hosts) as f:
            print(f"\n{C.GRAY}{f.read()}{C.RESET}")

    press_enter()
    module_network()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 6 — PERFORMANCE TWEAKS
# ═══════════════════════════════════════════════════════════════════════════════
def tweak_visual_effects():
    """Set visual effects to 'Best Performance'."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2)
        winreg.CloseKey(key)
        ok("Visual effects → Best Performance")
    except Exception as e:
        err(f"Visual effects: {e}")

def tweak_power_plan():
    """Switch to High Performance power plan."""
    out = run_cmd("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
    ok("Power plan → High Performance")

def tweak_disable_telemetry():
    """Disable Windows telemetry."""
    if not is_admin():
        err("Need admin for telemetry tweak")
        return
    run_cmd('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f')
    run_cmd('sc config DiagTrack start= disabled')
    run_cmd('sc stop DiagTrack')
    ok("Telemetry disabled (DiagTrack stopped)")

def tweak_disable_cortana():
    """Disable Cortana."""
    run_cmd('reg add "HKCU\\Software\\Microsoft\\Personalization\\Settings" /v AcceptedPrivacyPolicy /t REG_DWORD /d 0 /f')
    run_cmd('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f')
    ok("Cortana disabled")

def tweak_disable_xbox():
    """Disable Xbox Game DVR."""
    run_cmd('reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f')
    run_cmd('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f')
    ok("Xbox Game DVR disabled")

def tweak_enable_god_mode():
    """Create God Mode folder on Desktop."""
    desktop = Path(os.path.expanduser("~")) / "Desktop" / "GodMode.{ED7BA470-8E54-465E-825C-99712043E01C}"
    desktop.mkdir(exist_ok=True)
    ok(f"God Mode folder created on Desktop")

def tweak_clear_ram():
    """Empty working sets to free RAM."""
    run_cmd("powershell \"Get-Process | ForEach-Object {$_.MinWorkingSet = $_.MinWorkingSet}\"")
    ok("Working sets trimmed (RAM partially freed)")

def tweak_disable_fast_startup():
    """Disable Fast Startup (fixes some wake issues)."""
    if is_admin():
        run_cmd('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f')
        ok("Fast Startup disabled")
    else:
        err("Need admin")

def tweak_set_dns_cloudflare():
    """Set DNS to Cloudflare (1.1.1.1)."""
    if not is_admin():
        err("Need admin")
        return
    iface = run_cmd('powershell (Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1).Name')
    if iface:
        run_cmd(f'netsh interface ip set dns "{iface}" static 1.1.1.1')
        run_cmd(f'netsh interface ip add dns "{iface}" 1.0.0.1 index=2')
        ok(f"DNS set to Cloudflare 1.1.1.1 on '{iface}'")
    else:
        err("No active interface found")

def tweak_sfc():
    """Run System File Checker."""
    if not is_admin():
        err("Need admin")
        return
    info("Running SFC /scannow — this may take several minutes...")
    subprocess.Popen("sfc /scannow", shell=True)
    ok("SFC started — check results in a new window")

def tweak_disable_animations():
    """Disable window animations."""
    run_cmd('reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f')
    ok("Window animations disabled")

def tweak_defrag():
    """Analyze C: for fragmentation (SSD-safe)."""
    out = run_cmd("defrag C: /A /U")
    print(f"\n{C.GRAY}{out[:800]}{C.RESET}")

def tweak_repair_image():
    """DISM RestoreHealth."""
    if not is_admin():
        err("Need admin")
        return
    info("Running DISM RestoreHealth (needs internet)...")
    subprocess.Popen("dism /online /cleanup-image /restorehealth", shell=True)
    ok("DISM started — may take 10-20 min")

ALL_TWEAKS = [
    ("⚡", "Visual Effects → Best Performance",     tweak_visual_effects),
    ("🔋", "Power Plan → High Performance",          tweak_power_plan),
    ("🔕", "Disable Windows Telemetry",              tweak_disable_telemetry),
    ("🤫", "Disable Cortana",                        tweak_disable_cortana),
    ("🎮", "Disable Xbox Game DVR",                  tweak_disable_xbox),
    ("🪟", "Disable Window Animations",              tweak_disable_animations),
    ("💤", "Disable Fast Startup",                   tweak_disable_fast_startup),
    ("🧠", "Free RAM (trim working sets)",           tweak_clear_ram),
    ("🌐", "Set DNS to Cloudflare 1.1.1.1",         tweak_set_dns_cloudflare),
    ("🛠️",  "System File Checker (sfc /scannow)",    tweak_sfc),
    ("🏥", "DISM RestoreHealth",                     tweak_repair_image),
    ("💽", "Analyze Disk Fragmentation",             tweak_defrag),
    ("👁️",  "Create God Mode Folder (Desktop)",      tweak_enable_god_mode),
]

def module_tweaks():
    header()
    section("Performance & System Tweaks")
    opts = [(icon, label) for icon, label, _ in ALL_TWEAKS]
    opts.append(("🚀", "Apply ALL safe tweaks at once"))

    choice = menu(opts, "Choose a tweak")
    if choice == "0":
        return

    if choice == str(len(ALL_TWEAKS) + 1):
        # Apply all
        if confirm("Apply ALL safe tweaks? (some need admin)"):
            safe = ALL_TWEAKS[:10]  # skip defrag/godmode in bulk
            for icon, label, fn in safe:
                print(f"\n  {C.CYAN}Applying: {label}{C.RESET}")
                try:
                    fn()
                except Exception as e:
                    err(str(e))
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(ALL_TWEAKS):
            icon, label, fn = ALL_TWEAKS[idx]
            print()
            try:
                fn()
            except Exception as e:
                err(str(e))

    press_enter()
    module_tweaks()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 7 — DUPLICATE FILE FINDER
# ═══════════════════════════════════════════════════════════════════════════════
def module_duplicates():
    header()
    section("Duplicate File Finder")

    path = input(f"  {C.GRAY}Scan directory (Enter for Desktop):{C.RESET} ").strip()
    if not path:
        path = str(Path.home() / "Desktop")
    if not Path(path).exists():
        err("Path not found")
        press_enter()
        return

    info(f"Scanning: {path}")
    hashes = {}
    dupes = {}

    def scan():
        for f in Path(path).rglob("*"):
            if f.is_file():
                try:
                    h = hashlib.md5(f.read_bytes()).hexdigest()
                    if h in hashes:
                        dupes.setdefault(h, [hashes[h]]).append(str(f))
                    else:
                        hashes[h] = str(f)
                except:
                    pass

    with_spinner(scan, "Computing checksums...")

    if not dupes:
        ok("No duplicate files found")
    else:
        total_wasted = 0
        print(f"\n  {C.YELLOW}Found {len(dupes)} duplicate group(s):{C.RESET}\n")
        for h, files in list(dupes.items())[:20]:
            size = Path(files[0]).stat().st_size if Path(files[0]).exists() else 0
            wasted = size * (len(files) - 1)
            total_wasted += wasted
            print(f"  {C.WHITE}[{len(files)} copies — {fmt_bytes(size)} each]{C.RESET}")
            for fp in files:
                print(f"  {C.GRAY}  {fp[:70]}{C.RESET}")
            print()
        sep()
        print(f"  {C.ORANGE}Potential waste: {fmt_bytes(total_wasted)}{C.RESET}")

    press_enter()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 8 — LARGE FILE FINDER
# ═══════════════════════════════════════════════════════════════════════════════
def module_large_files():
    header()
    section("Large File Finder")

    path = input(f"  {C.GRAY}Scan directory (Enter for C:\\):{C.RESET} ").strip() or "C:\\"
    min_mb = input(f"  {C.GRAY}Minimum size in MB (Enter for 500):{C.RESET} ").strip()
    min_mb = int(min_mb) if min_mb.isdigit() else 500
    min_bytes = min_mb * 1024 * 1024

    files = []

    def scan():
        try:
            for f in Path(path).rglob("*"):
                if f.is_file():
                    try:
                        s = f.stat().st_size
                        if s >= min_bytes:
                            files.append((s, str(f)))
                    except:
                        pass
        except:
            pass

    with_spinner(scan, f"Looking for files > {min_mb} MB...")
    files.sort(reverse=True)

    if not files:
        info(f"No files larger than {min_mb} MB found")
    else:
        print(f"\n  {C.WHITE}Top {min(30, len(files))} large files:{C.RESET}\n")
        for size, fp in files[:30]:
            print(f"  {C.YELLOW}{fmt_bytes(size):>10}{C.RESET}  {C.GRAY}{fp[:60]}{C.RESET}")

    press_enter()

# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 9 — INSTALLED PROGRAMS
# ═══════════════════════════════════════════════════════════════════════════════
def module_programs():
    header()
    section("Installed Programs")

    out = run_cmd(
        'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall" /s /v DisplayName'
    )
    names = [l.split("REG_SZ")[-1].strip() for l in out.splitlines() if "DisplayName" in l and "REG_SZ" in l]

    out2 = run_cmd(
        'reg query "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall" /s /v DisplayName'
    )
    names += [l.split("REG_SZ")[-1].strip() for l in out2.splitlines() if "DisplayName" in l and "REG_SZ" in l]

    names = sorted(set(n for n in names if n))
    print(f"\n  {C.GRAY}Total installed: {C.WHITE}{len(names)}{C.RESET}\n")
    for i, n in enumerate(names, 1):
        col = C.WHITE if i % 2 == 0 else C.GRAY
        print(f"  {col}{i:>3}.  {n}{C.RESET}")

    sep()
    info("To uninstall, use: Settings → Apps, or run appwiz.cpl")
    press_enter()

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════
def main_menu():
    header()

    # Quick disk bar
    disk = shutil.disk_usage("C:\\")
    pct = disk.used / disk.total
    bar_len = 30
    filled = int(bar_len * pct)
    bar = "█" * filled + "░" * (bar_len - filled)
    col = C.RED if pct > 0.9 else C.YELLOW if pct > 0.7 else C.GREEN
    print(f"  C:\\  {col}{bar}{C.RESET}  {pct*100:.0f}%  ({fmt_bytes(disk.free)} free)\n")

    if not is_admin():
        print(f"  {C.BG_RED}{C.WHITE}  ⚠  Not running as Administrator — some features limited  {C.RESET}\n")

    opts = [
        ("💻", "System Info & Diagnostics"),
        ("🧹", "Disk Cleaner"),
        ("🛡️",  "Malware & Threat Scanner"),
        ("🚀", "Startup Manager"),
        ("🌐", "Network Tools"),
        ("⚙️",  "Performance Tweaks"),
        ("🔁", "Duplicate File Finder"),
        ("📦", "Large File Finder"),
        ("📋", "Installed Programs"),
    ]
    choice = menu(opts, "Main Menu")
    return choice

MODULES = {
    "1": module_sysinfo,
    "2": module_cleaner,
    "3": module_scanner,
    "4": module_startup,
    "5": module_network,
    "6": module_tweaks,
    "7": module_duplicates,
    "8": module_large_files,
    "9": module_programs,
}

def main():
    if sys.platform != "win32":
        print("This utility is designed for Windows only.")
        sys.exit(1)

    if not is_admin():
        print(f"\n{C.YELLOW}  Run as Administrator for full functionality.{C.RESET}")
        r = input(f"  Relaunch as admin now? [y/N] ").strip().lower()
        if r == "y":
            rerun_as_admin()

    while True:
        choice = main_menu()
        if choice == "0":
            clear()
            print(f"\n  {C.CYAN}Goodbye.{C.RESET}\n")
            break
        fn = MODULES.get(choice)
        if fn:
            fn()
        else:
            err("Invalid choice")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
