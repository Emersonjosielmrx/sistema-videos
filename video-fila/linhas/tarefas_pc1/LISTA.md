# Tarefas agendadas do PC1 que rodam o sistema (exportadas 29/10/2026 23h)

| tarefa | estado | comando |
|---|---|---|
| AdvanceSolar_Carrossel | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\ms-energy\bin\cron_carrossel_advance.bat"  |
| AgendadorVO3 | Disabled | wscript.exe "D:\rodar_oculto.vbs" "D:\postador-de-videos\bin\agendar_vo3_auto.bat" D:\postador-de-videos\bin |
| AnaliseMaquinas24h | Ready | "D:\veo\venv\Scripts\pythonw.exe" D:\video-fila\analise_maquinas.py  |
| AnimeOcioso | Disabled | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\ocioso.py D:\video-fila |
| AnimeRecapMonitor | Disabled | wscript.exe "D:\rodar_oculto.vbs" "D:\recapd-ambientes\producao\cron_anime_monitor.bat" D:\recapd-ambientes\producao |
| AnimeRecapNoturno | Disabled | wscript.exe "D:\rodar_oculto.vbs" "D:\recapd-ambientes\producao\cron_anime_noturno.bat" D:\recapd-ambientes\producao |
| ArgonManter | Running | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe -X utf8 D:\gemini-argo\argon_manter.py  |
| ArgonManterLogon | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe -X utf8 D:\gemini-argo\argon_manter.py  |
| ArgonZelador | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe -X utf8 D:\gemini-argo\argon_zelador.py  |
| Atlas - sincronizar | Disabled | wscript "D:\trader_binance\atlas\rodar_oculto.vbs" atlas.sincronizar  |
| Atlas - vigia | Disabled | wscript "D:\trader_binance\atlas\rodar_oculto.vbs" atlas.vigia  |
| AtualizarYtDlp | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe D:\video-fila\atualizar_ytdlp.py D:\video-fila |
| AvisoCredenciais | Ready | "C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe" "D:\projetos-navegador\credential-factory\aviso_credenciais.py" kaggle  |
| BackupCachesHipercool | Ready | D:\hipercool-videos\venv\Scripts\pythonw.exe D:\hipercool-videos\bin\backup_caches.py D:\hipercool-videos |
| BackupDriveVideos | Running | wscript.exe "D:\rodar_oculto.vbs" "D:\manhwa-react\scripts\backup_drive.bat" D:\manhwa-react\scripts |
| ClaudeCodeVideo | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\claude-code-video\cron_auto.bat"  |
| ClinePonte | Running | wscript.exe "D:\rodar_oculto.vbs" "D:\cline-ponte\iniciar.bat"  |
| CofreChecar | Ready | D:\hipercool-materiais\python\venv\Scripts\pythonw.exe -X utf8 "D:\logins-google\cofre.py" checar D:\logins-google |
| ControladorVideos | Ready | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\controlador.py D:\video-fila |
| Cortes_Agente | Disabled | D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe D:\video-fila\linhas\CORTES\agente\cortes_agente.py rodada D:\video-fila\linhas\CORTES\agente |
| Cortes_Juri | Running | D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe D:\recapd-ambientes\producao\bin\cortes_juri.py rodar  |
| Cortes_Melhorador | Disabled | D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe D:\recapd-ambientes\producao\bin\cortes_melhorador.py  |
| Cortes_UltimoVideo | Ready | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\linhas\CORTES\ultimo_video.py  |
| DesktopVigia | Ready | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\desktop_vigia.py  |
| EngenhariaReversaFila | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\video-fila\linhas\LONGOS\engenharia_reversa_fila.bat"  |
| EngenhariaReversaMedir | Running | wscript.exe "D:\rodar_oculto.vbs" "D:\video-fila\engenharia_reversa\medir_nossos.bat"  |
| EngenhariaReversaSemanal | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\video-fila\engenharia_reversa\semanal.bat"  |
| ERContinuo | Running | D:\veo\venv\Scripts\pythonw.exe -X utf8 D:\video-fila\engenharia_reversa\continuo.py  |
| GeminiChavesRetentativa | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\projetos-navegador\credential-factory\tarefa_gemini_massa.bat" D:\projetos-navegador\credential-factory |
| GpuKaggleFila | Ready | D:\hipercool-materiais\python\venv\Scripts\pythonw.exe "D:\hipercool-materiais\bin\kaggle_conversor.py" auto D:\hipercool-materiais\bin |
| HipercoolFila | Disabled | D:\hipercool-videos\venv\Scripts\pythonw.exe D:\hipercool-videos\bin\fila.py ciclo D:\hipercool-videos |
| HipercoolPC2 | Ready | D:\hipercool-videos\venv\Scripts\pythonw.exe D:\hipercool-videos\bin\fila.py pc2-trazer D:\hipercool-videos |
| HipercoolPostagem | Ready | D:\hipercool-videos\venv\Scripts\pythonw.exe D:\hipercool-videos\bin\fila.py postagem D:\hipercool-videos |
| HipercoolReligarProducao | Disabled | D:\hipercool-videos\venv\Scripts\pythonw.exe D:\hipercool-videos\bin\fila.py ligar D:\hipercool-videos |
| HipercoolShorts2h | Disabled | D:\hipercool-videos\venv\Scripts\pythonw.exe -X utf8 D:\hipercool-videos\bin\shorts_a_cada_2h.py D:\hipercool-videos |
| HipercoolVigia | Disabled | D:\hipercool-videos\venv\Scripts\pythonw.exe D:\hipercool-videos\bin\vigia_agente.py D:\hipercool-videos |
| HistoriasEmFrames-Producao | Disabled | D:\historias-em-frames\prod\venv\Scripts\pythonw.exe D:\historias-em-frames\auto_producer.py D:\historias-em-frames |
| InstagramCriarContas | Ready | wscript.exe "D:\rodar_oculto.vbs" "C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe" "-u" "D:\postador-de-videos\bin\instagram_criar |
| InstalarPC3 | Ready | D:\veo\venv\Scripts\pythonw.exe -X utf8 "D:\video-fila\instalar_pc3.py" --auto D:\video-fila |
| KaggleHoras | Ready | D:\hipercool-materiais\python\venv\Scripts\pythonw.exe -X utf8 "D:\video-fila\kaggle_horas.py" D:\video-fila |
| KaggleRecapManter | Disabled | D:\hipercool-videos\venv\Scripts\pythonw.exe D:\recapd-ambientes\producao\colab\kaggle_lancar.py manter  |
| Laboratorio - papeis | Disabled | wscript.exe "D:\trader_binance\trader_binance\laboratorio\papel\rodar_papeis_oculto.vbs"  |
| LimparCacheChrome | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe D:\video-fila\limpar_cache_chrome.py D:\video-fila |
| LimparEspaco_logins-google | Ready | wscript.exe "D:\rodar_oculto.vbs" "C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe" "D:\logins-google\limpar_espaco.py" "--drive" D |
| LimparRelatoriosWindows | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe D:\video-fila\limpar_relatorios_windows.py D:\video-fila |
| Limpeza source.mp4 anime | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe D:\hipercool-materiais\anime\limpar_source.py D:\hipercool-materiais\anime |
| ManhwaReact-Comentarios | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\manhwa-react\scripts\rede_comentarios.bat" D:\manhwa-react\scripts |
| ManhwaReact-Lote | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\manhwa-react\scripts\lote_noturno.bat" D:\manhwa-react\scripts |
| ManhwaReact-Rede | Running | wscript.exe "D:\rodar_oculto.vbs" "D:\manhwa-react\scripts\rede_hora_em_hora.bat" D:\manhwa-react\scripts |
| Marcas_Carrossel | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\postador-de-videos\bin\cron_carrossel_marcas.bat"  |
| MascoteProducao | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\video-fila\linhas\LONGOS\mascote_producao.bat"  |
| MedidorPC1 | Running | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\medidor_pc1.py  |
| MegaEngageMonitor | Disabled | powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\projetos-navegador\_monitor_agent.ps1  |
| MelhoradorCentral | Running | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe D:\video-fila\melhorador_central.py --rodar 9  |
| MelhoradorProdutos | Disabled | wscript.exe D:\rodar_oculto.vbs D:\postador-de-videos\bin\cron_melhorador_produtos.bat  |
| MonitorArgon | Ready | wscript.exe "D:\rodar_oculto.vbs" "C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe" -X utf8 "D:\gemini-argo\monitor_argon.py" D:\ge |
| MonitorOpus | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe D:\monitor_opus.py D:\ |
| MonitorSonnet | Ready | wscript.exe D:\rodar_oculto.vbs "D:\sonnet web\monitor_sonnet.bat"  |
| MSEnergy_Carrossel | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\ms-energy\bin\cron_carrossel.bat"  |
| MSEnergy_Gerar | Disabled | wscript.exe "D:\rodar_oculto.vbs" "D:\ms-energy\bin\cron_gerar_ms_energy.bat" "2" D:\ms-energy |
| MSEnergy_Metricas | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\ms-energy\bin\cron_metricas.bat"  |
| MSEnergy_PostarInsta | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\ms-energy\bin\cron_postar_insta.bat"  |
| MSEnergy_PostarTikTok | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\ms-energy\bin\cron_postar_tiktok.bat" D:\ms-energy\bin |
| MSEnergy_VigiaClientes | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\ms-energy\bin\cron_vigia_clientes.bat"  |
| NotificarTelegram | Running | D:\manhwa-react\.venv\Scripts\pythonw.exe D:\postador-de-videos\bin\notificar_telegram.py  |
| NSN_Banimento | Ready | D:\veo\venv\Scripts\pythonw.exe -X utf8 D:\projeto-navegador-sem-navegador\tools\monitor_banimento.py D:\projeto-navegador-sem-navegador |
| NSN_ColherNotebooks | Ready | wscript.exe D:\rodar_oculto.vbs "D:\veo\venv\Scripts\python.exe" D:\projeto-navegador-sem-navegador\tools\colher_notebooks.py  |
| NSN_Inteligencia | Ready | wscript.exe D:\rodar_oculto.vbs "D:\veo\venv\Scripts\python.exe" -m relatorios.inteligencia --tiktok D:\projeto-navegador-sem-navegador |
| NSN_ManterCookies | Ready | wscript.exe D:\rodar_oculto.vbs "D:\veo\venv\Scripts\python.exe" tools\manter_cookies.py D:\projeto-navegador-sem-navegador |
| NSN_Saude | Ready | D:\veo\venv\Scripts\pythonw.exe -X utf8 D:\projeto-navegador-sem-navegador\tools\saude.py  |
| PainelCanais | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\postador-de-videos\bin\painel_canais.bat" D:\postador-de-videos\bin |
| PainelClientes_Coletar | Ready | "C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe" "D:\painel-clientes\coletor\coletar_instagram.py"  |
| PainelTunel | Running | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\tunel_painel.py  |
| PainelVideos | Running | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\painel_controlador.py D:\video-fila |
| ParceiroKaijinre-Postagem | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\recapd-ambientes\producao\cron_parceiro.bat" "postar"  |
| ParceiroKaijinre-Producao | Disabled | wscript.exe "D:\rodar_oculto.vbs" "D:\recapd-ambientes\producao\cron_parceiro.bat" "producao"  |
| PostadorDeVideos | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\postador-de-videos\bin\postar_tudo_auto.bat" D:\postador-de-videos\bin |
| Produto_Videos | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\postador-de-videos\bin\cron_produto_videos.bat"  |
| ProxyCelular | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe -X utf8 D:\postador-de-videos\bin\proxy_celular.py --vez  |
| ReacoesColheita | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\hipercool-materiais\bin\reacoes_colheita.bat"  |
| RecapAlimentar | Running | D:\hipercool-videos\venv\Scripts\pythonw.exe -u cliente.py alimentar https://www.youtube.com/@Manhwa_Fresh/videos D:\recapd-ambientes\producao\colab |
| RecapCentralCasa | Running | wscript.exe "D:\rodar_oculto.vbs" "D:\recap_central_casa\central.bat"  |
| RecapCentralCasaLiberar | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\recap_central_casa\central.bat" liberar  |
| RecapMelhoradorLongo | Ready | D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe -X utf8 D:\recapd-ambientes\producao\colab\melhorador_longo.py D:\recapd-ambientes\producao\cola |
| RecapPostarLongos | Running | D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe -X utf8 D:\recapd-ambientes\producao\colab\postar_longos.py D:\recapd-ambientes\producao\colab |
| RecapSubirVozes | Ready | D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe -X utf8 D:\recapd-ambientes\producao\colab\subir_vozes.py D:\recapd-ambientes\producao\colab |
| SentinelaContinue | Running | "C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe" -I D:\sentinela_disparo.py  |
| SonnetWebMonitor | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\gemini-argo\sonnet_web_monitor.bat" D:\gemini-argo |
| SupervisorMelhorador | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe D:\video-fila\supervisor_melhorador.py D:\video-fila |
| TelaoChecklist | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe -X utf8 D:\video-fila\vitrine\checklist_like.py  |
| TikTokRodadaExtra | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\postador-de-videos\bin\tiktok_rodada_extra.bat"  |
| TikTok_MedirViews | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\postador-de-videos\bin\cron_medir_tiktok.bat"  |
| Trader Binance - limpeza de dados | Disabled | D:\trader_binance\atlas\venv\Scripts\pythonw.exe "D:\trader_binance\trader_binance\deploy\limpeza_dados.py" D:\trader_binance\trader_binance |
| TrechosNoite | Ready | D:\recapd-ambientes\producao\venv\Scripts\pythonw.exe D:\video-fila\trechos_noite.py D:\video-fila |
| TrocarVenvUnico | Disabled | powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File D:\hipercool-materiais\python\trocar_venv.ps1  |
| TunelCelularVPS | Ready | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe -X utf8 D:\whatsapp-notes\tunel_celular_vps.py  |
| VeoProducaoDiaria7h | Disabled | cmd /c "D:\veo\beta\Veo_START_DIARIO_7H.bat"  |
| Veo_Limpeza_Drive | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\veo\beta\tarefa_limpeza_drive.bat" D:\veo\beta |
| VigiaDesktop | Ready | wscript.exe "D:\rodar_oculto.vbs" "D:\video-fila\vigia_desktop.bat"  |
| VigiaMelhorias | Disabled | D:\manhwa-react\.venv\Scripts\pythonw.exe "D:\postador-de-videos\bin\vigia_melhorias.py" D:\postador-de-videos |
| VigiaVideos | Running | C:\Users\Haylla\AppData\Local\Programs\Python\Python313\pythonw.exe D:\video-fila\vigia_geral.py D:\video-fila |
| VisualizadorX200 | Disabled | D:\veo\venv\Scripts\pythonw.exe D:\video-fila\visualizador.py enviar D:\video-fila |
| VozClonadaFila | Disabled | D:\hipercool-materiais\python\venv_vozes\Scripts\pythonw.exe "D:\hipercool-materiais\bin\voz_clonada.py" fila --so-material D:\hipercool-materiais\bin |
| VozClonadaVigia | Ready | D:\hipercool-materiais\python\venv_vozes\Scripts\pythonw.exe "D:\hipercool-materiais\bin\voz_clonada.py" vigiar D:\hipercool-materiais\bin |
| VozFidelidadePiloto | Disabled | D:\hipercool-materiais\python\venv_vozes\Scripts\pythonw.exe "D:\hipercool-materiais\amostras_voz\clone2\fidelidade\piloto_fidelidade.py" D:\hipercool |
| ZeladorSonnet | Ready | wscript.exe D:\rodar_oculto.vbs "D:\sonnet web\zelador_sonnet.bat"  |
