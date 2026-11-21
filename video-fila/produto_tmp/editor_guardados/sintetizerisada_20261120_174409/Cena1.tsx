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

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Smooth entrance zoom push (1.08 -> 1.0) and fade over first 12 frames to connect seamlessly from Cena 0
  const entrancePush = interpolate(frame, [0, 12], [1.08, 1.0], {
    extrapolateRight: 'clamp',
  });
  const entranceOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Dramatic Punch-in of 15% exactly on the virada de fala at frame 110 ("e o horário já estava perdido")
  const punchScale = frame >= 110 ? 1.15 : 1.0;
  const baseScale = interpolate(
    frame,
    [0, 109, 110, 241],
    [1.0, 1.04, 1.0, 1.05],
    {extrapolateRight: 'clamp'}
  );
  const videoScale = baseScale * punchScale;

  // Top badge entrance
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Determine which phase/message is active according to speech timing:
  // 0-109 (4.89s-8.5s): "Eu acordava com mensagens de cancelamento da madrugada"
  // 110-174 (8.5s-10.7s): "e o horário já estava perdido." (punch-in frame 110)
  // 175+ (10.7s-12.91s): "Ninguém para ocupar a vaga."
  const phase = frame < 110 ? 0 : frame < 175 ? 1 : 2;

  // Springs for each phase transition
  const spring0 = spring({frame, fps, config: {damping: 12, stiffness: 100}});
  const spring1 = spring({
    frame: frame - 110,
    fps,
    config: {damping: 12, stiffness: 110},
  });
  const spring2 = spring({
    frame: frame - 175,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Micro-motion float
  const microFloat = Math.sin(frame / 12) * 4;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        transform: `scale(${entrancePush})`,
        opacity: entranceOpacity,
      }}
    >
      {/* Speaker Video in Full Screen */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 40%',
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
      </div>

      {/* Top Protective Gradient to guarantee >= 4.5:1 contrast strictly in y: 0 - 450 */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 460,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.78) 50%, rgba(15,23,42,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Category Badge (y: 165 - 225) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: '#1F2937',
            border: '2px solid #FFA94D',
            padding: '10px 24px',
            borderRadius: 999,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#FFA94D',
              boxShadow: '0 0 12px #FFA94D',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFA94D',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            O Problema • Relato Real
          </span>
        </div>
      </div>

      {/* Headline Card Strictly in y: 245 - 415 (NEVER covers speaker face below 480) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 80,
          right: 80,
          height: 165,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          transform: `translateY(${microFloat}px)`,
          zIndex: 20,
        }}
      >
        {phase === 0 && (
          <div
            style={{
              backgroundColor: 'rgba(31, 41, 55, 0.95)',
              border: '2px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 22,
              padding: '16px 24px',
              textAlign: 'center',
              boxShadow: '0 16px 36px rgba(0,0,0,0.7)',
              transform: `scale(${spring0})`,
              opacity: spring0,
              width: '100%',
              maxWidth: 920,
              boxSizing: 'border-box',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '-0.5px',
                textTransform: 'uppercase',
                textWrap: 'balance',
              }}
            >
              Mensagens na Madrugada
            </div>
            <div
              style={{
                marginTop: 6,
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#FFA94D',
              }}
            >
              Cancelamentos fora do expediente
            </div>
          </div>
        )}

        {phase === 1 && (
          <div
            style={{
              backgroundColor: 'rgba(31, 41, 55, 0.95)',
              border: '2px solid #EF4444',
              borderRadius: 22,
              padding: '16px 24px',
              textAlign: 'center',
              boxShadow: '0 16px 36px rgba(239, 68, 68, 0.35)',
              transform: `scale(${spring1})`,
              opacity: spring1,
              width: '100%',
              maxWidth: 920,
              boxSizing: 'border-box',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '-0.5px',
                textTransform: 'uppercase',
                textWrap: 'balance',
              }}
            >
              Horário Já Estava Perdido <span style={{color: '#EF4444'}}>❌</span>
            </div>
            <div
              style={{
                marginTop: 6,
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#E5E7EB',
              }}
            >
              Sem tempo hábil para encaixe
            </div>
          </div>
        )}

        {phase === 2 && (
          <div
            style={{
              backgroundColor: 'rgba(31, 41, 55, 0.95)',
              border: '2px solid #F59E0B',
              borderRadius: 22,
              padding: '16px 24px',
              textAlign: 'center',
              boxShadow: '0 16px 36px rgba(245, 158, 11, 0.35)',
              transform: `scale(${spring2})`,
              opacity: spring2,
              width: '100%',
              maxWidth: 920,
              boxSizing: 'border-box',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 900,
                color: '#FDE68A',
                letterSpacing: '-0.5px',
                textTransform: 'uppercase',
                textWrap: 'balance',
              }}
            >
              Ninguém para Ocupar a Vaga 📉
            </div>
            <div
              style={{
                marginTop: 6,
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#F3F4F6',
              }}
            >
              Horário vago e faturamento perdido
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
