#!/usr/bin/env python3
"""auto-validate.py — Validação automática de vídeo gerado.

Analisa o vídeo e gera um relatório completo sem precisar de humano.
Só escala pro humano se encontrar problema.

Uso:
    python bin/auto-validate.py --video path/to/video.mp4 --log path/to/run.log
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_duration(video):
    r = subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(video)], capture_output=True, text=True, timeout=10)
    return float(r.stdout.strip()) if r.stdout.strip() else 0

def get_resolution(video):
    r = subprocess.run(['ffprobe', '-v', 'quiet', '-select_streams', 'v', '-show_entries', 'stream=width,height,r_frame_rate,bit_rate', '-of', 'csv=p=0', str(video)], capture_output=True, text=True, timeout=10)
    parts = r.stdout.strip().split(',')
    if len(parts) >= 2:
        w, h = int(parts[0]), int(parts[1])
        fps_str = parts[2] if len(parts) > 2 else "30/1"
        try:
            num, den = fps_str.split('/')
            fps = round(int(num) / int(den), 1)
        except Exception:
            fps = 30.0
        bitrate = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
        return (w, h, fps, bitrate)
    return (0, 0, 0, 0)

def get_audio_info(video):
    r = subprocess.run(['ffprobe', '-v', 'quiet', '-select_streams', 'a', '-show_entries', 'stream=sample_rate,channels,duration', '-of', 'csv=p=0', str(video)], capture_output=True, text=True, timeout=10)
    parts = r.stdout.strip().split(',')
    if len(parts) >= 3:
        return {'sample_rate': int(parts[0]), 'channels': int(parts[1]), 'duration': float(parts[2])}
    return {'sample_rate': 0, 'channels': 0, 'duration': 0}

def measure_volume_segments(video, segment_dur=30):
    """Mede volume médio por segmento."""
    dur = get_duration(video)
    segments = []
    for start in range(0, int(dur), segment_dur):
        cmd = ['ffmpeg', '-ss', str(start), '-t', str(segment_dur), '-i', str(video), '-af', 'volumedetect', '-f', 'null', '-']
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        for line in r.stderr.split('\n'):
            if 'mean_volume' in line:
                vol = float(line.split('mean_volume:')[1].strip().split(' ')[0])
                segments.append({'time': f"{start//60}:{start%60:02d}", 'volume_db': vol})
                break
    return segments


def detect_silence(video, threshold_db=-40, min_duration=3.0):
    """Detecta trechos de silêncio prolongado (possível áudio cortado)."""
    cmd = ['ffmpeg', '-i', str(video), '-af',
           f'silencedetect=noise={threshold_db}dB:d={min_duration}', '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    silences = []
    for line in r.stderr.split('\n'):
        if 'silence_start' in line:
            try:
                start = float(line.split('silence_start:')[1].strip())
                silences.append({'start': start})
            except: pass
        elif 'silence_end' in line and silences:
            try:
                parts = line.split('silence_end:')[1].strip().split('|')
                end = float(parts[0].strip())
                dur_s = float(parts[1].split(':')[1].strip()) if len(parts) > 1 else end - silences[-1]['start']
                silences[-1]['end'] = end
                silences[-1]['duration'] = dur_s
            except: pass
    return silences


def detect_black_frames(video, threshold=0.01, min_duration=1.0):
    """Detecta trechos de tela preta (possível erro de renderização)."""
    cmd = ['ffmpeg', '-i', str(video), '-vf',
           f'blackdetect=d={min_duration}:pix_th={threshold}', '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    blacks = []
    for line in r.stderr.split('\n'):
        if 'black_start' in line:
            try:
                start = float(line.split('black_start:')[1].split(' ')[0])
                dur_s = float(line.split('black_duration:')[1].strip())
                blacks.append({'start': start, 'duration': dur_s})
            except: pass
    return blacks

def parse_log(log_path):
    """Extrai métricas do log de geração."""
    log = Path(log_path).read_text(encoding='utf-8', errors='replace') if Path(log_path).exists() else ""
    return {
        'clips': log.count('Clip '),
        'memes': log.count('🎭'),
        'tts_falhas': log.count('falhou'),
        'trilha_adicionada': 'Trilha dinâmica adicionada' in log or 'Trilha adicionada' in log,
        'legendas': 'Legendas + watermark queimados' in log,
        'upscale': 'Upscale' in log and 'feito' in log,
        'trilha_info': [l.strip() for l in log.split('\n') if '[TRILHA]' in l],
    }

def validate(video_path, log_path=None):
    """Validação completa. Retorna dict com resultado."""
    video = Path(video_path)
    if not video.exists():
        return {'status': 'ERRO', 'msg': 'Vídeo não existe'}

    result = {
        'video': str(video),
        'timestamp': datetime.now().isoformat(),
        'status': 'OK',
        'problemas': [],
    }

    # Técnico
    dur = get_duration(video)
    w, h, fps, bitrate = get_resolution(video)
    audio = get_audio_info(video)
    size_mb = video.stat().st_size / (1024*1024)

    result['tecnico'] = {
        'duracao_s': round(dur, 1),
        'duracao_min': f"{int(dur//60)}:{int(dur%60):02d}",
        'resolucao': f"{w}x{h}",
        'fps': fps,
        'bitrate_kbps': round(bitrate / 1000) if bitrate else 0,
        'tamanho_mb': round(size_mb, 1),
        'audio_sample_rate': audio['sample_rate'],
        'audio_channels': audio['channels'],
        'audio_duracao_s': round(audio['duration'], 1),
        'sync_diff_s': round(abs(dur - audio['duration']), 3),
    }

    # Validações
    TEST_MODE = int(os.environ.get("TEST_MODE", "0"))
    is_censured = "_CENSURADO" in video.name
    # Padrão nativo do principal é 720x1280 (1080 só se UPSCALE_MAIN ou for o _CENSURADO)
    if not is_censured and (w == 720 and h == 1280):
        pass # Aceita main em 720p validamente
    elif (w != 1080 or h != 1920) and TEST_MODE < 1:
        if not (w == 720 and h == 1280): # Aceita 720x1280 como base ok em test mode ou non-censured
            result['problemas'].append(f"Resolução {w}x{h} (esperado 1080x1920 ou 720x1280)")
    if fps < 24 or fps > 60:
        result['problemas'].append(f"FPS anormal: {fps} (esperado 25-30)")
    if abs(dur - audio['duration']) > 1.0:
        result['problemas'].append(f"Áudio dessincronizado ({abs(dur-audio['duration']):.1f}s)")
    if size_mb < 10:
        result['problemas'].append(f"Arquivo muito pequeno ({size_mb:.0f}MB)")
    if dur < 30:
        result['problemas'].append(f"Vídeo muito curto ({dur:.0f}s)")

    # Detecção de silêncio prolongado (> 3s)
    silences = detect_silence(video)
    result['silences'] = silences
    if silences:
        total_silence = sum(s.get('duration', 0) for s in silences)
        result['total_silence_s'] = round(total_silence, 1)
        if total_silence > 10:
            result['problemas'].append(f"Silêncio prolongado: {total_silence:.0f}s total em {len(silences)} trecho(s)")

    # Detecção de tela preta (> 1s)
    blacks = detect_black_frames(video)
    result['black_frames'] = blacks
    if blacks:
        total_black = sum(b.get('duration', 0) for b in blacks)
        result['total_black_s'] = round(total_black, 1)
        if total_black > 5:
            result['problemas'].append(f"Tela preta: {total_black:.0f}s total em {len(blacks)} trecho(s)")

    # Volume
    volumes = measure_volume_segments(video, 30)
    result['volume_segments'] = volumes
    if volumes:
        vols = [v['volume_db'] for v in volumes]
        vol_range = max(vols) - min(vols)
        result['volume_range_db'] = round(vol_range, 1)
        result['volume_min_db'] = round(min(vols), 1)
        result['volume_max_db'] = round(max(vols), 1)
        if vol_range > 20:
            result['problemas'].append(f"Volume inconsistente (range {vol_range:.0f}dB)")
        if min(vols) < -60:
            result['problemas'].append(f"Trecho quase silencioso ({min(vols):.0f}dB)")

    # Log
    if log_path:
        log_info = parse_log(log_path)
        result['log'] = log_info
        if not log_info['trilha_adicionada']:
            result['problemas'].append("Trilha NÃO foi adicionada")
        if not log_info['legendas']:
            result['problemas'].append("Legendas NÃO foram queimadas")
        if log_info['tts_falhas'] > 3:
            result['problemas'].append(f"Muitas falhas de TTS ({log_info['tts_falhas']})")

    # Status final
    if result['problemas']:
        result['status'] = 'PROBLEMAS'

    return result


def main():
    parser = argparse.ArgumentParser(description="Validação automática de vídeo")
    parser.add_argument("--video", required=True, help="Path do vídeo")
    parser.add_argument("--log", help="Path do log de geração")
    parser.add_argument("--output", help="Salvar relatório JSON")
    args = parser.parse_args()

    result = validate(args.video, args.log)

    # Imprimir resumo
    print(f"\n{'='*60}")
    print(f"  VALIDAÇÃO: {Path(args.video).name}")
    print(f"{'='*60}")
    print(f"  Status: {result['status']}")
    print(f"  Duração: {result['tecnico']['duracao_min']} ({result['tecnico']['duracao_s']}s)")
    print(f"  Resolução: {result['tecnico']['resolucao']} @ {result['tecnico']['fps']} fps")
    print(f"  Tamanho: {result['tecnico']['tamanho_mb']} MB")
    print(f"  Sync áudio/vídeo: {result['tecnico']['sync_diff_s']}s")
    if 'volume_range_db' in result:
        print(f"  Volume: {result['volume_min_db']} a {result['volume_max_db']} dB (range {result['volume_range_db']})")
    if 'log' in result:
        print(f"  Clips: {result['log']['clips']} | Memes: {result['log']['memes']} | TTS falhas: {result['log']['tts_falhas']}")
        print(f"  Trilha: {'✓' if result['log']['trilha_adicionada'] else '✗'} | Legendas: {'✓' if result['log']['legendas'] else '✗'}")
        if result['log']['trilha_info']:
            for t in result['log']['trilha_info'][:5]:
                print(f"    {t}")
    if result['problemas']:
        print(f"\n  ⚠️ PROBLEMAS:")
        for p in result['problemas']:
            print(f"    - {p}")
    else:
        print(f"\n  ✅ APROVADO — sem problemas detectados")
    print(f"{'='*60}\n")

    # Salvar JSON
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"  Relatório salvo: {args.output}")

    sys.exit(0 if result['status'] == 'OK' else 1)


if __name__ == "__main__":
    main()
