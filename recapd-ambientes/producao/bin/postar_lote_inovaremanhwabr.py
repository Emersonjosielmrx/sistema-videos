"""postar_lote_inovaremanhwabr.py — Posta videos deitados pendentes no canal inovaremanhwabr.
Gera títulos virais PT-BR sem usar o nome real do anime (copyright).
"""
import json, os, sys, subprocess, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

POSTER = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
YOUTUBE = r"D:\recapd-ambientes\producao\bin\youtube_poster.py"
CANAL = "inovaremanhwabr"
POSTADOS_DIR = Path(r"D:\recapd-ambientes\producao\postados\anime\anime")

TITULOS = {
    "0h1eoBeR4Jk_Book_of_Ruth_Summary__A_Complete_Animate": {
        "titulo": "📖 A História MAIS ÉPICA Da Antiguidade Que Ninguém Te Contou!",
        "descricao": "Uma jovem viúva que perdeu tudo faz uma escolha impossível: abandonar sua terra natal para seguir uma sogra sem esperanças. O que acontece depois mudou a história pra sempre.\n\n#anime #recap #animebrasil #historia",
        "tags": "anime,recap,historia,anime brasil,animação"
    },
    "26EivpCPHnQ_Three_Kingdoms___OverSimplified": {
        "titulo": "⚔️ 3 REINOS EM GUERRA — O Caos Total Que Dividiu Um Império INTEIRO!",
        "descricao": "Três generais. Um trono. Zero piedade. O império mais poderoso do mundo se despedaçou e o que veio depois foi BRUTAL.\n\n#anime #recap #treskingdoms #animebrasil",
        "tags": "anime,recap,tres reinos,historia,anime brasil"
    },
    "7X-WbtJhojk_He_was_Bullied_As_the_Weakest_E_Rank_Hun": {
        "titulo": "💀 TODOS ZOAVAM O CAÇADOR RANK-E... Até Ele DESPERTAR Sozinho Numa Dungeon!",
        "descricao": "Ele era o mais fraco entre os caçadores. Ninguém dava nada por ele. Até que uma dungeon de duplo portão mudou TUDO — e o que ele se tornou deixou o mundo em PÂNICO.\n\n#anime #recap #manhwa #animebrasil",
        "tags": "anime,recap,manhwa,caçador,dungeon,anime brasil"
    },
    "AP_c0bbMmRI_He_Accidentally_Reincarnated_As_A_Lv_1_S": {
        "titulo": "🔄 ELE REENCARNA ACIDENTALMENTE COMO LV.1 — Mas Seu Poder Secreto É ABSURDO!",
        "descricao": "Reencarnado no corpo mais fraco possível. Level 1. Zero respeito. Mas o sistema que ele recebeu faz QUALQUER um tremer de medo.\n\n#anime #recap #isekai #manhwa #animebrasil",
        "tags": "anime,recap,isekai,reencarnação,manhwa,anime brasil"
    },
    "AQgMrIf0lMk_The_Ultimate__KPop_Demon_Hunters__Recap": {
        "titulo": "🎤 IDOLS QUE CAÇAM DEMÔNIOS?! O Grupo Mais INSANO Do Mundo Sobrenatural!",
        "descricao": "De dia, estrelas do pop. De noite, caçadores implacáveis do sobrenatural. Ninguém suspeitava... até os demônios descobrirem da pior forma.\n\n#anime #recap #kpop #demônios #animebrasil",
        "tags": "anime,recap,kpop,demônios,sobrenatural,anime brasil"
    },
    "DE-6M2buqV0_He_Was_The_Worst_In_His_Class_Until_He_U": {
        "titulo": "📚 ERA O PIOR DA TURMA ATÉ DESPERTAR UM PODER QUE NINGUÉM PODIA PARAR!",
        "descricao": "Último da classe. Piada da escola. Alvo de todos os valentões. Um dia ele descobre uma habilidade oculta que vira o jogo completamente.\n\n#anime #recap #manhwa #escola #animebrasil",
        "tags": "anime,recap,manhwa,escola,poder,anime brasil"
    },
    "PjYQlW_R9Ak_Moist_Meter___Cyberpunk_Edgerunners": {
        "titulo": "🌆 ELE VENDEU O CORPO POR IMPLANTES... E Perdeu a Alma Na Cidade Mais Suja Do Futuro!",
        "descricao": "Numa megalópole onde a carne humana vale menos que metal, um garoto de rua faz de tudo pra sobreviver — e o preço é mais alto do que ele imagina.\n\n#anime #recap #cyberpunk #futuro #animebrasil",
        "tags": "anime,recap,cyberpunk,ficção,futuro,anime brasil"
    },
    "W6dM0G3OaEc_Anime_vs_The_Rumbling": {
        "titulo": "🌍 O ESTRONDO! O DIA EM QUE MILHÕES DE TITÃS MARCHARAM SOBRE O MUNDO!",
        "descricao": "O plano mais insano já concebido: soltar TODOS os titãs colossais pra pisar em tudo. O mundo inteiro contra um único homem determinado a acabar com TUDO.\n\n#anime #recap #titan #estrondo #animebrasil",
        "tags": "anime,recap,titan,estrondo,animação,anime brasil"
    },
    "X5r9llgHfqo_Elemental_Explained_By_An_Asian": {
        "titulo": "🔥💧 FOGO E ÁGUA NUNCA DEVIAM SE ENCONTRAR... Mas O Amor Não Segue Regras!",
        "descricao": "Numa cidade onde cada elemento vive separado, dois opostos se encontram por acidente. O que deveria ser impossível se torna a história mais bonita já contada.\n\n#anime #recap #elementos #animação #animebrasil",
        "tags": "anime,recap,elementos,animação,romance,anime brasil"
    },
    "YczZRgRwuhA_BLACK_CLOVER_IN_37_MINUTES": {
        "titulo": "⚡ ELE NASCEU SEM MAGIA NUM MUNDO DE MAGOS... E Mesmo Assim NUNCA DESISTIU!",
        "descricao": "Sem um pingo de poder mágico, cercado por gênios. Todos o chamavam de inútil. Mas a determinação dele era mais forte que QUALQUER feitiço.\n\n#anime #recap #magia #animebrasil",
        "tags": "anime,recap,magia,determinação,anime brasil"
    },
    "YfDVrAfh4dU_Nasceu_Sem_Talento_Magico": {
        "titulo": "✨ NASCEU SEM TALENTO MÁGICO... Mas Encontrou Um Poder Que NENHUM Mago Tinha!",
        "descricao": "Num mundo onde magia é tudo, ele veio ao mundo sem NADA. Chamado de fracasso pela própria família. Até descobrir que seu 'defeito' era na verdade a arma mais poderosa.\n\n#anime #recap #manhwa #magia #animebrasil",
        "tags": "anime,recap,manhwa,magia,talento,anime brasil"
    },
    "kP0KdA-s128_Boy_is_Reincarnated_As_The_Weakest_F_Ran": {
        "titulo": "🗡️ REENCARNADO COMO RANK-F! O Mais Fraco Que Virou PESADELO Dos Mais Fortes!",
        "descricao": "Rank F. O fundo do poço. Ninguém apostava nele. Mas com memórias de outra vida e uma vontade de ferro, ele subiu ranking por ranking até fazer os S-Rank tremerem.\n\n#anime #recap #manhwa #isekai #animebrasil",
        "tags": "anime,recap,manhwa,isekai,reencarnação,anime brasil"
    },
    "lknNsZgzG1g_SPACE_KING_1___Pilot": {
        "titulo": "🚀 REI DO ESPAÇO — O Piloto Que Desafiou Um Império INTEIRO Sozinho!",
        "descricao": "No espaço profundo, um piloto rebelde recebe uma missão impossível. O que ele descobre pode salvar — ou destruir — civilizações inteiras.\n\n#anime #recap #espaço #ficção #animebrasil",
        "tags": "anime,recap,espaço,ficção científica,piloto,anime brasil"
    },
    "may2s9j4RLk_The_myth_behind_the_Chinese_zodiac___Meg": {
        "titulo": "🐉 O MITO POR TRÁS DO ZODÍACO CHINÊS — A Corrida Que Definiu 12 Destinos!",
        "descricao": "12 animais. Uma corrida épica. E o rato que trapaceou de um jeito GENIAL. A verdadeira história por trás do zodíaco chinês que todo mundo deveria conhecer.\n\n#anime #recap #zodíaco #mito #animebrasil",
        "tags": "anime,recap,zodíaco,mito,china,anime brasil"
    },
    "yI7eqsXSoWU_CYBERPUNK__EDGERUNNERS_IS_RUTHLESS": {
        "titulo": "💔 A ANIMAÇÃO MAIS CRUEL QUE VOCÊ VAI ASSISTIR — Sem Piedade, Sem Final Feliz!",
        "descricao": "Eles te fazem amar os personagens... pra depois destruir cada um deles na sua frente. A história mais brutal e emocionante da ficção futurista.\n\n#anime #recap #cyberpunk #animação #animebrasil",
        "tags": "anime,recap,cyberpunk,animação,brutal,anime brasil"
    },
}

