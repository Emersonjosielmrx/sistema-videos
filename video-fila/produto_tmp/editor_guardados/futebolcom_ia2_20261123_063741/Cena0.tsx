import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera (push-in dinâmico >= 4%)
  const bgScale = interpolate(frame, [0, 152], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica viva contínua
  const floatY = Math.sin(frame / 12) * 6;
  const floatRot = Math.sin(frame / 15) * 1.0;

  // Entrada do Badge superior (0.0s - 0.3s)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Título Principal (0.3s = frame 9)
  const titleSpring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Entrada do Card Caótico 1 (0.5s = frame 15)
  const card1Spring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Entrada do Card Caótico 2 - Áudio (1.2s = frame 36)
  const card2Spring = spring({
    frame: Math.max(0, frame - 36),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Entrada do Card Caótico 3 - Erro/Atraso (1.8s = frame 54)
  const card3Spring = spring({
    frame: Math.max(0, frame - 54),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Destaque dramático da palavra "BAGUNÇADO" (2.2s = frame 66)
  const baguncadoSpring = spring({
    frame: Math.max(0, frame - 60),
    fps,
    config: {damping: 10, stiffness: 140},
  });

  // Alerta de dor final (2.6s = frame 78)
  const alertSpring = spring({
    frame: Math.max(0, frame - 78),
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Pulso na palavra bagunçado
  const pulseBaguncado = 1 + Math.sin((frame - 60) / 6) * 0.04;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: BRIEFING.cores.fundo_escuro,
        fontFamily,
      }}
    >
      {/* Fundo com foto e gradiente com push-in contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <img
          src={staticFile('img_0.jpg')}
          alt="Fundo"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.45,
            filter: 'brightness(0.7) contrast(1.1)',
          }}
        />
        {/* Vinheta e iluminação dramática */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at 50% 40%, rgba(225, 29, 72, 0.25) 0%, rgba(49, 6, 15, 0.95) 80%)`,
          }}
        />
      </div>

      {/* Grid sutil de design para profundidade */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(rgba(255, 255, 255, 0.08) 1.5px, transparent 1.5px)',
          backgroundSize: '40px 40px',
          opacity: 0.6,
          pointerEvents: 'none',
        }}
      />

      {/* Topo: Badge de Categoria (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 0,
          right: 0,
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
            padding: '10px 28px',
            borderRadius: 30,
            background: 'rgba(15, 23, 42, 0.95)',
            border: `2px solid ${BRIEFING.cores.marca}`,
            boxShadow: `0 8px 24px rgba(225, 29, 72, 0.4)`,
          }}
        >
          <span
            style={{
              fontSize: 34,
              color: BRIEFING.cores.apoio,
              lineHeight: 1,
            }}
          >
            ⚡
          </span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            RESTAURANTES & DELIVERY
          </span>
        </div>
      </div>

      {/* Título Principal Cinético (y=255 a y=500) */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 25,
          transform: `translateY(${(1 - titleSpring) * 35}px) scale(${titleSpring})`,
          opacity: titleSpring,
        }}
      >
        {/* Bloco 1 da pergunta */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.94)',
            padding: '14px 28px',
            borderRadius: 20,
            border: '1.5px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 12px 35px rgba(0, 0, 0, 0.7)',
            marginBottom: 14,
          }}
        >
          <span
            style={{
              fontSize: 48,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.25,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            SEU CLIENTE PEDE E O PEDIDO
          </span>
        </div>

        {/* Bloco 2 com a palavra de dor BAGUNÇADO */}
        {frame >= 50 && (
          <div
            style={{
              transform: `scale(${baguncadoSpring * (frame >= 60 ? pulseBaguncado : 1)})`,
              opacity: baguncadoSpring,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 16,
              background: `linear-gradient(135deg, ${BRIEFING.cores.marca} 0%, #9F1239 100%)`,
              padding: '16px 36px',
              borderRadius: 24,
              border: `3px solid ${BRIEFING.cores.apoio}`,
              boxShadow: `0 14px 40px rgba(225, 29, 72, 0.75)`,
            }}
          >
            <span
              style={{
                fontSize: 58,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 4px 12px rgba(0,0,0,0.8)',
              }}
            >
              CHEGA BAGUNÇADO?
            </span>
          </div>
        )}
      </div>

      {/* ÁREA DOS MOCKUPS CAÓTICOS (Simulação da Dor no WhatsApp) (y=530 a y=1380) */}
      <div
        style={{
          position: 'absolute',
          top: 530,
          left: 60,
          right: 60,
          height: 840,
          transform: `translateY(${floatY}px) rotate(${floatRot}deg)`,
          zIndex: 15,
        }}
      >
        {/* Card Caótico 1: Pergunta solta */}
        {frame >= 12 && (
          <div
            style={{
              position: 'absolute',
              top: 15,
              left: 20,
              width: 800,
              transform: `scale(${card1Spring}) rotate(-2.5deg)`,
              opacity: card1Spring,
              background: 'rgba(15, 23, 42, 0.95)',
              borderRadius: 24,
              border: '2px solid rgba(239, 68, 68, 0.4)',
              padding: '20px 28px',
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.75)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 22,
                  background: '#334155',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                }}
              >
                👤
              </div>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#94A3B8',
                }}
              >
                Cliente no WhatsApp
              </span>
              <span
                style={{
                  marginLeft: 'auto',
                  fontSize: 30,
                  color: '#64748B',
                }}
              >
                19:42
              </span>
            </div>
            <p
              style={{
                margin: 0,
                fontSize: 36,
                fontWeight: 600,
                color: '#F8FAFC',
                lineHeight: 1.3,
              }}
            >
              “Oi! Qual o cardápio de hoje? Tem foto e os preços dos lanches?”
            </p>
          </div>
        )}

        {/* Card Caótico 2: Áudio longo + personalização confusa */}
        {frame >= 32 && (
          <div
            style={{
              position: 'absolute',
              top: 205,
              right: 15,
              width: 800,
              transform: `scale(${card2Spring}) rotate(2deg)`,
              opacity: card2Spring,
              background: 'rgba(15, 23, 42, 0.96)',
              borderRadius: 24,
              border: '2px solid rgba(250, 204, 21, 0.45)',
              padding: '20px 28px',
              boxShadow: '0 18px 40px rgba(0, 0, 0, 0.8)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 22,
                  background: '#1E293B',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                }}
              >
                🎙️
              </div>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: BRIEFING.cores.apoio,
                }}
              >
                Mensagem de Áudio (02:14)
              </span>
            </div>
            <p
              style={{
                margin: 0,
                fontSize: 36,
                fontWeight: 600,
                color: '#F8FAFC',
                lineHeight: 1.3,
              }}
            >
              “Manda um burguer sem cebola, maionese à parte e troco pra cem...”
            </p>
          </div>
        )}

        {/* Card Caótico 3: Erro / retrabalho */}
        {frame >= 50 && (
          <div
            style={{
              position: 'absolute',
              top: 395,
              left: 30,
              width: 780,
              transform: `scale(${card3Spring}) rotate(-1.5deg)`,
              opacity: card3Spring,
              background: 'rgba(30, 10, 15, 0.96)',
              borderRadius: 24,
              border: `2px solid ${BRIEFING.cores.marca}`,
              padding: '20px 28px',
              boxShadow: '0 20px 45px rgba(225, 29, 72, 0.5)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                marginBottom: 8,
              }}
            >
              <span style={{fontSize: 34}}>⚠️</span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FDA4AF',
                  textTransform: 'uppercase',
                }}
              >
                Retrabalho na Anotação
              </span>
            </div>
            <p
              style={{
                margin: 0,
                fontSize: 36,
                fontWeight: 600,
                color: '#FFFFFF',
                lineHeight: 1.3,
              }}
            >
              “Você esqueceu o refrigerante? Qual era o sabor mesmo?”
            </p>
          </div>
        )}

        {/* Banner de Impacto da Dor (y=610 relativo) */}
        {frame >= 70 && (
          <div
            style={{
              position: 'absolute',
              top: 600,
              left: 20,
              right: 20,
              transform: `scale(${alertSpring})`,
              opacity: alertSpring,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.96)',
                border: '2px solid #EF4444',
                padding: '16px 36px',
                borderRadius: 22,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 16,
                boxShadow: '0 12px 30px rgba(239, 68, 68, 0.45)',
              }}
            >
              <span style={{fontSize: 36}}>🛑</span>
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                }}
              >
                TEMPO PERDIDO E CONFUSÃO
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
