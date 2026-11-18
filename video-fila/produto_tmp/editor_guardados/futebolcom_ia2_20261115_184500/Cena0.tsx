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

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom and pan — dynamic, warm, cinematic
  const bgScale = interpolate(frame, [0, 143], [1.02, 1.20], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 143], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Fade out transition at the end (from frame 130 to 143)
  const sceneOpacity = interpolate(frame, [130, 143], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Immediate punchy entry from frame 0
  const hook1Progress = spring({
    frame,
    fps,
    config: {damping: 10, stiffness: 180},
  });

  // Smartphone Digital Menu Card enters at frame 0 with dynamic zoom
  const menuCardProgress = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Continuous zoom (1.0 -> 1.08) on the card
  const mockupKenBurns = interpolate(frame, [0, 143], [0.98, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Customer doubt notification pops right at frame 0 with spring bounce
  const questionPop = spring({
    frame,
    fps,
    config: {damping: 9, stiffness: 180},
  });
  const questionTremor =
    frame <= 25
      ? Math.sin(frame * 0.7) * Math.exp(-frame * 0.1) * 3
      : 0;

  // Conflict impact badge enters early at 0.3s (frame 9) so q01 (0-1.5s) shows full conflict!
  const alertBannerPop = spring({
    frame: Math.max(0, frame - 9),
    fps,
    config: {damping: 10, stiffness: 165},
  });

  // Continuous Ken Burns zoom & pan on the real appetizing dish photograph (1.02 -> 1.25)
  const dishKenBurns = interpolate(frame, [0, 143], [1.02, 1.25], {
    extrapolateRight: 'clamp',
  });
  const dishPanX = interpolate(frame, [0, 143], [10, -28], {
    extrapolateRight: 'clamp',
  });
  const dishPanY = interpolate(frame, [0, 143], [6, -22], {
    extrapolateRight: 'clamp',
  });

  // Reflective light sheen sweeping across the real dish photo
  const photoSheenX = interpolate(frame, [0, 140], [-250, 1150], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Continuous floating motion on card
  const floatY = Math.sin(frame * 0.14) * 8;
  const floatX = Math.cos(frame * 0.10) * 4;
  const tilt3D = interpolate(frame, [0, 70, 143], [-3.5, 3.0, -2.0], {
    extrapolateRight: 'clamp',
  });
  const questionPulse = 1.0 + Math.sin(frame * 0.22) * 0.03;

  return (
    <AbsoluteFill
      style={{
        opacity: sceneOpacity,
        backgroundColor: '#31060F',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background with continuous zoom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
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
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 42%, rgba(225, 29, 72, 0.22) 0%, rgba(49, 6, 15, 0.72) 68%, rgba(18, 2, 5, 0.88) 100%)',
          }}
        />
      </div>

      {/* Main Kinetic Content + Smartphone Mockup (y=170 to y=1395) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 18,
          zIndex: 10,
          transform: `translate(${floatX}px, ${floatY}px)`,
        }}
      >
        {/* Single Main Impact Callout at Top: "PERDENDO VENDAS?" (No redundant stacked questions!) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
            opacity: hook1Progress,
            transform: `scale(${0.85 + hook1Progress * 0.15})`,
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
              padding: '10px 28px',
              borderRadius: 20,
              border: '2px solid rgba(255, 255, 255, 0.35)',
              boxShadow: '0 10px 30px rgba(225, 29, 72, 0.7)',
            }}
          >
            <span
              style={{
                fontSize: 60,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
                lineHeight: 1.05,
              }}
            >
              PERDENDO
            </span>
          </div>
          <span
            style={{
              fontSize: 60,
              fontWeight: 900,
              color: '#FACC15',
              textTransform: 'uppercase',
              letterSpacing: '0.02em',
              lineHeight: 1.05,
              textShadow: '0 6px 24px rgba(0, 0, 0, 0.9)',
            }}
          >
            VENDAS?
          </span>
        </div>

        {/* Foreground Smartphone Mockup showing Digital Menu with REAL Appetizing Dish Photo & Continuous Ken Burns */}
        <div
          style={{
            position: 'relative',
            width: 920,
            opacity: menuCardProgress,
            transform: `perspective(1100px) rotateY(${tilt3D}deg) scale(${(0.86 + menuCardProgress * 0.14) * mockupKenBurns})`,
            background: 'linear-gradient(180deg, #1E070E 0%, #110307 100%)',
            border: '5px solid #334155',
            borderRadius: 38,
            padding: '20px 26px',
            boxShadow:
              '0 28px 65px rgba(0, 0, 0, 0.88), 0 0 38px rgba(225, 29, 72, 0.38)',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            overflow: 'hidden',
          }}
        >
          {/* Smartphone Top Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255, 255, 255, 0.14)',
              paddingBottom: 12,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  background: '#E11D48',
                  boxShadow: '0 0 10px #E11D48',
                }}
              />
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Cardápio Digital
              </span>
            </div>
            <div
              style={{
                background: 'rgba(250, 204, 21, 0.22)',
                border: '2px solid #FACC15',
                padding: '5px 16px',
                borderRadius: 14,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FACC15',
                }}
              >
                📸 Fotos no Celular
              </span>
            </div>
          </div>

          {/* Menu Item Container with Real Gastronomic Photography & Immediate Doubt Pop-Up */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            {/* Real High-Impact Food Photograph Window with Continuous Ken Burns & Reflective Sheen */}
            <div
              style={{
                position: 'relative',
                width: '100%',
                height: 550,
                borderRadius: 24,
                overflow: 'hidden',
                border: '2.5px solid rgba(250, 204, 21, 0.65)',
                boxShadow: '0 14px 34px rgba(0, 0, 0, 0.75)',
                background: '#1A0B05',
              }}
            >
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  transform: `scale(${dishKenBurns}) translate(${dishPanX}px, ${dishPanY}px)`,
                  transformOrigin: 'center center',
                }}
              >
                <Img
                  src={staticFile('prato_executivo.jpg')}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />
              </div>

              {/* Subtle gradient for overlay legibility */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background:
                    'linear-gradient(180deg, rgba(0,0,0,0.5) 0%, transparent 28%, transparent 62%, rgba(0,0,0,0.72) 100%)',
                  pointerEvents: 'none',
                }}
              />

              {/* Glossy reflective light sweep across the dish photograph */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: photoSheenX,
                  width: 180,
                  background:
                    'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%)',
                  transform: 'skewX(-25deg)',
                  pointerEvents: 'none',
                }}
              />

              {/* Dish Title Badge inside Food Photo */}
              <div
                style={{
                  position: 'absolute',
                  top: 16,
                  left: 18,
                  background: 'rgba(15, 3, 6, 0.9)',
                  border: '1.5px solid rgba(255, 255, 255, 0.38)',
                  borderRadius: 16,
                  padding: '8px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  boxShadow: '0 6px 16px rgba(0,0,0,0.65)',
                }}
              >
                <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                  Prato Executivo Especial
                </span>
              </div>
            </div>

            {/* Immediate Pop-Up Notification of Customer's Doubt (Active from frame 3 / 0.1s!) */}
            <div
              style={{
                opacity: questionPop,
                transform: `scale(${(0.82 + questionPop * 0.18) * questionPulse}) rotate(${questionTremor}deg)`,
                background: 'linear-gradient(135deg, #E11D48 0%, #9F1239 100%)',
                border: '3px solid #FACC15',
                borderRadius: 24,
                padding: '18px 24px',
                boxShadow:
                  '0 16px 36px rgba(225, 29, 72, 0.7), 0 0 24px rgba(250, 204, 21, 0.45)',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#FACC15',
                    textTransform: 'uppercase',
                    letterSpacing: '0.03em',
                  }}
                >
                  💬 Dúvida do Cliente no Cardápio
                </span>
                <span
                  style={{
                    background: 'rgba(15, 3, 6, 0.75)',
                    border: '1.5px solid #FACC15',
                    borderRadius: 12,
                    padding: '3px 12px',
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Agora
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span style={{fontSize: 38}}>❓</span>
                <span
                  style={{
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.18,
                  }}
                >
                  "A salada vem separada do prato quente?"
                </span>
              </div>
            </div>

            {/* Conflict Callout (enters at 0.3s / frame 8) establishing the conflict immediately in q01 */}
            {frame >= 8 && (
              <div
                style={{
                  opacity: alertBannerPop,
                  transform: `translateY(${(1 - alertBannerPop) * 16}px) scale(${0.92 + alertBannerPop * 0.08})`,
                  background: 'rgba(250, 204, 21, 0.18)',
                  border: '2px solid #FACC15',
                  borderRadius: 18,
                  padding: '12px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 12,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
                }}
              >
                <span style={{fontSize: 34}}>⚠️</span>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FACC15',
                  }}
                >
                  Dúvida sem resposta na hora = Venda perdida
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
