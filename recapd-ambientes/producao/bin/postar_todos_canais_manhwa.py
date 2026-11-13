"""postar_todos_canais_manhwa.py — Posta deitados em TODOS os canais manhwa que ainda não receberam.
Roda canal por canal, até bater limite de cada um.
"""
import json, os, sys, subprocess, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

POSTER = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
YOUTUBE = r"D:\recapd-ambientes\producao\bin\youtube_poster.py"
POSTADOS_DIR = Path(r"D:\recapd-ambientes\producao\postados\anime\anime")

CANAIS = [
    "Animescomia",
    "Inovare Manhwa esp",
    "inovare Manhwa french",
    "Inovaremanhwaversehindi",
    "Inovare Manhwa eng",
    "inovaremanhwaverseita",
    "inovare manhwa verse ru",
    "Inovaremanhwaversethai",
    "@Inovaremanhwaversethai",
]

TITULOS = {
    "0h1eoBeR4Jk_Book_of_Ruth_Summary__A_Complete_Animate": {
        "titulo": "A História MAIS ÉPICA Da Antiguidade Que Ninguém Te Contou!",
        "descricao": "Uma jovem viúva que perdeu tudo faz uma escolha impossível.\n\n#anime #recap #animebrasil",
        "tags": "anime,recap,historia,animação"
    },
    "26EivpCPHnQ_Three_Kingdoms___OverSimplified": {
        "titulo": "3 REINOS EM GUERRA — O Caos Total Que Dividiu Um Império!",
        "descricao": "Três generais. Um trono. Zero piedade.\n\n#anime #recap #animebrasil",
        "tags": "anime,recap,tres reinos,historia"
    },
    "7X-WbtJhojk_He_was_Bullied_As_the_Weakest_E_Rank_Hun": {
        "titulo": "TODOS ZOAVAM O CAÇADOR RANK-E... Até Ele DESPERTAR!",
        "descricao": "Ele era o mais fraco entre os caçadores. Até que uma dungeon mudou TUDO.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,caçador,dungeon"
    },
    "AP_c0bbMmRI_He_Accidentally_Reincarnated_As_A_Lv_1_S": {
        "titulo": "ELE REENCARNA COMO LV.1 — Mas Seu Poder Secreto É ABSURDO!",
        "descricao": "Reencarnado no corpo mais fraco possível. Mas o sistema que ele recebeu faz QUALQUER um tremer.\n\n#anime #recap #isekai",
        "tags": "anime,recap,isekai,reencarnação,manhwa"
    },
    "AQgMrIf0lMk_The_Ultimate__KPop_Demon_Hunters__Recap": {
        "titulo": "IDOLS QUE CAÇAM DEMÔNIOS?! O Grupo Mais INSANO!",
        "descricao": "De dia, estrelas do pop. De noite, caçadores do sobrenatural.\n\n#anime #recap #kpop",
        "tags": "anime,recap,kpop,demônios,sobrenatural"
    },
    "DE-6M2buqV0_He_Was_The_Worst_In_His_Class_Until_He_U": {
        "titulo": "ERA O PIOR DA TURMA ATÉ DESPERTAR UM PODER IMPOSSÍVEL!",
        "descricao": "Último da classe. Piada da escola. Até descobrir uma habilidade oculta.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,escola,poder"
    },
    "PjYQlW_R9Ak_Moist_Meter___Cyberpunk_Edgerunners": {
        "titulo": "ELE VENDEU O CORPO POR IMPLANTES... E Perdeu a Alma!",
        "descricao": "Numa megalópole onde carne vale menos que metal, um garoto faz de tudo pra sobreviver.\n\n#anime #recap #cyberpunk",
        "tags": "anime,recap,cyberpunk,futuro"
    },
    "W6dM0G3OaEc_Anime_vs_The_Rumbling": {
        "titulo": "O DIA EM QUE MILHÕES DE TITÃS MARCHARAM SOBRE O MUNDO!",
        "descricao": "O plano mais insano: soltar TODOS os titãs colossais.\n\n#anime #recap #titan",
        "tags": "anime,recap,titan,animação"
    },
    "X5r9llgHfqo_Elemental_Explained_By_An_Asian": {
        "titulo": "FOGO E ÁGUA NUNCA DEVIAM SE ENCONTRAR... Mas O Amor Não Segue Regras!",
        "descricao": "Dois opostos se encontram por acidente. Uma história impossível e linda.\n\n#anime #recap #animação",
        "tags": "anime,recap,elementos,animação,romance"
    },
    "YczZRgRwuhA_BLACK_CLOVER_IN_37_MINUTES": {
        "titulo": "ELE NASCEU SEM MAGIA... E Mesmo Assim NUNCA DESISTIU!",
        "descricao": "Sem poder mágico, cercado por gênios. Mas a determinação era mais forte.\n\n#anime #recap #magia",
        "tags": "anime,recap,magia,determinação"
    },
    "YfDVrAfh4dU_Nasceu_Sem_Talento_Magico": {
        "titulo": "NASCEU SEM TALENTO MÁGICO... Mas Encontrou Um Poder Único!",
        "descricao": "Num mundo onde magia é tudo, ele veio sem NADA. Até descobrir seu 'defeito' era a arma mais poderosa.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,magia,talento"
    },
    "kP0KdA-s128_Boy_is_Reincarnated_As_The_Weakest_F_Ran": {
        "titulo": "REENCARNADO COMO RANK-F! O Mais Fraco Que Virou PESADELO!",
        "descricao": "Rank F. Ninguém apostava nele. Mas com memórias de outra vida, subiu até fazer os S-Rank tremerem.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,isekai,reencarnação"
    },
    "lknNsZgzG1g_SPACE_KING_1___Pilot": {
        "titulo": "REI DO ESPAÇO — O Piloto Que Desafiou Um Império Sozinho!",
        "descricao": "No espaço profundo, um piloto rebelde recebe uma missão impossível.\n\n#anime #recap #espaço",
        "tags": "anime,recap,espaço,ficção científica"
    },
    "may2s9j4RLk_The_myth_behind_the_Chinese_zodiac___Meg": {
        "titulo": "O MITO DO ZODÍACO CHINÊS — A Corrida Que Definiu 12 Destinos!",
        "descricao": "12 animais. Uma corrida épica. A verdadeira história do zodíaco chinês.\n\n#anime #recap #zodíaco",
        "tags": "anime,recap,zodíaco,mito,china"
    },
    "yI7eqsXSoWU_CYBERPUNK__EDGERUNNERS_IS_RUTHLESS": {
        "titulo": "A ANIMAÇÃO MAIS CRUEL — Sem Piedade, Sem Final Feliz!",
        "descricao": "Eles te fazem amar os personagens... pra depois destruir cada um. A história mais brutal.\n\n#anime #recap #cyberpunk",
        "tags": "anime,recap,cyberpunk,animação,brutal"
    },
}

