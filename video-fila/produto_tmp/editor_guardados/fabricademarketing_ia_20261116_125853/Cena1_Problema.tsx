import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1_Problema: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Crossfade suave de entrada e saída
  const opacity = interpolate(frame, [0, 8, 222, 230], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento de câmera contínuo sutil
  const videoScale = interpolate(frame, [0, 230], [1.02, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge de etapa (rel ~0.7s -> frame 21)
  const headerSpring = spring({
    frame: Math.max(0, frame - 21),
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Entrada do título na fala "operação sozinho" (rel ~1.77s -> frame 53)
  const titleSpring = spring({
    frame: Math.max(0, frame - 53),
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Alerta de sobrecarga na fala "impossível manter" (rel ~3.19s -> frame 96) — elimina a pausa estática
  const alertSobrecarga = spring({
    frame: Math.max(0, frame - 96),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Entrada sincronizada rigorosamente com a locução:
  // t_abs = 9.81s (rel 4.27s -> frame 128): "redes"
  const badgeRedes = spring({
    frame: Math.max(0, frame - 128),
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // t_abs = 10.99s (rel 5.45s -> frame 164): "site"
  const badgeSite = spring({
    frame: Math.max(0, frame - 164),
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // t_abs = 11.41s (rel 5.87s -> frame 176): "áudio"
  const badgeAudio = spring({
    frame: Math.max(0, frame - 176),
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // t_abs = 11.71s (rel 6.17s -> frame 185): "atualizados"
  const alertStatus = spring({
    frame: Math.max(0, frame - 185),
    fps,
    config: {damping: 11, stiffness: 160},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
        opacity,
      }}
    >
      {/* Vídeo do Dono: Rebaixado (+75px) para dar folga generosa (>80px) aos letreiros */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `translateY(75px) scale(${videoScale})`,
          transformOrigin: '50% 30%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Gradiente escuro no topo e atenuação da janela estourada ao fundo */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(to bottom, rgba(17, 24, 39, 0.94) 0%, rgba(17, 24, 39, 0.75) 55%, rgba(17, 24, 39, 0) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa Superior Informativa (y=156 a 380) — Rosto do Dono Fica Totalmente Livre com > 60px de respiro */}
      <div
        style={{
          position: 'absolute',
          top: 156,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 40,
        }}
      >
        {/* Rótulo da Etapa */}
        <div
          style={{
            transform: `scale(${headerSpring})`,
            padding: '8px 22px',
            borderRadius: 18,
            backgroundColor: 'rgba(239, 68, 68, 0.25)',
            border: '1.5px solid rgba(239, 68, 68, 0.7)',
            color: '#FCA5A5',
            fontSize: 32,
            fontWeight: 800,
            letterSpacing: 0.8,
            textTransform: 'uppercase',
            marginBottom: 10,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
          }}
        >
          ⚠️ O PROBLEMA
        </div>

        {/* Título com Concordância Nominal Correta ("Operando sozinho") */}
        <div
          style={{
            transform: `scale(${titleSpring})`,
            opacity: titleSpring,
            fontSize: 42,
            fontWeight: 800,
            lineHeight: 1.2,
            color: '#FFFFFF',
            textAlign: 'center',
            textWrap: 'balance',
            textShadow: '0 4px 16px rgba(0,0,0,0.95)',
            marginBottom: 14,
          }}
        >
          Operando sozinho: impossível manter tudo
        </div>

        {/* Badges Sincronizados com Cada Palavra Falada */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            flexWrap: 'wrap',
          }}
        >
          {/* Tag de Alerta Inicial que quebra o silêncio visual dos primeiros segundos */}
          {alertSobrecarga > 0.05 && badgeRedes <= 0.05 && (
            <div
              style={{
                transform: `scale(${alertSobrecarga})`,
                opacity: alertSobrecarga,
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(239, 68, 68, 0.3)',
                border: '1px solid rgba(239, 68, 68, 0.8)',
                color: '#FECACA',
                fontSize: 32,
                fontWeight: 800,
              }}
            >
              ⚠️ Sobrecarga total
            </div>
          )}

          {badgeRedes > 0.05 && (
            <div
              style={{
                transform: `scale(${badgeRedes})`,
                opacity: badgeRedes,
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(220, 38, 38, 0.92)',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                boxShadow: '0 4px 14px rgba(220, 38, 38, 0.45)',
              }}
            >
              📱 Redes ✕
            </div>
          )}

          {badgeSite > 0.05 && (
            <div
              style={{
                transform: `scale(${badgeSite})`,
                opacity: badgeSite,
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(220, 38, 38, 0.92)',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                boxShadow: '0 4px 14px rgba(220, 38, 38, 0.45)',
              }}
            >
              🌐 Site ✕
            </div>
          )}

          {badgeAudio > 0.05 && (
            <div
              style={{
                transform: `scale(${badgeAudio})`,
                opacity: badgeAudio,
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(220, 38, 38, 0.92)',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                boxShadow: '0 4px 14px rgba(220, 38, 38, 0.45)',
              }}
            >
              🎙️ Áudio ✕
            </div>
          )}

          {alertStatus > 0.05 && (
            <div
              style={{
                transform: `scale(${alertStatus})`,
                opacity: alertStatus,
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: '#F59E0B',
                color: '#111827',
                fontSize: 32,
                fontWeight: 900,
                boxShadow: '0 4px 16px rgba(245, 158, 11, 0.55)',
              }}
            >
              DESATUALIZADOS
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