def escolher_video(pasta):
    """Prefere _ads quando existe."""
    ads = pasta / "final_anime_deitado_ads.mp4"
    normal = pasta / "final_anime_deitado.mp4"
    if ads.exists():
        return ads
    if normal.exists():
        return normal
    return None

def main():
    postados = 0
    erros = 0
    limite = False

    for nome_pasta, meta in TITULOS.items():
        if limite:
            break

        pasta = POSTADOS_DIR / nome_pasta
        video = escolher_video(pasta)

        if not video:
            print(f"[SKIP] {nome_pasta} — sem video")
            continue

        print(f"\n[{postados+1}] Postando no {CANAL}: {meta['titulo'][:60]}...")
        print(f"     Arquivo: {video} ({video.stat().st_size // (1024*1024)}MB)")

        cmd = [
            POSTER, YOUTUBE,
            "--video", str(video),
            "--titulo", meta["titulo"],
            "--descricao", meta["descricao"],
            "--tags", meta["tags"],
            "--canal", CANAL,
        ]

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
            out = result.stdout.strip()
            err = result.stderr.strip()

            if "POSTADO" in out:
                print(f"     ✅ {out}")
                postados += 1
            elif "uploadLimitExceeded" in (out + err) or "LIMITE REAL" in (out + err):
                print(f"     🛑 LIMITE DO CANAL ATINGIDO")
                limite = True
            else:
                print(f"     ❌ ERRO: {out}")
                if err:
                    print(f"     stderr: {err[:200]}")
                erros += 1

        except subprocess.TimeoutExpired:
            print(f"     ⏰ TIMEOUT (600s)")
            erros += 1
        except Exception as e:
            print(f"     ❌ {e}")
            erros += 1

        time.sleep(3)

    print(f"\n{'='*60}")
    print(f"RESUMO: {postados} postados | {erros} erros | limite={'SIM' if limite else 'NAO'}")
    print(f"Canal: {CANAL}")

if __name__ == "__main__":
    main()
