import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom contínuo no fundo (1.02 -> 1.12)
  const bgScale = interpolate(frame, [0, 116], [1.02, 1.12], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entrada em cascata com overshoot:
  // 1. Logo (frame 2)
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // 2. Card de Benefícios (frame 5)
  const cardSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 3. Botão CTA Monumental (frame 8)
  const btnSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 11, stiffness: 120},
  });

  // 4. Perfil Oficial @cardapiodigital.ia (frame 11)
  const profileSpring = spring({
    frame: frame - 11,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Pulso contínuo vivo do CTA (escala suave entre 1.0 e 1.06)
  const pulseScale = 1.0 + Math.sin((frame * 2 * Math.PI) / 32) * 0.045;

  // Efeito Shimmer contínuo passando pelo botão
  const shimmerPos = interpolate(
    (frame % 45),
    [0, 28],
    [-250, 950],
    {extrapolateRight: 'clamp'}
  );

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#0F0205',
        fontFamily,
      }}
    >
      {/* Fundo com desfoque e véu escuro das cores da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
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
            filter: 'blur(20px)',
          }}
        />
        {/* Véu radial elegante com contraste perfeito */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(49,6,15,0.85) 0%, rgba(15,2,5,0.96) 80%)',
          }}
        />
      </div>

      {/* Conteúdo perfeitamente distribuído verticalmente entre y=180 e y=1440 */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 24,
        }}
      >
        {/* 1. Logo e Marca Oficial */}
        {logoSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${logoSpring}) translateY(${(1 - logoSpring) * 20}px)`,
              opacity: logoSpring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                width: 96,
                height: 96,
                borderRadius: 28,
                backgroundColor: '#E11D48',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 52,
                boxShadow: '0 10px 30px rgba(225, 29, 72, 0.6)',
              }}
            >
              🍔
            </div>
            <div
              style={{
                fontSize: 64,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.5px',
                textTransform: 'uppercase',
                textAlign: 'center',
                textShadow: '0 4px 16px rgba(0,0,0,0.85)',
              }}
            >
              CARDÁPIO DIGITAL
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#FACC15',
                textTransform: 'uppercase',
                letterSpacing: '0.8px',
                textAlign: 'center',
              }}
            >
              Com Pedido no WhatsApp & Atendimento com IA
            </div>
          </div>
        )}

        {/* 2. Card de Benefícios e Fatos Reais */}
        {cardSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${cardSpring}) translateY(${(1 - cardSpring) * 20}px)`,
              opacity: cardSpring,
              width: '100%',
              backgroundColor: '#0B0D13FA',
              borderRadius: 26,
              border: '2px solid rgba(225, 29, 72, 0.4)',
              padding: '24px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.9)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 34}}>📸</span>
              <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
                Cardápio com fotos no celular para o cliente escolher
              </span>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 34}}>🤖</span>
              <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
                IA responde na hora e tira dúvidas sem espera
              </span>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 34}}>💬</span>
              <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
                Pedido chega direto no seu WhatsApp organizado
              </span>
            </div>
          </div>
        )}

        {/* 3. BOTÃO MONUMENTAL DE CTA COM PULSAÇÃO DINÂMICA */}
        {btnSpring > 0.01 && (
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'center',
              marginTop: 6,
            }}
          >
            <div
              style={{
                width: '100%',
                maxWidth: 920,
                transform: `scale(${btnSpring * pulseScale})`,
                opacity: btnSpring,
                backgroundColor: '#E11D48',
                borderRadius: 26,
                padding: '26px 32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 18,
                boxShadow:
                  '0 18px 45px rgba(225, 29, 72, 0.65), 0 0 30px rgba(225, 29, 72, 0.45)',
                border: '2.5px solid rgba(255, 255, 255, 0.35)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Efeito Shimmer */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: shimmerPos,
                  width: 90,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                  transform: 'skewX(-25deg)',
                  pointerEvents: 'none',
                }}
              />
              <span style={{fontSize: 44}}>👉</span>
              <span
                style={{
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                CHAME NO DIRECT
              </span>
            </div>
          </div>
        )}

        {/* 4. Perfil Oficial da Marca (@cardapiodigital.ia) */}
        {profileSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${profileSpring}) translateY(${(1 - profileSpring) * 15}px)`,
              opacity: profileSpring,
              width: '100%',
              backgroundColor: '#0B0D13F8',
              borderRadius: 24,
              border: '1.5px solid rgba(255, 255, 255, 0.16)',
              padding: '18px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.85)',
              marginTop: 4,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background:
                    'linear-gradient(45deg, #F58529, #DD2A7B, #8134AF, #515BD4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  color: '#FFFFFF',
                }}
              >
                📷
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                  <span
                    style={{
                      fontSize: 40,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    @cardapiodigital.ia
                  </span>
                  <span style={{fontSize: 34, color: '#38BDF8'}}>✓</span>
                </div>
                <span style={{fontSize: 34, color: '#CBD5E1', fontWeight: 600}}>
                  Envie uma mensagem agora
                </span>
              </div>
            </div>
            <div
              style={{
                padding: '10px 20px',
                borderRadius: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                fontSize: 32,
                fontWeight: 800,
                color: '#FACC15',
                textTransform: 'uppercase',
              }}
            >
              Direct
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
