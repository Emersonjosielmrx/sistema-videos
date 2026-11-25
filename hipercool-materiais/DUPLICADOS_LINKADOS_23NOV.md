# Copias duplicadas trocadas por hardlinks (23/11/2026)

Cada linha abaixo era uma COPIA identica (sha1 conferido) de outro arquivo do D:. Foi trocada por um hardlink:
o caminho antigo continua existindo e abre exatamente o mesmo conteudo, mas o espaco em disco e usado uma vez so.

- Scripts que buscam o caminho antigo NAO dao erro.
- O espaco so volta quando TODOS os nomes do arquivo forem apagados (apagar um nome nao apaga o outro).
- Os dois nomes sao o mesmo arquivo: se um programa gravar DENTRO do arquivo, os dois mudam.
- Voltar a ter copia independente de um caminho: `$t="$p.tmp"; Copy-Item $p $t; Remove-Item $p; Move-Item $t $p`

Liberado: 5.61 GB | trocados: 143 | lista completa e pulados: C:\Users\Haylla\AppData\Local\Temp\claude\res\p_linkar.txt

| MB | caminho (hardlink) | mesmo arquivo que |
|---:|---|---|
| 461.1 | `D:\hipercool-materiais\models\huggingface\hub\models--Systran--faster-whisper-small\blobs\3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671` | `D:\hipercool-materiais\models\whisper\blobs\42\429ffc84492c1122da005d7274fc397bf142fe12066eb7e4612dc25c579db2ea` |
| 461.1 | `D:\caches\huggingface\faster-whisper\blobs\42\429ffc84492c1122da005d7274fc397bf142fe12066eb7e4612dc25c579db2ea` | `D:\hipercool-materiais\models\whisper\blobs\42\429ffc84492c1122da005d7274fc397bf142fe12066eb7e4612dc25c579db2ea` |
| 330.4 | `D:\caches\huggingface\hub\blobs\c8\c8fbb9045765cfcd09a7dfc2fc1212bc67ae7da796b71f6f60ebd1a8a24fc1ae` | `D:\hipercool-materiais\models\huggingface\hub\blobs\c8\c8fbb9045765cfcd09a7dfc2fc1212bc67ae7da796b71f6f60ebd1a8a24fc1ae` |
| 186.2 | `D:\hipercool-materiais\models\rvc\vozes\rem\rem.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\rem\added_IVF1584_Flat_nprobe_1_rem_v2.index` |
| 94.6 | `D:\hipercool-materiais\models\huggingface\hub\blobs\5e\5e62aeb30213d75799f02269c41d8084fa078c2f88fd3540faef2a46b5ec2842` | `D:\hipercool-materiais\modelos\hf\hub\models--depth-anything--Depth-Anything-V2-Small-hf\blobs\3152477ce0d8d6978d76b995120de97cb5b928701fd0f817769f59e249a16b70` |
| 90.3 | `D:\hipercool-materiais\models\rvc\vozes\pato_donald_galvan\pato_donald_galvan.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\pato_donald_galvan\added_IVF768_Flat_nprobe_1_patodonald_v2.index` |
| 82.6 | `D:\hipercool-materiais\models\rvc\vozes\anya_forger_e500\anya_forger_e500.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\anya_forger_e500\Anya Forger BRe500.index` |
| 72.0 | `D:\hipercool-materiais\models\huggingface\hub\models--Systran--faster-whisper-tiny\blobs\dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1` | `D:\hipercool-materiais\models\whisper\models--Systran--faster-whisper-tiny\blobs\dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1` |
| 67.5 | `D:\hipercool-materiais\models\rvc\vozes\optimus_prime\optimus_prime.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\optimus_prime\optimus_prime_v4.index` |
| 65.7 | `D:\hipercool-materiais\models\rvc\vozes\jonah_jameson_santa_cruz\jonah_jameson_santa_cruz.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\jonah_jameson_santa_cruz\added_IVF559_Flat_nprobe_1_jonah-jameson_v2.index` |
| 57.5 | `D:\hipercool-materiais\models\rvc\vozes\chaves_chapolin\chaves_chapolin.index` | `D:\hipercool-materiais\models\rvc\vozes\chapolin_colorado\chapolin_colorado.index` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\anya_forger\anya_forger.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\anya_forger\AnyaForgerLolipopBR69.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\anya_forger_e500\anya_forger_e500.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\anya_forger_e500\Anya Forger BRe500.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\chopper\chopper.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\chopper\chopperonepiece.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\buggy\buggy.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\buggy\buggyopalhaco.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\jack_sparrow\jack_sparrow.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\jack_sparrow\jacksparrow.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\hinata_hyuga\hinata_hyuga.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\hinata_hyuga\hinatahyuga.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\goten_gohan_crianca\goten_gohan_crianca.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\goten_gohan_crianca\gohangoten.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\sonic_manolo_rey\sonic_manolo_rey.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\sonic_manolo_rey\sonicfilme.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\magneto_santa_cruz\magneto_santa_cruz.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\magneto_santa_cruz\magneto.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\emilia\emilia.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\emilia\emilia.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\shadow_cid\shadow_cid.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\shadow_cid\shadow.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\subaru\subaru.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\subaru\subaru.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\loid_forger\loid_forger.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\loid_forger\loide.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\muzan\muzan.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\muzan\muzan.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\ram\ram.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\ram\ram.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\rem\rem.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\rem\rem.pth` |
| 54.9 | `D:\hipercool-materiais\models\rvc\vozes\yor_forger\yor_forger.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\yor_forger\yor.pth` |
| 53.6 | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\jarvis\jarvis_v4.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\visao_vingadores\visao_vingadores_v4.pth` |
| 53.6 | `D:\hipercool-materiais\models\rvc\vozes\optimus_prime\optimus_prime.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\optimus_prime\optimus_prime_v4.pth` |
| 52.7 | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\pato_donald_galvan\patodonald_e160_s3360.pth` | `D:\hipercool-materiais\models\rvc\vozes\pato_donald\pato_donald.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\pato_donald_galvan\pato_donald_galvan.pth` | `D:\hipercool-materiais\models\rvc\vozes\pato_donald\pato_donald.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\jonah_jameson_santa_cruz\jonah_jameson_santa_cruz.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\jonah_jameson_santa_cruz\jonah-jameson.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\sam_winchester\sam_winchester.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\sam_winchester\samwinchester.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\barba_branca\barba_branca.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\barba_branca\barbabranca.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\pan_dbz\pan_dbz.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\pan_dbz\mynewmodel.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\pedro_bial\pedro_bial.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\pedro_bial\PedroBial.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\chaves_chapolin\chaves_chapolin.pth` | `D:\hipercool-materiais\models\rvc\vozes\chapolin_colorado\chapolin_colorado.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\saitama\saitama.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\saitama\Saitama.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\freeza\freeza.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\freeza\freeza.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\julius\julius.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\julius\julius.pth` |
| 52.7 | `D:\hipercool-materiais\models\rvc\vozes\sukuna\sukuna.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\sukuna\sukuna.pth` |
| 52.6 | `D:\hipercool-materiais\models\rvc\vozes\enel\enel.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\enel\enel.pth` |
| 52.6 | `D:\hipercool-materiais\models\rvc\vozes\asta\asta.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\asta\asta.pth` |
| 52.6 | `D:\hipercool-materiais\models\rvc\vozes\dean_winchester\dean_winchester.pth` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\dean_winchester\dean.pth` |
| 50.3 | `D:\hipercool-materiais\models\rvc\vozes\loid_forger\loid_forger.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\loid_forger\added_IVF428_Flat_nprobe_1_loide_v2.index` |
| 49.7 | `D:\hipercool-materiais\models\rvc\vozes\magneto_santa_cruz\magneto_santa_cruz.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\magneto_santa_cruz\added_IVF423_Flat_nprobe_1_magneto_v2.index` |
| 49.4 | `D:\hipercool-materiais\models\rvc\vozes\ram\ram.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\ram\added_IVF420_Flat_nprobe_1_ram_v2.index` |
| 48.9 | `D:\hipercool-materiais\models\rvc\vozes\goten_gohan_crianca\goten_gohan_crianca.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\goten_gohan_crianca\added_IVF416_Flat_nprobe_1_gohangoten_v2.index` |
| 48.9 | `D:\hipercool-materiais\models\rvc\vozes\buggy\buggy.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\buggy\added_IVF416_Flat_nprobe_1_buggyopalhaco_v2.index` |
| 48.9 | `D:\hipercool-materiais\models\rvc\vozes\muzan\muzan.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\muzan\added_IVF416_Flat_nprobe_1_muzan_v2.index` |
| 48.9 | `D:\hipercool-materiais\models\rvc\vozes\chopper\chopper.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\chopper\added_IVF416_Flat_nprobe_1_chopperonepiece_v2.index` |
| 48.9 | `D:\hipercool-materiais\models\rvc\vozes\sonic_manolo_rey\sonic_manolo_rey.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\sonic_manolo_rey\added_IVF416_Flat_nprobe_1_sonicfilme_v2.index` |
| 47.3 | `D:\hipercool-materiais\models\rvc\vozes\emilia\emilia.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\emilia\added_IVF402_Flat_nprobe_1_emilia_v2.index` |
| 46.8 | `D:\hipercool-materiais\models\rvc\vozes\saitama\saitama.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\saitama\added_IVF397_Flat_nprobe_1_Saitama_v2.index` |
| 46.5 | `D:\hipercool-materiais\models\rvc\vozes\hinata_hyuga\hinata_hyuga.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\hinata_hyuga\added_IVF395_Flat_nprobe_1_hinatahyuga_v2.index` |
| 44.3 | `D:\hipercool-materiais\models\rvc\vozes\jack_sparrow\jack_sparrow.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\jack_sparrow\added_IVF376_Flat_nprobe_1_jacksparrow_v2.index` |
| 42.5 | `D:\caches\huggingface\hub\blobs\0f\0f670ec237dda1a0de7e0b5163f188df2d0410896e853aa5c640fa99cb875c54` | `D:\hipercool-materiais\models\anime_face_yolov8s.onnx` |
| 42.4 | `D:\hipercool-materiais\models\rvc\vozes\shadow_cid\shadow_cid.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\shadow_cid\added_IVF360_Flat_nprobe_1_shadow_v2.index` |
| 40.7 | `D:\hipercool-materiais\models\rvc\vozes\barba_branca\barba_branca.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\barba_branca\added_IVF346_Flat_nprobe_1_barbabranca_v2.index` |
| 38.1 | `D:\hipercool-materiais\models\rvc\vozes\asta\asta.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\asta\added_IVF323_Flat_nprobe_1_asta_v2.index` |
| 37.7 | `D:\hipercool-materiais\models\rvc\vozes\yor_forger\yor_forger.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\yor_forger\added_IVF321_Flat_nprobe_1_yor_v2.index` |
| 37.6 | `D:\hipercool-materiais\models\rvc\vozes\enel\enel.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\enel\added_IVF320_Flat_nprobe_1_enel_v2.index` |
| 36.9 | `D:\hipercool-materiais\models\rvc\vozes\dean_winchester\dean_winchester.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\dean_winchester\added_IVF313_Flat_nprobe_1_dean_v2.index` |
| 33.8 | `D:\hipercool-materiais\models\rvc\vozes\freeza\freeza.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\freeza\added_IVF287_Flat_nprobe_1_freeza_v2.index` |
| 32.4 | `D:\hipercool-materiais\models\rvc\vozes\subaru\subaru.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\subaru\added_IVF275_Flat_nprobe_1_subaru_v2.index` |
| 32.2 | `D:\kit3d-producao\_conferir_3d\1117_0302_tamanho-das-veias.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-tamanho-das-veias\video_sem_capa.mp4` |
| 31.6 | `D:\hipercool-materiais\models\rvc\vozes\sam_winchester\sam_winchester.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\sam_winchester\added_IVF268_Flat_nprobe_1_samwinchester_v2.index` |
| 29.5 | `D:\hipercool-materiais\models\rvc\vozes\pedro_bial\pedro_bial.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\pedro_bial\added_IVF251_Flat_nprobe_1_PedroBial_v2.index` |
| 27.6 | `D:\hipercool-materiais\models\rvc\vozes\anya_forger\anya_forger.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\anya_forger\added_IVF234_Flat_nprobe_1_AnyaForgerLolipopBR69_v2.index` |
| 27.6 | `D:\hipercool-materiais\models\rvc\vozes\sukuna\sukuna.index` | `D:\hipercool-materiais\amostras_voz\vozes_novas_1011\sukuna\added_IVF234_Flat_nprobe_1_sukuna_v2.index` |
| 25.0 | `D:\postador-de-videos\remotion\trabalhos\vpsblindada_ia_20261110_143858\video.mp4` | `D:\postador-de-videos\remotion\trabalhos\vpsblindada_ia_20261110_143858\melhor.mp4` |
| 24.2 | `D:\kit3d-producao\_conferir_3d\1116_1644_abelha-ferrao.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-abelha-ferrao\video_sem_capa.mp4` |
| 24.2 | `D:\kit3d-producao\_conferir_3d\1116_2112_colher-mcflurry.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-colher-mcflurry\video_sem_capa.mp4` |
| 23.9 | `D:\postador-de-videos\remotion\trabalhos\gestaodegrupos_ia_20261116_201720\video.mp4` | `D:\postador-de-videos\remotion\trabalhos\gestaodegrupos_ia_20261116_201720\melhor.mp4` |
| 23.3 | `D:\kit3d-producao\_conferir_3d\1116_1022_geladeira-v2.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-geladeira-v2\video_sem_capa.mp4` |
| 22.8 | `D:\kit3d-producao\_conferir_3d\1117_0924_enxerto-de-osso.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-enxerto-de-osso\video_sem_capa.mp4` |
| 22.2 | `D:\kit3d-producao\_conferir_3d\1116_1447_pontos-cirurgia.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-pontos-cirurgia\video_sem_capa.mp4` |
| 21.5 | `D:\kit3d-producao\_conferir_3d\1117_0512_serra-para-no-dedo.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-serra-para-no-dedo\video_sem_capa.mp4` |
| 21.1 | `D:\kit3d-producao\_conferir_3d\1117_0712_veia-estourada.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-veia-estourada\video_sem_capa.mp4` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_angry.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_cheer.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_cheer.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_cry.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_cry.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_laugh.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_laugh.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_love.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_love.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_popcorn.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_popcorn.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_shock.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_shock.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_shy.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_shy.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_sleepy.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_sleepy.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_think.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_think.mov` | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_angry.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_surprise.mov` | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_point.mov` | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot.mov` |
| 18.9 | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot_thumbsup.mov` | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot.mov` | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_point.mov` | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_surprise.mov` | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot.mov` |
| 18.9 | `D:\hipercool-materiais\assets\mascote_mov\fx_mascot_thumbsup.mov` | `D:\hipercool-materiais\assets\overlays\elemental\fx_mascot.mov` |
| 18.2 | `D:\kit3d-producao\_conferir_3d\1116_1844_farpa-sai-sozinha.mp4` | `D:\hipercool-materiais\historias-em-frames\3d-farpa-sai-sozinha\video_sem_capa.mp4` |
| 6.9 | `D:\claude-code-video\trabalhos\globosolarenergiag_20261123_081518\public\trilha.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 6.9 | `D:\hipercool-materiais\assets\trilhas\Beyond - Patrick Patrikios.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 6.9 | `D:\postador-de-videos\remotion\trabalhos\followupia_ia_20261029_182908\public\trilha.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 6.9 | `D:\postador-de-videos\remotion\trabalhos\gestaodegrupos_ia_20261116_201720\public\trilha.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 6.9 | `D:\postador-de-videos\remotion\trabalhos\inovareagenda_20261119_183337\public\trilha.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 6.9 | `D:\postador-de-videos\remotion\trabalhos\inovarecrm_20261121_000607\public\trilha.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 6.9 | `D:\postador-de-videos\remotion\trabalhos\vitrineia_inovare_20261120_010728\public\trilha.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 6.9 | `D:\postador-de-videos\remotion\trabalhos\vpsblindada_ia_20261110_143858\public\trilha.mp3` | `D:\claude-code-video\trabalhos\futebolcom_ia2_20261026_032652\public\trilha.mp3` |
| 3.6 | `D:\downloads\Construindo site estáticos com IA\artools_final\artools\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\Construindo site estáticos com IA\artools_inicial\artools\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\modelo de site\artools_final\artools\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\modelo de site\artools_inicial\artools\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\saas de agentes de atendimento no whatsapp com evolutionn api e assas\app_final_revisado\static\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\saas de agentes de atendimento no whatsapp com evolutionn api e assas\app_intermediario_teste\static\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\saas de agentes de atendimento no whatsapp com evolutionn api e assas\referencia_node_legado\static\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\VITRINE_EIA_V2\JARVIS_OPS_COMPLETE_V13_20260518_101741\jarvis_ops\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\VITRINE_EIA_V2\JARVIS_OPS_COMPLETE_V13_20260518_101741\jarvis_ops\bild_vps_jarvis\assets\raw_files\video.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video.mp4` |
| 3.6 | `D:\downloads\Construindo site estáticos com IA\artools_final\artools\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\Construindo site estáticos com IA\artools_inicial\artools\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\modelo de site\artools_final\artools\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\modelo de site\artools_inicial\artools\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\saas de agentes de atendimento no whatsapp com evolutionn api e assas\app_final_revisado\static\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\saas de agentes de atendimento no whatsapp com evolutionn api e assas\app_intermediario_teste\static\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\saas de agentes de atendimento no whatsapp com evolutionn api e assas\referencia_node_legado\static\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\VITRINE_EIA_V2\JARVIS_OPS_COMPLETE_V13_20260518_101741\jarvis_ops\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.6 | `D:\downloads\VITRINE_EIA_V2\JARVIS_OPS_COMPLETE_V13_20260518_101741\jarvis_ops\bild_vps_jarvis\assets\raw_files\video2.mp4` | `D:\downloads\construindo\final\artools\assets\raw_files\video2.mp4` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\disparoemmassa_ia_20261116_020642\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\disparoemmassa_ia_20261118_102227\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\followupia_ia_20261114_030252\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\futebolcom_ia2_20261110_045334\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\futebolcom_ia2_20261119_050319\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\inovareagenda_20261113_051134\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\inovareclaw_ia_20261115_052513\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\inovarecrm_20261119_135324\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\inovarecrm_20261122_052621\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
| 3.5 | `D:\postador-de-videos\remotion\trabalhos\sintetizerisada_20261101_003218\public\trilha.mp3` | `D:\hipercool-materiais\assets\trilhas\calm_chill.mp3` |