def escolher_video(pasta):
    ads = pasta / "final_anime_deitado_ads.mp4"
    normal = pasta / "final_anime_deitado.mp4"
    if ads.exists():
        return ads
    if normal.exists():
        return normal
    return None

def postar_no_canal(canal, videos_meta):
    postados = 0
    limite = False
    erros = 0

    print(f"\n{'='*60}")
    print(f"CANAL: {canal}")
    print(f"{'='*60}")

    for nome_pasta, meta in videos_meta.items():
        if limite:
            break

        pasta = POSTADOS_DIR / nome_pasta
        video = escolher_video(pasta)
        if not video:
            continue

        print(f"  [{postados+1}] {meta['titulo'][:55]}... ({video.stat().st_size//(1024*1024)}MB)")

        cmd = [
            POSTER, YOUTUBE,
            "--video", str(video),
            "--titulo", meta["titulo"],
            "--descricao", meta["descricao"],
            "--tags", meta["tags"],
            "--canal", canal,
        ]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
            out = result.stdout.strip()
            err = result.stderr.strip()

            if "POSTADO" in out:
                print(f"    ✅ {out[:120]}")
                postados += 1
            elif "uploadLimitExceeded" in (out + err) or "LIMITE REAL" in (out + err):
                print(f"    🛑 LIMITE ATINGIDO")
                limite = True
            elif "is disabled" in (out + err):
                print(f"    ⚠️ API DESABILITADA neste canal")
                limite = True
            elif "invalid_grant" in (out + err) or "Token has been" in (out + err):
                print(f"    ⚠️ TOKEN EXPIRADO")
                limite = True
            else:
                print(f"    ❌ {(out or err)[:200]}")
                erros += 1
        except subprocess.TimeoutExpired:
            print(f"    ⏰ TIMEOUT")
            erros += 1
        except Exception as e:
            print(f"    ❌ {e}")
            erros += 1

        time.sleep(3)

    print(f"  → {canal}: {postados} postados | {erros} erros | limite={'SIM' if limite else 'NAO'}")
    return postados, erros, limite

def main():
    total_postados = 0
    total_erros = 0
    resumo_canais = {}

    for canal in CANAIS:
        p, e, lim = postar_no_canal(canal, TITULOS)
        total_postados += p
        total_erros += e
        resumo_canais[canal] = {"postados": p, "erros": e, "limite": lim}

    print(f"\n{'='*60}")
    print(f"RESUMO GERAL")
    print(f"{'='*60}")
    for canal, info in resumo_canais.items():
        status = "LIMITE" if info["limite"] else "OK"
        print(f"  {canal:40s} {info['postados']:3d} postados | {status}")
    print(f"\n  TOTAL: {total_postados} postados | {total_erros} erros")
    print(f"  Canais tentados: {len(CANAIS)}")

if __name__ == "__main__":
    main()
