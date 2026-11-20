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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera no fundo (Ken Burns cinematográfico)
  const bgScale = interpolate(frame, [0, 145], [1.02, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 145], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição para a cena do dono
  const sceneOpacity = interpolate(frame, [136, 145], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação da Badge Superior (Entra aos ~0.15s)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Animação 1: "VOU PARAR DE" (entra em ~0.32s = frame 10)
  const t1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 120},
  });

  // Animação 2: "PERDER CLIENTE" (entra em ~1.00s = frame 30)
  const t2Spring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 12, mass: 0.8, stiffness: 140},
  });

  // Animação 3: "POR DEMORA" (entra em ~2.04s = frame 61)
  const t3Spring = spring({
    frame: frame - 61,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 130},
  });

  // Animação 4: "NO ATENDIMENTO?" (entra em ~2.55s = frame 76)
  const t4Spring = spring({
    frame: frame - 76,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Animação 5: Gancho fixo "Cliente some por demora?" (entra em ~2.8s = frame 85)
  const ganchoSpring = spring({
    frame: frame - 85,
    fps,
    config: {damping: 12, mass: 0.8},
  });

  // Pulso e micro-flutuação para manter a cena viva até o final
  const ganchoFloat = Math.sin((frame - 85) / 8) * 6;
  const alertPulse = Math.sin(frame / 6) * 0.03 + 1.0;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Imagem de Fundo com Movimento Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Camada de escurecimento e contraste graduado */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11,13,19,0.92) 0%, rgba(17,24,39,0.80) 45%, rgba(11,13,19,0.95) 100%)',
          }}
        />
      </div>

      {/* Topo Informativo: Badge chanfrado com corte diagonal (item aprovado 28a1924f) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.max(0, badgeSpring),
          transform: `translateY(${(1 - Math.max(0, badgeSpring)) * -25}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid #A78BFA',
            borderRadius: '16px 4px 16px 4px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#A78BFA',
              boxShadow: '0 0 10px #A78BFA',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#DDD6FE',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            DÚVIDA FREQUENTE DO LOJISTA
          </span>
        </div>
      </div>

      {/* Bloco Central de Tipografia Cinética de Alto Impacto */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 20,
        }}
      >
        {/* Linha 1: VOU PARAR DE */}
        <div
          style={{
            opacity: Math.max(0, t1Spring),
            transform: `scale(${Math.max(0.7, t1Spring)}) translateY(${(1 - Math.max(0, t1Spring)) * 30}px)`,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
              textShadow: '0 4px 16px rgba(0,0,0,0.9)',
            }}
          >
            VOU PARAR DE
          </span>
        </div>

        {/* Linha 2: PERDER CLIENTE (Destaque Marca-texto / Box Roxo da Marca) */}
        <div
          style={{
            opacity: Math.max(0, t2Spring),
            transform: `scale(${Math.max(0.7, t2Spring)})`,
          }}
        >
          <div
            style={{
              backgroundColor: '#A78BFA',
              padding: '12px 36px',
              borderRadius: 20,
              boxShadow: '0 12px 35px rgba(167, 139, 250, 0.45)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 66,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              PERDER CLIENTE
            </span>
          </div>
        </div>

        {/* Linha 3: POR DEMORA (Badge de Alerta em Vermelho Vibrante) */}
        <div
          style={{
            opacity: Math.max(0, t3Spring),
            transform: `scale(${Math.max(0.7, t3Spring)}) translateY(${(1 - Math.max(0, t3Spring)) * 20}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.22)',
              border: '3px solid #EF4444',
              padding: '10px 32px',
              borderRadius: 18,
              boxShadow: '0 8px 25px rgba(239, 68, 68, 0.35)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 56,
                fontWeight: 900,
                color: '#FECACA',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              POR DEMORA
            </span>
          </div>
        </div>

        {/* Linha 4: NO ATENDIMENTO? */}
        <div
          style={{
            opacity: Math.max(0, t4Spring),
            transform: `translateY(${(1 - Math.max(0, t4Spring)) * 20}px)`,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
              textShadow: '0 4px 16px rgba(0,0,0,0.9)',
            }}
          >
            NO ATENDIMENTO?
          </span>
        </div>
      </div>

      {/* Selo Fixo: gancho_tela ("Cliente some por demora?") com ícone pulsante */}
      {frame >= 80 && (
        <div
          style={{
            position: 'absolute',
            top: 1040,
            left: 80,
            right: 80,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.max(0, ganchoSpring),
            transform: `translateY(${ganchoFloat}px) scale(${alertPulse})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 16,
              padding: '16px 36px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '2px solid rgba(167, 139, 250, 0.6)',
              borderRadius: 24,
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(12px)',
            }}
          >
            <svg
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#A78BFA"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 1,
              }}
            >
              Cliente some por demora?
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
