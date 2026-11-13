import React from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena0Pergunta: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // 0.0s to 5.17s

  // Continuous background camera movement
  const bgScale = interpolate(t, [0, 5.17], [1.02, 1.12], {extrapolateRight: 'clamp'});

  // Exit transition fade/slide at the end of scene (4.82 -> 5.17)
  const exitProgress = interpolate(t, [4.82, 5.15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const containerOpacity = 1 - exitProgress;
  const containerTranslateY = interpolate(exitProgress, [0, 1], [0, -50]);

  // Hook badge entry at t=0.05s
  const hookSpring = spring({
    frame: Math.max(0, frame - 1),
    fps,
    config: {damping: 14, stiffness: 160},
  });

  // Title block entry
  const titleSpring = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 14, stiffness: 145},
  });

  // Diagnostic comparison card enters smoothly at t=1.65s ('produto digital sem perder vendas')
  // This makes the initial hook (0 - 1.65s) a ultra-dynamic presenter + question hook, and then brings in the animated comparison card with slow zoom (1.0 -> 1.04)!
  const cardSpring = spring({
    frame: Math.max(0, frame - Math.round(1.45 * fps)),
    fps,
    config: {damping: 15, stiffness: 125},
  });

  // Staggered entry for row 2 synchronized with speech ('sem perder vendas' at 2.52s)
  const row2Spring = spring({
    frame: Math.max(0, frame - Math.round(2.35 * fps)),
    fps,
    config: {damping: 14, stiffness: 135},
  });

  const cardFloatY = Math.sin(t * 4.0) * 6;
  const cardContinuousScale = interpolate(t, [1.45, 5.17], [1.0, 1.04], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Word highlight states synchronized with speech
  const wComoApresentar = t >= 0.25;
  const wProdutoDigital = t >= 1.15;
  const wSemPerderVendas = t >= 2.52;

  // Continuous motion inside mockup card
  const pulseScale = 1 + Math.sin(t * 6.5) * 0.035;
  // Progress bar fills to 100% red on 'sem perder vendas' (2.52s -> 4.5s)
  const barFill = interpolate(t, [1.5, 2.52, 4.4], [25, 58, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#111827',
        opacity: containerOpacity,
        transform: `translateY(${containerTranslateY}px)`,
      }}
    >
      {/* Dynamic Background: Real Presenter B-roll starting from active frame (startFrom=30 -> 1.0s) so presenter is immediately visible from frame 0! */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale})`,
          }}
        />
      </AbsoluteFill>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          startFrom={30}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translateY(58px)`,
          }}
        />
      </AbsoluteFill>

      {/* Subtle top and bottom protective gradient keeping presenter's face & chest 100% clear in the center */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.22) 24%, rgba(17,24,39,0.0) 42%, rgba(17,24,39,0.12) 68%, rgba(17,24,39,0.86) 100%)',
        }}
      />

      {/* TOP ZONE (y=154 to y=435): Hook Pill + Main Question Title strictly above presenter's head (y>=485) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          fontFamily,
        }}
      >
        {/* Top Hook Pill: gancho_tela */}
        <div
          style={{
            alignSelf: 'flex-start',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid #F59E0B',
            borderRadius: 999,
            padding: '6px 22px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.55)',
            transform: `scale(${interpolate(hookSpring, [0, 1], [0.75, 1])}) translateY(${interpolate(hookSpring, [0, 1], [-20, 0])}px)`,
            opacity: hookSpring,
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: '#F59E0B',
              boxShadow: '0 0 12px #F59E0B',
              transform: `scale(${pulseScale})`,
            }}
          />
          <span
            style={{
              color: '#F59E0B',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 0.4,
            }}
          >
            Lançando seu produto digital?
          </span>
        </div>

        {/* Main Kinetic Question Box (fala da pergunta) */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.92)',
            border: '2px solid rgba(245, 158, 11, 0.55)',
            borderRadius: 24,
            padding: '16px 24px',
            boxShadow: '0 16px 40px rgba(0,0,0,0.65)',
            transform: `translateY(${interpolate(titleSpring, [0, 1], [25, 0])}px)`,
            opacity: titleSpring,
          }}
        >
          <div
            style={{
              fontSize: 40,
              fontWeight: 900,
              lineHeight: 1.18,
              color: '#FFFFFF',
              textWrap: 'balance',
            }}
          >
            <span style={{opacity: wComoApresentar ? 1 : 0.75}}>
              Como apresentar{' '}
            </span>
            <span
              style={{
                display: 'inline-block',
                background: wProdutoDigital ? '#F59E0B' : 'rgba(245, 158, 11, 0.24)',
                color: wProdutoDigital ? '#121216' : '#FFFFFF',
                padding: '2px 12px',
                borderRadius: 10,
                margin: '2px 0',
                transform: `scale(${wProdutoDigital ? 1 : 0.97})`,
              }}
            >
              meu novo produto digital
            </span>{' '}
            <span
              style={{
                display: 'inline-block',
                background: wSemPerderVendas ? '#EF4444' : 'rgba(239, 68, 68, 0.28)',
                color: '#FFFFFF',
                padding: '2px 12px',
                borderRadius: 10,
                marginTop: 4,
              }}
            >
              sem perder vendas?
            </span>
          </div>
        </div>
      </div>

      {/* LOWER DIAGNOSTIC CARD (y=1140 to y=1310): Enters at t=1.45s strictly below presenter's beard (y<=1070), leaving face and neck 100% clear. Slow zoom 1.0 -> 1.05, high contrast white text, red progress bar filling to 100%, ZERO empty skeletons */}
      <div
        style={{
          position: 'absolute',
          top: 1140,
          left: 60,
          right: 60,
          background: 'linear-gradient(145deg, rgba(17,24,39,0.96) 0%, rgba(30,41,59,0.96) 100%)',
          border: '2px solid #F59E0B',
          borderRadius: 24,
          padding: '16px 22px',
          boxShadow: '0 22px 55px rgba(0,0,0,0.8)',
          transform: `translateY(${interpolate(cardSpring, [0, 1], [50, 0]) + cardFloatY}px) scale(${interpolate(cardSpring, [0, 1], [0.92, 1]) * cardContinuousScale})`,
          opacity: cardSpring,
          fontFamily,
        }}
      >
        <div style={{display: 'flex', flexDirection: 'column', gap: 10}}>
          {/* Row 1: Seu Produto */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.96)',
              borderRadius: 16,
              padding: '12px 20px',
              border: '2px solid #F59E0B',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{color: '#F59E0B', fontSize: 34, fontWeight: 900}}>
              1. Seu Produto
            </span>
            <span style={{color: '#FFFFFF', fontSize: 34, fontWeight: 800}}>
              Pronto para lançar
            </span>
          </div>

          {/* Row 2: Sem Página (High contrast pure #FFFFFF on dark red/wine background) */}
          <div
            style={{
              background: wSemPerderVendas
                ? 'rgba(185, 28, 28, 0.96)'
                : 'rgba(30, 41, 59, 0.95)',
              borderRadius: 16,
              padding: '12px 20px',
              border: wSemPerderVendas ? '2px solid #EF4444' : '2px solid rgba(239, 68, 68, 0.55)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              transform: `translateY(${interpolate(row2Spring, [0, 1], [14, 0])}px) scale(${wSemPerderVendas ? pulseScale : 1})`,
              opacity: interpolate(row2Spring, [0, 1], [0.65, 1]),
            }}
          >
            <span style={{color: '#FFFFFF', fontSize: 34, fontWeight: 900}}>
              2. Sem Página
            </span>
            <span
              style={{
                background: wSemPerderVendas ? '#EF4444' : 'rgba(239, 68, 68, 0.35)',
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 900,
                padding: '4px 16px',
                borderRadius: 12,
              }}
            >
              Perde vendas
            </span>
          </div>
        </div>

        {/* Dynamic Animated Progress Bar filling to 100% red */}
        <div
          style={{
            marginTop: 12,
            width: '100%',
            height: 14,
            background: 'rgba(255,255,255,0.16)',
            borderRadius: 999,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${barFill}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #F59E0B 0%, #EF4444 100%)',
              borderRadius: 999,
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
