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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo do frame 0 ao final (1.05 a 1.15)
  const bgScale = interpolate(frame, [0, 116], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos blocos
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 100},
  });

  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 100},
  });

  const buttonSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 110},
  });

  // Pulso ativo contínuo no botão até o frame final (scale 1.0 a 1.08)
  const pulseFactor = 1.04 + Math.sin(frame * 0.18) * 0.04;
  const buttonScale = Math.max(0, buttonSpring) * pulseFactor;

  // Shimmer passando sobre o botão a cada 40 frames
  const shimmerPos = (frame % 40) / 40;
  const shimmerTranslate = interpolate(shimmerPos, [0, 1], [-200, 900]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Imagem de fundo com zoom constante */}
      <Img
        src={staticFile('img_4.jpg')}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
        }}
      />

      {/* Véu de contraste escuro da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(225, 29, 72, 0.4) 0%, rgba(49, 6, 15, 0.92) 75%, rgba(20, 2, 6, 0.98) 100%)',
        }}
      />

      {/* CONTEÚDO PRINCIPAL (Safe Zone centralizada y = 200 a 1480) */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        {/* Categoria / Rótulo */}
        <div
          style={{
            transform: `scale(${Math.max(0, logoSpring)})`,
            opacity: Math.min(1, logoSpring),
            background: 'rgba(255, 255, 255, 0.12)',
            padding: '8px 24px',
            borderRadius: 20,
            border: '1px solid rgba(250, 204, 21, 0.5)',
            marginBottom: 20,
          }}
        >
          <span
            style={{
              color: '#FACC15',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            SOLUÇÃO PARA DELIVERY E RESTAURANTES
          </span>
        </div>

        {/* Marca Grande em Alto Contraste */}
        <div
          style={{
            transform: `scale(${Math.max(0, logoSpring)})`,
            opacity: Math.min(1, logoSpring),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginBottom: 36,
          }}
        >
          <div
            style={{
              color: '#FFFFFF',
              fontSize: 70,
              fontWeight: 900,
              letterSpacing: -1,
              lineHeight: 1.05,
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.9)',
            }}
          >
            CARDÁPIO DIGITAL
          </div>
          <div
            style={{
              width: 180,
              height: 6,
              background: 'linear-gradient(90deg, #E11D48 0%, #FACC15 100%)',
              borderRadius: 3,
              marginTop: 12,
            }}
          />
        </div>

        {/* Card de Proposta de Valor / Benefícios */}
        <div
          style={{
            width: 920,
            transform: `scale(${Math.max(0, cardSpring)})`,
            opacity: Math.min(1, cardSpring),
            background: 'rgba(30, 5, 10, 0.9)',
            borderRadius: 28,
            padding: '32px 36px',
            border: '1.5px solid rgba(250, 204, 21, 0.35)',
            boxShadow: '0 12px 35px rgba(0, 0, 0, 0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            marginBottom: 44,
          }}
        >
          <div
            style={{
              color: '#FACC15',
              fontSize: 34,
              fontWeight: 800,
              textAlign: 'center',
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            Atendimento Rápido e Inteligente
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              textAlign: 'left',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{color: '#10B981', fontSize: 34, fontWeight: 900}}>
                ✓
              </span>
              <span style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600}}>
                Cardápio com fotos no celular
              </span>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{color: '#10B981', fontSize: 34, fontWeight: 900}}>
                ✓
              </span>
              <span style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600}}>
                Atendimento com IA respondendo dúvidas
              </span>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{color: '#10B981', fontSize: 34, fontWeight: 900}}>
                ✓
              </span>
              <span style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600}}>
                Pedido direto pelo WhatsApp sem espera
              </span>
            </div>
          </div>
        </div>

        {/* Botão de Chamada para Ação (CTA) — Pulsando e Vivo */}
        <div
          style={{
            transform: `scale(${buttonScale})`,
            width: 860,
            height: 110,
            background: 'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
            borderRadius: 30,
            boxShadow:
              '0 12px 35px rgba(225, 29, 72, 0.6), inset 0 2px 4px rgba(255, 255, 255, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            position: 'relative',
            overflow: 'hidden',
            marginBottom: 36,
            border: '2px solid rgba(255, 255, 255, 0.25)',
          }}
        >
          {/* Shimmer sweep */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 140,
              background:
                'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.4) 50%, rgba(255,255,255,0) 100%)',
              transform: `translateX(${shimmerTranslate}px) skewX(-25deg)`,
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              color: '#FFFFFF',
              fontSize: 44,
              fontWeight: 900,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 2px 8px rgba(0,0,0,0.5)',
            }}
          >
            CHAME NO DIRECT
          </span>
          <span style={{color: '#FFFFFF', fontSize: 40}}>👉</span>
        </div>

        {/* Perfil Oficial (@marca) — Visível desde o frame 0 da cena */}
        <div
          style={{
            background: 'rgba(15, 2, 5, 0.88)',
            padding: '12px 32px',
            borderRadius: 24,
            border: '1.5px solid rgba(250, 204, 21, 0.5)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <div
            style={{
              color: '#FACC15',
              fontSize: 38,
              fontWeight: 800,
              letterSpacing: 1,
            }}
          >
            @futebolcom.ia2
          </div>
          <div
            style={{
              color: '#E2E8F0',
              fontSize: 32,
              fontWeight: 500,
            }}
          >
            Tire suas dúvidas e modernize seu delivery
          </div>
        </div>
      </div>
    </div>
  );
};
