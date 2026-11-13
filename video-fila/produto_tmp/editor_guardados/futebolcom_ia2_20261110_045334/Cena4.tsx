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

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom contínuo na foto do fundo
  const bgScale = interpolate(frame, [0, 116], [1.08, 1.20], {
    extrapolateRight: 'clamp',
  });

  // Entrada em cascata com springs naturais
  const logoSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const phraseSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const iconSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  const btnSpring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const handleSpring = spring({
    frame: frame - 32,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Movimentos contínuos para garantir > 10% de mudança do início ao fim
  // 1. Pulsação contínua e suave do botão CTA
  const btnPulse = 1 + Math.sin(frame / 7) * 0.04;
  // 2. Feixe de brilho (shimmer) varrendo o botão
  const shimmerPos = interpolate(frame % 45, [0, 45], [-100, 200]);
  // 3. Flutuação suave da marca e do ícone
  const floatY = Math.sin(frame / 12) * 6;

  return (
    <AbsoluteFill style={{backgroundColor: '#1a0409', overflow: 'hidden'}}>
      {/* Imagem de Fundo com desfoque de ambiente */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          filter: 'blur(22px)',
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
      </div>

      {/* Véu Escuro Premium da Marca para Contraste com Luz Acolhedora */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(49, 6, 15, 0.68) 0%, rgba(18, 2, 6, 0.90) 100%)',
        }}
      />

      {/* Conteúdo Central dentro da Safe Zone (y=180 a 1480) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          fontFamily,
          zIndex: 30,
        }}
      >
        {/* Bloco 1: Logo e Marca (y=220 a 380) */}
        <div
          style={{
            opacity: Math.max(0, logoSpring),
            transform: `translateY(${(1 - logoSpring) * -30 + floatY}px) scale(${interpolate(logoSpring, [0, 1], [0.85, 1])})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            marginBottom: 20,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(225, 29, 72, 0.25)',
              border: '2px solid rgba(225, 29, 72, 0.8)',
              padding: '8px 28px',
              borderRadius: 999,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 34}}>📱</span>
            <span
              style={{
                color: '#FACC15',
                fontSize: 34,
                fontWeight: 900,
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              Tecnologia Para Delivery
            </span>
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-1px',
              textTransform: 'uppercase',
              textShadow: '0 8px 30px rgba(0,0,0,0.8)',
            }}
          >
            Cardápio Digital
          </h1>
        </div>

        {/* Bloco 2: Frase do Produto (y=420 a 540) */}
        <div
          style={{
            opacity: Math.max(0, phraseSpring),
            transform: `translateY(${(1 - phraseSpring) * 20}px)`,
            maxWidth: 880,
            marginBottom: 40,
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 38,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.35,
              textWrap: 'balance',
              textShadow: '0 4px 16px rgba(0,0,0,0.7)',
            }}
          >
            Pedidos com fotos no celular e atendimento com IA direto no WhatsApp
          </p>
        </div>

        {/* Bloco 3: Ícone Central Elegante Flutuante (y=580 a 820) */}
        <div
          style={{
            opacity: Math.max(0, iconSpring),
            transform: `scale(${interpolate(iconSpring, [0, 1], [0.6, 1])}) translateY(${floatY * -1}px)`,
            width: 170,
            height: 170,
            borderRadius: 85,
            background:
              'linear-gradient(135deg, #E11D48 0%, #BE123C 50%, #9F1239 100%)',
            border: '4px solid #FACC15',
            boxShadow:
              '0 20px 50px rgba(225, 29, 72, 0.5), 0 0 35px rgba(250, 204, 21, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 84,
            marginBottom: 50,
          }}
        >
          💬
        </div>

        {/* Bloco 4: Botão CTA Gigante Pulsante (y=920 a 1100) */}
        <div
          style={{
            opacity: Math.max(0, btnSpring),
            transform: `scale(${interpolate(btnSpring, [0, 1], [0.8, 1]) * btnPulse}) translateY(${(1 - btnSpring) * 30}px)`,
            width: 820,
            position: 'relative',
            overflow: 'hidden',
            backgroundColor: '#E11D48',
            border: '4px solid #FACC15',
            borderRadius: 36,
            padding: '28px 40px',
            boxShadow:
              '0 20px 60px rgba(225, 29, 72, 0.6), 0 0 40px rgba(250, 204, 21, 0.4)',
            marginBottom: 40,
          }}
        >
          {/* Shimmer de luz varrendo o botão */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: `${shimmerPos}%`,
              width: '50%',
              height: '100%',
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
              textShadow: '0 4px 16px rgba(0,0,0,0.5)',
            }}
          >
            Chame no Direct
          </span>
        </div>

        {/* Bloco 5: Handle Oficial do Instagram (y=1160 a 1260) */}
        <div
          style={{
            opacity: Math.max(0, handleSpring),
            transform: `translateY(${(1 - handleSpring) * 20}px)`,
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            border: '2px solid rgba(250, 204, 21, 0.5)',
            borderRadius: 999,
            padding: '14px 44px',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            boxShadow: '0 8px 25px rgba(0,0,0,0.4)',
          }}
        >
          <span style={{fontSize: 38}}>📷</span>
          <span
            style={{
              fontSize: 42,
              fontWeight: 800,
              color: '#FACC15',
              letterSpacing: 1,
            }}
          >
            @futebolcom.ia2
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
