import sys
import os
import json
import urllib.request
import urllib.parse
import time

# Force UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.app_secrets import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
except ImportError:
    print("❌ Could not import secrets.")
    sys.exit(1)

def test_http_insert():
    print("Testing Low-Level HTTP Insert (urllib)...")
    
    url = f"{SUPABASE_URL}/rest/v1/documents"
    key = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    data = {
        "content": "Diagnostics Test: HTTP Probe",
        "metadata": {
            "source": "urllib_test",
            "topic": "db_diagnostics_http",
            "timestamp": time.time()
        }
    }
    
    encoded_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method='POST')
    
    print(f"POSTing to {url}...")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Status Code: {resp.status}")
            response_body = resp.read().decode('utf-8')
            print(f"✅ Response: {response_body}")
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_http_insert()
