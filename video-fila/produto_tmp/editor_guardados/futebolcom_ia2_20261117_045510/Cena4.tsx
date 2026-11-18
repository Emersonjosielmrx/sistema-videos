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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com pan e zoom contínuos
  const bgScale = interpolate(frame, [0, 115], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Card Principal
  const cardSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Botão de Ação (CTA)
  const ctaSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Pulso contínuo no botão CTA para prender a atenção até o último segundo
  const pulseScale = 1.0 + Math.sin(frame / 6) * 0.04;

  // Brilho passando pelo botão (shimmer)
  const shimmerX = interpolate(frame % 40, [0, 40], [-150, 550]);

  // Leve flutuação de todo o card para movimento 100% contínuo
  const cardFloatY = Math.sin(frame / 16) * 6;

  return (
    <AbsoluteFill style={{backgroundColor: '#20040A', overflow: 'hidden'}}>
      {/* Imagem de Fundo Desfocada com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          filter: 'blur(16px) brightness(0.35)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu radial com as cores oficiais da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at center, rgba(225, 29, 72, 0.40) 0%, rgba(32, 4, 10, 0.94) 85%)',
        }}
      />

      {/* Conteúdo Perfeitamente Balanceado na Safe Zone (y: 280 a 1450) */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${cardFloatY}px)`,
        }}
      >
        {/* Card Centralizador Elegante */}
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(28, 5, 12, 0.94)',
            border: '3px solid #E11D48',
            borderRadius: 36,
            padding: '48px 40px',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.95), 0 0 50px rgba(225, 29, 72, 0.45)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            transform: `scale(${cardSpring})`,
            opacity: cardSpring,
          }}
        >
          {/* Ícone da Solução */}
          <div
            style={{
              width: 104,
              height: 104,
              borderRadius: '50%',
              backgroundColor: '#E11D48',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 54,
              marginBottom: 22,
              boxShadow: '0 8px 30px rgba(225, 29, 72, 0.7)',
              border: '3px solid #FACC15',
            }}
          >
            🍔
          </div>

          {/* Nome da Marca / Produto */}
          <span
            style={{
              fontFamily,
              fontSize: 60,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
              lineHeight: 1.15,
              marginBottom: 16,
              textShadow: '0 4px 18px rgba(0,0,0,0.8)',
            }}
          >
            CARDÁPIO DIGITAL
          </span>

          {/* Resumo da Proposta de Valor (100% briefing) */}
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 700,
              color: '#FACC15',
              lineHeight: 1.35,
              maxWidth: 820,
              marginBottom: 36,
            }}
          >
            Pedido direto no WhatsApp com fotos dos pratos e atendimento com IA
          </span>

          {/* Benefícios em Grid 2x2 com alta legibilidade */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 16,
              width: '100%',
              marginBottom: 42,
            }}
          >
            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.18)',
                borderRadius: 14,
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
              }}
            >
              <span style={{fontSize: 32}}>📱</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Acesso no Celular
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.18)',
                borderRadius: 14,
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
              }}
            >
              <span style={{fontSize: 32}}>📸</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Fotos dos Pratos
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.18)',
                borderRadius: 14,
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
              }}
            >
              <span style={{fontSize: 32}}>🤖</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 700,
                  color: '#86EFAC',
                }}
              >
                IA tira dúvidas
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.18)',
                borderRadius: 14,
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
              }}
            >
              <span style={{fontSize: 32}}>⚡</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 700,
                  color: '#FACC15',
                }}
              >
                Delivery Ágil
              </span>
            </div>
          </div>

          {/* Botão de Chamada para Ação (CTA) — Sincronizado estritamente com convite_voz */}
          <div
            style={{
              transform: `scale(${ctaSpring * pulseScale})`,
              opacity: ctaSpring,
              backgroundColor: '#E11D48',
              borderRadius: 24,
              padding: '24px 60px',
              border: '3px solid #FACC15',
              boxShadow: '0 12px 35px rgba(225, 29, 72, 0.8)',
              position: 'relative',
              overflow: 'hidden',
              cursor: 'pointer',
              marginBottom: 32,
              width: '92%',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            {/* Efeito de brilho cruzando o botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 70,
                transform: `translateX(${shimmerX}px) skewX(-20deg)`,
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%)',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              CHAME NO DIRECT 💬
            </span>
          </div>

          {/* Arroba Oficial */}
          <div
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.65)',
              padding: '12px 36px',
              borderRadius: 16,
              border: '1px solid rgba(255, 255, 255, 0.15)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 800,
                color: '#E2E8F0',
                letterSpacing: 1,
              }}
            >
              @futebolcom.ia2
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
