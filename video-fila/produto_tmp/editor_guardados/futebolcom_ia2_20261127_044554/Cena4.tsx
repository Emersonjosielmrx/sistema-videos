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

  // Movimento de câmera no fundo (zoom constante 1.00 a 1.08)
  const bgScale = interpolate(frame, [0, 116], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada da cena (overlap com cena 3)
  const sceneOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Entrada em cascata rápida (stagger completo em < 0.35s / 10 frames)
  // Bloco 1: Topo / Marca (entra no frame 1)
  const sprMarca = spring({
    frame: frame - 1,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Bloco 2: Card de Recursos (entra no frame 3)
  const sprCard = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Bloco 3: Botão CTA (entra no frame 5)
  const sprBtn = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Bloco 4: @handle oficial (entra no frame 7, simultâneo com a entrada do CTA)
  const sprHandle = spring({
    frame: frame - 7,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Push-in contínuo na câmera / conteúdo para reter a atenção até o último frame
  const contentScale = interpolate(frame, [0, 116], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Pulso contínuo e suave de escala do botão CTA (1.00 a 1.05)
  const btnPulse = 1.0 + 0.04 * Math.sin((frame * Math.PI) / 10);

  // Brilho pulsante e dinâmico na sombra do botão CTA
  const btnGlow = 0.65 + 0.3 * Math.sin((frame * Math.PI) / 10);
  const btnBorderGlow = 0.5 + 0.4 * Math.sin((frame * Math.PI) / 10);

  // Efeito Shimmer / Varredura de luz contínua passando no botão CTA a cada 32 frames
  const shimmerPos = interpolate(frame % 32, [0, 22], [-140, 240], {
    extrapolateRight: 'clamp',
  });

  // Flutuação contínua e micro-respiração no badge do @handle
  const handleFloatY = Math.sin((frame * Math.PI) / 14) * 3;
  const handleScale = 1.0 + 0.02 * Math.sin((frame * Math.PI) / 14);

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
        opacity: sceneOpacity,
      }}
    >
      {/* Imagem de Fundo com Blur e Zoom */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(8px)',
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
        {/* Véu escuro da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(49, 6, 15, 0.88) 0%, rgba(11, 13, 19, 0.96) 100%)',
          }}
        />
      </div>

      {/* Partículas de luz / bokeh quentes subindo dinamicamente no fundo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          overflow: 'hidden',
        }}
      >
        {[0, 1, 2, 3, 4, 5].map((i) => {
          const pY = interpolate((frame * 1.8 + i * 55) % 360, [0, 360], [1500, 250]);
          const pX = 100 + i * 165;
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: pX,
                top: pY,
                width: 16 + (i % 3) * 8,
                height: 16 + (i % 3) * 8,
                borderRadius: '50%',
                background:
                  i % 2 === 0
                    ? 'radial-gradient(circle, rgba(250, 204, 21, 0.38) 0%, transparent 70%)'
                    : 'radial-gradient(circle, rgba(225, 29, 72, 0.45) 0%, transparent 70%)',
              }}
            />
          );
        })}
      </div>

      {/* Conteúdo Central do Cartão Final com Push-in Contínuo de Atenção (Safe Zone y = 150 a 1580) */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 44,
          zIndex: 20,
          transform: `scale(${contentScale})`,
          transformOrigin: 'center center',
        }}
      >
        {/* Badge Superior */}
        <div
          style={{
            transform: `scale(${sprMarca})`,
            opacity: sprMarca,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 30,
            background: 'rgba(225, 29, 72, 0.25)',
            border: '1.5px solid #E11D48',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.8)',
          }}
        >
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FACC15',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            PARA RESTAURANTES E DELIVERY
          </span>
        </div>

        {/* Marca Grande em Alto Contraste */}
        <div
          style={{
            transform: `scale(${sprMarca})`,
            opacity: sprMarca,
            textAlign: 'center',
            maxWidth: 960,
          }}
        >
          <h1
            style={{
              margin: 0,
              fontSize: 76,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
              textShadow: '0 10px 30px rgba(0, 0, 0, 0.9)',
              lineHeight: 1.15,
            }}
          >
            CARDÁPIO DIGITAL
          </h1>
          <div
            style={{
              fontSize: 38,
              fontWeight: 700,
              color: '#FACC15',
              marginTop: 16,
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}
          >
            Pedidos no WhatsApp com Atendimento por IA
          </div>
        </div>

        {/* Card de Recursos e Fatos Autorizados */}
        <div
          style={{
            transform: `scale(${sprCard})`,
            opacity: sprCard,
            width: '100%',
            maxWidth: 920,
            background: 'rgba(11, 13, 19, 0.94)',
            borderRadius: 28,
            border: '2px solid rgba(225, 29, 72, 0.4)',
            padding: '40px 44px',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.9)',
            display: 'flex',
            flexDirection: 'column',
            gap: 28,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: '#E11D48',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                color: '#FFFFFF',
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <div
              style={{
                fontSize: 38,
                fontWeight: 700,
                color: '#FFFFFF',
                lineHeight: 1.3,
              }}
            >
              Fotos dos pratos e cardápio direto no celular do cliente
            </div>
          </div>

          <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: '#E11D48',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                color: '#FFFFFF',
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <div
              style={{
                fontSize: 38,
                fontWeight: 700,
                color: '#FFFFFF',
                lineHeight: 1.3,
              }}
            >
              IA responde dúvidas e confirma o pedido no WhatsApp
            </div>
          </div>
        </div>

        {/* Botão CTA Principal Pulsante com Brilho e Shimmer Passando */}
        <div
          style={{
            marginTop: 24,
            transform: `scale(${sprBtn * btnPulse})`,
            opacity: sprBtn,
            width: '100%',
            maxWidth: 860,
            position: 'relative',
            borderRadius: 30,
            overflow: 'hidden',
            boxShadow: `0 20px 50px rgba(225, 29, 72, ${btnGlow}), 0 0 30px rgba(250, 204, 21, ${btnBorderGlow})`,
            transition: 'box-shadow 0.15s ease',
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
              padding: '32px 48px',
              textAlign: 'center',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              border: '2.5px solid #FACC15',
              borderRadius: 30,
            }}
          >
            <span
              style={{
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          {/* Shimmer Sweep Effect Mais Marcante e Visível */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${shimmerPos}%`,
              width: '50%',
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.45) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />
        </div>

        {/* @Handle Oficial da Conta com Entrada Fluida e Respiração */}
        <div
          style={{
            transform: `scale(${sprHandle * handleScale}) translateY(${handleFloatY}px)`,
            opacity: sprHandle,
            marginTop: 12,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid rgba(250, 204, 21, 0.45)',
            padding: '16px 44px',
            borderRadius: 24,
            boxShadow: '0 12px 35px rgba(0, 0, 0, 0.85), 0 0 15px rgba(250, 204, 21, 0.25)',
          }}
        >
          <span
            style={{
              fontSize: 42,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
            }}
          >
            @futebolcom.ia2
          </span>
        </div>
      </div>
    </div>
  );
};
