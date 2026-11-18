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

export const Cena3_Resultado: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Crossfade suave
  const opacity = interpolate(frame, [0, 8, 211, 219], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Volta para 1.00x e aplica slow push-in contínuo (1.00 -> 1.06) disfarçando o corte de ângulo
  const videoScale = interpolate(frame, [0, 219], [1.00, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Header aos 0.15s (frame 5)
  const headerSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // t_abs = 22.18s (rel 1.64s -> frame 49): "presença forte"
  const card1Spring = spring({
    frame: Math.max(0, frame - 49),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // t_abs = 24.88s (rel 4.34s -> frame 130): "sem precisar contratar terceiros"
  const card2Spring = spring({
    frame: Math.max(0, frame - 130),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Pulso contínuo vivo no status ativo
  const pulseScale = 1.0 + Math.sin(frame * 0.16) * 0.035;

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
      {/* Vídeo do Dono: Rebaixado ligeiramente (+45px) para dar folga generosa (>50px) aos letreiros */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `translateY(45px) scale(${videoScale})`,
          transformOrigin: '50% 30%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Gradiente escuro no topo para contraste do texto */}
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

      {/* Faixa Superior Informativa (y=156 a 380) — Rosto do Dono Fica 100% Livre com folga > 55px */}
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
            backgroundColor: 'rgba(16, 185, 129, 0.25)',
            border: '1.5px solid #10B981',
            color: '#34D399',
            fontSize: 32,
            fontWeight: 800,
            letterSpacing: 0.8,
            textTransform: 'uppercase',
            marginBottom: 10,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
          }}
        >
          🚀 O RESULTADO
        </div>

        {/* Título Cinético */}
        <div
          style={{
            transform: `scale(${headerSpring})`,
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
          Presença forte sem equipe extra
        </div>

        {/* Cards de Conquista Sincronizados Rigorosamente com a Fala */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 14,
            flexWrap: 'wrap',
          }}
        >
          {card1Spring > 0.05 && (
            <div
              style={{
                transform: `scale(${card1Spring * pulseScale})`,
                opacity: card1Spring,
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(16, 185, 129, 0.95)',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                boxShadow: '0 4px 16px rgba(16, 185, 129, 0.5)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>🟢</span> Presença Ativa
            </div>
          )}

          {card2Spring > 0.05 && (
            <div
              style={{
                transform: `scale(${card2Spring})`,
                opacity: card2Spring,
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: '#F472B6',
                color: '#111827',
                fontSize: 32,
                fontWeight: 900,
                boxShadow: '0 4px 18px rgba(244, 114, 182, 0.6)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>⚡</span> Sem Contratar Terceiros
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
