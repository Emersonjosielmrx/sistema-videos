# Teste 03/11: 1 Short renderizado no Kaggle de ponta a ponta (fila_shorts -> conta de curto -> volta)
import os, sys, logging, json
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
os.chdir(r"D:\recapd-ambientes\producao\bin")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    filename=r"D:\hipercool-materiais\_teste_kaggle_short.log", encoding="utf-8")
from pathlib import Path
import anime_voz_clonada, lote_shorts_kaggle
work = Path(r"D:\recapd-ambientes\producao\workspace\anime\J_0l755RUfU_Eu_alugo_gatos_para_ajudar_as_pessoas__d")
clone = anime_voz_clonada.proxima(anime_voz_clonada.nicho_do_video("curiosidades", None))
env = dict(os.environ, PYTHONUTF8="1")
if clone:
    env.update(VOZ_CLONADA=clone[0], VOZ_CLONADA_BASE=clone[1], VOZ_CLONADA_VERSAO="2",
               VOZ_CLONADA_CONFIG=anime_voz_clonada.config_da_vez())
logging.info(f"TESTE: voz {clone}")
os.environ["SHORTS_KAGGLE_ESPERA_MIN"] = "120"
vf = work / "final_kaggle_teste.mp4"
ok = lote_shorts_kaggle.renderizar(work, work / "source.mp4", work / "roteiro.txt",
                                   {"id": "J_0l755RUfU", "title": "Eu alugo gatos para ajudar as pessoas"},
                                   "native", env, vf)
logging.info(f"TESTE RESULTADO: ok={ok} arquivo={vf if vf.exists() else None}")
