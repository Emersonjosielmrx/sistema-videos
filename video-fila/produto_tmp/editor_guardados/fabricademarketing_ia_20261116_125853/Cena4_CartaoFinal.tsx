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

export const Cena4_CartaoFinal: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Crossfade de entrada
  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Zoom lento contínuo no fundo (1.00 -> 1.08)
  const bgScale = interpolate(frame, [0, 118], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Entrada do topo da marca
  const brandSpring = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Entrada do card principal
  const cardSpring = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const cardScale = interpolate(cardSpring, [0, 1], [0.90, 1.0]);

  // STAGGER SEQUENCIAL com spring nos 3 tópicos (elimina o congelamento do cartão):
  // Item 1: frame 14 (~0.47s)
  const item1Spring = spring({
    frame: Math.max(0, frame - 14),
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Item 2: frame 26 (~0.87s)
  const item2Spring = spring({
    frame: Math.max(0, frame - 26),
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Item 3: frame 38 (~1.27s)
  const item3Spring = spring({
    frame: Math.max(0, frame - 38),
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Entrada do botão CTA: frame 46 (~1.53s)
  const btnSpring = spring({
    frame: Math.max(0, frame - 46),
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Pulso contínuo de escala sutil (1.00 para 1.04) para chamar atenção para a conversão
  const pulseScale =
    frame >= 46
      ? interpolate(Math.sin((frame - 46) * 0.18), [-1, 1], [1.0, 1.04])
      : 1.0;

  // Reflexo luminoso (shimmer sweep) contínuo varrendo da esquerda (-250px) para a direita (+1150px)
  const shimmerCycle = (frame % 40) / 40;
  const shimmerX = interpolate(shimmerCycle, [0, 1], [-250, 1150]);

  // Entrada do arroba: frame 56 (~1.87s)
  const arrobaSpring = spring({
    frame: Math.max(0, frame - 56),
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const floatArroba = Math.sin(frame * 0.1) * 3;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
        opacity,
      }}
    >
      {/* Imagem de Fundo com Zoom Contínuo */}
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
          }}
        />
        {/* Véu escuro com glow gradiente da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(244, 114, 182, 0.22) 0%, rgba(17, 24, 39, 0.88) 60%, rgba(17, 24, 39, 0.98) 100%)',
          }}
        />
      </div>

      {/* Topo: Nome da Marca (y=190 a 270) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 14,
          zIndex: 40,
          transform: `scale(${brandSpring})`,
          opacity: brandSpring,
        }}
      >
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #F472B6 0%, #DB2777 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 26,
            boxShadow: '0 0 16px rgba(244, 114, 182, 0.6)',
          }}
        >
          ⚡
        </div>
        <div
          style={{
            fontSize: 38,
            fontWeight: 800,
            color: '#FFFFFF',
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            textShadow: '0 2px 10px rgba(0,0,0,0.8)',
          }}
        >
          Fábrica de Marketing IA
        </div>
      </div>

      {/* Centro: Card Principal do Produto (y=340 a 900) */}
      <div
        style={{
          position: 'absolute',
          top: 340,
          left: 70,
          right: 70,
          transform: `scale(${cardScale})`,
          opacity: cardSpring,
          backgroundColor: 'rgba(17, 24, 39, 0.92)',
          borderRadius: 36,
          border: '1.5px solid rgba(244, 114, 182, 0.4)',
          padding: '48px 36px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 35,
        }}
      >
        {/* Nome do Produto */}
        <div
          style={{
            fontSize: 58,
            fontWeight: 900,
            lineHeight: 1.15,
            color: '#F472B6',
            textAlign: 'center',
            textTransform: 'uppercase',
            letterSpacing: 0.5,
            marginBottom: 16,
            textShadow: '0 4px 20px rgba(244, 114, 182, 0.4)',
          }}
        >
          Fábrica de Conteúdo
        </div>

        {/* Frase Oficial do Produto (Fatos do Briefing) */}
        <div
          style={{
            fontSize: 36,
            fontWeight: 600,
            color: '#E5E7EB',
            textAlign: 'center',
            lineHeight: 1.3,
            marginBottom: 36,
            textWrap: 'balance',
          }}
        >
          Da ideia à postagem automática
        </div>

        {/* Linha Divisória */}
        <div
          style={{
            width: '80%',
            height: 2,
            background:
              'linear-gradient(to right, transparent, rgba(244, 114, 182, 0.6), transparent)',
            marginBottom: 36,
          }}
        />

        {/* 3 Pilares Comprovados com STAGGER SEQUENCIAL */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            width: '100%',
          }}
        >
          {/* Item 1 */}
          <div
            style={{
              transform: `translateY(${interpolate(item1Spring, [0, 1], [30, 0])}px) scale(${item1Spring})`,
              opacity: item1Spring,
              padding: '16px 24px',
              borderRadius: 18,
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(244, 114, 182, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              fontSize: 34,
              fontWeight: 700,
              color: '#FFFFFF',
            }}
          >
            <span style={{fontSize: 32}}>⚡</span> Automação Full Post
          </div>

          {/* Item 2 */}
          <div
            style={{
              transform: `translateY(${interpolate(item2Spring, [0, 1], [30, 0])}px) scale(${item2Spring})`,
              opacity: item2Spring,
              padding: '16px 24px',
              borderRadius: 18,
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(244, 114, 182, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              fontSize: 34,
              fontWeight: 700,
              color: '#FFFFFF',
            }}
          >
            <span style={{fontSize: 32}}>📝</span> Blog SEO + 🎙️ Podcast
          </div>

          {/* Item 3 */}
          <div
            style={{
              transform: `translateY(${interpolate(item3Spring, [0, 1], [30, 0])}px) scale(${item3Spring})`,
              opacity: item3Spring,
              padding: '16px 24px',
              borderRadius: 18,
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(244, 114, 182, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              fontSize: 34,
              fontWeight: 700,
              color: '#FFFFFF',
            }}
          >
            <span style={{fontSize: 32}}>💬</span> Agente de Respostas
          </div>
        </div>
      </div>

      {/* Botão de Ação CTA (y=980 a 1120) — Pulsando e com Shimmer Sweep Contínuo */}
      <div
        style={{
          position: 'absolute',
          top: 980,
          left: 70,
          right: 70,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 45,
          transform: `scale(${btnSpring * pulseScale})`,
          opacity: btnSpring,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: '100%',
            padding: '28px 24px',
            borderRadius: 30,
            background: 'linear-gradient(135deg, #F472B6 0%, #FB7185 100%)',
            boxShadow: `0 15px 40px rgba(244, 114, 182, ${0.45 + (pulseScale - 1.0) * 8}), 0 0 25px rgba(244, 114, 182, 0.4)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            overflow: 'hidden',
          }}
        >
          {/* Efeito Shimmer Sweep Correndo da Esquerda para a Direita */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 200,
              left: shimmerX,
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.75) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: '#111827',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            CHAME NO DIRECT ➔
          </span>
        </div>
      </div>

      {/* Rodapé: @fabricademarketing.ia (y=1220 a 1300) — Totalmente livre de y > 1580 */}
      <div
        style={{
          position: 'absolute',
          top: 1220,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 40,
          transform: `translateY(${floatArroba}px) scale(${arrobaSpring})`,
          opacity: arrobaSpring,
        }}
      >
        <div
          style={{
            padding: '12px 34px',
            borderRadius: 24,
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            color: '#FFFFFF',
            fontSize: 36,
            fontWeight: 700,
            letterSpacing: 0.8,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
          }}
        >
          @fabricademarketing.ia
        </div>
      </div>
    </div>
  );
};
