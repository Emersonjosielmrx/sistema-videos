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

export const Cena3: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Cortes de aproximação cinematográfica (punch-in zoom de 10% a 15%) nas mudanças de frase
  const tChega = Math.round(2.73 * fps); // frame 82: "mensagem com o pedido chega"
  const tTempo = Math.round(5.4 * fps); // frame 162: "sem tomar meu tempo"

  const cameraScale =
    frame < tChega
      ? interpolate(frame, [0, tChega], [1.06, 1.11], {extrapolateRight: 'clamp'})
      : frame < tTempo
      ? interpolate(frame, [tChega, tTempo], [1.18, 1.23], {extrapolateRight: 'clamp'})
      : interpolate(frame, [tTempo, 8.19 * fps], [1.26, 1.30], {extrapolateRight: 'clamp'});

  const sprBadge = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const sprCard1 = spring({frame: frame - 0.6 * fps, fps, config: {damping: 14, stiffness: 120}});
  const sprNotif = spring({frame: frame - tChega, fps, config: {damping: 14, stiffness: 150}});
  const sprZero = spring({frame: frame - tTempo, fps, config: {damping: 14, stiffness: 140}});

  const pulseSuccess = 1 + Math.sin(frame * 0.2) * 0.03;

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', overflow: 'hidden'}}>
      {/* Vídeo do dono */}
      <div
        style={{
          width: '100%',
          height: '100%',
          transform: `scale(${cameraScale})`,
          transformOrigin: '50% 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Vinhetas */}
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

      {/* Top HUD (y = 175 a 420, rosto livre!) */}
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
        {/* Rótulo: O RESULTADO */}
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
              ✅ O RESULTADO NA PRÁTICA
            </span>
          </div>
        )}

        {/* Card 1: Escolha simples */}
        {frame < tChega && sprCard1 > 0.01 && (
          <div
            style={{
              padding: '12px 28px',
              backgroundColor: CORES.card_fundo,
              border: `1.5px solid ${CORES.borda_card}`,
              borderRadius: 20,
              boxShadow: '0 10px 25px rgba(0,0,0,0.8)',
              transform: `translateY(${(1 - sprCard1) * -15}px)`,
              opacity: sprCard1,
              maxWidth: 820,
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              ESCOLHA SIMPLES E ÁGIL
            </span>
          </div>
        )}

        {/* Card 2: B-roll animado de notificação de pedido chegando na prática */}
        {frame >= tChega && frame < tTempo && sprNotif > 0.01 && (
          <div
            style={{
              padding: '12px 24px',
              backgroundColor: '#064E3B',
              border: '2px solid #34D399',
              borderRadius: 22,
              boxShadow: '0 14px 35px rgba(6, 78, 59, 0.7), 0 0 25px rgba(52, 211, 153, 0.4)',
              transform: `scale(${pulseSuccess * sprNotif})`,
              opacity: sprNotif,
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
              maxWidth: 880,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span style={{fontSize: 28}}>🔔</span>
              <span style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#FFFFFF', textTransform: 'uppercase'}}>
                Pedido chega no WhatsApp
              </span>
            </div>
            <div style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#A7F3D0', paddingLeft: 38}}>
              Notificação direta com itens e endereço confirmados ✓
            </div>
          </div>
        )}

        {/* Card 3: Badge de resultado - SEM TOMAR MEU TEMPO */}
        {frame >= tTempo && sprZero > 0.01 && (
          <div
            style={{
              padding: '14px 32px',
              backgroundColor: CORES.apoio,
              border: '2px solid #FFFFFF',
              borderRadius: 22,
              boxShadow: '0 12px 30px rgba(250, 204, 21, 0.5)',
              transform: `scale(${sprZero})`,
              opacity: sprZero,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              maxWidth: 880,
            }}
          >
            <span style={{fontSize: 36}}>⏱️</span>
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#111111',
                letterSpacing: '0.02em',
                textTransform: 'uppercase',
              }}
            >
              SEM TOMAR MEU TEMPO
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
