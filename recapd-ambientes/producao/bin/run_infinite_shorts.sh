while true; do
  echo "=> Inciando anime_auto.py batch (Modo Short)..."
  PYTHONUTF8=1 GEMINI_TTS_PROXY_ENABLED=1 venv/Scripts/python.exe bin/anime_auto.py --modo short --top 100 --limit 0

  if [ $? -eq 0 ]; then
    echo "Processo Python saiu com sucesso (0). Nao tentaremos de novo imediatamente para não sobrecarregar."
    sleep 300
  else
    echo "Processo Python saiu com erro (provavel hard crash do Whisper). Reiniciando rapidamente com o proximo id..."
    sleep 5
  fi
done