// Primeiro trabalho no ffmpeg na nuvem: tira o áudio (para a transcrição) e um quadro (para a IA ver o vídeo, para
// o fundo do cartão final e para saber se o vídeo é em pé ou deitado). A duração vem da transcrição.
const v = $('🧩 Pega o vídeo').first().json;
return [{ json: { corpo: JSON.stringify({
  input_files: { 'in_video.mp4': v.video_url },
  output_files: [`audio-${v.job}.mp3`, `quadro-${v.job}.jpg`],
  machine: 'cpu', timeout_seconds: 300,
  ffmpeg_commands: [
    `-i inputs/in_video.mp4 -vn -ac 1 -ar 16000 -b:a 48k outputs/audio-${v.job}.mp3`,
    // até 720 px no lado maior, mantendo a proporção (em pé x deitado)
    `-ss 1 -i inputs/in_video.mp4 -frames:v 1 -vf "scale='if(gt(iw,ih),720,-2)':'if(gt(iw,ih),-2,720)'" -q:v 3 outputs/quadro-${v.job}.jpg`,
  ],
}) } }];
