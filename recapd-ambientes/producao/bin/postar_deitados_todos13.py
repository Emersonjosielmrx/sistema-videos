#!/usr/bin/env python3
"""Posta deitados em TODOS os 13 canais manhwa ate limite."""
import json, os, sys, subprocess, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

POSTER = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
YOUTUBE = r"D:\recapd-ambientes\producao\bin\youtube_poster.py"
POSTADOS_DIR = Path(r"D:\recapd-ambientes\producao\postados\anime\anime")

CANAIS = [
    "InovareManhwaVerse",
    "inovaremanhwabr",
    "Animescomia",
    "Inovare Manhwa esp",
    "inovare Manhwa french",
    "Inovaremanhwaversehindi",
    "YouTube inovaremanhwaverseind",
    "Inovare Manhwa eng ",
    "inovaremanhwaverseita",
    "inovare manhwa verse ru",
    "Inovaremanhwaversethai",
    "YouTube inovaremanhwaverseviet",
    "@Inovaremanhwaversethai",
]

TITULOS = {
    "0h1eoBeR4Jk_Book_of_Ruth_Summary__A_Complete_Animate": {
        "titulo": "A Historia MAIS EPICA Da Antiguidade Que Ninguem Te Contou!",
        "descricao": "Uma jovem viuva que perdeu tudo faz uma escolha impossivel.\n\n#anime #recap #animebrasil",
        "tags": "anime,recap,historia,animacao"
    },
    "26EivpCPHnQ_Three_Kingdoms___OverSimplified": {
        "titulo": "3 REINOS EM GUERRA - O Caos Total Que Dividiu Um Imperio!",
        "descricao": "Tres generais. Um trono. Zero piedade.\n\n#anime #recap #animebrasil",
        "tags": "anime,recap,tres reinos,historia"
    },
    "7X-WbtJhojk_He_was_Bullied_As_the_Weakest_E_Rank_Hun": {
        "titulo": "TODOS ZOAVAM O CACADOR RANK-E... Ate Ele DESPERTAR!",
        "descricao": "Ele era o mais fraco entre os cacadores. Ate que uma dungeon mudou TUDO.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,cacador,dungeon"
    },
    "AP_c0bbMmRI_He_Accidentally_Reincarnated_As_A_Lv_1_S": {
        "titulo": "ELE REENCARNA COMO LV.1 - Mas Seu Poder Secreto E ABSURDO!",
        "descricao": "Reencarnado no corpo mais fraco possivel. Mas o sistema que ele recebeu faz QUALQUER um tremer.\n\n#anime #recap #isekai",
        "tags": "anime,recap,isekai,reencarnacao,manhwa"
    },
    "AQgMrIf0lMk_The_Ultimate__KPop_Demon_Hunters__Recap": {
        "titulo": "IDOLS QUE CACAM DEMONIOS?! O Grupo Mais INSANO!",
        "descricao": "De dia, estrelas do pop. De noite, cacadores do sobrenatural.\n\n#anime #recap #kpop",
        "tags": "anime,recap,kpop,demonios,sobrenatural"
    },
    "DE-6M2buqV0_He_Was_The_Worst_In_His_Class_Until_He_U": {
        "titulo": "ERA O PIOR DA TURMA ATE DESPERTAR UM PODER IMPOSSIVEL!",
        "descricao": "Ultimo da classe. Piada da escola. Ate descobrir uma habilidade oculta.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,escola,poder"
    },
    "PjYQlW_R9Ak_Moist_Meter___Cyberpunk_Edgerunners": {
        "titulo": "ELE VENDEU O CORPO POR IMPLANTES... E Perdeu a Alma!",
        "descricao": "Numa megalopole onde carne vale menos que metal, um garoto faz de tudo pra sobreviver.\n\n#anime #recap #cyberpunk",
        "tags": "anime,recap,cyberpunk,futuro"
    },
    "W6dM0G3OaEc_Anime_vs_The_Rumbling": {
        "titulo": "O DIA EM QUE MILHOES DE TITAS MARCHARAM SOBRE O MUNDO!",
        "descricao": "O plano mais insano: soltar TODOS os titas colossais.\n\n#anime #recap #titan",
        "tags": "anime,recap,titan,animacao"
    },
    "X5r9llgHfqo_Elemental_Explained_By_An_Asian": {
        "titulo": "FOGO E AGUA NUNCA DEVIAM SE ENCONTRAR... Mas O Amor Nao Segue Regras!",
        "descricao": "Dois opostos se encontram por acidente. Uma historia impossivel e linda.\n\n#anime #recap #animacao",
        "tags": "anime,recap,elementos,animacao,romance"
    },
    "YczZRgRwuhA_BLACK_CLOVER_IN_37_MINUTES": {
        "titulo": "ELE NASCEU SEM MAGIA... E Mesmo Assim NUNCA DESISTIU!",
        "descricao": "Sem poder magico, cercado por genios. Mas a determinacao era mais forte.\n\n#anime #recap #magia",
        "tags": "anime,recap,magia,determinacao"
    },
    "YfDVrAfh4dU_Nasceu_Sem_Talento_Magico": {
        "titulo": "NASCEU SEM TALENTO MAGICO... Mas Encontrou Um Poder Unico!",
        "descricao": "Num mundo onde magia e tudo, ele veio sem NADA. Ate descobrir seu defeito era a arma mais poderosa.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,magia,talento"
    },
    "kP0KdA-s128_Boy_is_Reincarnated_As_The_Weakest_F_Ran": {
        "titulo": "REENCARNADO COMO RANK-F! O Mais Fraco Que Virou PESADELO!",
        "descricao": "Rank F. Ninguem apostava nele. Mas com memorias de outra vida, subiu ate fazer os S-Rank tremerem.\n\n#anime #recap #manhwa",
        "tags": "anime,recap,manhwa,isekai,reencarnacao"
    },
    "lknNsZgzG1g_SPACE_KING_1___Pilot": {
        "titulo": "REI DO ESPACO - O Piloto Que Desafiou Um Imperio Sozinho!",
        "descricao": "No espaco profundo, um piloto rebelde recebe uma missao impossivel.\n\n#anime #recap #espaco",
        "tags": "anime,recap,espaco,ficcao cientifica"
    },
    "may2s9j4RLk_The_myth_behind_the_Chinese_zodiac___Meg": {
        "titulo": "O MITO DO ZODIACO CHINES - A Corrida Que Definiu 12 Destinos!",
        "descricao": "12 animais. Uma corrida epica. A verdadeira historia do zodiaco chines.\n\n#anime #recap #zodiaco",
        "tags": "anime,recap,zodiaco,mito,china"
    },
    "yI7eqsXSoWU_CYBERPUNK__EDGERUNNERS_IS_RUTHLESS": {
        "titulo": "A ANIMACAO MAIS CRUEL - Sem Piedade, Sem Final Feliz!",
        "descricao": "Eles te fazem amar os personagens... pra depois destruir cada um. A historia mais brutal.\n\n#anime #recap #cyberpunk",
        "tags": "anime,recap,cyberpunk,animacao,brutal"
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

total_geral = 0
for canal in CANAIS:
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"CANAL: {canal}")
    print(f"{sep}")
    postados = 0
    limite = False
    for nome_pasta, meta in TITULOS.items():
        if limite:
            break
        pasta = POSTADOS_DIR / nome_pasta
        video = escolher_video(pasta)
        if not video:
            continue
        sz = video.stat().st_size // (1024 * 1024)
        tit_short = meta["titulo"][:55]
        print(f"  [{postados+1}] {tit_short}... ({sz}MB)")
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
            result = subprocess.run(
                cmd, capture_output=True, text=True, env=env,
                timeout=600, encoding="utf-8", errors="replace"
            )
            out = (result.stdout or "").strip()
            err = (result.stderr or "").strip()
            combined = out + err
            if "POSTADO" in combined:
                url = ""
                for tok in combined.split():
                    if "youtu.be/" in tok:
                        url = tok
                        break
                print(f"    OK {url}")
                postados += 1
            elif "uploadLimitExceeded" in combined or "quotaExceeded" in combined:
                print("    LIMITE ATINGIDO")
                limite = True
            elif "is disabled" in combined:
                print("    API DESABILITADA")
                limite = True
            elif "invalid_grant" in combined or "Unauthorized" in combined:
                print("    TOKEN/AUTH FALHOU")
                limite = True
            else:
                print(f"    ERRO: {combined[:200]}")
        except subprocess.TimeoutExpired:
            print("    TIMEOUT")
        except Exception as e:
            print(f"    ERRO: {e}")
        time.sleep(2)
    total_geral += postados
    lim_txt = "SIM" if limite else "NAO"
    print(f"  => {canal}: {postados} postados | limite={lim_txt}")

print(f"\n=== TOTAL GERAL DEITADOS: {total_geral} ===")
