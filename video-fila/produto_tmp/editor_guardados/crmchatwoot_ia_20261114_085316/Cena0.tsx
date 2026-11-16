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

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 160], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior (0.1s / frame 3)
  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Entrada do Título Principal (0.3s / frame 10)
  const title1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Entrada das Tags de Conflito:
  // Tag 1 (Suporte): 1.0s / frame 30
  const tag1Spring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 11, stiffness: 90},
  });

  // Tag 2 (Vendas): 1.7s / frame 51
  const tag2Spring = spring({
    frame: frame - 51,
    fps,
    config: {damping: 11, stiffness: 90},
  });

  // Linha 2 do Título: 2.2s / frame 66
  const title2Spring = spring({
    frame: frame - 66,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Selo Gancho Fixo: 3.2s / frame 96
  const hookSpring = spring({
    frame: frame - 96,
    fps,
    config: {damping: 10, stiffness: 120},
  });

  // Flutuação contínua suave das tags
  const floatOffset1 = Math.sin(frame / 14) * 8;
  const floatOffset2 = Math.cos(frame / 14) * 8;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Imagem de Fundo com zoom contínuo */}
      <AbsoluteFill style={{transform: `scale(${bgScale})`}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Camada escura de contraste para legibilidade absoluta */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.72) 45%, rgba(15,23,42,0.92) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo dentro da Safe Zone (x: 60-1020, y: 150-1580) */}
      <AbsoluteFill style={{padding: '0 60px'}}>
        {/* Badge de Topo */}
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-20, 0])}px)`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 24px',
              borderRadius: 30,
              background: 'rgba(31, 147, 255, 0.18)',
              border: '2px solid rgba(31, 147, 255, 0.6)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#1F93FF',
                boxShadow: '0 0 10px #1F93FF',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#93C5FD',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              ATENDIMENTO AO CLIENTE
            </span>
          </div>
        </div>

        {/* Título Cinético - Pergunta do Cliente */}
        <div
          style={{
            position: 'absolute',
            top: 280,
            left: 60,
            right: 60,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              opacity: interpolate(title1Spring, [0, 1], [0, 1]),
              transform: `scale(${interpolate(title1Spring, [0, 1], [0.85, 1])})`,
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 56,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(0,0,0,0.8)',
              }}
            >
              MENSAGENS DE
            </div>
            <div
              style={{
                display: 'inline-block',
                marginTop: 6,
                padding: '6px 22px',
                borderRadius: 16,
                background: 'linear-gradient(90deg, #1F93FF 0%, #0284C7 100%)',
                boxShadow: '0 8px 30px rgba(31,147,255,0.4)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 58,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                SUPORTE E VENDAS
              </span>
            </div>
          </div>

          <div
            style={{
              marginTop: 18,
              opacity: interpolate(title2Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(title2Spring, [0, 1], [25, 0])}px)`,
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#F8FAFC',
                lineHeight: 1.2,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(0,0,0,0.8)',
              }}
            >
              SE MISTURAM NO SEU
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 66,
                fontWeight: 900,
                color: '#38BDF8',
                lineHeight: 1.1,
                textTransform: 'uppercase',
                textShadow: '0 4px 24px rgba(56,189,248,0.5)',
              }}
            >
              ATENDIMENTO?
            </div>
          </div>
        </div>

        {/* Visual de Conflito: Duas Notificações em Choque */}
        <div
          style={{
            position: 'absolute',
            top: 720,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
            alignItems: 'center',
          }}
        >
          {/* Card 1: Mensagem de Suporte (Laranja / Alerta) */}
          <div
            style={{
              width: '100%',
              maxWidth: 880,
              padding: '20px 28px',
              borderRadius: 20,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(245, 158, 11, 0.7)',
              boxShadow: '0 12px 35px rgba(0,0,0,0.6), 0 0 20px rgba(245,158,11,0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              opacity: interpolate(tag1Spring, [0, 1], [0, 1]),
              transform: `translateX(${interpolate(tag1Spring, [0, 1], [-120, 0])}px) translateY(${floatOffset1}px)`,
            }}
          >
            <div
              style={{
                width: 60,
                height: 60,
                borderRadius: 16,
                background: 'rgba(245, 158, 11, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                flexShrink: 0,
              }}
            >
              ⚠️
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FBBF24',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                SUPORTE URGENTE
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  marginTop: 4,
                }}
              >
                "Preciso de ajuda urgente com a fatura!"
              </div>
            </div>
          </div>

          {/* Card 2: Mensagem de Vendas (Azul / Oportunidade) */}
          <div
            style={{
              width: '100%',
              maxWidth: 880,
              padding: '20px 28px',
              borderRadius: 20,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(31, 147, 255, 0.8)',
              boxShadow: '0 12px 35px rgba(0,0,0,0.6), 0 0 20px rgba(31,147,255,0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              opacity: interpolate(tag2Spring, [0, 1], [0, 1]),
              transform: `translateX(${interpolate(tag2Spring, [0, 1], [120, 0])}px) translateY(${floatOffset2}px)`,
            }}
          >
            <div
              style={{
                width: 60,
                height: 60,
                borderRadius: 16,
                background: 'rgba(31, 147, 255, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                flexShrink: 0,
              }}
            >
              💰
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#60A5FA',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                NOVA VENDA
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  marginTop: 4,
                }}
              >
                "Quero fechar a proposta comercial agora!"
              </div>
            </div>
          </div>
        </div>

        {/* Selo Gancho Fixado (3.2s) */}
        {frame >= 90 && (
          <div
            style={{
              position: 'absolute',
              top: 1040,
              left: 60,
              right: 60,
              display: 'flex',
              justifyContent: 'center',
              opacity: interpolate(hookSpring, [0, 1], [0, 1]),
              transform: `scale(${interpolate(hookSpring, [0, 1], [0.8, 1])})`,
            }}
          >
            <div
              style={{
                padding: '16px 36px',
                borderRadius: 24,
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid #1F93FF',
                boxShadow: '0 10px 40px rgba(31,147,255,0.4)',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: 1,
                  textTransform: 'uppercase',
                }}
              >
                VENDAS E SUPORTE SEPARADOS?
              </div>
            </div>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
