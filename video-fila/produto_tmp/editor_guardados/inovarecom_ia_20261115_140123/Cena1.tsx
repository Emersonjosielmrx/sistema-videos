import React from 'react';
import {
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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phases tied to voice:
  // Phase 1 (0..99): "Minha equipe passava o dia discando..."
  // Phase 2 (100..157): "para listas gigantescas..." (starts ~8.29s absolute -> frame 100 from 4.96s)
  // Phase 3 (158..246): "e acabava o expediente totalmente exausta." (starts ~10.21s absolute -> frame 158)
  const isPhase2 = frame >= 100 && frame < 158;
  const isPhase3 = frame >= 158;

  // Distinct scale cut from Scene 0 + digital punch-ins on emphasis moments, keeping head shifted down for generous headroom
  const baseZoom = isPhase3
    ? interpolate(frame, [158, 246], [1.22, 1.28], {extrapolateRight: 'clamp'})
    : isPhase2
    ? interpolate(frame, [100, 157], [1.12, 1.16], {extrapolateRight: 'clamp'})
    : interpolate(frame, [0, 99], [1.02, 1.07], {extrapolateRight: 'clamp'});

  const panY = isPhase3 ? 120 : isPhase2 ? 110 : 100;

  // Active micro-animation for meter
  const meterWidth = interpolate(frame, [100, 158], [30, 96], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Dynamic Pain B-Roll Widget (Spreadsheet & Rejected Calls Queue) in lower chest zone
  const painWidgetSpring = spring({
    frame: isPhase3 ? frame - 158 : isPhase2 ? frame - 100 : Math.max(0, frame - 12),
    fps,
    config: {damping: 13, stiffness: 115},
  });

  const rejectedCount = Math.floor(
    interpolate(frame, [0, 240], [128, 249], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );

  // Spring entrance
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  const cardSpring = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Dynamic zoom-through + directional wipe transition into Scene 2 at the end of Scene 1
  const exitZoom = interpolate(frame, [230, 246], [1, 1.35], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitBlur = interpolate(frame, [230, 246], [0, 14], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [234, 246], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
        opacity: exitOpacity,
        transform: `scale(${exitZoom})`,
        filter: exitBlur > 0 ? `blur(${exitBlur}px)` : undefined,
      }}
    >
      {/* Video of Company Owner with Color Grading (taming blown-out window highlights) & Crisp Punch-in Cut */}
      <OffthreadVideo
        src={staticFile('dono_1.mp4')}
        muted
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          filter: 'brightness(0.88) contrast(1.1) saturate(0.95) sepia(0.08)',
          transformOrigin: '50% 38%',
          transform: `scale(${baseZoom}) translateY(${panY}px)`,
        }}
      />

      {/* Subtle Corporate Emerald Color-Grading Overlay to unify color temperature & tame bright background windows */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 42%, rgba(8, 46, 22, 0.08) 0%, rgba(6, 28, 16, 0.42) 75%, rgba(4, 18, 10, 0.68) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Gentle top shadow STRICTLY above y=380 (owner face starts at ~y=400) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background:
            'linear-gradient(180deg, rgba(6, 24, 14, 0.92) 0%, rgba(6, 24, 14, 0.62) 60%, rgba(6, 24, 14, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Bottom vignette for Karaoke readability */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 460,
          background:
            'linear-gradient(0deg, rgba(5, 22, 12, 0.85) 0%, rgba(5, 22, 12, 0.4) 55%, rgba(5, 22, 12, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Zone Content (Safe Zone: y=154..315, completely clear of presenter's forehead & hair) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          zIndex: 10,
        }}
      >
        {/* Rótulo Badge — Consistently fixed as '🔴 O PROBLEMA REAL' in red throughout Scene 1 */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            background: 'rgba(239, 68, 68, 0.28)',
            border: '2px solid #EF4444',
            borderRadius: 9999,
            padding: '6px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
          }}
        >
          <span
            style={{
              display: 'inline-block',
              width: 14,
              height: 14,
              borderRadius: 7,
              backgroundColor: '#FF4D4D',
              boxShadow: '0 0 10px #FF4D4D',
              opacity: Math.sin(frame * 0.25) > 0 ? 1 : 0.4,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}
          >
            🔴 O PROBLEMA REAL
          </span>
        </div>

        {/* Evolving Compact Top Card (Height ~100px, strictly stays above y=315) */}
        <div
          style={{
            transform: `scale(${cardSpring})`,
            opacity: cardSpring,
            width: '100%',
            maxWidth: 960,
            background: 'rgba(8, 22, 14, 0.92)',
            border: '2px solid rgba(239, 68, 68, 0.55)',
            borderRadius: 18,
            padding: '10px 20px',
            textAlign: 'center',
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.65)',
          }}
        >
          {!isPhase2 && !isPhase3 && (
            <div>
              <div
                style={{
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.18,
                }}
              >
                DISCAGEM MANUAL SEM FIM
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                  marginTop: 2,
                }}
              >
                Equipe sobrecarregada o dia todo ao telefone
              </div>
            </div>
          )}

          {isPhase2 && (
            <div>
              <div
                style={{
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FBBF24',
                  lineHeight: 1.18,
                }}
              >
                LISTAS GIGANTESCAS
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 14,
                  marginTop: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#E2E8F0',
                  }}
                >
                  Sobrecarga de contatos
                </span>
                <div
                  style={{
                    width: 180,
                    height: 10,
                    borderRadius: 5,
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${meterWidth}%`,
                      height: '100%',
                      backgroundColor: '#FBBF24',
                      borderRadius: 5,
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {isPhase3 && (
            <div>
              <div
                style={{
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FF5555',
                  lineHeight: 1.18,
                }}
              >
                EQUIPE TOTALMENTE EXAUSTA
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                  marginTop: 2,
                }}
              >
                Vendedores esgotados sem tempo para fechar vendas
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Dynamic Visual Support / Motion B-Roll Card in Lower Zone (y=1220..1340) on presenter's chest clear of chin & well above karaoke */}
      <div
        style={{
          position: 'absolute',
          top: 1220,
          left: 60,
          right: 60,
          zIndex: 10,
          transform: `scale(${painWidgetSpring}) translateY(${interpolate(
            painWidgetSpring,
            [0, 1],
            [35, 0]
          )}px)`,
          opacity: painWidgetSpring,
          background: 'rgba(12, 18, 26, 0.95)',
          border: '2px solid rgba(239, 68, 68, 0.65)',
          borderRadius: 22,
          padding: '16px 24px',
          boxShadow: '0 16px 40px rgba(0, 0, 0, 0.75)',
        }}
      >
        {!isPhase2 && !isPhase3 && (
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 38}}>📵</span>
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  FILA DE CHAMADAS MANUAL
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#CBD5E1'}}>
                  Tentativa #{rejectedCount} • Sem resposta
                </div>
              </div>
            </div>
            <div
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                background: '#EF4444',
                padding: '8px 18px',
                borderRadius: 12,
              }}
            >
              REJEITADA
            </div>
          </div>
        )}

        {isPhase2 && (
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 38}}>📊</span>
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  PLANILHA INTERMINÁVEL
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#FBBF24'}}>
                  Linha {rejectedCount} • Discando um por um
                </div>
              </div>
            </div>
            <div
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                background: '#D97706',
                padding: '8px 18px',
                borderRadius: 12,
              }}
            >
              LENTO
            </div>
          </div>
        )}

        {isPhase3 && (
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 38}}>🪫</span>
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  FIM DO EXPEDIENTE
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#FCA5A5'}}>
                  Zero energia para fechar negócios
                </div>
              </div>
            </div>
            <div
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                background: '#EF4444',
                padding: '8px 18px',
                borderRadius: 12,
              }}
            >
              EXAUSTOS
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
