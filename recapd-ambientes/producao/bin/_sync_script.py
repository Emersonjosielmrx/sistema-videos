import base64, os, sys

target = r"C:\recapd-e-animes\bin\anime_script.py"
b64_data = """${B64_PLACEHOLDER}"""

try:
    data = base64.b64decode(b64_data)
    open(target, "wb").write(data)
    print(f"OK anime_script.py ({len(data)} bytes)")
except Exception as e:
    print(f"FAIL anime_script.py: {e}")
