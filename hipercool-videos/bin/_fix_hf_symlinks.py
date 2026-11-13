# -*- coding: utf-8 -*-
"""Fix HF cache on NAS: convert symlinks to real files (SMB doesn't preserve symlinks)."""
import pathlib, os, shutil

NAS_HF = pathlib.Path("//100.118.234.102/d$/historias-em-frames/workspace/hf_cache/hub")

print("Fixing symlinks in NAS HF cache...")

for model_dir in NAS_HF.iterdir():
    if not model_dir.is_dir() or model_dir.name.startswith("."):
        continue
    snapshots = model_dir / "snapshots"
    if not snapshots.exists():
        continue
    for snap_dir in snapshots.iterdir():
        if not snap_dir.is_dir():
            continue
        for f in snap_dir.iterdir():
            if f.is_symlink():
                target = os.readlink(str(f))
                # Target is relative: ../../blobs/xxx
                real_target = (f.parent / target).resolve()
                if real_target.exists():
                    # Copy the actual file content
                    real_target_file = pathlib.Path(str(real_target).replace("/", "\\"))
                    print(f"  Fixing {f.relative_to(NAS_HF)} -> {real_target_file.name}")
                    try:
                        shutil.copy2(real_target_file, f)
                    except Exception as e:
                        print(f"    ERR: {e}")
                else:
                    print(f"  SKIP (target not found): {target}")

print("\nDone.")
nas_size = sum(f.stat().st_size for f in NAS_HF.rglob("*") if f.is_file()) // 1024//1024
print(f"NAS HF cache: {nas_size} MB")
