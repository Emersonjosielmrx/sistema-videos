"""Bot wrapper com stderr separado pra debug."""
import sys, os, traceback

os.chdir("C:/projetos-navegador")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, "C:/projetos-navegador")

log_out = open("C:/projetos-navegador/bot_output.log", "w", encoding="utf-8", buffering=1)
log_err = open("C:/projetos-navegador/bot_error.log", "w", encoding="utf-8", buffering=1)

sys.stdout = log_out
sys.stderr = log_err

print("=== BOT WRAPPER DEBUG START ===", flush=True)
print("=== BOT WRAPPER DEBUG START ===", file=sys.stderr, flush=True)

try:
    print("Importing engage_modules.main...", flush=True)
    from engage_modules.main import main
    print("Import OK, calling main()...", flush=True)
    main()
except Exception as e:
    print(f"EXCEPTION: {e}", flush=True)
    print(f"EXCEPTION: {e}", file=sys.stderr, flush=True)
    traceback.print_exc()
    traceback.print_exc(file=sys.stderr)
finally:
    print("=== BOT WRAPPER DEBUG EXIT ===", flush=True)
    print("=== BOT WRAPPER DEBUG EXIT ===", file=sys.stderr, flush=True)
    log_out.close()
    log_err.close()
