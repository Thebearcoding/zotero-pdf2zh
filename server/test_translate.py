#!/usr/bin/env python3
"""Test script to simulate the Zotero plugin sending a PDF for translation."""
import base64
import json
import requests
import sys
import os

# Config
SERVER_URL = "http://localhost:8890"
PDF_PATH = "/Users/athebear/Documents/GitHub/zotero-pdf2zh/Jiang和Li - 2016 - Deep Cross-Modal Hashing.pdf"

# Step 1: Check server health
print("=" * 60)
print("Step 1: Checking server health...")
try:
    resp = requests.get(f"{SERVER_URL}/health", timeout=5)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.json()}")
except Exception as e:
    print(f"  ERROR: Server unreachable: {e}")
    sys.exit(1)

# Step 2: Test the third-party API directly
print("\n" + "=" * 60)
print("Step 2: Testing third-party API connectivity...")
API_URL = "http://104.236.54.43:8317/v1"
API_KEY = "sk-xinran-secret-password-2025"
MODEL = "gpt-5"

try:
    resp = requests.post(
        f"{API_URL}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": "Translate to Chinese: Hello world"}],
            "max_tokens": 50
        },
        timeout=30
    )
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Model: {data.get('model', 'N/A')}")
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"  Response: {content[:200]}")
    else:
        print(f"  Error response: {resp.text[:500]}")
except Exception as e:
    print(f"  ERROR: API unreachable: {e}")
    print("  Continuing with translation test anyway...")

# Step 3: Send PDF for translation
print("\n" + "=" * 60)
print("Step 3: Sending PDF for translation...")
print(f"  PDF: {os.path.basename(PDF_PATH)}")
print(f"  Size: {os.path.getsize(PDF_PATH) / 1024:.1f} KB")

# Read and encode PDF
with open(PDF_PATH, "rb") as f:
    pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

# Build request body (same format as the Zotero plugin)
request_body = {
    "fileName": os.path.basename(PDF_PATH),
    "fileContent": f"data:application/pdf;base64,{pdf_base64}",
    
    # Server config
    "serverUrl": SERVER_URL,
    "engine": "pdf2zh_next",
    "service": "openai",
    "next_service": "openai",
    
    # Language
    "sourceLang": "en",
    "targetLang": "zh-CN",
    
    # Parameters
    "threadNum": "4",
    "qps": "10",
    "poolSize": "0",
    "skipLastPages": "0",
    
    # Generation config
    "mono": "true",
    "dual": "true",
    "mono_cut": "false",
    "dual_cut": "false",
    "crop_compare": "false",
    "compare": "false",
    
    # pdf2zh_next config
    "noWatermark": "true",
    "transFirst": "true",
    "ocr": "false",
    "autoOcr": "true",
    "fontFamily": "auto",
    "dualMode": "LR",
    "noDual": "false",
    "noMono": "false",
    "skipClean": "false",
    "disableRichTextTranslate": "false",
    "enhanceCompatibility": "false",
    "translateTableText": "false",
    "saveGlossary": "false",
    "disableGlossary": "false",
    
    # LLM API config
    "llm_api": {
        "service": "openai",
        "model": MODEL,
        "apiKey": API_KEY,
        "apiUrl": API_URL,
        "extraData": {}
    }
}

print(f"  Engine: {request_body['engine']}")
print(f"  Service: {request_body['next_service']}")
print(f"  Model: {request_body['llm_api']['model']}")
print(f"  API URL: {request_body['llm_api']['apiUrl']}")
print(f"  Sending request to {SERVER_URL}/translate ...")
print(f"  (This may take several minutes...)")

try:
    resp = requests.post(
        f"{SERVER_URL}/translate",
        headers={"Content-Type": "application/json"},
        json=request_body,
        timeout=600  # 10 minute timeout
    )
    print(f"\n  Status: {resp.status_code}")
    result = resp.json()
    print(f"  Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        print("\n✅ Translation succeeded!")
        print("  Generated files:")
        for f in result.get("fileList", []):
            print(f"    - {f}")
            print(f"      Download: {SERVER_URL}/translatedFile/{f}")
    else:
        print(f"\n❌ Translation failed: {result.get('message', 'Unknown error')}")
except requests.exceptions.Timeout:
    print("\n❌ Request timed out (10 minutes)")
except Exception as e:
    print(f"\n❌ Request failed: {e}")
