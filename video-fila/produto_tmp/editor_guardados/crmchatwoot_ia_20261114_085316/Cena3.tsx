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

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background pan/zoom contínuo
  const bgScale = interpolate(frame, [0, 205], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 205], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Top header spring (frame 2)
  const headerSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Entrada inicial da estrutura dos cards (0.15s / frame 4) - Evita qualquer vácuo gráfico
  const baseEnterSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Card 1 ativação: "atendimento" (1.62s / frame 48)
  const isCard1Active = frame >= 48;
  const card1Spring = spring({
    frame: frame - 48,
    fps,
    config: {damping: 10, stiffness: 130},
  });

  // Card 2 ativação: "tickets" (2.55s / frame 76)
  const isCard2Active = frame >= 76;
  const card2Spring = spring({
    frame: frame - 76,
    fps,
    config: {damping: 10, stiffness: 130},
  });

  // Card 3 ativação: "histórico" (3.11s / frame 93)
  const isCard3Active = frame >= 93;
  const card3Spring = spring({
    frame: frame - 93,
    fps,
    config: {damping: 10, stiffness: 130},
  });

  // Banner "centralizados" (4.52s / frame 135)
  const bannerSpring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 10, stiffness: 120},
  });

  // Movimento sutil contínuo nos cards
  const float1 = Math.sin(frame / 12) * 5;
  const float2 = Math.cos(frame / 12) * 5;
  const float3 = Math.sin((frame + 6) / 12) * 5;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Background com movimento contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.80) 45%, rgba(15,23,42,0.95) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo na Safe Zone (x: 60-1020, y: 150-1580) */}
      <AbsoluteFill style={{padding: '0 60px'}}>
        {/* Header Superior */}
        <div
          style={{
            position: 'absolute',
            top: 165,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            opacity: interpolate(headerSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(headerSpring, [0, 1], [-20, 0])}px)`,
          }}
        >
          <div
            style={{
              padding: '6px 20px',
              borderRadius: 20,
              background: 'rgba(31, 147, 255, 0.2)',
              border: '1.5px solid #1F93FF',
              marginBottom: 8,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#60A5FA',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              O RESULTADO
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.15,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            SUA OPERAÇÃO INTEGRADA
          </div>
        </div>

        {/* 3 Cards de Benefícios Centralizados (g - Checklist de 3 benefícios) */}
        <div
          style={{
            position: 'absolute',
            top: 295,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            alignItems: 'center',
            opacity: interpolate(baseEnterSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(baseEnterSpring, [0, 1], [30, 0])}px)`,
          }}
        >
          {/* Card 1: Atendimento (entra na palavra "atendimento") */}
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              padding: '20px 24px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.94)',
              border: isCard1Active
                ? '2px solid rgba(31, 147, 255, 0.9)'
                : '2px solid rgba(255, 255, 255, 0.14)',
              boxShadow: isCard1Active
                ? '0 12px 35px rgba(0,0,0,0.65), 0 0 25px rgba(31, 147, 255, 0.35)'
                : '0 8px 25px rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 20,
              opacity: isCard1Active ? 1 : 0.72,
              transform: `scale(${isCard1Active ? interpolate(card1Spring, [0, 1], [0.97, 1.02]) : 0.98}) translateY(${float1}px)`,
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 16,
                  background: isCard1Active
                    ? 'rgba(31, 147, 255, 0.25)'
                    : 'rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  flexShrink: 0,
                }}
              >
                💬
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 38,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  ATENDIMENTO CENTRALIZADO
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: isCard1Active ? '#94A3B8' : '#64748B',
                    marginTop: 4,
                  }}
                >
                  WhatsApp e canais em uma única fila
                </div>
              </div>
            </div>

            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: isCard1Active ? '#10B981' : 'rgba(255, 255, 255, 0.1)',
                boxShadow: isCard1Active ? '0 0 15px rgba(16,185,129,0.6)' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 26,
                color: isCard1Active ? '#FFF' : '#64748B',
                fontWeight: 900,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
          </div>

          {/* Card 2: Tickets (entra na palavra "tickets") */}
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              padding: '20px 24px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.94)',
              border: isCard2Active
                ? '2px solid rgba(56, 189, 248, 0.9)'
                : '2px solid rgba(255, 255, 255, 0.14)',
              boxShadow: isCard2Active
                ? '0 12px 35px rgba(0,0,0,0.65), 0 0 25px rgba(56, 189, 248, 0.35)'
                : '0 8px 25px rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 20,
              opacity: isCard2Active ? 1 : 0.72,
              transform: `scale(${isCard2Active ? interpolate(card2Spring, [0, 1], [0.97, 1.02]) : 0.98}) translateY(${float2}px)`,
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 16,
                  background: isCard2Active
                    ? 'rgba(56, 189, 248, 0.25)'
                    : 'rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  flexShrink: 0,
                }}
              >
                🎫
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 38,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  TICKETS & HELPDESK
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: isCard2Active ? '#94A3B8' : '#64748B',
                    marginTop: 4,
                  }}
                >
                  Chamados organizados sem perder nada
                </div>
              </div>
            </div>

            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: isCard2Active ? '#10B981' : 'rgba(255, 255, 255, 0.1)',
                boxShadow: isCard2Active ? '0 0 15px rgba(16,185,129,0.6)' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 26,
                color: isCard2Active ? '#FFF' : '#64748B',
                fontWeight: 900,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
          </div>

          {/* Card 3: Histórico (entra na palavra "histórico") */}
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              padding: '20px 24px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.94)',
              border: isCard3Active
                ? '2px solid rgba(147, 197, 253, 0.9)'
                : '2px solid rgba(255, 255, 255, 0.14)',
              boxShadow: isCard3Active
                ? '0 12px 35px rgba(0,0,0,0.65), 0 0 25px rgba(147, 197, 253, 0.35)'
                : '0 8px 25px rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 20,
              opacity: isCard3Active ? 1 : 0.72,
              transform: `scale(${isCard3Active ? interpolate(card3Spring, [0, 1], [0.97, 1.02]) : 0.98}) translateY(${float3}px)`,
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 16,
                  background: isCard3Active
                    ? 'rgba(147, 197, 253, 0.25)'
                    : 'rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  flexShrink: 0,
                }}
              >
                📊
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 38,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  HISTÓRICO DO CLIENTE
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: isCard3Active ? '#94A3B8' : '#64748B',
                    marginTop: 4,
                  }}
                >
                  Registro completo de cada contato
                </div>
              </div>
            </div>

            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: isCard3Active ? '#10B981' : 'rgba(255, 255, 255, 0.1)',
                boxShadow: isCard3Active ? '0 0 15px rgba(16,185,129,0.6)' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 26,
                color: isCard3Active ? '#FFF' : '#64748B',
                fontWeight: 900,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
          </div>

          {/* Banner de Consolidação: "centralizados" */}
          {frame >= 130 && (
            <div
              style={{
                width: '100%',
                maxWidth: 920,
                marginTop: 8,
                padding: '18px 24px',
                borderRadius: 22,
                background: 'linear-gradient(90deg, #1F93FF 0%, #0284C7 100%)',
                boxShadow:
                  '0 12px 40px rgba(31, 147, 255, 0.5), 0 0 25px rgba(31, 147, 255, 0.4)',
                textAlign: 'center',
                opacity: interpolate(bannerSpring, [0, 1], [0, 1]),
                transform: `scale(${interpolate(bannerSpring, [0, 1], [0.9, 1])})`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                ⚡ TUDO CENTRALIZADO COM INTELIGÊNCIA ARTIFICIAL
              </div>
            </div>
          )}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
