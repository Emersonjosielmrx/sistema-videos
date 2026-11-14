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

export const Cena1Dono: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom suave e contínuo no vídeo
  const zoom = interpolate(frame, [0, 241], [1.12, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Badge "O PROBLEMA" entra aos 0.3s (frame 10)
  const badgeSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // "OPERANDO NO ESCURO" entra no frame 26 (~5.53s na narração)
  const titleSpring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 13, stiffness: 100},
  });

  // "SEM CÓPIA DE SEGURANÇA" entra no frame 115 (~8.49s)
  const backupAlertSpring = spring({
    frame: frame - 115,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // "SEM ALERTAS DE FALHA" entra no frame 151 (~9.69s)
  const failAlertSpring = spring({
    frame: frame - 151,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Pulso sutil dos alertas
  const pulse = Math.sin(frame * 0.2) * 0.5 + 0.5;

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
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada 2: Vídeo do Apresentador deslocado para baixo (cabelo em y ~390, respiro > 50px do HUD) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 5,
          transform: `translateY(270px) scale(${zoom})`,
          transformOrigin: 'center top',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada 3: Véu de contraste no topo (sólido até y=280 para texto, 100% transparente a partir de y=380 para proteger rosto) */}
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
        {/* Rótulo da Cena: O PROBLEMA */}
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
            border: '2px solid rgba(239, 68, 68, 0.7)',
            boxShadow: '0 4px 16px rgba(239, 68, 68, 0.3)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: `0 0 ${8 + pulse * 6}px #EF4444`,
            }}
          />
          <span
            style={{
              color: '#FCA5A5',
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            O PROBLEMA
          </span>
        </div>

        {/* Título Principal: OPERANDO NO ESCURO */}
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
          OPERANDO NO ESCURO
        </div>

        {/* Badges de Falhas Reais do Relato (entram sincronizadas com a fala) */}
        <div
          style={{
            marginTop: 12,
            display: 'flex',
            justifyContent: 'center',
            gap: 14,
            flexWrap: 'wrap',
          }}
        >
          {/* Badge 1: Sem Cópia de Segurança */}
          {frame >= 110 && (
            <div
              style={{
                opacity: backupAlertSpring,
                transform: `scale(${interpolate(backupAlertSpring, [0, 1], [0.85, 1])})`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 18px',
                borderRadius: 14,
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid rgba(239, 68, 68, 0.7)',
                boxShadow: '0 4px 14px rgba(0,0,0,0.7)',
              }}
            >
              <span style={{fontSize: 28}}>⚠️</span>
              <span
                style={{
                  color: '#FEF2F2',
                  fontSize: 33,
                  fontWeight: 800,
                  letterSpacing: 0.5,
                }}
              >
                Sem Backup
              </span>
            </div>
          )}

          {/* Badge 2: Sem Alertas */}
          {frame >= 145 && (
            <div
              style={{
                opacity: failAlertSpring,
                transform: `scale(${interpolate(failAlertSpring, [0, 1], [0.85, 1])})`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 18px',
                borderRadius: 14,
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid rgba(239, 68, 68, 0.7)',
                boxShadow: '0 4px 14px rgba(0,0,0,0.7)',
              }}
            >
              <span style={{fontSize: 28}}>❌</span>
              <span
                style={{
                  color: '#FEF2F2',
                  fontSize: 33,
                  fontWeight: 800,
                  letterSpacing: 0.5,
                }}
              >
                Sem Alertas
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
