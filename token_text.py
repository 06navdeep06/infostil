import requests
import json
import time
import sys
from datetime import datetime

print("=== Discord Token Tester & Quick Login Helper (2026) ===\n")

def test_token(token: str):
    # Basic format check - Discord tokens have 3 parts separated by dots
    if not token or '.' not in token:
        print("   Invalid token format. Discord tokens should have dots separating parts")
        return False
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Testing token...")

    # 1. Basic User Info
    try:
        r = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=10)
        if r.status_code == 200:
            user = r.json()
            print(f"✅ TOKEN IS VALID!")
            print(f"   Username : {user.get('username')}#{user.get('discriminator', '0')}")
            print(f"   User ID  : {user.get('id')}")
            print(f"   Email    : {user.get('email', 'None')}")
            print(f"   Nitro    : {user.get('premium_type', 0)}")
            print(f"   Phone    : {user.get('phone', 'None')}\n")
            
            # 2. Quick Check for Servers & DMs
            guilds = requests.get("https://discord.com/api/v10/users/@me/guilds", headers=headers, timeout=10)
            print(f"   Servers  : {len(guilds.json()) if guilds.status_code == 200 else 'Failed'}")
            
            # 3. Try to get recent DMs (proof it has real access)
            dms = requests.get("https://discord.com/api/v10/users/@me/channels", headers=headers, timeout=10)
            if dms.status_code == 200:
                print(f"   DM Access: YES ({len(dms.json())} channels)\n")
            else:
                print("   DM Access: Limited\n")
                
            return True
        else:
            print(f"❌ Token invalid or expired (Status: {r.status_code})")
            if r.status_code == 401:
                print("   This usually means:")
                print("   - Token is expired")
                print("   - Token was revoked")
                print("   - Token format is wrong")
            print(r.text[:300])
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def quick_browser_login(token: str):
    print("Opening browser with token (works better in 2026)...")
    print("1. Open Chrome/Edge in Incognito mode")
    print("2. Press F12 → Console")
    print("3. Paste the script below and press Enter:\n")
    
    script = f"""
    // === DISCORD TOKEN LOGIN 2026 (more reliable) ===
    (() => {{
        const token = "{token}";
        localStorage.setItem("token", `"${{token}}"`);
        localStorage.setItem("user_id_cache", ""); // clear old cache
        
        // Force mobile-like fingerprint (helps bypass some checks)
        Object.defineProperty(navigator, 'userAgent', {{value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'}});
        
        console.log("%cToken injected. Reloading...", "color: lime; font-size: 16px");
        setTimeout(() => location.reload(), 800);
    }})();
    """
    print(script)
    print("\n4. After reload, if it asks for verification → try again or use mobile view (F12 → Toggle device toolbar → iPhone)")

if __name__ == "__main__":
    print("Paste your Discord token below (or type 'exit' to quit):")
    while True:
        token = input("\nToken: ").strip()
        if token.lower() in ['exit', 'quit', 'q']:
            break
        if len(token) < 50:
            print("Token too short. Try again.")
            continue
            
        success = test_token(token)
        if success:
            choice = input("Do you want the quick browser login script? (y/n): ").lower()
            if choice == 'y':
                quick_browser_login(token)
        
        print("-" * 60)