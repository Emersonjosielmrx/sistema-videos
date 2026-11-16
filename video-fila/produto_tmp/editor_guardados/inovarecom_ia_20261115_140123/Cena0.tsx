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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Immediate dynamic punch-in from 0-1.5s (0.90 -> 1.06, +17% zoom) + continuous camera motion across the scene
  const bgScale = interpolate(frame, [0, 36, 160], [0.90, 1.06, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 160], [-20, 24], {
    extrapolateRight: 'clamp',
  });
  // Positive translateY (110..90px) shifts the presenter down to guarantee generous headroom under top box
  const bgTranslateY = interpolate(frame, [0, 160], [110, 90], {
    extrapolateRight: 'clamp',
  });

  // Immediate hook entrance + dialer card animating right away from frame 0
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 115},
  });

  const questionSpring = spring({
    frame: Math.max(0, frame - 2),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  const cardSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 115},
  });

  // Animated exit slide-down + fade-out for the dialer card before Scene 1
  const cardExitY = interpolate(frame, [134, 152], [0, 160], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardExitOpacity = interpolate(frame, [134, 150], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Smooth exit transition into Scene 1
  const exitOpacity = interpolate(frame, [146, 159], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Keyword highlights synchronized with speech
  const isCansado = frame >= 44; // ~1.46s ("vive cansado")
  const isListas = frame >= 80; // ~2.66s ("discar para listas enormes")

  // Dynamic counter & progress bar evolving continuously from the first second until the end
  const currentContact = Math.floor(
    interpolate(frame, [10, 145], [42, 244], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );
  const barPercent = interpolate(frame, [10, 145], [18, 95], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const callStatuses = [
    {lead: 'Lead #142', status: 'Caixa postal • Pendente', cor: '#F59E0B'},
    {lead: 'Contato #189', status: 'Sem resposta • Rediscar', cor: '#EF4444'},
    {lead: 'Cliente #238', status: 'Ocupado • Fila manual', cor: '#EF4444'},
  ];
  const statusIdx = frame >= 100 ? 2 : frame >= 52 ? 1 : 0;
  const activeCall = callStatuses[statusIdx];

  // Sweeping ambient light behind cards for continuous visual motion (>4% change)
  const glowShiftY = interpolate(frame, [0, 160], [250, 1250]);

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
        opacity: exitOpacity,
        backgroundColor: '#071E12',
      }}
    >
      {/* Clearly Visible Presenter in Full-Screen Video with Smooth Ken Burns (no heavy blur or dark blackout) */}
      <OffthreadVideo
        src={staticFile('dono_1.mp4')}
        muted
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          filter: 'brightness(0.86) contrast(1.08) saturate(1.05)',
          transformOrigin: '50% 40%',
          transform: `scale(${bgScale}) translate(${bgTranslateX}px, ${bgTranslateY}px)`,
        }}
      />

      {/* Warm Corporate Emerald/Slate Gradient leaving the Presenter's Face (y=420..880) Bright & Clear */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(6, 26, 15, 0.88) 0%, rgba(6, 26, 15, 0.35) 24%, rgba(6, 26, 15, 0.12) 48%, rgba(6, 26, 15, 0.82) 72%, rgba(5, 20, 12, 0.95) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Moving Ambient Light Sweep to guarantee lively depth throughout the entire scene */}
      <div
        style={{
          position: 'absolute',
          top: glowShiftY,
          left: 540,
          width: 900,
          height: 420,
          transform: 'translate(-50%, -50%)',
          background:
            'radial-gradient(circle, rgba(239, 68, 68, 0.22) 0%, rgba(37, 211, 102, 0.12) 50%, transparent 75%)',
          filter: 'blur(30px)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Hook Banner (y=154..315) — Generous headroom for presenter's head/hair */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          zIndex: 10,
        }}
      >
        {/* Alert Pill */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            background: 'rgba(239, 68, 68, 0.28)',
            border: '2px solid #EF4444',
            borderRadius: 9999,
            padding: '6px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              lineHeight: 1,
              transform: `scale(${1 + 0.15 * Math.sin(frame * 0.3)})`,
            }}
          >
            ⚠️
          </span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}
          >
            Vendedores esgotados de ligar?
          </span>
        </div>

        {/* Clean Kinetic Question Headline */}
        <div
          style={{
            transform: `scale(${questionSpring})`,
            opacity: questionSpring,
            width: '100%',
            background: 'rgba(8, 22, 14, 0.90)',
            border: '2px solid rgba(255, 255, 255, 0.22)',
            borderRadius: 18,
            padding: '10px 20px',
            textAlign: 'center',
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.65)',
          }}
        >
          <div
            style={{
              fontSize: 38,
              fontWeight: 900,
              lineHeight: 1.18,
              color: '#FFFFFF',
              textWrap: 'balance',
            }}
          >
            Seu time de vendas{' '}
            <span
              style={{
                color: isCansado ? '#FF6B6B' : '#FFFFFF',
                background: isCansado ? 'rgba(239, 68, 68, 0.25)' : 'transparent',
                padding: '2px 8px',
                borderRadius: 8,
              }}
            >
              vive cansado
            </span>{' '}
            de discar para{' '}
            <span
              style={{
                color: isListas ? '#FBBF24' : '#E2E8F0',
                background: isListas ? 'rgba(245, 158, 11, 0.25)' : 'transparent',
                padding: '2px 8px',
                borderRadius: 8,
              }}
            >
              listas enormes?
            </span>
          </div>
        </div>
      </div>

      {/* Bottom Compact Single-Call Overload Widget (y=1220..1390) — Positioned lower on chest, completely clear of beard/chin and well above karaoke (y=1510) */}
      <div
        style={{
          position: 'absolute',
          top: 1220,
          left: 60,
          right: 60,
          zIndex: 10,
          transform: `scale(${cardSpring}) translateY(${
            interpolate(cardSpring, [0, 1], [40, 0]) + cardExitY
          }px)`,
          opacity: cardSpring * cardExitOpacity,
          background: 'rgba(10, 18, 26, 0.96)',
          border: '2.5px solid #EF4444',
          borderRadius: 22,
          padding: '16px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          boxShadow: '0 18px 45px rgba(0, 0, 0, 0.8)',
        }}
      >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              <span
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: 8,
                  backgroundColor: '#EF4444',
                  boxShadow: '0 0 12px #EF4444',
                  display: 'inline-block',
                }}
              />
              🎧 DISCAGEM MANUAL
            </div>
            <div
              style={{
                fontSize: 35,
                fontWeight: 900,
                color: '#FFFFFF',
                background: '#D97706',
                padding: '6px 18px',
                borderRadius: 12,
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
              }}
            >
              Contato {currentContact} de 250
            </div>
          </div>

          {/* Progress Bar */}
          <div
            style={{
              width: '100%',
              height: 14,
              borderRadius: 7,
              backgroundColor: 'rgba(255, 255, 255, 0.16)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${barPercent}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #F59E0B 0%, #EF4444 100%)',
                borderRadius: 7,
              }}
            />
          </div>

          {/* Single Active Contact Row (High contrast white text + bold status badge) */}
          <div
            style={{
              height: 72,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(22, 32, 46, 0.98)',
              borderLeft: `6px solid ${activeCall.cor}`,
              borderRadius: 14,
              padding: '0 18px',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span style={{fontSize: 34}}>📞</span>
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                {activeCall.lead}
              </span>
            </div>
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                background: activeCall.cor,
                padding: '6px 16px',
                borderRadius: 10,
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.4)',
              }}
            >
              {activeCall.status}
            </span>
          </div>
        </div>
    </div>
  );
};
