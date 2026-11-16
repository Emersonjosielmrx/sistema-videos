import React from 'react';
import {
  Img,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3Dono: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Escala compensatória (1.22x para eliminar as tarjas pretas laterais de dono_3.mp4) + zoom contínuo de câmera
  const zoom = interpolate(frame, [0, 242], [1.22, 1.28], {
    extrapolateRight: 'clamp',
  });

  // Badge "O RESULTADO" entra no frame 6
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Título: "TRANQUILIDADE OPERACIONAL" entra no frame 10 (~18.68s)
  const titleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 100},
  });

  // Badge: "PROTEÇÃO DIÁRIA & CONTÍNUA" entra no frame 118 (~22.46s na fala)
  const protectionBadgeSpring = spring({
    frame: frame - 118,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Pulso de tranquilidade
  const pulse = Math.sin(frame * 0.18) * 0.5 + 0.5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Camada 1: Fundo Tecnológico de Apoio */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 1,
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada 2: Vídeo do Apresentador compensado (sem tarjas pretas) e deslocado para baixo (cabelo em y ~420) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 5,
          transform: `translateY(240px) scale(${zoom})`,
          transformOrigin: 'center top',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada 3: Véu de contraste no topo para legibilidade do texto, 100% transparente a partir de y=380 para proteger rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 420,
          zIndex: 10,
          background:
            'linear-gradient(to bottom, #0F172A 0%, rgba(15, 23, 42, 0.98) 260px, rgba(15, 23, 42, 0.6) 330px, transparent 400px)',
          pointerEvents: 'none',
        }}
      />

      {/* ================= TOPO INFORMATIVO (y: 165 a 330 - Respiro > 50px até o Cabelo) ================= */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 25,
        }}
      >
        {/* Rótulo da Cena: O RESULTADO */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `scale(${badgeSpring})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.92)',
            border: '2px solid rgba(16, 185, 129, 0.7)',
            boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: `0 0 ${8 + pulse * 6}px #10B981`,
            }}
          />
          <span
            style={{
              color: '#6EE7B7',
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            O RESULTADO
          </span>
        </div>

        {/* Título Principal: TRANQUILIDADE TOTAL */}
        <div
          style={{
            marginTop: 14,
            opacity: titleSpring,
            transform: `translateY(${(1 - titleSpring) * 15}px)`,
            fontSize: 48,
            fontWeight: 900,
            color: '#FFFFFF',
            textShadow: '0 4px 16px rgba(0,0,0,0.95)',
            letterSpacing: -0.5,
          }}
        >
          TRANQUILIDADE OPERACIONAL
        </div>

        {/* Badge de Proteção Diária e Contínua (entra no frame 118) */}
        {frame >= 115 && (
          <div
            style={{
              marginTop: 12,
              opacity: protectionBadgeSpring,
              transform: `scale(${interpolate(protectionBadgeSpring, [0, 1], [0.85, 1])})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 22px',
              borderRadius: 16,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '2px solid rgba(14, 165, 233, 0.8)',
              boxShadow: '0 6px 20px rgba(14, 165, 233, 0.4)',
            }}
          >
            <span style={{fontSize: 32}}>🛡️</span>
            <span
              style={{
                color: '#38BDF8',
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 0.5,
              }}
            >
              PROTEÇÃO DIÁRIA & CONTÍNUA
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
