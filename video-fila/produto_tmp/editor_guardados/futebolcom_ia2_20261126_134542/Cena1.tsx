import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {fontFamily} from './fontes';

const CORES = {
  marca: '#E11D48',
  apoio: '#FACC15',
  card_fundo: 'rgba(18, 4, 8, 0.94)',
  borda_card: 'rgba(255, 255, 255, 0.16)',
};

export const Cena1: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Cortes dinâmicos de aproximação (punch-in zoom de 10% a 15%) nas mudanças de frase-chave
  const tTroca = Math.round(3.1 * fps); // frame 93: "sem resposta"
  const tDesistir = Math.round(4.6 * fps); // frame 138: "até desistir do lanche"

  // Variação de câmera com 2 cortes de escala para eliminar a monotonia de selfie
  const cameraScale =
    frame < tTroca
      ? interpolate(frame, [0, tTroca], [1.0, 1.05], {extrapolateRight: 'clamp'})
      : frame < tDesistir
      ? interpolate(frame, [tTroca, tDesistir], [1.14, 1.19], {extrapolateRight: 'clamp'})
      : interpolate(frame, [tDesistir, 6.94 * fps], [1.22, 1.27], {extrapolateRight: 'clamp'});

  const sprBadge = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const sprCard1 = spring({frame: frame - 12, fps, config: {damping: 16, stiffness: 140}});
  const sprDesistirAlert = spring({frame: frame - tDesistir, fps, config: {damping: 12, stiffness: 160}});

  // Transição rápida e limpa entre Card 1 e Card 2 aos 3.1s (frame 93), garantindo escala 100%
  const card1Opacity = interpolate(frame, [tTroca - 5, tTroca], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const card2Opacity = interpolate(frame, [tTroca - 2, tTroca + 3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Pulso de alerta sutil
  const alertPulse = 1 + Math.sin(frame * 0.18) * 0.03;

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', overflow: 'hidden'}}>
      {/* Vídeo do apresentador com push-in cinematográfico */}
      <div
        style={{
          width: '100%',
          height: '100%',
          transform: `scale(${cameraScale})`,
          transformOrigin: '50% 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Vinhetas superior e inferior para proteger o texto e a legenda */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background: 'linear-gradient(to bottom, rgba(15, 3, 6, 0.94) 0%, rgba(15, 3, 6, 0.6) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 520,
          background: 'linear-gradient(to top, rgba(11, 13, 19, 0.95) 0%, rgba(11, 13, 19, 0.5) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top HUD (Zona y = 175 a 420, rosto livre!) */}
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
          zIndex: 30,
        }}
      >
        {/* Badge do bloco: O PROBLEMA */}
        {sprBadge > 0.01 && (
          <div
            style={{
              padding: '8px 24px',
              backgroundColor: CORES.marca,
              borderRadius: 30,
              boxShadow: '0 6px 20px rgba(225, 29, 72, 0.5)',
              transform: `scale(${sprBadge})`,
              opacity: sprBadge,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              ⚠️ O PROBLEMA NO DELIVERY
            </span>
          </div>
        )}

        {/* Card 1: Mensagem no movimento (até a troca) */}
        {frame < tTroca && sprCard1 > 0.01 && (
          <div
            style={{
              padding: '14px 28px',
              backgroundColor: CORES.card_fundo,
              border: `1.5px solid ${CORES.borda_card}`,
              borderRadius: 20,
              boxShadow: '0 10px 25px rgba(0,0,0,0.8)',
              opacity: card1Opacity,
              maxWidth: 820,
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
              }}
            >
              MENSAGEM NO MOVIMENTO
            </span>
          </div>
        )}

        {/* Card 2: Sem resposta = pedido perdido */}
        {frame >= tTroca - 2 && frame < tDesistir && (
          <div
            style={{
              padding: '14px 30px',
              backgroundColor: 'rgba(225, 29, 72, 0.95)',
              border: '2px solid #FFFFFF',
              borderRadius: 20,
              boxShadow: '0 10px 30px rgba(225, 29, 72, 0.6)',
              transform: `scale(${alertPulse})`,
              opacity: card2Opacity,
              maxWidth: 860,
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
                textTransform: 'uppercase',
              }}
            >
              SEM RESPOSTA = PEDIDO PERDIDO
            </span>
          </div>
        )}

        {/* Card 3: Notificação flutuante de desistência do cliente em pop/bounce aos 4.6s */}
        {frame >= tDesistir && sprDesistirAlert > 0.01 && (
          <div
            style={{
              padding: '14px 32px',
              backgroundColor: '#DC2626',
              border: `2px solid ${CORES.apoio}`,
              borderRadius: 22,
              boxShadow: '0 12px 35px rgba(220, 38, 38, 0.75), 0 0 25px rgba(250, 204, 21, 0.4)',
              transform: `scale(${sprDesistirAlert * alertPulse})`,
              opacity: sprDesistirAlert,
              maxWidth: 880,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 34}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
                textTransform: 'uppercase',
              }}
            >
              DESISTÊNCIA POR FALTA DE RESPOSTA
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
