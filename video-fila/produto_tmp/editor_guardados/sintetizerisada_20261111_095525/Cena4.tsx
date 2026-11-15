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
  cores: {
    marca: string;
    destaque: string;
    apoio: string;
    fundo_escuro: string;
  };
  arroba: string;
  convite: string;
};

export const Cena4: React.FC<Props> = ({
  fontFamily,
  cores,
  arroba,
  convite,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de zoom de fundo (1.1 -> 1.24)
  const bgScale = interpolate(frame, [0, 120], [1.1, 1.24], {
    extrapolateRight: 'clamp',
  });

  // Entrada rápida e coordenada dos elementos do encerramento
  const brandAnim = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Botão CTA
  const buttonAnim = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Entrada do Handle (@)
  const handleAnim = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Pulso contínuo do botão CTA (vivo do 1º ao último frame)
  const buttonPulse = 1 + 0.04 * Math.sin(frame * 0.2);

  // Efeito Shimmer (brilho passando pelo botão)
  const shimmerPos = interpolate(frame % 45, [0, 45], [-150, 150]);

  // Respiração contínua do logo e glow
  const glowScale = 1 + 0.08 * Math.sin(frame * 0.15);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: cores.fundo_escuro,
        overflow: 'hidden',
      }}
    >
      {/* Foto de Fundo Desfocada com Zoom Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          filter: 'blur(16px)',
          opacity: 0.3,
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Véu Escuro Elegante */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(255, 169, 77, 0.15) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(10, 15, 28, 0.98) 100%)',
        }}
      />

      {/* Conteúdo Centralizado na Safe Zone */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 10,
        }}
      >
        {/* Halo de Luz Pulsante atrás do Logo */}
        <div
          style={{
            position: 'absolute',
            top: 20,
            width: 380,
            height: 380,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${cores.destaque} 0%, rgba(255, 169, 77, 0) 70%)`,
            filter: 'blur(45px)',
            opacity: 0.35 * glowScale,
            transform: `scale(${glowScale})`,
            pointerEvents: 'none',
          }}
        />

        {/* Ícone e Nome da Marca */}
        <div
          style={{
            opacity: brandAnim,
            transform: `scale(${brandAnim}) translateY(${interpolate(brandAnim, [0, 1], [30, 0])}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginBottom: 20,
          }}
        >
          {/* Emblema / Ícone */}
          <div
            style={{
              width: 110,
              height: 110,
              borderRadius: 30,
              backgroundColor: 'rgba(31, 41, 55, 0.95)',
              border: `3px solid ${cores.destaque}`,
              boxShadow: `0 12px 35px rgba(0,0,0,0.6), 0 0 25px rgba(255, 169, 77, 0.4)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 56,
              marginBottom: 24,
            }}
          >
            📅
          </div>

          <div
            style={{
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span>Agenda</span>
            <span style={{color: cores.destaque}}>IA</span>
          </div>

          {/* 1 frase do que o produto faz (fatos autorizados do briefing) */}
          <div
            style={{
              fontSize: 36,
              fontWeight: 600,
              color: '#E5E7EB',
              textAlign: 'center',
              marginTop: 14,
              maxWidth: 820,
              lineHeight: 1.3,
              textShadow: '0 2px 10px rgba(0,0,0,0.8)',
            }}
          >
            Agendamentos automáticos com IA 24h
          </div>
        </div>

        {/* Botão Principal Pulsante (Ação idêntica ao convite de voz) */}
        <div
          style={{
            marginTop: 70,
            opacity: buttonAnim,
            transform: `scale(${buttonAnim * buttonPulse}) translateY(${interpolate(buttonAnim, [0, 1], [40, 0])}px)`,
            width: '100%',
            maxWidth: 860,
            height: 112,
            backgroundColor: cores.destaque,
            borderRadius: 56,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            boxShadow: `0 15px 45px rgba(0,0,0,0.7), 0 0 35px rgba(255, 169, 77, 0.55)`,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Linha de Shimmer animada */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 60,
              background:
                'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
              transform: `skewX(-25deg) translateX(${shimmerPos}%)`,
            }}
          />

          <span
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: cores.apoio,
              textTransform: 'uppercase',
              letterSpacing: '0.03em',
            }}
          >
            {convite.toUpperCase()}
          </span>
          <span style={{fontSize: 42, color: cores.apoio}}>➔</span>
        </div>

        {/* Handle / Arroba */}
        <div
          style={{
            marginTop: 40,
            opacity: handleAnim,
            transform: `translateY(${interpolate(handleAnim, [0, 1], [25, 0])}px)`,
            backgroundColor: 'rgba(31, 41, 55, 0.9)',
            border: '2px solid rgba(255, 255, 255, 0.18)',
            borderRadius: 30,
            padding: '12px 32px',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
          }}
        >
          <span style={{fontSize: 34}}>💬</span>
          <span
            style={{
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.02em',
            }}
          >
            {arroba}
          </span>
        </div>
      </div>
    </div>
  );
};
