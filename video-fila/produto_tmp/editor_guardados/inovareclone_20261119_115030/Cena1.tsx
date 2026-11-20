import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES, fontFamily} from './constants';

export const Cena1: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no vídeo (push-in sutil 1.0 -> 1.06)
  const videoScale = interpolate(frame, [0, 232], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Fade in na entrada (0 a 10 frames) e transição de saída (220 a 232 frames)
  const fadeIn = interpolate(frame, [0, 10], [0.8, 1], {
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [220, 232], [1, 0.85], {
    extrapolateRight: 'clamp',
  });

  // Animação da Badge de Contexto no topo (entra no frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: "TRAVAVA NA HORA DE GRAVAR" (entra no frame 55 ~ 1.8s cena, quando fala "Eu travava...")
  const card1Spring = spring({
    frame: frame - 55,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 2: "PERFIL SEM VÍDEOS" (entra no frame 155 ~ 5.1s cena, quando fala "e o perfil ficava sem vídeos")
  const card2Spring = spring({
    frame: frame - 155,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Flutuação ativa sutil para manter dinamismo sem tapar o rosto
  const floatY = Math.sin(frame / 14) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
        opacity: fadeIn * fadeOut,
      }}
    >
      {/* Vídeo do Dono com push-in sutil */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 35%',
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
        {/* Leve gradiente protetor no topo e na base (protege textos e karaokê sem escurecer o rosto) */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11, 13, 20, 0.75) 0%, rgba(11, 13, 20, 0.15) 25%, rgba(11, 13, 20, 0.0) 45%, rgba(11, 13, 20, 0.2) 75%, rgba(11, 13, 20, 0.85) 100%)',
          }}
        />
      </div>

      {/* ÁREA SUPERIOR (y: 165 a 380) — Rosto e tronco do dono 100% livres! */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 20,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Badge superior: Rótulo "O PROBLEMA" + "RELATO REAL" */}
        <div
          style={{
            opacity: Math.max(0, badgeSpring),
            transform: `translateY(${(1 - badgeSpring) * -18}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 20px',
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '1.5px solid rgba(239, 68, 68, 0.4)',
            borderRadius: 24,
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 600,
              color: '#F87171',
              paddingLeft: 6,
              borderLeft: '1.5px solid rgba(255,255,255,0.2)',
            }}
          >
            Relato Real
          </span>
        </div>

        {/* Card dinâmico sincronizado com a fala */}
        {frame < 155 ? (
          // Fase 1: TRAVAVA NA HORA DE GRAVAR (a partir de ~1.8s)
          frame >= 50 && (
            <div
              style={{
                opacity: Math.max(0, card1Spring),
                transform: `scale(${Math.max(0.85, card1Spring)})`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '16px 32px',
                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(139, 92, 246, 0.45)',
                borderRadius: 22,
                boxShadow: '0 12px 35px rgba(0, 0, 0, 0.75)',
                maxWidth: 920,
                textAlign: 'center',
              }}
            >
              <span
                style={{
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 0.8,
                  textTransform: 'uppercase',
                  textShadow: '0 3px 12px rgba(0, 0, 0, 0.8)',
                }}
              >
                Travava na hora de gravar
              </span>
              <span
                style={{
                  marginTop: 6,
                  fontSize: 32,
                  fontWeight: 600,
                  color: CORES.marcaClara,
                  letterSpacing: 0.5,
                }}
              >
                Cobrança de sentar na frente da lente
              </span>
            </div>
          )
        ) : (
          // Fase 2: PERFIL SEM VÍDEOS (a partir de ~5.1s)
          <div
            style={{
              opacity: Math.max(0, card2Spring),
              transform: `scale(${Math.max(0.85, card2Spring)})`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '16px 32px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid rgba(239, 68, 68, 0.5)',
              borderRadius: 22,
              boxShadow: '0 12px 35px rgba(0, 0, 0, 0.75)',
              maxWidth: 920,
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 0.8,
                textTransform: 'uppercase',
                textShadow: '0 3px 12px rgba(0, 0, 0, 0.8)',
              }}
            >
              Perfil ficava sem vídeos
            </span>
            <span
              style={{
                marginTop: 6,
                fontSize: 32,
                fontWeight: 600,
                color: '#F87171',
                letterSpacing: 0.5,
              }}
            >
              Falta de constância nas redes
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
