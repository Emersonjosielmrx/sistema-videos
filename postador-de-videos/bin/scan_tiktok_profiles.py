"""Scan Chrome profiles for TikTok login - porta unica por perfil."""
import subprocess, time, os, sys, json

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
PROFILES_DIR = r'D:\logins-google\chrome-profiles'
SKIP = {'mundosolar1995', 'seebotsia', 'canalalucinaai', 'emersonjosiel649'}
BASE_PORT = 9270
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PYTHON = r'D:\hipercool-videos\venv\Scripts\python.exe'
TEST_SCRIPT = r'D:\hipercool-producao\bin\test_tiktok_profile.py'

all_profiles = sorted([d for d in os.listdir(PROFILES_DIR) 
                       if os.path.isdir(os.path.join(PROFILES_DIR, d)) and d not in SKIP])

print(f'Testando {len(all_profiles)} perfis...', flush=True)
results = {'logado': [], 'sem_conta': [], 'erro': []}

# Primeiro matar qualquer Chrome remanescente nas portas de teste
for i in range(30):
    subprocess.run(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr ":{BASE_PORT+i}"\') do taskkill /F /PID %a',
                   shell=True, capture_output=True, timeout=5)

procs = []

for idx, profile in enumerate(all_profiles):
    profile_path = os.path.join(PROFILES_DIR, profile)
    port = BASE_PORT + idx
    print(f'\n[{idx+1}/{len(all_profiles)}] {profile} (porta {port})', end=' ... ', flush=True)
    
    # Launch Chrome
    chrome_proc = subprocess.Popen([
        CHROME,
        f'--remote-debugging-port={port}',
        f'--user-data-dir={profile_path}',
        '--no-first-run', '--disable-default-apps', '--disable-extensions',
        '--disable-gpu', '--disable-software-rasterizer'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs.append(chrome_proc)
    
    time.sleep(8)
    
    # Test via subprocess
    try:
        r = subprocess.run(
            [PYTHON, TEST_SCRIPT, profile_path, str(port)],
            capture_output=True, text=True, timeout=70,
            env={**os.environ, 'PYTHONUTF8': '1'}
        )
        output = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else 'EMPTY'
        print(f'{output}', flush=True)
        
        if output == 'LOGADO':
            results['logado'].append({'profile': profile, 'port': port})
        elif output == 'NAO_LOGADO':
            results['sem_conta'].append(profile)
        elif output == 'CHROME_OFF':
            results['erro'].append(profile)
        else:
            results['erro'].append(profile)
    except subprocess.TimeoutExpired:
        print('TIMEOUT', flush=True)
        results['erro'].append(profile)
    except Exception as e:
        print(f'ERR: {e}', flush=True)
        results['erro'].append(profile)
    
    # Kill this Chrome
    try:
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(chrome_proc.pid)], 
                       capture_output=True, timeout=10)
    except:
        pass
    time.sleep(2)

print('\n' + '='*50, flush=True)
print(f'LOGADOS: {[x["profile"] for x in results["logado"]]}', flush=True)
print(f'SEM CONTA TIKTOK: {results["sem_conta"]}', flush=True)
print(f'ERRO: {results["erro"]}', flush=True)

with open(r'D:\hipercool-producao\logs\tiktok_scan_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('Salvo em logs/tiktok_scan_results.json', flush=True)
