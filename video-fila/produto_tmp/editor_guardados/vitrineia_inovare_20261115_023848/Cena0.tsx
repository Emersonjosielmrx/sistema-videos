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

export const Cena0: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // 0.0 to 4.5s

  // Continuous slow zoom/Ken Burns (1.03x -> 1.14x) + horizontal pan across Scene 0
  const bgScale = interpolate(t, [0, 4.5], [1.03, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgX = interpolate(t, [0, 4.5], [-16, 20], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(t, [0, 4.5], [18, 6], {
    extrapolateRight: 'clamp',
  });

  // Exit transition (4.15s -> 4.50s)
  const exitOpacity = interpolate(t, [4.15, 4.48], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitY = interpolate(t, [4.15, 4.48], [0, -40], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Single clean kinetic hook question in the first 2 seconds (no redundant pills or stacked chat boxes)
  const titleIn = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  const duvidaAtiva = t >= 0.98;
  const desisteAtivo = t >= 1.56;

  // Stage 1 (t >= 2.00s, visible in q02 at 2.25s): Status bar appears at y=1160 (well below face/chin!)
  // Stage 2 (t >= 2.55s, between q02 and q03 at 3.60s): Dynamic spring entrance of 'Venda perdida' stamp!
  const cardVisivel = t >= 2.0;
  const vendaPerdidaAtiva = t >= 2.55;

  const cardIn = spring({
    frame: Math.max(0, frame - Math.round(2.0 * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  const seloPerdaSpring = spring({
    frame: Math.max(0, frame - Math.round(2.55 * fps)),
    fps,
    config: {damping: 10, stiffness: 180},
  });

  // Continuous floating & pulse so q02 -> q03 is full of life
  const floatY = Math.sin(t * 4.8) * 10;
  const pulseAlert = 1 + Math.sin(t * 8.5) * 0.055;

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: exitOpacity}}>
      {/* Live store owner gesturing in electronics store with continuous Ken Burns motion */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transformOrigin: '50% 25%',
            transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Top and bottom contrast gradients keeping presenter's entire face & chest bright and unobstructed */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.88) 0%, rgba(17,24,39,0.35) 24%, rgba(17,24,39,0.0) 50%, rgba(17,24,39,0.88) 100%)',
        }}
      />

      {/* SINGLE CLEAN HOOK QUESTION IN TOP ZONE (y=162..375) */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(titleIn, [0, 1], [-32, 0]) + exitY}px) scale(${interpolate(titleIn, [0, 1], [0.92, 1])})`,
          opacity: titleIn,
        }}
      >
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(17, 24, 39, 0.93)',
            border: `2.5px solid ${desisteAtivo ? '#EF4444' : '#A78BFA'}`,
            borderRadius: 28,
            padding: '18px 26px',
            boxShadow: '0 18px 40px rgba(0,0,0,0.6)',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.16,
              color: '#FFFFFF',
              textWrap: 'balance',
            }}
          >
            Cliente fica{' '}
            <span
              style={{
                display: 'inline-block',
                padding: '2px 12px',
                borderRadius: 12,
                backgroundColor: duvidaAtiva
                  ? '#A78BFA'
                  : 'rgba(255,255,255,0.12)',
                color: duvidaAtiva ? '#121216' : '#FFFFFF',
              }}
            >
              em dúvida
            </span>{' '}
            e{' '}
            <span
              style={{
                display: 'inline-block',
                padding: '2px 12px',
                borderRadius: 12,
                backgroundColor: desisteAtivo
                  ? '#EF4444'
                  : 'rgba(255,255,255,0.12)',
                color: '#FFFFFF',
              }}
            >
              desiste da compra?
            </span>
          </div>
        </div>
      </div>

      {/* LOWER CHEST/WAIST STATUS CARD at y=1165 (100% below face, chin & neck, and above Karaoke at y=1380) */}
      {cardVisivel && (
        <div
          style={{
            position: 'absolute',
            top: 1165,
            left: 60,
            right: 60,
            transform: `translateY(${interpolate(cardIn, [0, 1], [50, 0]) + floatY + exitY}px) scale(${interpolate(cardIn, [0, 1], [0.86, 1])})`,
            opacity: cardIn,
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            borderRadius: 26,
            border: `3px solid ${vendaPerdidaAtiva ? '#EF4444' : '#A78BFA'}`,
            padding: '18px 26px',
            boxShadow: '0 22px 48px rgba(0,0,0,0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                backgroundColor: vendaPerdidaAtiva ? '#EF4444' : '#A78BFA',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily,
                fontSize: 33,
                fontWeight: 900,
                color: vendaPerdidaAtiva ? '#FFFFFF' : '#121216',
                transform: `scale(${pulseAlert})`,
              }}
            >
              {vendaPerdidaAtiva ? '✕' : '?'}
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              {vendaPerdidaAtiva
                ? 'Saiu sem comprar'
                : 'Cliente indeciso na loja'}
            </span>
          </div>

          {/* 'Venda perdida' dynamic stamp springing in between q02 (2.25s) and q03 (3.60s) */}
          {vendaPerdidaAtiva && (
            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                backgroundColor: '#EF4444',
                padding: '10px 24px',
                borderRadius: 999,
                transform: `scale(${interpolate(seloPerdaSpring, [0, 0.6, 1], [0.3, 1.18, 1]) * pulseAlert})`,
                boxShadow: '0 10px 26px rgba(239, 68, 68, 0.6)',
                whiteSpace: 'nowrap',
              }}
            >
              Venda perdida
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};
