import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena4Props {
  fontFamily: string;
  destaque: string;
  arroba: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily, destaque, arroba}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Slow push-in contínuo de câmera até o último frame do vídeo
  const sceneScale = interpolate(frame, [0, 119], [1.0, 1.10], {
    extrapolateRight: 'clamp',
  });

  // Entrada ágil do cartão via spring desde o frame 0
  const cardEntrance = spring({
    frame,
    fps,
    config: {damping: 15, stiffness: 140},
  });

  // Animação contínua de escala pulsante (scale 1.0 para 1.04 em loop suave) no botão 'CHAME NO DIRECT'
  const buttonPulse = 1.0 + 0.04 * (0.5 + 0.5 * Math.sin(frame * 0.14));

  // Feixe de luz passando (shimmer sweep) a cada 1.5s (45 frames) até o fim do vídeo
  const shimmerCycle = frame % 45;
  const shimmerProgress = shimmerCycle / 45;
  const shimmerTranslate = interpolate(shimmerProgress, [0, 1], [-350, 950]);

  // Micro-animações contínuas de flutuação e pulso de glow
  const iconFloatY = Math.sin(frame * 0.14) * 8;
  const buttonFloatY = Math.sin(frame * 0.12) * 5;
  const badgeFloatY = Math.sin(frame * 0.12 + 1.2) * 4;
  const cardFloatY = Math.sin(frame * 0.1 + 0.8) * 4;
  const orbScale = 1.0 + 0.08 * Math.sin(frame * 0.1);
  const orbY1 = interpolate(frame, [0, 119], [300, 420]);
  const orbY2 = interpolate(frame, [0, 119], [1050, 930]);

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#070A12',
        fontFamily,
      }}
    >
      {/* Fundo dinâmico com iluminação viva, zoom contínuo e malha de grafismos de marca */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${sceneScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.45,
          }}
        />

        {/* Gradiente luminoso superior */}
        <div
          style={{
            position: 'absolute',
            width: 880,
            height: 880,
            borderRadius: '50%',
            background: `radial-gradient(circle, rgba(91, 108, 255, 0.45) 0%, rgba(91, 108, 255, 0.1) 50%, transparent 75%)`,
            top: orbY1,
            left: 100,
            filter: 'blur(70px)',
            transform: `scale(${orbScale})`,
          }}
        />

        {/* Gradiente luminoso inferior preenchendo a base */}
        <div
          style={{
            position: 'absolute',
            width: 900,
            height: 700,
            borderRadius: '50%',
            background: `radial-gradient(circle, rgba(91, 108, 255, 0.35) 0%, rgba(56, 189, 248, 0.1) 50%, transparent 75%)`,
            top: orbY2,
            left: 90,
            filter: 'blur(75px)',
          }}
        />

        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px)',
            backgroundSize: '80px 80px',
            opacity: 0.65,
          }}
        />
      </div>

      {/* Container Central com Distribuição Vertical Harmoniosa (y = 220 a 1470, centro em y ≈ 900~950) */}
      {/* Elimina qualquer vazio morto e posiciona o CTA na zona nobre de toque sem invadir y > 1580 */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          bottom: 450,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          textAlign: 'center',
          transform: `scale(${Math.max(0, cardEntrance)})`,
          opacity: Math.min(1, Math.max(0, cardEntrance)),
          zIndex: 20,
        }}
      >
        {/* 1. Bloco Superior: Logo, Nome, Proposta e Chips */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          {/* Ícone da Marca com leve floating contínuo e brilho neon */}
          <div
            style={{
              transform: `translateY(${iconFloatY}px)`,
              width: 110,
              height: 110,
              borderRadius: 28,
              backgroundColor: destaque,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 18px 45px rgba(91, 108, 255, 0.75), 0 0 35px ${destaque}`,
              marginBottom: 20,
              border: '2.5px solid rgba(255, 255, 255, 0.65)',
            }}
          >
            <svg
              width="58"
              height="58"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              <line x1="8" y1="10" x2="16" y2="10" />
              <line x1="12" y1="7" x2="12" y2="13" />
            </svg>
          </div>

          {/* Nome da Marca */}
          <div>
            <h1
              style={{
                fontSize: 68,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '-0.01em',
                margin: '0 0 12px 0',
                textShadow: '0 4px 24px rgba(0, 0, 0, 0.95)',
              }}
            >
              SuperChat IA
            </h1>
          </div>

          {/* Proposta de valor oficial */}
          <div>
            <p
              style={{
                fontSize: 36,
                fontWeight: 700,
                color: '#E2E8F0',
                maxWidth: 860,
                margin: '0 0 24px 0',
                lineHeight: 1.3,
                textWrap: 'balance',
              }}
            >
              Multi atendimento com CRM e IA 24h
            </p>
          </div>

          {/* Chips dos canais oficiais integrados */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 14,
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#4ADE80',
                backgroundColor: 'rgba(34, 197, 94, 0.18)',
                border: '1.5px solid rgba(34, 197, 94, 0.5)',
                padding: '8px 22px',
                borderRadius: 14,
                boxShadow: '0 6px 18px rgba(0, 0, 0, 0.6)',
              }}
            >
              ● WhatsApp
            </span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#38BDF8',
                backgroundColor: 'rgba(56, 189, 248, 0.18)',
                border: '1.5px solid rgba(56, 189, 248, 0.5)',
                padding: '8px 22px',
                borderRadius: 14,
                boxShadow: '0 6px 18px rgba(0, 0, 0, 0.6)',
              }}
            >
              ● Telegram
            </span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#FFA0D0',
                backgroundColor: 'rgba(225, 48, 108, 0.18)',
                border: '1.5px solid rgba(225, 48, 108, 0.5)',
                padding: '8px 22px',
                borderRadius: 14,
                boxShadow: '0 6px 18px rgba(0, 0, 0, 0.6)',
              }}
            >
              ● Instagram
            </span>
          </div>
        </div>

        {/* 2. Bloco Central: Card de Resumo de Recursos (elimina o vazio entre topo e CTA) */}
        <div
          style={{
            transform: `translateY(${cardFloatY}px)`,
            width: '100%',
            maxWidth: 880,
            backgroundColor: 'rgba(15, 23, 42, 0.88)',
            border: '2px solid rgba(91, 108, 255, 0.45)',
            borderRadius: 24,
            padding: '20px 28px',
            boxSizing: 'border-box',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.85), 0 0 25px rgba(91, 108, 255, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            textAlign: 'left',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <span style={{color: '#4ADE80', fontSize: 32, fontWeight: 900}}>✓</span>
            <span style={{color: '#FFFFFF', fontSize: 32, fontWeight: 700}}>
              Centraliza WhatsApp, Telegram e Instagram
            </span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <span style={{color: '#4ADE80', fontSize: 32, fontWeight: 900}}>✓</span>
            <span style={{color: '#FFFFFF', fontSize: 32, fontWeight: 700}}>
              Atendimento IA 24h no WhatsApp
            </span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <span style={{color: '#4ADE80', fontSize: 32, fontWeight: 900}}>✓</span>
            <span style={{color: '#FFFFFF', fontSize: 32, fontWeight: 700}}>
              Multi atendimento com CRM e IA no mesmo painel
            </span>
          </div>
        </div>

        {/* 3. Bloco Inferior: Botão de Ação CTA e Badge @ na zona nobre de toque */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          {/* Botão de Ação CTA com escala contínua pulsante (1.00 para 1.04) e feixe de luz passando a cada 1.5s */}
          <div
            style={{
              transform: `translateY(${buttonFloatY}px) scale(${buttonPulse})`,
              marginBottom: 26,
              width: '100%',
              maxWidth: 880,
              position: 'relative',
            }}
          >
            <div
              style={{
                backgroundColor: destaque,
                borderRadius: 26,
                padding: '24px 44px',
                border: '3px solid rgba(255, 255, 255, 0.75)',
                boxShadow: `0 20px 52px rgba(91, 108, 255, 0.85), 0 0 45px rgba(91, 108, 255, 0.65)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 18,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              {/* Efeito Sheen de feixe de luz passando a cada 1.5s (shimmer sweep) */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  width: 160,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.85), transparent)',
                  transform: `translateX(${shimmerTranslate}px) skewX(-25deg)`,
                  pointerEvents: 'none',
                }}
              />

              <span
                style={{
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                  textShadow: '0 3px 12px rgba(0, 0, 0, 0.5)',
                }}
              >
                CHAME NO DIRECT
              </span>

              <svg
                width="42"
                height="42"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </div>

          {/* Perfil Oficial (@superchatia.ia) com micro-flutuação, alto contraste e respeitando y < 1580 */}
          <div
            style={{
              transform: `translateY(${badgeFloatY}px)`,
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 14,
                backgroundColor: '#0F172A',
                border: '2px solid rgba(91, 108, 255, 0.65)',
                borderRadius: 999,
                padding: '14px 40px',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.85), 0 0 20px rgba(91, 108, 255, 0.35)',
              }}
            >
              <span style={{color: destaque, fontSize: 36}}>★</span>
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 40,
                  fontWeight: 800,
                  letterSpacing: '0.02em',
                }}
              >
                {arroba}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
