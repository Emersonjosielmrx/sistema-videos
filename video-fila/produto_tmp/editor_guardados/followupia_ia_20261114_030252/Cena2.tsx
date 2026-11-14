import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo
  const bgScale = interpolate(frame, [0, 269], [1.02, 1.10], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 269], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Top badge
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Balão 1: frame 28 (~0.9s)
  const m1Spring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Balão 2: frame 118 (~3.9s)
  const m2Spring = spring({
    frame: frame - 118,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Balão 3: frame 188 (~6.2s)
  const m3Spring = spring({
    frame: frame - 188,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Selo final automático abaixo do celular: frame 210 (~7.0s)
  const badgeFinalSpring = spring({
    frame: frame - 210,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Digitando 1 (entre frame 65 e 118)
  const isTyping1 = frame >= 65 && frame < 118;
  // Digitando 2 (entre frame 150 e 188)
  const isTyping2 = frame >= 150 && frame < 188;

  // Flutuação do mockup
  const floatY = Math.sin(frame / 16) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Fundo dinâmico com blur e zoom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(16px)',
          opacity: 0.55,
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Véu de contraste escuro */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 30%, rgba(17, 24, 39, 0.75) 0%, rgba(17, 24, 39, 0.95) 100%)',
        }}
      />

      {/* Topo: Rótulo "Como funciona" (y=162) */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, badgeSpring)})`,
          opacity: Math.min(1, Math.max(0, badgeSpring)),
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 20,
            backgroundColor: 'rgba(78, 205, 196, 0.15)',
            border: '1.5px solid #4ECDC4',
            backdropFilter: 'blur(8px)',
          }}
        >
          <span style={{fontSize: 26}}>⚡</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#4ECDC4',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>
      </div>

      {/* Título da cena no topo (y=214) */}
      <div
        style={{
          position: 'absolute',
          top: 214,
          left: 60,
          right: 60,
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        <div
          style={{
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            textTransform: 'uppercase',
            textShadow: '0 4px 16px rgba(0,0,0,0.9)',
          }}
        >
          IA CONVERSA NO WHATSAPP SOZINHA
        </div>
      </div>

      {/* Mockup do Smartphone com WhatsApp (y=310 a 1270) */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          left: 100,
          width: 880,
          height: 960,
          borderRadius: 36,
          backgroundColor: '#0B141B',
          border: '2.5px solid rgba(78, 205, 196, 0.45)',
          boxShadow:
            '0 24px 60px rgba(0, 0, 0, 0.8), 0 0 35px rgba(78, 205, 196, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          transform: `translateY(${floatY}px)`,
          zIndex: 10,
        }}
      >
        {/* Header do WhatsApp */}
        <div
          style={{
            height: 96,
            backgroundColor: '#1F2C34',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                backgroundColor: '#4ECDC4',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
              }}
            >
              🤖
            </div>
            <div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#E9EDEF',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                Follow-up IA
                <span
                  style={{
                    color: '#4ECDC4',
                    fontSize: 24,
                  }}
                >
                  ✓
                </span>
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#25D366',
                }}
              >
                Online agora
              </div>
            </div>
          </div>

          {/* Selo Simulação obrigatório */}
          <div
            style={{
              padding: '6px 14px',
              borderRadius: 10,
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              fontSize: 32,
              fontWeight: 700,
              color: '#94A3B8',
              textTransform: 'uppercase',
              letterSpacing: 0.8,
            }}
          >
            Simulação
          </div>
        </div>

        {/* Corpo do Chat */}
        <div
          style={{
            flex: 1,
            padding: '24px 22px',
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
            justifyContent: 'flex-start',
            backgroundImage:
              'radial-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px)',
            backgroundSize: '20px 20px',
          }}
        >
          {/* Mensagem 1: Empresa (Follow-up IA) */}
          {frame >= 28 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '84%',
                backgroundColor: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                padding: '16px 20px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                transform: `scale(${Math.max(0, m1Spring)})`,
                opacity: Math.min(1, Math.max(0, m1Spring)),
              }}
            >
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#E9EDEF',
                  lineHeight: 1.25,
                }}
              >
                Olá, tudo bem? Conseguiu avaliar a proposta que te passei?
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: 6,
                  marginTop: 6,
                }}
              >
                <span style={{fontSize: 20, color: '#8696A0'}}>10:14</span>
                <span style={{fontSize: 18, color: '#53BDEB'}}>✓✓</span>
              </div>
            </div>
          )}

          {/* Indicador digitando do Cliente */}
          {isTyping1 && (
            <div
              style={{
                alignSelf: 'flex-start',
                backgroundColor: '#202C33',
                borderRadius: '16px 16px 16px 4px',
                padding: '12px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span style={{fontSize: 32, color: '#8696A0'}}>
                Cliente digitando...
              </span>
            </div>
          )}

          {/* Mensagem 2: Cliente */}
          {frame >= 118 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '84%',
                backgroundColor: '#202C33',
                borderRadius: '20px 20px 20px 4px',
                padding: '16px 20px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                transform: `scale(${Math.max(0, m2Spring)})`,
                opacity: Math.min(1, Math.max(0, m2Spring)),
              }}
            >
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#E9EDEF',
                  lineHeight: 1.25,
                }}
              >
                Oi! Na correria acabei esquecendo. Vamos fechar sim!
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  marginTop: 6,
                }}
              >
                <span style={{fontSize: 20, color: '#8696A0'}}>10:15</span>
              </div>
            </div>
          )}

          {/* Indicador digitando da IA */}
          {isTyping2 && (
            <div
              style={{
                alignSelf: 'flex-end',
                backgroundColor: '#005C4B',
                borderRadius: '16px 16px 4px 16px',
                padding: '12px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span style={{fontSize: 32, color: '#4ECDC4'}}>
                Follow-up IA digitando...
              </span>
            </div>
          )}

          {/* Mensagem 3: Empresa (Follow-up IA) */}
          {frame >= 188 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '84%',
                backgroundColor: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                padding: '16px 20px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                transform: `scale(${Math.max(0, m3Spring)})`,
                opacity: Math.min(1, Math.max(0, m3Spring)),
              }}
            >
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#E9EDEF',
                  lineHeight: 1.25,
                }}
              >
                Perfeito! Vou gerar o pedido para darmos andamento agora.
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: 6,
                  marginTop: 6,
                }}
              >
                <span style={{fontSize: 20, color: '#8696A0'}}>10:15</span>
                <span style={{fontSize: 18, color: '#53BDEB'}}>✓✓</span>
              </div>
            </div>
          )}
        </div>

        {/* Rodapé do Chat com status de automação */}
        <div
          style={{
            height: 64,
            backgroundColor: '#1F2C34',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 700,
              color: '#4ECDC4',
            }}
          >
            🔒 Resposta Automática Inteligente
          </span>
        </div>
      </div>

      {/* Selo de impacto posicionado em y=1310 (ABAIXO do celular e ACIMA do karaokê em y=1560) */}
      {frame >= 205 && (
        <div
          style={{
            position: 'absolute',
            top: 1300,
            left: 100,
            right: 100,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid #4ECDC4',
            borderRadius: 22,
            padding: '14px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            boxShadow: '0 16px 36px rgba(0,0,0,0.8), 0 0 25px rgba(78,205,196,0.35)',
            transform: `scale(${Math.max(0, badgeFinalSpring)})`,
            opacity: Math.min(1, Math.max(0, badgeFinalSpring)),
            zIndex: 30,
          }}
        >
          <span style={{fontSize: 32}}>✨</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textTransform: 'uppercase',
            }}
          >
            Sem Mensagens Manuais
          </span>
        </div>
      )}
    </div>
  );
};
