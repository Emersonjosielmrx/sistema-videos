import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: zoom contínuo de 1.0 a 1.08 ao longo de toda a cena
  const scale = interpolate(frame, [0, 162], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge de topo aos 0.15s (frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Linha 1 ("CANSADO DE") aos 0.3s (frame 9)
  const l1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Linha 2 ("CRM ENGESSADO") aos 0.9s (frame 27)
  const l2Spring = spring({
    frame: frame - 27,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Linha 3 ("que sua equipe não consegue usar?") aos 2.0s (frame 60)
  const l3Spring = spring({
    frame: frame - 60,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso no destaque azul
  const pulse = Math.sin(frame * 0.12) * 0.025;

  // Saída suave para transição nos últimos 12 frames
  const fadeOut = interpolate(frame, [150, 162], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: fadeOut}}>
      {/* Imagem de Fundo com zoom contínuo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale})`,
            filter: 'brightness(0.72) contrast(1.08)',
          }}
        />
        {/* Gradiente lateral protegendo a atendente à direita (rosto totalmente livre) */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(90deg, rgba(17,24,39,0.94) 0%, rgba(17,24,39,0.78) 50%, rgba(17,24,39,0.2) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo dentro da Safe Zone (y: 150 a 1580, laterais >= 60px) */}
      <AbsoluteFill style={{padding: '0 60px', pointerEvents: 'none'}}>
        {/* Badge de Topo */}
        <div
          style={{
            position: 'absolute',
            top: 180,
            left: 60,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: 'rgba(31, 147, 255, 0.22)',
            border: '2px solid rgba(31, 147, 255, 0.75)',
            padding: '10px 24px',
            borderRadius: 30,
            opacity: badgeSpring,
            transform: `translateY(${(1 - badgeSpring) * -20}px)`,
            backdropFilter: 'blur(8px)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#1F93FF',
              boxShadow: '0 0 12px #1F93FF',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Produtividade Comercial
          </span>
        </div>

        {/* Bloco de Gancho Cinético (largura 540px na esquerda) */}
        <div
          style={{
            position: 'absolute',
            top: 260,
            left: 60,
            width: 530,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Linha 1: CANSADO DE */}
          {frame >= 8 && (
            <div
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                opacity: l1Spring,
                transform: `scale(${l1Spring})`,
                transformOrigin: 'left center',
                textShadow: '0 4px 16px rgba(0,0,0,0.9)',
              }}
            >
              CANSADO DE
            </div>
          )}

          {/* Linha 2: CRM ENGESSADO com destaque azul */}
          {frame >= 25 && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                alignSelf: 'flex-start',
                backgroundColor: '#1F93FF',
                padding: '12px 26px',
                borderRadius: 18,
                boxShadow: '0 8px 30px rgba(31, 147, 255, 0.6)',
                opacity: l2Spring,
                transform: `scale(${l2Spring + pulse})`,
                transformOrigin: 'left center',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 56,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 1.2,
                  textTransform: 'uppercase',
                }}
              >
                CRM ENGESSADO
              </span>
            </div>
          )}

          {/* Linha 3: QUE SUA EQUIPE NÃO CONSEGUE USAR? */}
          {frame >= 58 && (
            <div
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.92)',
                border: '2px solid rgba(255, 255, 255, 0.2)',
                borderRadius: 20,
                padding: '22px 26px',
                marginTop: 6,
                opacity: l3Spring,
                transform: `translateY(${(1 - l3Spring) * 20}px)`,
                boxShadow: '0 12px 30px rgba(0,0,0,0.7)',
                backdropFilter: 'blur(10px)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.35,
                  display: 'block',
                }}
              >
                que sua equipe <span style={{color: '#60A5FA', fontWeight: 900}}>não consegue</span> usar?
              </span>
            </div>
          )}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
