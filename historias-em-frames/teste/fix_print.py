for script in ['bin/story_pipeline.py', 'bin/parallax25d.py', 'bin/edge_tts_engine.py']:
    with open(script, 'r', encoding='utf-8') as f:
        code = f.read()
    code = code.replace("→", "->").replace("✓", "[OK]").replace("✗", "[X]").replace("⚠", "[!]").replace("🔄", "[*]")
    with open(script, 'w', encoding='utf-8') as f:
        f.write(code)
