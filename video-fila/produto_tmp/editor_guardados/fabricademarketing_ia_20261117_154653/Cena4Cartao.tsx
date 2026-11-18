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
import {CORES} from './constants';

interface Cena4Props {
  fontFamily: string;
}

export const Cena4Cartao: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo constante (1.00 -> 1.08)
  const bgScale = interpolate(frame, [0, 119], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Fade in de entrada suave nos primeiros 6 frames
  const entradaOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação de entrada rápida para que todos os blocos estejam vivos já no início
  const logoSpring = spring({frame: frame - 1, fps, config: {damping: 14, stiffness: 160}});
  const titleSpring = spring({frame: frame - 3, fps, config: {damping: 13, stiffness: 150}});
  const subSpring = spring({frame: frame - 5, fps, config: {damping: 14, stiffness: 150}});

  // Cards de benefícios
  const c1Spring = spring({frame: frame - 6, fps, config: {damping: 14, stiffness: 150}});
  const c2Spring = spring({frame: frame - 8, fps, config: {damping: 14, stiffness: 150}});
  const c3Spring = spring({frame: frame - 10, fps, config: {damping: 14, stiffness: 150}});

  // Botão CTA pulsa continuamente (1.00 a 1.06) até o último frame
  const ctaSpring = spring({frame: frame - 12, fps, config: {damping: 12, stiffness: 160}});
  const ctaPulse = Math.sin(frame / 6) * 0.03 + 1.03;

  // Brilho que desliza continuamente pelo botão
  const sheenPos = interpolate(frame % 38, [0, 38], [-120, 220]);

  // Arroba entra no frame 14
  const arrobaSpring = spring({frame: frame - 14, fps, config: {damping: 14, stiffness: 150}});

  return (
    <AbsoluteFill style={{opacity: entradaOpacity, overflow: 'hidden'}}>
      {/* Imagem de Fundo com Zoom e Desfoque */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(10px)',
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

      {/* Véu escuro da marca para contraste absoluto */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(17, 24, 39, 0.78) 0%, rgba(11, 15, 25, 0.96) 100%)',
        }}
      />

      {/* Orbs de luz em movimento vivo */}
      <div
        style={{
          position: 'absolute',
          top: 360 + Math.sin(frame / 15) * 20,
          left: 80,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(244,114,182,0.22) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 350 + Math.cos(frame / 15) * 20,
          right: 60,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(219,39,119,0.2) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Layout Vertical Perfeitamente Distribuído na Safe Zone: y = 230 a 1450 */}
      <div
        style={{
          position: 'absolute',
          top: 230,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 40,
        }}
      >
        {/* Marca Oficial (Top Badge) */}
        <div
          style={{
            opacity: logoSpring,
            transform: `translateY(${(1 - logoSpring) * -15}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 30,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: `1.5px solid ${CORES.bordaCard}`,
            boxShadow: '0 4px 20px rgba(0,0,0,0.6)',
            marginBottom: 32,
          }}
        >
          <span style={{fontSize: 28}}>✨</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: CORES.textoPrincipal,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Fábrica de Marketing IA
          </span>
        </div>

        {/* Nome do Produto em Destaque Hero */}
        <div
          style={{
            opacity: titleSpring,
            transform: `scale(${0.92 + titleSpring * 0.08})`,
            marginBottom: 16,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 64,
              fontWeight: 900,
              color: CORES.marca,
              textTransform: 'uppercase',
              letterSpacing: 1,
              textShadow: `0 0 35px ${CORES.marcaGlow}, 0 4px 14px rgba(0,0,0,0.8)`,
              lineHeight: 1.15,
            }}
          >
            FÁBRICA DE CONTEÚDO
          </div>
        </div>

        {/* 1 Frase do que o produto faz (Fato oficial) */}
        <div
          style={{
            opacity: subSpring,
            transform: `translateY(${(1 - subSpring) * 12}px)`,
            marginBottom: 52,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 700,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            Da ideia à postagem automática
          </span>
        </div>

        {/* 3 Pilares em Cards Elegantes (Fatos Reais do Briefing) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
            width: '100%',
            maxWidth: 880,
            marginBottom: 56,
          }}
        >
          {/* Item 1: Blog SEO */}
          <div
            style={{
              opacity: Math.max(0, Math.min(1, c1Spring)),
              transform: `translateY(${(1 - c1Spring) * 15}px)`,
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              borderRadius: 22,
              padding: '20px 28px',
              border: '1.5px solid rgba(255, 255, 255, 0.14)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 38}}>✍️</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Blog post com SEO
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 800,
                color: '#38BDF8',
              }}
            >
              Automático
            </span>
          </div>

          {/* Item 2: Podcast */}
          <div
            style={{
              opacity: Math.max(0, Math.min(1, c2Spring)),
              transform: `translateY(${(1 - c2Spring) * 15}px)`,
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              borderRadius: 22,
              padding: '20px 28px',
              border: '1.5px solid rgba(255, 255, 255, 0.14)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 38}}>🎙️</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Podcast integrado
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 800,
                color: CORES.marca,
              }}
            >
              Automático
            </span>
          </div>

          {/* Item 3: Agente de Respostas */}
          <div
            style={{
              opacity: Math.max(0, Math.min(1, c3Spring)),
              transform: `translateY(${(1 - c3Spring) * 15}px)`,
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              borderRadius: 22,
              padding: '20px 28px',
              border: '1.5px solid rgba(16, 185, 129, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 6px 20px rgba(0,0,0,0.5), 0 0 16px rgba(16, 185, 129, 0.18)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 38}}>💬</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Resposta em comentários
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 800,
                color: '#34D399',
              }}
            >
              IA 24/7
            </span>
          </div>
        </div>

        {/* BOTÃO CTA PULSANTE VIVO */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, ctaSpring)),
            transform: `scale(${ctaSpring * ctaPulse})`,
            width: '100%',
            maxWidth: 860,
            marginBottom: 42,
          }}
        >
          <div
            style={{
              position: 'relative',
              background: `linear-gradient(135deg, ${CORES.marca} 0%, #DB2777 100%)`,
              borderRadius: 32,
              padding: '28px 44px',
              boxShadow: `0 16px 45px ${CORES.marcaGlow}, 0 4px 14px rgba(0,0,0,0.6)`,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
            }}
          >
            {/* Brilho que passa pelo botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 70,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
                transform: `translateX(${sheenPos}%) skewX(-20deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.4)',
              }}
            >
              CHAME NO DIRECT
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 700,
                color: '#FCE7F3',
                letterSpacing: 1,
              }}
            >
              Tire dúvidas e comece hoje
            </span>
          </div>
        </div>

        {/* @ Arroba da Conta */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, arrobaSpring)),
            transform: `translateY(${(1 - arrobaSpring) * 12}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '16px 36px',
            borderRadius: 28,
            backgroundColor: 'rgba(17, 24, 39, 0.96)',
            border: '1.5px solid rgba(255, 255, 255, 0.25)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.6)',
          }}
        >
          <span style={{fontSize: 32}}>📲</span>
          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 800,
              color: CORES.textoPrincipal,
              letterSpacing: 1,
            }}
          >
            @fabricademarketing.ia
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
