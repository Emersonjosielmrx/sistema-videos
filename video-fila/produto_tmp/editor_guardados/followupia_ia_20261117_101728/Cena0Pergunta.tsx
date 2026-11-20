import React from 'react';
import {
  AbsoluteFill,
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

export const Cena0Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous push-in zoom on background
  const bgScale = interpolate(frame, [0, 145], [1.05, 1.2], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 145], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Badge hook entrance (0.2s = frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Phrase 1: "CLIENTE SOME..." (0.3s = frame 9)
  const phrase1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Phrase 2: "DEPOIS DO ORÇAMENTO?" (1.0s = frame 30)
  const phrase2Spring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Phrase 3: "...E NÃO RESPONDE MAIS?" (2.1s = frame 63)
  const phrase3Spring = spring({
    frame: frame - 63,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Chat preview card (enters at frame 20)
  const cardSpring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 15, stiffness: 110},
  });

  // Floating unread badge
  const floatY = Math.sin(frame / 12) * 8;

  // Stagnation timer (counter simulating days passed)
  const diasPassados = Math.min(5, Math.floor(frame / 24) + 1);

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', overflow: 'hidden'}}>
      {/* Background image with continuous motion */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Dark vignette overlay for 100% text readability */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.92) 0%, rgba(17,24,39,0.78) 45%, rgba(17,24,39,0.95) 100%)',
          }}
        />
      </div>

      {/* Top hook badge at y=175 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            backgroundColor: 'rgba(239, 68, 68, 0.18)',
            border: '2px solid rgba(239, 68, 68, 0.75)',
            borderRadius: 30,
            backdropFilter: 'blur(8px)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            A Dor de Todo Vendedor
          </span>
        </div>
      </div>

      {/* Kinetic Headline block (y=270 to 650) */}
      <div
        style={{
          position: 'absolute',
          top: 270,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 18,
          textAlign: 'center',
        }}
      >
        {/* Line 1: CLIENTE SOME */}
        <div
          style={{
            transform: `scale(${phrase1Spring}) translateY(${interpolate(
              phrase1Spring,
              [0, 1],
              [30, 0]
            )}px)`,
            opacity: phrase1Spring,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 62,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: '-1px',
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            Cliente Some
          </span>
        </div>

        {/* Line 2: DEPOIS DO ORÇAMENTO? */}
        <div
          style={{
            transform: `scale(${phrase2Spring}) translateY(${interpolate(
              phrase2Spring,
              [0, 1],
              [30, 0]
            )}px)`,
            opacity: phrase2Spring,
          }}
        >
          <div
            style={{
              display: 'inline-block',
              padding: '8px 26px',
              backgroundColor: '#4ECDC4',
              borderRadius: 18,
              boxShadow: '0 8px 30px rgba(78, 205, 196, 0.35)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#121216',
                textTransform: 'uppercase',
                letterSpacing: '-0.5px',
              }}
            >
              Depois do Orçamento?
            </span>
          </div>
        </div>

        {/* Line 3: E NÃO RESPONDE MAIS? */}
        <div
          style={{
            transform: `scale(${phrase3Spring}) translateY(${interpolate(
              phrase3Spring,
              [0, 1],
              [25, 0]
            )}px)`,
            opacity: phrase3Spring,
          }}
        >
          <div
            style={{
              display: 'inline-block',
              padding: '8px 24px',
              backgroundColor: 'rgba(239, 68, 68, 0.22)',
              border: '2px solid #EF4444',
              borderRadius: 18,
              backdropFilter: 'blur(8px)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              E não responde mais?
            </span>
          </div>
        </div>
      </div>

      {/* Floating Simulated Chat Box showing the problem (y=590 to 1180) */}
      <div
        style={{
          position: 'absolute',
          top: 590,
          left: 70,
          right: 70,
          transform: `translateY(${floatY}px) scale(${cardSpring})`,
          opacity: cardSpring,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(23, 30, 48, 0.92)',
            border: '2px solid rgba(255, 255, 255, 0.12)',
            borderRadius: 32,
            padding: 34,
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            flexDirection: 'column',
            gap: 22,
          }}
        >
          {/* Header of message simulation */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              paddingBottom: 16,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: '50%',
                  backgroundColor: '#374151',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                }}
              >
                👤
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Contato do Lead
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#9CA3AF',
                  }}
                >
                  Visto há {diasPassados} dias
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '6px 16px',
                backgroundColor: 'rgba(239, 68, 68, 0.22)',
                border: '1px solid #EF4444',
                borderRadius: 14,
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#F87171',
              }}
            >
              Sem Resposta
            </div>
          </div>

          {/* Sent Proposal Balloon */}
          <div
            style={{
              alignSelf: 'flex-end',
              maxWidth: '85%',
              backgroundColor: '#1E3A5F',
              borderRadius: '24px 24px 6px 24px',
              padding: '20px 24px',
              border: '1px solid rgba(78, 205, 196, 0.3)',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 600,
                color: '#F1F5F9',
                lineHeight: 1.35,
              }}
            >
              Olá! Conseguiu avaliar o orçamento enviado? Ficou com alguma
              dúvida?
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                alignItems: 'center',
                gap: 6,
                marginTop: 8,
                fontFamily,
                fontSize: 32,
                color: '#94A3B8',
              }}
            >
              <span>14:35</span>
              <span style={{color: '#94A3B8'}}>✓✓</span>
            </div>
          </div>

          {/* Status Alert Bar */}
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              borderLeft: '5px solid #EF4444',
              borderRadius: '0 16px 16px 0',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <span style={{fontSize: 32}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#FECACA',
              }}
            >
              Proposta parada no vácuo por falta de retorno
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
