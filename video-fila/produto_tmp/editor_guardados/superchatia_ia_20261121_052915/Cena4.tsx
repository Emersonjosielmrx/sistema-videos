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

  // Movimento de câmera contínuo no fundo (> 4% variação garantida)
  const scale = interpolate(frame, [0, 119], [1.05, 1.26], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 119], [0, 45], {
    extrapolateRight: 'clamp',
  });

  // Entrada escalonada dos elementos com stagger de 0.15s (~5 frames)
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const ctaSpring = spring({
    frame: frame - 7,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const atSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const cardSpring = spring({
    frame: frame - 17,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Efeito contínuo de pulso suave ('breathing') no botão de CTA
  const pulseScale = 1.0 + 0.05 * Math.sin((frame / 22) * Math.PI * 2);

  // Microinteração contínua de flutuação no logo e na pílula do @
  const logoFloat = Math.sin((frame / 25) * Math.PI * 2) * 5;
  const atPulse = 1.0 + 0.025 * Math.sin((frame / 30) * Math.PI * 2);

  // Efeito shimmer passando pelo botão
  const shimmerProgress = (frame % 45) / 45;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-200, 1000]);

  // Transição de entrada suave
  const sceneOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Fundo com foto desfocada e véu azul profundo da marca */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${scale}) translateY(${panY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(24px)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(30,58,138,0.85) 0%, rgba(11,13,19,0.96) 100%)',
          }}
        />
      </div>

      {/* Distribuição segura e equilibrada (y=180 a y=1430, acima de y=1580) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 48,
        }}
      >
        {/* Bloco 1: Identidade e Proposta de Valor (y ~ 180 a 620) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 14,
            transform: `scale(${logoSpring}) translateY(${logoFloat}px)`,
            transformOrigin: 'top center',
          }}
        >
          {/* Ícone com brilho e anéis */}
          <div
            style={{
              width: 104,
              height: 104,
              borderRadius: 28,
              background: 'linear-gradient(135deg, #5B6CFF 0%, #3B4CCA 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 12px 35px rgba(91, 108, 255, 0.65)',
              border: '2px solid rgba(255, 255, 255, 0.28)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 56,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              ⚡
            </span>
          </div>

          {/* Nome da Marca */}
          <div
            style={{
              fontFamily,
              fontSize: 70,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.2,
            }}
          >
            SuperChat IA
          </div>

          {/* Frase oficial do que o produto faz (fatos permitidos) */}
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: '#E2E8F0',
              maxWidth: 880,
              lineHeight: 1.3,
              textWrap: 'balance',
            }}
          >
            Multi atendimento e CRM com inteligência artificial
          </div>

          {/* Chips dos canais permitidos */}
          <div
            style={{
              display: 'flex',
              gap: 12,
              marginTop: 4,
            }}
          >
            {['WhatsApp', 'Instagram', 'Telegram'].map((canal) => (
              <div
                key={canal}
                style={{
                  padding: '8px 20px',
                  borderRadius: 14,
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1.5px solid rgba(255, 255, 255, 0.16)',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#CBD5E1',
                }}
              >
                {canal}
              </div>
            ))}
          </div>
        </div>

        {/* Bloco 2: Botão de CTA Pulsante com Ação Idêntica à Voz (y ~ 740 a 900) */}
        <div
          style={{
            width: '100%',
            maxWidth: 900,
            transform: `scale(${ctaSpring * pulseScale})`,
            transformOrigin: 'center center',
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              width: '100%',
              padding: '28px 24px',
              borderRadius: 30,
              background: 'linear-gradient(135deg, #5B6CFF 0%, #4353E8 100%)',
              border: '2px solid rgba(255, 255, 255, 0.35)',
              boxShadow: '0 20px 50px rgba(91, 108, 255, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
            }}
          >
            {/* Feixe Shimmer de brilho */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.45) 50%, transparent 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Chame no Direct
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 48,
                color: '#FFFFFF',
              }}
            >
              ➔
            </span>
          </div>
        </div>

        {/* Bloco 3: Perfil Oficial e Prova de Confiança (posicionado na faixa y=1200 a 1450) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 22,
            width: '100%',
            marginTop: 90,
          }}
        >
          {/* Perfil Oficial (@marca) visível desde o frame 0.0s com leve pulso */}
          <div
            style={{
              padding: '14px 38px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.96)',
              border: '1.5px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.65)',
              fontFamily,
              fontSize: 44,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              transform: `scale(${atSpring * atPulse})`,
            }}
          >
            @superchatia.ia
          </div>

          {/* Card dos Fatos Permitidos (ancorado com folga acima de y=1580) */}
          <div
            style={{
              width: '100%',
              maxWidth: 900,
              padding: '16px 22px',
              borderRadius: 20,
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1.5px solid rgba(255, 255, 255, 0.14)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
              transform: `scale(${cardSpring})`,
            }}
          >
            <span style={{color: '#5B6CFF', fontSize: 32}}>✓</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#CBD5E1',
                textAlign: 'center',
              }}
            >
              Centraliza WhatsApp, Telegram e Instagram no mesmo painel
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
