# -*- coding: utf-8 -*-
"""Sync HF cache from local D: to NAS so PC2 daemon can access models."""
import shutil, os
from pathlib import Path

SRC = Path("D:/modelos_cache/huggingface")
DST = Path("//100.118.234.102/d$/historias-em-frames/workspace/hf_cache")

print(f"Source: {SRC}")
print(f"Dest:   {DST}")
src_size = sum(f.stat().st_size for f in SRC.rglob("*") if f.is_file())
print(f"Source size: {src_size // 1024//1024} MB")

DST.mkdir(parents=True, exist_ok=True)

for item in (SRC / "hub").iterdir():
    if item.name.startswith(".") or item.name.startswith("_"):
        continue
    dst_item = DST / "hub" / item.name
    if not dst_item.exists():
        dst_item.mkdir(parents=True, exist_ok=True)
    elif not dst_item.is_dir():
        dst_item.unlink()
        dst_item.mkdir(parents=True, exist_ok=True)
    print(f"\nSyncing {item.name}...")
    copied = 0
    skipped = 0
    errs = 0
    if item.is_dir():
        for subitem in item.iterdir():
            dst_sub = dst_item / subitem.name
            if subitem.is_file():
                try:
                    if not dst_sub.exists() or dst_sub.stat().st_size != subitem.stat().st_size:
                        shutil.copy2(subitem, dst_sub)
                        copied += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errs += 1
                    if errs <= 3:
                        print(f"  ERR {subitem.name}: {e}")
            elif subitem.is_dir():
                if not dst_sub.exists():
                    dst_sub.mkdir(exist_ok=True)
                elif not dst_sub.is_dir():
                    dst_sub.unlink()
                    dst_sub.mkdir(parents=True, exist_ok=True)
                for f in subitem.iterdir():
                    dst_f = dst_sub / f.name
                    if f.is_file() and not f.is_symlink():
                        try:
                            # Note: Path.exists() returns True for SMB symlinks.
                            # os.path.islink() correctly detects them. We need to
                            # overwrite if: dst doesn't exist as regular file, OR
                            # dst is a symlink, OR sizes differ.
                            dst_is_sym = os.path.islink(str(dst_f))
                            dst_is_real_file = dst_f.exists() and not dst_is_sym
                            if not dst_is_real_file:
                                shutil.copy2(f, dst_f)
                                copied += 1
                            elif dst_f.stat().st_size != f.stat().st_size:
                                shutil.copy2(f, dst_f)
                                copied += 1
                            else:
                                skipped += 1
                        except Exception as e:
                            errs += 1
                            if errs <= 5:
                                print(f"  ERR {f.name}: {e}")
    print(f"  copied={copied} skipped={skipped} errors={errs}")

print("\n\nSync complete!")
nas_size = sum(f.stat().st_size for f in DST.rglob("*") if f.is_file()) // 1024//1024
print(f"NAS HF cache size: {nas_size} MB (was {src_size//1024//1024} MB)")

