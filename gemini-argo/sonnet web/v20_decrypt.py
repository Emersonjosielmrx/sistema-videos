#!/usr/bin/env python3
r"""Decripta cookies v20 (App-Bound Encryption) do Chrome via o servico IElevator.
Testa extrair o sessionKey do claude.ai de um perfil SEM abrir o Chrome.

Uso: python v20_decrypt.py "Profile 13"
"""
import os, sys, json, base64, sqlite3, shutil, tempfile, ctypes
from ctypes import wintypes, POINTER, byref, c_void_p, c_ulong, c_long
import comtypes
from comtypes import GUID, IUnknown, COMMETHOD, HRESULT, BSTR
from comtypes.client import CreateObject
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

UD = os.path.join(os.environ["LOCALAPPDATA"], r"Google\Chrome\User Data")

CLSID_ELEVATOR = "{708860E0-F641-4611-8895-7D867DD3675B}"   # Google Chrome
IID_IELEVATOR  = "{463ABECF-410D-407F-8AF5-0DF35A005CC8}"

# --- COM security (o elevator exige cloaking + privacy) ---
RPC_C_AUTHN_LEVEL_PKT_PRIVACY = 6
RPC_C_IMP_LEVEL_IMPERSONATE = 3
EOAC_DYNAMIC_CLOAKING = 0x40
CLSCTX_LOCAL_SERVER = 4


class IElevator(IUnknown):
    _iid_ = GUID(IID_IELEVATOR)
    _methods_ = [
        COMMETHOD([], HRESULT, "RunRecoveryCRXElevated",
                  (['in'], ctypes.c_wchar_p, "crx_path"),
                  (['in'], ctypes.c_wchar_p, "browser_appid"),
                  (['in'], ctypes.c_wchar_p, "browser_version"),
                  (['in'], ctypes.c_wchar_p, "session_id"),
                  (['in'], wintypes.DWORD, "caller_proc_id"),
                  (['out'], POINTER(wintypes.HANDLE), "proc_handle")),
        COMMETHOD([], HRESULT, "EncryptData",
                  (['in'], c_long, "protection_level"),
                  (['in'], BSTR, "plaintext"),
                  (['out'], POINTER(BSTR), "ciphertext"),
                  (['out'], POINTER(c_ulong), "last_error")),
        COMMETHOD([], HRESULT, "DecryptData",
                  (['in'], BSTR, "ciphertext"),
                  (['out'], POINTER(BSTR), "plaintext"),
                  (['out'], POINTER(c_ulong), "last_error")),
    ]


def _bstr_from_bytes(data: bytes):
    # BSTR que guarda bytes crus (SysAllocStringByteLen)
    ptr = ctypes.windll.oleaut32.SysAllocStringByteLen(data, len(data))
    return ctypes.cast(ptr, ctypes.c_void_p)


def _bytes_from_bstr(bstr) -> bytes:
    ptr = ctypes.cast(bstr, ctypes.c_void_p)
    if not ptr.value:
        return b""
    n = ctypes.windll.oleaut32.SysStringByteLen(ptr)
    return ctypes.string_at(ptr, n)


def get_app_bound_key():
    ls = json.load(open(os.path.join(UD, "Local State"), encoding="utf-8"))
    b64 = ls["os_crypt"]["app_bound_encrypted_key"]
    blob = base64.b64decode(b64)
    assert blob[:4] == b"APPB", f"prefixo inesperado: {blob[:4]!r}"
    enc = blob[4:]

    # init COM com seguranca exigida pelo elevator
    ctypes.windll.ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED
    ctypes.windll.ole32.CoInitializeSecurity(
        None, -1, None, None,
        RPC_C_AUTHN_LEVEL_PKT_PRIVACY, RPC_C_IMP_LEVEL_IMPERSONATE,
        None, EOAC_DYNAMIC_CLOAKING, None)

    elevator = CreateObject(CLSID_ELEVATOR, interface=IElevator,
                            clsctx=CLSCTX_LOCAL_SERVER)
    in_bstr = _bstr_from_bytes(enc)
    last_err = c_ulong(0)
    out = elevator.DecryptData(in_bstr, byref(last_err))
    # comtypes pode retornar (plaintext,) conforme out params
    key = _bytes_from_bstr(out)
    return key


def decrypt_v20(enc_value: bytes, key: bytes) -> str:
    # enc: 'v20' + nonce(12) + ciphertext + tag(16)
    nonce = enc_value[3:15]
    ct = enc_value[15:]
    pt = AESGCM(key).decrypt(nonce, ct, None)
    # v20 tem 32 bytes de prefixo (flags/hash) antes do valor
    return pt[32:].decode("utf-8", "replace")


def main(prof):
    key = get_app_bound_key()
    print("app-bound key len:", len(key), "(esperado 32)")
    if len(key) != 32:
        print("KEY INVALIDA — IElevator provavelmente recusou o caller")
        return
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(os.path.join(UD, prof, "Network", "Cookies"), tmp)
    con = sqlite3.connect(tmp); cur = con.cursor()
    cur.execute("select name, encrypted_value from cookies where host_key like '%claude.ai%'")
    rows = cur.fetchall(); con.close(); os.remove(tmp)
    sk = ""
    for name, enc in rows:
        if enc[:3] == b"v20":
            try:
                val = decrypt_v20(enc, key)
            except Exception as e:
                val = f"(erro {e})"
        else:
            val = "(nao-v20)"
        if name == "sessionKey":
            sk = val
        print(f"  {name} = {val[:30]}")
    print("sessionKey len:", len(sk))
    if sk.startswith("sk-ant"):
        print("OK! sessionKey valido:", sk[:20] + "...")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Profile 13")
