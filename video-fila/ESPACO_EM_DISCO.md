# Espaço em disco do PC1: o que roda sozinho e o que fazer se apertar

Montado em 23/10/2026, a pedido da dona. Regras fixas:
- **Nunca** remover perfil do Chrome nem nada que obrigue a logar de novo (cookie, Login Data, Local State, Preferences). Só cache.
- Arquivo do Claude (`%LOCALAPPDATA%\Temp\claude`) só sai com mais de 7 dias.
- Nada é apagado sem estar no Drive, exceto cache e temporário.

## 1. Roda sozinho todo dia (`faxina_disco.py`, vigia geral, a partir das 4 h)
| O quê | Regra |
|---|---|
| Cache do Chrome normal (C:) e do cofre (D:) | só as pastas de cache; perfil aberto é pulado (fica pro dia seguinte) |
| Temp do Windows | arquivos com mais de 3 dias (fora do Claude) |
| Temp do Claude | mais de 7 dias |
| Cache do uv (Python) | limpa (C: e `D:\hipercool-materiais\python\uv_cache`) |
| `D:\veo\beta\pos_producao\tmp` | mais de 7 dias |
| Vozes RVC paradas | o `.index` vai pro Drive (`vozes_drive.py`); o `.pth` fica |
| Fontes do anime | `source.*` usado há 3 dias vai pro Drive (`fontes_drive.py`); sobra de download é apagada |
| Mapa do Drive | refeito (`MAPA_DRIVE.md`) |

O backup (`manhwa-react\scripts\backup_drive.py`) também tira do PC:
- o que já foi postado (catálogo);
- o hipercool postado (`hipercool_postados`) e o estoque longe da vez (`hipercool_estoque`);
- os Shorts do recap 3 dias depois de públicos.

## 2. Volta do Drive sozinho, na hora de usar (sem IA)
- **Voz RVC:** `voz_clonada` e `kaggle_conversor` chamam `vozes_drive.garantir(voz)`.
- **Fonte do anime:** `anime_fetch.download_video` chama `fontes_drive.trazer(pasta)` antes do YouTube.
- **16:9 do hipercool:** o compilado chama `fila._do_drive` (busca os `capNN.mp4`).
- **Capítulo do estoque do hipercool:** `fila._janela_local` traz quando entra nos próximos a sair (pasta com `_NO_DRIVE.txt`).

## 3. Se apertar (medidas, da mais simples pra mais forte)
1. **Janela do hipercool de 3 para 1 capítulo:** só o próximo de cada língua fica no PC; o resto do estoque vai pro Drive.
   - Já é **automático** com o D: abaixo de **10 GB** livres (`fila.JANELA_APERTO_GB`).
   - Para fixar à mão: em `D:\hipercool-videos\config\fila.json`, `"janela_local": 1` (voltar: `3` ou tirar a chave).
2. **Revisar os capítulos do hipercool "em revisão":** enquanto esperam a dona, ficam no PC (23/10 eram 9).
3. **Fechar perfis do Chrome normal** que não estão em uso: a faxina só limpa o cache de perfil fechado (~10 GB em 23/10).
4. **Vozes:** baixar `vozes_drive.DIAS` (7) ou `NOVA_DIAS` (14) manda mais vozes pro Drive.
5. **Fontes:** baixar `fontes_drive.DIAS` (3).
6. **`hipercool-materiais\veo\limpos` (4,4 GB):** estoque do reuso TikTok/Instagram. Só com decisão (o `catalogo.versao_limpa` exige o arquivo no PC).
7. **`amostras_voz` (4,8 GB):** material de treino de voz. Combinar com a sessão do clone de voz antes.

## 4. Achar e pegar algo no Drive à mão
Ver **`D:\video-fila\MAPA_DRIVE.md`**: pastas, quantidade, tamanho, data do último envio, o que é cada uma e os comandos do rclone. Para refazer o mapa na hora:

```
python D:\video-fila\mapa_drive.py
```
