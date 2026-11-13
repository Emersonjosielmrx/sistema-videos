with open("D:/hipercool-inferior-fix/bin/hiper-pipeline.py", "r", encoding="utf8") as f:
    lines = f.readlines()

lines[1396] = "        try:\n"
lines[1397] = "            prev.rename(demoted)\n"
lines[1398] = "        except PermissionError:\n"
lines[1399] = "            import shutil\n"
lines[1400] = "            try: shutil.move(str(prev), str(demoted))\n"
lines[1401] = "            except: pass\n"

with open("D:/hipercool-inferior-fix/bin/hiper-pipeline.py", "w", encoding="utf8") as f:
    f.writelines(lines)
