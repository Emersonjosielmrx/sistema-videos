#!/usr/bin/env python3
r"""Decripta cookies v20 (App-Bound Encryption) do Chrome via o servico IElevator2Chrome.
Le o sessionKey do claude.ai de um perfil SEM abrir o Chrome.

Chrome 156 trocou o IID: IElevator2Chrome = {ID_UUID_DA_SUA_INSTALACAO}
(herda IElevator2 <- IElevator; DecryptData e o 3o metodo de IElevator).

Uso: python v20_decrypt.py "Profile 13"
"""
import os, sys, json, base64, sqlite3, shutil, tempfile, ctypes
from ctypes import wintypes, POINTER, byref, c_void_p, c_ulong, c_long
import comtypes
from comtypes import GUID, IUnknown, COMMETHOD, HRESULT
from comtypes.client import CreateObject
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

UD = os.path.join(os.environ["LOCALAPPDATA"], r"Google\Chrome\User Data")
CLSID_ELEVATOR = "{ID_UUID_DA_SUA_INSTALACAO}"
IID_IELEVATOR2CHROME = "{ID_UUID_DA_SUA_INSTALACAO}"

CLSCTX_LOCAL_SERVER = 4
RPC_C_AUTHN_LEVEL_PKT_PRIVACY = 6
RPC_C_IMP_LEVEL_IMPERSONATE = 3
EOAC_DYNAMIC_CLOAKING = 0x40

_ole = ctypes.windll.oleaut32
_ole.SysAllocStringByteLen.restype = c_void_p
_ole.SysAllocStringByteLen.argtypes = [ctypes.c_char_p, ctypes.c_uint]
_ole.SysStringByteLen.restype = ctypes.c_uint
_ole.SysStringByteLen.argtypes = [c_void_p]


class IElevator2Chrome(IUnknown):
    _iid_ = GUID(IID_IELEVATOR2CHROME)
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
                  (['in'], c_void_p, "plaintext"),
                  (['out'], POINTER(c_void_p), "ciphertext"),
                  (['out'], POINTER(c_ulong), "last_error")),
        COMMETHOD([], HRESULT, "DecryptData",
                  (['in'], c_void_p, "ciphertext"),
                  (['out'], POINTER(c_void_p), "plaintext"),
                  (['out'], POINTER(c_ulong), "last_error")),
    ]


def get_app_bound_key():
    ls = json.load(open(os.path.join(UD, "Local State"), encoding="utf-8"))
    blob = base64.b64decode(ls["os_crypt"]["app_bound_encrypted_key"])
    assert blob[:4] == b"APPB", f"prefixo inesperado: {blob[:4]!r}"
    enc = blob[4:]

    ctypes.windll.ole32.CoInitializeEx(None, 0x2)
    ctypes.windll.ole32.CoInitializeSecurity(
        None, -1, None, None, RPC_C_AUTHN_LEVEL_PKT_PRIVACY,
        RPC_C_IMP_LEVEL_IMPERSONATE, None, EOAC_DYNAMIC_CLOAKING, None)

    elevator = CreateObject(CLSID_ELEVATOR, interface=IElevator2Chrome,
                            clsctx=CLSCTX_LOCAL_SERVER)
    in_bstr = _ole.SysAllocStringByteLen(enc, len(enc))
    # comtypes trata os 2 params [out] como retorno: (plaintext_bstr, last_error)
    out_ptr, last_err = elevator.DecryptData(in_bstr)
    p = out_ptr if isinstance(out_ptr, int) else (out_ptr.value if out_ptr else 0)
    n = _ole.SysStringByteLen(c_void_p(p))
    key = ctypes.string_at(p, n)
    return key, last_err


def decrypt_v20(enc_value: bytes, key: bytes) -> str:
    nonce = enc_value[3:15]
    ct = enc_value[15:]
    pt = AESGCM(key).decrypt(nonce, ct, None)
    return pt[32:].decode("utf-8", "replace")


def extrair_sessionkey(prof, key):
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(os.path.join(UD, prof, "Network", "Cookies"), tmp)
    con = sqlite3.connect(tmp); cur = con.cursor()
    cur.execute("select name, encrypted_value from cookies "
                "where host_key like '%claude.ai%' and name='sessionKey'")
    rows = cur.fetchall(); con.close()
    try: os.remove(tmp)
    except Exception: pass
    if not rows:
        return ""
    enc = rows[0][1]
    if enc[:3] != b"v20":
        return ""
    return decrypt_v20(enc, key)


def main(prof):
    key, err = get_app_bound_key()
    print(f"app-bound key len={len(key)} (esperado 32)  last_error={err}")
    if len(key) != 32:
        print("KEY INVALIDA"); return
    sk = extrair_sessionkey(prof, key)
    print("sessionKey len:", len(sk), "| inicio:", sk[:22])
    if sk.startswith("sk-ant"):
        print("OK! sessionKey valido")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Profile 13")
