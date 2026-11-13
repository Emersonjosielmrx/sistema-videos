import re

with open('/d/hipercool-inferior-fix/bin/hiper-pipeline.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix the broken try block inside censura
bad_code = """        try:
            import censura_visual
try:
    from censura_manual_override import get_override
except:
    get_override = lambda o, c, f: None as _cv"""

good_code = """        try:
            import censura_visual as _cv
        except ImportError:
            _cv = None
        try:
            from censura_manual_override import get_override
        except ImportError:
            get_override = lambda o, c, f: None"""

code = code.replace(bad_code, good_code)

with open('/d/hipercool-inferior-fix/bin/hiper-pipeline.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("hiper-pipeline fixed.")
