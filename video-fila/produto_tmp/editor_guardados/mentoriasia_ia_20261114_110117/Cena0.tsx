import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {COLORS, fontFamily} from './theme';

export const Cena0: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: push-in contínuo (1.00 -> 1.08)
  const bgScale = interpolate(frame, [0, 142], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Gancho pop inicial aos 0.3s (frame ~9)
  const popGancho = spring({
    frame: frame - 9,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Linha 2 ("TRAVAM A ROTINA") aos 1.74s (frame ~52)
  const popTravam = spring({
    frame: frame - 52,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Linha 3 ("DA EMPRESA?") aos 2.6s (frame ~78)
  const popEmpresa = spring({
    frame: frame - 78,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Gancho fixo superior entra aos 2.2s (frame ~66)
  const popSeloGancho = spring({
    frame: frame - 66,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Pulso contínuo das ondas de radar
  const pulseRing1 = (frame * 1.5) % 90;
  const pulseRing2 = ((frame + 45) * 1.5) % 90;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: COLORS.fundoEscuro,
      }}
    >
      {/* Imagem de Fundo com Movimento */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
            opacity: 0.88,
          }}
        />
        {/* Overlay escuro elegante */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(17, 24, 39, 0.4) 0%, rgba(11, 15, 25, 0.9) 100%)',
          }}
        />
      </div>

      {/* Grid tech sutil */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(circle, rgba(59, 130, 246, 0.18) 1.5px, transparent 1.5px)',
          backgroundSize: '48px 48px',
          opacity: 0.55,
          transform: `translateY(${frame * 0.5}px)`,
        }}
      />

      {/* Anéis de pulso de automação/radar no centro de fundo */}
      <div
        style={{
          position: 'absolute',
          top: 860,
          left: 540,
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
          zIndex: 10,
        }}
      >
        <div
          style={{
            position: 'absolute',
            width: pulseRing1 * 7,
            height: pulseRing1 * 7,
            borderRadius: '50%',
            border: '2px solid rgba(59, 130, 246, 0.4)',
            transform: 'translate(-50%, -50%)',
            opacity: 1 - pulseRing1 / 90,
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: pulseRing2 * 7,
            height: pulseRing2 * 7,
            borderRadius: '50%',
            border: '2px solid rgba(37, 99, 235, 0.3)',
            transform: 'translate(-50%, -50%)',
            opacity: 1 - pulseRing2 / 90,
          }}
        />
      </div>

      {/* Selo Fixo: Gancho de Tela (Aparece aos ~2.2s em y=210) */}
      {frame >= 66 && (
        <div
          style={{
            position: 'absolute',
            top: 210,
            left: 0,
            right: 0,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${Math.min(1, Math.max(0, popSeloGancho))})`,
            zIndex: 30,
          }}
        >
          <div
            style={{
              padding: '14px 32px',
              borderRadius: 30,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '2px solid #EF4444',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 8px 30px rgba(239, 68, 68, 0.45)',
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                background: COLORS.vermelhoAlerta,
                boxShadow: `0 0 12px ${COLORS.vermelhoAlerta}`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
              }}
            >
              Processos lentos na empresa?
            </span>
          </div>
        </div>
      )}

      {/* Bloco Central Cinético de Impacto (y=500 a 1180) */}
      <div
        style={{
          position: 'absolute',
          top: 520,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 36,
          zIndex: 25,
          textAlign: 'center',
        }}
      >
        {/* Linha 1: "SEUS PROCESSOS INTERNOS" (entra aos 0.3s) */}
        <div
          style={{
            transform: `scale(${Math.min(1, Math.max(0, popGancho))})`,
            opacity: interpolate(frame, [9, 16], [0, 1], {
              extrapolateRight: 'clamp',
            }),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 800,
              color: '#94A3B8',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}
          >
            Seus
          </span>
          <div
            style={{
              padding: '16px 42px',
              borderRadius: 24,
              background: 'linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%)',
              border: '3px solid rgba(147, 197, 253, 0.7)',
              boxShadow: '0 14px 40px rgba(37, 99, 235, 0.55)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 62,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.03em',
                textTransform: 'uppercase',
              }}
            >
              Processos Internos
            </span>
          </div>
        </div>

        {/* Linha 2: "TRAVAM A ROTINA" (entra aos 1.74s) */}
        {frame >= 48 && (
          <div
            style={{
              transform: `scale(${Math.min(1, Math.max(0, popTravam))})`,
              opacity: interpolate(frame, [48, 56], [0, 1], {
                extrapolateRight: 'clamp',
              }),
              padding: '18px 46px',
              borderRadius: 28,
              background:
                'linear-gradient(135deg, #991B1B 0%, #DC2626 50%, #EF4444 100%)',
              border: '3px solid #FCA5A5',
              boxShadow:
                '0 16px 50px rgba(220, 38, 38, 0.65), 0 0 30px rgba(239, 68, 68, 0.4)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 70,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.03em',
              }}
            >
              Travam a Rotina
            </span>
          </div>
        )}

        {/* Linha 3: "DA EMPRESA?" (entra aos 2.6s) */}
        {frame >= 74 && (
          <div
            style={{
              transform: `scale(${Math.min(1, Math.max(0, popEmpresa))})`,
              opacity: interpolate(frame, [74, 82], [0, 1], {
                extrapolateRight: 'clamp',
              }),
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 58,
                fontWeight: 900,
                color: '#F8FAFC',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              }}
            >
              Da Empresa?
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
