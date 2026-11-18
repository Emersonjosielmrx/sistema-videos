import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous Ken Burns slow zoom & pan across the entire Scene 3 (never freezes between q10, q11, q12)
  // Shifted up (translateY -245 -> -285) so the 3 commercial team members' faces sit at y=350..660, 100% clear of the CRM card!
  const bgScale = interpolate(frame, [0, 223], [1.05, 1.24], {
    extrapolateRight: 'clamp',
  });
  const bgPanX = interpolate(frame, [0, 223], [-24, 24], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 223], [-240, -280], {
    extrapolateRight: 'clamp',
  });

  // Single Top Badge entrance
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 105},
  });

  // CRM Card entrance
  const crmSpring = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Stage transitions synchronized with voice:
  // Stage 1 (0..82): "Desafoguei meus vendedores" -> ATENDIDO
  // Stage 2 (83..149): "e agora mantemos atendimento com inteligência artificial" (~22.15s) -> EM FECHAMENTO
  // Stage 3 (150..223): "vinte e quatro horas" (~24.4s) -> 24H ATIVO
  const stage = frame >= 150 ? 2 : frame >= 83 ? 1 : 0;
  const stageStartFrame = stage === 2 ? 150 : stage === 1 ? 83 : 8;
  const stageSpring = spring({
    frame: Math.max(0, frame - stageStartFrame),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const events = [
    {
      titulo: 'Lead Qualificado • Atendido',
      subtitulo: 'Vendedores livres para fechar negócios',
      status: 'ATENDIDO',
      icone: '📞',
    },
    {
      titulo: 'Atendimento IA • Voz Real',
      subtitulo: 'Qualificação automática no WhatsApp',
      status: 'EM FECHAMENTO',
      icone: '🤖',
    },
    {
      titulo: 'Operação Comercial • IA 24h',
      subtitulo: 'Ligações automáticas sem parar',
      status: '24H ATIVO',
      icone: '⚡',
    },
  ];
  const currentEvent = events[stage];

  // Continuous badge pulse & shimmer so between q11 (frame 112) and q12 (frame 178) there is strong visual motion
  const statusPulse = 1 + 0.06 * Math.sin(frame * 0.38);
  const progressSweep = interpolate((frame % 55), [0, 54], [15, 100]);

  // Exit transition
  const exitOpacity = interpolate(frame, [212, 223], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
        opacity: exitOpacity,
        backgroundColor: '#05180E',
      }}
    >
      {/* Continuous Single Take Background shifted up so all 3 faces stay in the upper-middle window (y=310..700) */}
      <Img
        src={staticFile('img_2.jpg')}
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          filter: 'brightness(0.86) contrast(1.08) saturate(1.05)',
          transform: `scale(${bgScale}) translate(${bgPanX}px, ${bgPanY}px)`,
        }}
      />

      {/* Subtle Top Gradient strictly above y=280 */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 280,
          background:
            'linear-gradient(180deg, rgba(5, 22, 12, 0.90) 0%, rgba(5, 22, 12, 0.45) 60%, rgba(5, 22, 12, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Bottom Gradient starting below the faces (y=800..1920) leaving faces at y=310..750 100% unobstructed */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 1100,
          background:
            'linear-gradient(0deg, rgba(4, 18, 10, 0.96) 0%, rgba(5, 22, 13, 0.88) 52%, rgba(5, 22, 13, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Single Clean Top Pill (y=165..235) — No double header, leaving maximum headroom for the team */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 10,
          transform: `scale(${headerSpring})`,
          opacity: headerSpring,
        }}
      >
        <div
          style={{
            background: 'rgba(8, 28, 16, 0.94)',
            border: '2px solid #25D366',
            borderRadius: 9999,
            padding: '8px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.55)',
          }}
        >
          <span
            style={{
              display: 'inline-block',
              width: 14,
              height: 14,
              borderRadius: 7,
              backgroundColor: '#25D366',
              boxShadow: '0 0 12px #25D366',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.8,
              textTransform: 'uppercase',
              whiteSpace: 'nowrap',
            }}
          >
            O Resultado • Vendedores Desafogados
          </span>
        </div>
      </div>

      {/* Focused Single-Event Highlight CRM Card in Lower Zone (y=920..1270) — Well below the team's faces & bodies, no extra bottom pill */}
      <div
        style={{
          position: 'absolute',
          top: 930,
          left: 60,
          right: 60,
          zIndex: 10,
          transform: `scale(${crmSpring})`,
          opacity: crmSpring,
          background: 'rgba(9, 24, 16, 0.96)',
          border: '2.5px solid #25D366',
          borderRadius: 28,
          padding: '24px 30px',
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
          boxShadow: '0 22px 55px rgba(0, 0, 0, 0.85)',
        }}
      >
        {/* CRM Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1.5px solid rgba(37, 211, 102, 0.3)',
            paddingBottom: 14,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <span
              style={{
                width: 16,
                height: 16,
                borderRadius: 8,
                backgroundColor: '#25D366',
                boxShadow: '0 0 14px #25D366',
                display: 'inline-block',
                transform: `scale(${1 + 0.25 * Math.sin(frame * 0.35)})`,
              }}
            />
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#25D366',
                letterSpacing: 0.8,
              }}
            >
              PAINEL CRM • HERMES CALL
            </span>
          </div>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#E2E8F0',
              background: 'rgba(255, 255, 255, 0.1)',
              padding: '4px 16px',
              borderRadius: 10,
            }}
          >
            Simulação
          </span>
        </div>

        {/* Single High-Impact Highlight Event (Large Font, Vertical Slide + Fade Entrance, Pulsing Status) */}
        <div
          style={{
            transform: `translateY(${interpolate(stageSpring, [0, 1], [28, 0])}px)`,
            opacity: stageSpring,
            background: 'rgba(16, 42, 27, 0.95)',
            borderLeft: '8px solid #25D366',
            borderRadius: 20,
            padding: '22px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
            boxShadow: '0 10px 28px rgba(0, 0, 0, 0.45)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 42}}>{currentEvent.icone}</span>
              <span
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                }}
              >
                {currentEvent.titulo}
              </span>
            </div>

            <div
              style={{
                transform: `scale(${statusPulse})`,
                fontSize: 33,
                fontWeight: 900,
                color: '#061A0E',
                background: '#25D366',
                padding: '10px 20px',
                borderRadius: 12,
                boxShadow: '0 0 20px rgba(37, 211, 102, 0.75)',
                whiteSpace: 'nowrap',
              }}
            >
              {currentEvent.status}
            </div>
          </div>

          <div
            style={{
              fontSize: 34,
              fontWeight: 700,
              color: '#A7F3D0',
              lineHeight: 1.25,
            }}
          >
            {currentEvent.subtitulo}
          </div>

          {/* Live Activity Progress Bar (Guarantees continuous motion across every frame of Scene 3) */}
          <div
            style={{
              width: '100%',
              height: 10,
              borderRadius: 5,
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
              overflow: 'hidden',
              marginTop: 4,
            }}
          >
            <div
              style={{
                width: `${progressSweep}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #10B981 0%, #25D366 100%)',
                borderRadius: 5,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
