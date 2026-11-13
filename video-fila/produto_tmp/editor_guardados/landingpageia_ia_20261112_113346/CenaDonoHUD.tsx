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

export const CenaDonoHUD: React.FC<{
  cenaN: 1 | 2 | 3;
  videoSrc: string;
  duracaoCena: number;
  fontFamily: string;
}> = ({cenaN, videoSrc, duracaoCena, fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const localT = frame / fps;

  // Absolute time in the video based on scene start
  const sceneStart = cenaN === 1 ? 4.82 : cenaN === 2 ? 12.5 : 20.17;
  const absT = sceneStart + localT;

  // Entry & exit transitions
  const enterProgress = spring({
    frame,
    fps,
    config: {damping: 16, stiffness: 140},
  });
  const exitProgress = interpolate(
    localT,
    [duracaoCena - 0.32, duracaoCena],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Distinct camera framing across scenes 1, 2, and 3 to avoid monotonous static jump-cuts:
  // - Scene 1: Medium shot (1.0 -> 1.05, punch-in at 8.55s to 1.13)
  // - Scene 2: Immediate 1.16x close-up punch-in on entry + split composition during mockup demonstration where presenter shifts left so face & hands stay 100% clear while realistic Landing Page & Video Demo mockup displays on the right!
  // - Scene 3: Dynamic medium-close zoom (1.05 -> 1.11, punch-in at 23.4s to 1.20)
  const isPunchInCena1 = cenaN === 1 && absT >= 8.55;
  const isPunchInCena3 = cenaN === 3 && absT >= 23.4;

  // In Scene 2, show the side-by-side high-fidelity product mockup starting from 13.0s
  const mockupProgress =
    cenaN === 2
      ? spring({
          frame: Math.max(0, frame - Math.round((13.0 - 12.5) * fps)),
          fps,
          config: {damping: 15, stiffness: 120},
        })
      : 0;

  const videoScale =
    cenaN === 1
      ? isPunchInCena1
        ? interpolate(localT, [3.73, duracaoCena], [1.12, 1.17], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        : interpolate(localT, [0, 3.73], [1.0, 1.05], {extrapolateRight: 'clamp'})
      : cenaN === 2
      ? interpolate(localT, [0, duracaoCena], [1.16, 1.24], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : isPunchInCena3
      ? interpolate(localT, [3.23, duracaoCena], [1.16, 1.22], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : interpolate(localT, [0, 3.23], [1.05, 1.11], {extrapolateRight: 'clamp'});

  const videoTranslateY = cenaN === 1 ? 68 : cenaN === 2 ? 78 : 64;
  // Shift presenter to the left in Scene 2 when the high-fidelity mockup enters on the right, keeping presenter's face & hands completely unobstructed
  const videoTranslateX =
    cenaN === 2 ? interpolate(mockupProgress, [0, 1], [0, -210]) : 0;

  const hudTranslateY =
    interpolate(enterProgress, [0, 1], [-40, 0]) +
    interpolate(exitProgress, [0, 1], [0, -40]);
  const hudOpacity = enterProgress * (1 - exitProgress);

  // Continuous subtle progress bar inside top card
  const progressPct = interpolate(localT, [0, duracaoCena], [8, 100], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: 1 - exitProgress * 0.95}}>
      {/* Fullscreen Owner Video - Face strictly protected */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile(videoSrc)}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${videoScale}) translate(${videoTranslateX}px, ${videoTranslateY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Subtle top and bottom protective gradient for high contrast without darkening the presenter */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.20) 22%, rgba(17,24,39,0.0) 45%, rgba(17,24,39,0.0) 75%, rgba(17,24,39,0.76) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Graphic HUD strictly between y=154 and y=405 (head top is at y>=485) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          transform: `translateY(${hudTranslateY}px)`,
          opacity: hudOpacity,
          fontFamily,
        }}
      >
        {cenaN === 1 && (
          <HUDCena1 absT={absT} frame={frame} fps={fps} progressPct={progressPct} />
        )}
        {cenaN === 2 && (
          <HUDCena2 absT={absT} frame={frame} fps={fps} progressPct={progressPct} />
        )}
        {cenaN === 3 && (
          <HUDCena3 absT={absT} frame={frame} fps={fps} progressPct={progressPct} />
        )}
      </div>

      {/* Scene 2 Right-Side High-Fidelity Smartphone Landing Page & Video Demo Mockup (x=540..1020, y=445..1245) - Zero overlap with presenter's face or hands on the left! */}
      {cenaN === 2 && (
        <MockupCelularCena2
          absT={absT}
          frame={frame}
          fps={fps}
          fontFamily={fontFamily}
          enterProgress={mockupProgress}
        />
      )}
    </AbsoluteFill>
  );
};

/* ---------------- CENA 1: O PROBLEMA (4.82s - 12.85s) ---------------- */
const HUDCena1: React.FC<{
  absT: number;
  frame: number;
  fps: number;
  progressPct: number;
}> = ({absT, frame, fps, progressPct}) => {
  const fase2 = absT >= 8.55;
  const fase3 = absT >= 11.1;

  const card2Spring = spring({
    frame: Math.max(0, frame - Math.round((8.55 - 4.82) * fps)),
    fps,
    config: {damping: 14, stiffness: 150},
  });

  return (
    <div
      style={{
        background: 'rgba(17, 24, 39, 0.92)',
        border: '2px solid rgba(245, 158, 11, 0.65)',
        borderRadius: 26,
        padding: '18px 26px',
        boxShadow: '0 16px 40px rgba(0,0,0,0.65)',
      }}
    >
      {/* Top Header Row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 14,
        }}
      >
        <div
          style={{
            background: '#F59E0B',
            color: '#121216',
            fontSize: 32,
            fontWeight: 900,
            padding: '4px 18px',
            borderRadius: 999,
            textTransform: 'uppercase',
          }}
        >
          O problema
        </div>
        <div
          style={{
            color: '#F8FAFC',
            fontSize: 32,
            fontWeight: 700,
          }}
        >
          {fase3 ? 'Primeiros clientes' : fase2 ? 'Desafio na apresentação' : 'Produto criado'}
        </div>
      </div>

      {/* Split Comparison inside HUD */}
      <div style={{display: 'flex', gap: 16, alignItems: 'center'}}>
        <div
          style={{
            flex: 1,
            background: 'rgba(16, 185, 129, 0.16)',
            border: '2px solid #10B981',
            borderRadius: 18,
            padding: '12px 18px',
          }}
        >
          <div style={{color: '#ECFDF5', fontSize: 34, fontWeight: 800}}>
            ✓ Produto criado
          </div>
        </div>

        <div
          style={{
            flex: 1.35,
            background: fase2 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(30, 41, 59, 0.95)',
            border: fase2 ? '2px solid #EF4444' : '2px solid rgba(255,255,255,0.45)',
            borderRadius: 18,
            padding: '12px 18px',
            transform: `scale(${fase2 ? interpolate(card2Spring, [0, 1], [0.92, 1]) : 1})`,
          }}
        >
          <div
            style={{
              color: fase2 ? '#FFFFFF' : 'rgba(255, 255, 255, 0.88)',
              fontSize: 34,
              fontWeight: 800,
              whiteSpace: 'nowrap',
            }}
          >
            {fase2 ? 'Como apresentar?' : 'Próximo passo...'}
          </div>
        </div>
      </div>

      {/* Bottom live progress indicator */}
      <div
        style={{
          marginTop: 12,
          height: 6,
          width: '100%',
          background: 'rgba(255,255,255,0.12)',
          borderRadius: 99,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${progressPct}%`,
            height: '100%',
            background: '#F59E0B',
          }}
        />
      </div>
    </div>
  );
};

/* ---------------- CENA 2: COMO FUNCIONA (12.50s - 20.52s) ---------------- */
const HUDCena2: React.FC<{
  absT: number;
  frame: number;
  fps: number;
  progressPct: number;
}> = ({absT, progressPct}) => {
  // Step 1: "landing page pronta" (14.26s)
  // Step 2: "vídeo demo" (15.98s)
  // Step 3: "transformar visita em cliente" (17.14s)
  const currentStep = absT >= 17.1 ? 3 : absT >= 15.85 ? 2 : 1;

  // Strictly consistent nomenclature between header status and step tabs!
  const etapaTitulo =
    currentStep === 3
      ? 'Etapa 3/3 · Vendas'
      : currentStep === 2
      ? 'Etapa 2/3 · Vídeo'
      : 'Etapa 1/3 · Página';

  const steps = [
    {num: 1, label: 'Página'},
    {num: 2, label: 'Vídeo'},
    {num: 3, label: 'Vendas'},
  ];

  return (
    <div
      style={{
        background: 'rgba(17, 24, 39, 0.94)',
        border: '2px solid #F59E0B',
        borderRadius: 26,
        padding: '16px 22px',
        boxShadow: '0 16px 40px rgba(0,0,0,0.65)',
      }}
    >
      {/* Top Header Row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
        }}
      >
        <div
          style={{
            background: '#F59E0B',
            color: '#121216',
            fontSize: 32,
            fontWeight: 900,
            padding: '4px 18px',
            borderRadius: 999,
            textTransform: 'uppercase',
          }}
        >
          Como funciona
        </div>
        <div
          style={{
            color: '#F59E0B',
            fontSize: 33,
            fontWeight: 800,
          }}
        >
          {etapaTitulo}
        </div>
      </div>

      {/* 3 Sequential Steps Row with active highlight strictly on current step */}
      <div style={{display: 'flex', gap: 12}}>
        {steps.map((s) => {
          const isCurrent = currentStep === s.num;
          const isDone = currentStep > s.num;
          return (
            <div
              key={s.num}
              style={{
                flex: 1,
                background: isCurrent
                  ? '#F59E0B'
                  : isDone
                  ? 'rgba(16, 185, 129, 0.22)'
                  : 'rgba(30, 41, 59, 0.92)',
                color: isCurrent ? '#121216' : '#FFFFFF',
                borderRadius: 16,
                padding: '12px 14px',
                border: isCurrent
                  ? '3px solid #FEF08A'
                  : isDone
                  ? '2px solid #10B981'
                  : '2px solid rgba(255,255,255,0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
              }}
            >
              <span style={{fontSize: 33, fontWeight: 900}}>
                {isDone ? '✓' : `${s.num}.`}
              </span>
              <span style={{fontSize: 33, fontWeight: 800, whiteSpace: 'nowrap'}}>
                {s.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Subtle bottom progress bar */}
      <div
        style={{
          marginTop: 10,
          height: 5,
          width: '100%',
          background: 'rgba(255,255,255,0.12)',
          borderRadius: 99,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${progressPct}%`,
            height: '100%',
            background: '#F59E0B',
          }}
        />
      </div>
    </div>
  );
};

/* ---------------- CENA 2 MOCKUP REAL: SMARTPHONE COM LANDING PAGE ROLANDO + VÍDEO DEMO + VENDAS ---------------- */
const MockupCelularCena2: React.FC<{
  absT: number;
  frame: number;
  fps: number;
  fontFamily: string;
  enterProgress: number;
}> = ({absT, frame, fps, fontFamily, enterProgress}) => {
  const currentStep = absT >= 17.1 ? 3 : absT >= 15.85 ? 2 : 1;

  // Smooth vertical slide transitions between the 3 stages inside the smartphone landing page:
  const step2Slide = spring({
    frame: Math.max(0, frame - Math.round((15.85 - 12.5) * fps)),
    fps,
    config: {damping: 15, stiffness: 120},
  });
  const step3Slide = spring({
    frame: Math.max(0, frame - Math.round((17.1 - 12.5) * fps)),
    fps,
    config: {damping: 15, stiffness: 120},
  });

  // Scroll stops cleanly on whole cards:
  // Step 1: 0px (Card 1 visible)
  // Step 2: -204px (Card 2 visible)
  // Step 3: -408px (Card 3 visible cleanly)
  const pageScrollY = interpolate(step2Slide, [0, 1], [0, -204]) + interpolate(step3Slide, [0, 1], [0, -204]);

  const floatY = Math.sin((frame / fps) * 4.2) * 8;
  const playPulse = 1 + Math.sin((frame / fps) * 7.5) * 0.06;

  return (
    <div
      style={{
        position: 'absolute',
        top: 470,
        right: 60,
        width: 460,
        height: 520,
        background: '#0F172A',
        border: '4px solid #F59E0B',
        borderRadius: 42,
        padding: '18px 18px',
        boxShadow: '0 28px 65px rgba(0,0,0,0.85)',
        display: 'flex',
        flexDirection: 'column',
        transform: `translateX(${interpolate(enterProgress, [0, 1], [120, 0])}px) translateY(${interpolate(enterProgress, [0, 1], [40, 0]) + floatY}px) scale(${interpolate(enterProgress, [0, 1], [0.9, 1])})`,
        opacity: enterProgress,
        fontFamily,
        overflow: 'hidden',
      }}
    >
      {/* Smartphone Top Speaker / Status Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingBottom: 14,
          marginBottom: 12,
          borderBottom: '2px solid rgba(255,255,255,0.14)',
        }}
      >
        <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
          <div style={{width: 14, height: 14, borderRadius: 7, background: '#10B981'}} />
          <span style={{color: '#F8FAFC', fontSize: 32, fontWeight: 900}}>
            {currentStep === 3 ? '3. Vendas' : currentStep === 2 ? '2. Vídeo' : '1. Página'}
          </span>
        </div>
        <div
          style={{
            width: 58,
            height: 10,
            borderRadius: 99,
            background: 'rgba(255,255,255,0.25)',
          }}
        />
      </div>

      {/* Scrolling Landing Page Viewport */}
      <div style={{flex: 1, overflow: 'hidden', position: 'relative'}}>
        <div
          style={{
            transform: `translateY(${pageScrollY}px)`,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* SECTION 1: HERO DA LANDING PAGE PRONTA (exact height 186px) */}
          <div
            style={{
              height: 186,
              boxSizing: 'border-box',
              background:
                currentStep === 1
                  ? 'linear-gradient(145deg, rgba(245,158,11,0.26) 0%, rgba(30,41,59,0.98) 100%)'
                  : 'rgba(30, 41, 59, 0.92)',
              border:
                currentStep === 1
                  ? '3px solid #F59E0B'
                  : '2px solid rgba(255,255,255,0.16)',
              borderRadius: 24,
              padding: '16px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div
              style={{
                alignSelf: 'flex-start',
                background: '#F59E0B',
                color: '#121216',
                fontSize: 32,
                fontWeight: 900,
                padding: '4px 14px',
                borderRadius: 10,
              }}
            >
              1. Página
            </div>
            <div
              style={{
                color: '#FFFFFF',
                fontSize: 35,
                fontWeight: 900,
                lineHeight: 1.18,
              }}
            >
              Landing Page Pronta
            </div>
            <div
              style={{
                height: 14,
                width: '78%',
                borderRadius: 99,
                background: 'rgba(245, 158, 11, 0.55)',
              }}
            />
          </div>

          {/* SECTION 2: PLAYER DE VÍDEO DEMO INTEGRADO NA PÁGINA */}
          <div
            style={{
              background:
                currentStep === 2
                  ? 'linear-gradient(145deg, rgba(245,158,11,0.28) 0%, rgba(15,23,42,0.98) 100%)'
                  : 'rgba(30, 41, 59, 0.92)',
              border:
                currentStep === 2
                  ? '3px solid #F59E0B'
                  : '2px solid rgba(255,255,255,0.16)',
              borderRadius: 24,
              padding: '20px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <span style={{color: '#F59E0B', fontSize: 33, fontWeight: 900}}>
                2. Vídeo Demo
              </span>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: '50%',
                  background: '#F59E0B',
                  color: '#121216',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  fontWeight: 900,
                  transform: `scale(${currentStep === 2 ? playPulse : 1})`,
                  boxShadow: currentStep === 2 ? '0 0 22px rgba(245,158,11,0.7)' : 'none',
                }}
              >
                ▶
              </div>
            </div>
            <div style={{color: '#FFFFFF', fontSize: 33, fontWeight: 800}}>
              Apresentar Produto
            </div>
            {/* Video timeline bar */}
            <div
              style={{
                height: 10,
                width: '100%',
                background: 'rgba(255,255,255,0.18)',
                borderRadius: 99,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: currentStep >= 2 ? '75%' : '25%',
                  height: '100%',
                  background: '#F59E0B',
                }}
              />
            </div>
          </div>

          {/* SECTION 3: BLOCO DE CONVERSÃO / VENDAS (VISITA EM CLIENTE) */}
          <div
            style={{
              background:
                currentStep === 3
                  ? 'linear-gradient(145deg, rgba(16,185,129,0.32) 0%, rgba(15,23,42,0.98) 100%)'
                  : 'rgba(30, 41, 59, 0.92)',
              border:
                currentStep === 3
                  ? '3px solid #10B981'
                  : '2px solid rgba(255,255,255,0.16)',
              borderRadius: 24,
              padding: '20px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <div style={{color: '#A7F3D0', fontSize: 32, fontWeight: 900}}>
              3. Vendas
            </div>
            <div
              style={{
                background: currentStep === 3 ? '#10B981' : 'rgba(16, 185, 129, 0.25)',
                color: currentStep === 3 ? '#121216' : '#FFFFFF',
                borderRadius: 16,
                padding: '14px 16px',
                fontSize: 33,
                fontWeight: 900,
                textAlign: 'center',
                boxShadow: currentStep === 3 ? '0 0 24px rgba(16,185,129,0.55)' : 'none',
              }}
            >
              ✓ Visita em Cliente
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ---------------- CENA 3: O RESULTADO (20.17s - 28.19s) ---------------- */
const HUDCena3: React.FC<{
  absT: number;
  frame: number;
  fps: number;
  progressPct: number;
}> = ({absT, frame, fps, progressPct}) => {
  // Phase 1 (20.17s): "Hoje tenho uma página de vendas pronta"
  // Phase 2 (23.40s): "que vende" (validation bounce & glow)
  // Phase 3 (25.10s): "e uma comunicação clara no mercado"
  const phase2 = absT >= 23.4;
  const phase3 = absT >= 25.1;

  const phase2Spring = spring({
    frame: Math.max(0, frame - Math.round((23.4 - 20.17) * fps)),
    fps,
    config: {damping: 12, stiffness: 160},
  });

  const phase3Spring = spring({
    frame: Math.max(0, frame - Math.round((25.1 - 20.17) * fps)),
    fps,
    config: {damping: 13, stiffness: 155},
  });

  const checkBounce = 1 + Math.sin((frame / fps) * 8) * 0.08;

  const statusRight = phase3
    ? 'Comunicação no mercado'
    : phase2
    ? 'Página pronta que vende ✓'
    : 'Página de vendas pronta';

  return (
    <div
      style={{
        background: 'rgba(17, 24, 39, 0.94)',
        border: '2px solid #10B981',
        borderRadius: 26,
        padding: '18px 24px',
        boxShadow: '0 16px 40px rgba(0,0,0,0.65)',
      }}
    >
      {/* Top Header Row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 14,
        }}
      >
        <div
          style={{
            background: '#10B981',
            color: '#121216',
            fontSize: 32,
            fontWeight: 900,
            padding: '4px 18px',
            borderRadius: 999,
            textTransform: 'uppercase',
          }}
        >
          O resultado
        </div>
        <div
          style={{
            color: phase3 ? '#FDE68A' : '#A7F3D0',
            fontSize: 32,
            fontWeight: 800,
            transform: `scale(${phase2 && !phase3 ? interpolate(phase2Spring, [0, 0.5, 1], [1, 1.06, 1]) : 1})`,
          }}
        >
          {statusRight}
        </div>
      </div>

      {/* Result Badges Row */}
      <div style={{display: 'flex', gap: 14}}>
        <div
          style={{
            flex: 1,
            background: phase2
              ? 'rgba(245, 158, 11, 0.28)'
              : 'rgba(245, 158, 11, 0.16)',
            border: phase2 ? '3px solid #F59E0B' : '2px solid rgba(245,158,11,0.65)',
            borderRadius: 18,
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: phase2 ? '0 0 22px rgba(245,158,11,0.35)' : 'none',
            transform: `scale(${phase2 ? interpolate(phase2Spring, [0, 1], [0.94, 1]) : 1})`,
          }}
        >
          <span
            style={{
              color: '#F59E0B',
              fontSize: 34,
              fontWeight: 900,
              display: 'inline-block',
              transform: `scale(${checkBounce})`,
            }}
          >
            ✓
          </span>
          <span style={{color: '#FFFFFF', fontSize: 33, fontWeight: 800, whiteSpace: 'nowrap'}}>
            Página que vende
          </span>
        </div>

        <div
          style={{
            flex: 1,
            background: phase3
              ? 'rgba(16, 185, 129, 0.28)'
              : 'rgba(30, 41, 59, 0.90)',
            border: phase3
              ? '3px solid #10B981'
              : '2px solid rgba(255,255,255,0.22)',
            borderRadius: 18,
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: phase3 ? '0 0 22px rgba(16,185,129,0.4)' : 'none',
            transform: `scale(${phase3 ? interpolate(phase3Spring, [0, 1], [0.92, 1]) : 1})`,
          }}
        >
          <span
            style={{
              color: phase3 ? '#10B981' : '#94A3B8',
              fontSize: 34,
              fontWeight: 900,
              display: 'inline-block',
              transform: `scale(${phase3 ? checkBounce : 1})`,
            }}
          >
            ✓
          </span>
          <span
            style={{
              color: '#FFFFFF',
              fontSize: 33,
              fontWeight: 800,
              whiteSpace: 'nowrap',
            }}
          >
            Comunicação clara
          </span>
        </div>
      </div>

      {/* Bottom live progress bar */}
      <div
        style={{
          marginTop: 12,
          height: 5,
          width: '100%',
          background: 'rgba(255,255,255,0.12)',
          borderRadius: 99,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${progressPct}%`,
            height: '100%',
            background: '#10B981',
          }}
        />
      </div>
    </div>
  );
};
