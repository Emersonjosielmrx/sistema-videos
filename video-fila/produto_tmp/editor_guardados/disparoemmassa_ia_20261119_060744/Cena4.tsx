import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo (1.05 -> 1.15)
  const bgScale = interpolate(frame, [0, 118], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Entrada em mola do bloco principal
  const entranceSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Entrada escalonada dos 3 benefícios para garantir movimento contínuo
  const item1Spring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 110},
  });
  const item2Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 110},
  });
  const item3Spring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Pulso contínuo e ativo do botão CTA (1.00 a 1.07) até o último frame
  const buttonPulse = 1.035 + Math.sin(frame * 0.22) * 0.035;

  // Efeito de brilho (shimmer) contínuo varrendo o botão
  const shimmerProgress = (frame % 45) / 45;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-200, 600]);

  // Micro flutuação contínua da marca
  const floatY = Math.sin(frame * 0.1) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
      }}
    >
      {/* Fundo com Zoom Contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(10px)',
          }}
        />
        {/* Véu escuro da marca para contraste absoluto */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(17, 24, 39, 0.78) 0%, rgba(10, 14, 23, 0.95) 100%)',
          }}
        />
      </div>

      {/* Grafismos de luz verde de fundo */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: '50%',
          width: 650,
          height: 650,
          transform: 'translateX(-50%)',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(34, 197, 94, 0.22) 0%, transparent 70%)',
          filter: 'blur(45px)',
          pointerEvents: 'none',
        }}
      />

      {/* CONTEÚDO DO CARTÃO FINAL (Safe Zone: y = 290 a 1480) */}
      <div
        style={{
          position: 'absolute',
          top: 290,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 32,
          zIndex: 30,
          transform: `scale(${entranceSpring})`,
          opacity: entranceSpring,
        }}
      >
        {/* Ícone Tecnológico da Marca */}
        <div
          style={{
            width: 114,
            height: 114,
            borderRadius: 34,
            background: 'linear-gradient(135deg, #22C55E, #15803D)',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            boxShadow: '0 14px 40px rgba(34, 197, 94, 0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `translateY(${floatY}px)`,
          }}
        >
          <svg
            width="68"
            height="68"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#121216"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
          </svg>
        </div>

        {/* Nome da Marca */}
        <div
          style={{
            fontFamily,
            fontSize: 66,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            letterSpacing: 0.5,
            textShadow: '0 4px 24px rgba(0, 0, 0, 0.85)',
          }}
        >
          Disparo em Massa IA
        </div>

        {/* Proposta de Valor Oficial */}
        <div
          style={{
            fontFamily,
            fontSize: 38,
            fontWeight: 600,
            color: '#E2E8F0',
            lineHeight: 1.35,
            maxWidth: 880,
            textWrap: 'balance',
          }}
        >
          Disparo inteligente no WhatsApp com rotação de números e atendimento seguro.
        </div>

        {/* Três Pilares / Recursos Oficiais */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            width: '100%',
            maxWidth: 820,
            marginTop: 8,
          }}
        >
          {[
            {
              icon: (
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="23 4 23 10 17 10" />
                  <polyline points="1 20 1 14 7 14" />
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                </svg>
              ),
              titulo: 'Rotação Automática de Instâncias',
              s: item1Spring,
              show: true,
            },
            {
              icon: (
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              ),
              titulo: 'Mensagens Personalizadas',
              s: item2Spring,
              show: frame >= 14,
            },
            {
              icon: (
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <polyline points="9 12 11 14 15 10" />
                </svg>
              ),
              titulo: 'Atendimento Principal Protegido',
              s: item3Spring,
              show: frame >= 28,
            },
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                padding: '16px 28px',
                borderRadius: 22,
                background: 'rgba(17, 24, 39, 0.94)',
                border: '1.5px solid rgba(255, 255, 255, 0.12)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
                transform: `scale(${item.s})`,
                opacity: item.show ? item.s : 0,
              }}
            >
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 14,
                  background: 'rgba(34, 197, 94, 0.15)',
                  border: '1px solid rgba(34, 197, 94, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {item.icon}
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                {item.titulo}
              </span>
            </div>
          ))}
        </div>

        {/* Botão CTA Principal Pulsante com Efeito Shimmer */}
        <div
          style={{
            marginTop: 18,
            width: '100%',
            maxWidth: 820,
            height: 114,
            borderRadius: 32,
            background: 'linear-gradient(135deg, #22C55E 0%, #16A34A 100%)',
            boxShadow:
              '0 12px 42px rgba(34, 197, 94, 0.65), inset 0 2px 0 rgba(255, 255, 255, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            overflow: 'hidden',
            transform: `scale(${buttonPulse})`,
            cursor: 'pointer',
          }}
        >
          {/* Barra Shimmer animada */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 150,
              transform: `translateX(${shimmerX}px) skewX(-25deg)`,
              background:
                'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.55), transparent)',
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#121216',
              letterSpacing: 2,
              textTransform: 'uppercase',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            Chame no Direct
            <span style={{fontSize: 44}}>↗</span>
          </span>
        </div>

        {/* Perfil Oficial da Marca (@arroba) */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 16,
            padding: '12px 34px',
            borderRadius: 999,
            background: 'rgba(255, 255, 255, 0.08)',
            border: '1.5px solid rgba(255, 255, 255, 0.2)',
            marginTop: 4,
          }}
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#22C55E"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
          </svg>
          <span
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}
          >
            @disparoemmassa.ia
          </span>
        </div>
      </div>
    </div>
  );
};
