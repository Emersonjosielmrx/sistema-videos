import os, sys, shutil
sys.path.insert(0, r"D:\hipercool-inferior-fix")
from bin.censura_visual import processar_painel

origem = r'D:\hipercool-inferior-fix\workspace\panels\the-meek-cat-cap06'
BASE_OUT = r'D:\downloads\will_protect_NOVOS_NIVEIS\CAP06_SEQUENCIA_COMPLETA'
os.makedirs(BASE_OUT, exist_ok=True)

# Garante que as censuras triggerem a nossa nova obra-prima
os.environ['CENSURA_MODO'] = 'sutil'

pins = sorted([f for f in os.listdir(origem) if f.endswith('.jpg') or f.endswith('.png')])
print(f'Rodando todo o Cap 06 ({len(pins)} paineis) na deteccao oficial SightEngine...')

censurados = 0

for f in pins:
    pin = os.path.join(origem, f)
    pout = os.path.join(BASE_OUT, f)
    
    # Roda a detecção igualzinho o pipeline original faz
    res = processar_painel(pin, pout, modo='hibrido')
    
    if res and res.get('nivel') not in ['intacto', 'falha', None]:
        print(f"[CENSURADO - {res['nivel'].upper()} | Score: {res['score']:.2f}] {f}")
        censurados += 1
    else:
        # Se tá intacto, copia a imagem original pra lá pra manter a leitura em ordem!
        shutil.copy2(pin, pout)
        score = res.get('score', 0) if res else 0
        if score > 0.15:
            print(f"[INOCENTE  | Score: {score:.2f}] {f}")

print(f'\nPronto! Capitulo 6 COMPLETO montado (com {censurados} fotos foscadas) em: {BASE_OUT}')
