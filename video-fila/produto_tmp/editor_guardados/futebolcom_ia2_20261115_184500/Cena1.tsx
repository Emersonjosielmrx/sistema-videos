import React from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  interpolate,
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

  // Phase 1 (0..107, 4.41s to 8.0s): Medium shot (scale 0.98 -> 1.02, shifted down shiftY=200 so hair top is at y ~520)
  // Phase 2 (108..241, 8.0s to 12.43s): Clean 1.06x -> 1.10x Punch-In shifted down shiftY=250 so hair top stays at y ~530, leaving >230px of generous headroom!
  let baseScale = 0.98;
  let shiftY = 200;
  let shiftX = 0;

  if (frame < 108) {
    baseScale = interpolate(frame, [0, 107], [0.98, 1.02], {
      extrapolateRight: 'clamp',
    });
    shiftY = 200;
    shiftX = 0;
  } else {
    const punchSpring = spring({
      frame: frame - 108,
      fps,
      config: {damping: 14, stiffness: 180},
    });
    const progressivePush = interpolate(frame, [108, 241], [0, 0.03], {
      extrapolateRight: 'clamp',
    });
    baseScale = 1.02 + punchSpring * 0.06 + progressivePush; // 1.06x -> 1.10x
    shiftY = 200 + punchSpring * 50; // 250px downward shift places hair top safely at y ~530
    shiftX = -14 * punchSpring;
  }

  // Editorial flash at punch-cut boundary (frame 108)
  const cutFlash = frame === 108 || frame === 109 ? 0.16 : 0;

  // Whip-pan slide out to the left at the end (frames 229 to 241) to connect smoothly to Cena 2
  const whipExitX = interpolate(frame, [229, 241], [0, -1080], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const sceneOpacity = interpolate(frame, [233, 241], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top badge spring
  const badgeProgress = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: Horário de pico (local frames 0 to 57)
  const card1Progress = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 2: Sem parar para detalhar (local frames 57 to 108)
  const card2Progress = spring({
    frame: frame - 57,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Card 3 (from 8.0s / frame 108): Dynamic B-Roll Dish + Accompaniments Strip
  const card3Progress = spring({
    frame: frame - 108,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const tag1Pop = spring({
    frame: frame - 118,
    fps,
    config: {damping: 11, stiffness: 150},
  });
  const tag2Pop = spring({
    frame: frame - 142,
    fps,
    config: {damping: 11, stiffness: 150},
  });
  const tag3Pop = spring({
    frame: frame - 168,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  // Subtle vertical pulse
  const pulseY = Math.sin(frame * 0.14) * 3;

  return (
    <AbsoluteFill
      style={{
        opacity: sceneOpacity,
        transform: `translateX(${whipExitX}px)`,
        backgroundColor: '#000000',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Owner Video shifted down with ample headroom (>140px below top badges) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `translate(${shiftX}px, ${shiftY}px) scale(${baseScale})`,
          transformOrigin: 'center center',
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

      {/* Subtle editorial punch-cut flash */}
      {cutFlash > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: `rgba(255, 255, 255, ${cutFlash})`,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Solid Dark Top Header Gradient (y 0 to 440) to isolate top pills from restaurant ceiling lamp */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 440,
          background:
            'linear-gradient(180deg, rgba(8, 2, 4, 0.98) 0%, rgba(8, 2, 4, 0.94) 75%, rgba(8, 2, 4, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Badge Row (y=158) */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeProgress,
          transform: `translateY(${(1 - badgeProgress) * -14}px)`,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '6px 24px',
            borderRadius: 20,
            background: '#4C0519',
            border: '2px solid #E11D48',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.85)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            {frame < 108 ? 'O Problema' : 'O Problema • Detalhar Cada Prato'}
          </span>
        </div>
      </div>

      {/* Single Clean Row of Dynamic Support Graphics at y=220 (Ends at y=292, >140px above presenter's hair!) */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 20,
          transform: `translateY(${pulseY}px)`,
        }}
      >
        {/* Phase 1 (frames 0 to 57): "HORÁRIO DE PICO DO DELIVERY" */}
        {frame < 57 && (
          <div
            style={{
              opacity: card1Progress,
              transform: `scale(${0.92 + card1Progress * 0.08}) translateY(${(1 - card1Progress) * 10}px)`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '12px 28px',
              borderRadius: 22,
              background: '#0D0206',
              border: '2.5px solid #E11D48',
              boxShadow: '0 12px 28px rgba(0, 0, 0, 0.92)',
              whiteSpace: 'nowrap',
            }}
          >
            <span style={{fontSize: 36}}>⏱️</span>
            <span
              style={{
                fontSize: 35,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
                whiteSpace: 'nowrap',
              }}
            >
              Horário de Pico do Delivery
            </span>
          </div>
        )}

        {/* Phase 2 (frames 57 to 108): "SEM PARAR PARA DETALHAR" */}
        {frame >= 57 && frame < 108 && (
          <div
            style={{
              opacity: card2Progress,
              transform: `scale(${0.92 + card2Progress * 0.08}) translateY(${(1 - card2Progress) * 10}px)`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '12px 28px',
              borderRadius: 22,
              background: '#0D0206',
              border: '2.5px solid #FACC15',
              boxShadow: '0 12px 28px rgba(0, 0, 0, 0.92)',
              whiteSpace: 'nowrap',
            }}
          >
            <span style={{fontSize: 36}}>⚠️</span>
            <span
              style={{
                fontSize: 35,
                fontWeight: 900,
                color: '#FACC15',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
                whiteSpace: 'nowrap',
              }}
            >
              Sem Parar Para Detalhar
            </span>
          </div>
        )}

        {/* Phase 3 (from 8.0s / frame 108 to 241): Large High-Contrast Accompaniment Pills at y=216..290 */}
        {frame >= 108 && (
          <div
            style={{
              opacity: card3Progress,
              display: 'flex',
              gap: 16,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            {frame >= 108 && (
              <div
                style={{
                  opacity: tag1Pop,
                  transform: `scale(${0.85 + tag1Pop * 0.15})`,
                  background: '#070204',
                  border: '3.5px solid #FACC15',
                  borderRadius: 20,
                  padding: '12px 24px',
                  boxShadow: '0 12px 28px rgba(0, 0, 0, 0.98)',
                }}
              >
                <span style={{fontSize: 40, fontWeight: 900, color: '#FACC15'}}>
                  🥩 Ponto?
                </span>
              </div>
            )}
            {frame >= 136 && (
              <div
                style={{
                  opacity: tag2Pop,
                  transform: `scale(${0.85 + tag2Pop * 0.15})`,
                  background: '#04120B',
                  border: '3.5px solid #22C55E',
                  borderRadius: 20,
                  padding: '12px 24px',
                  boxShadow: '0 12px 28px rgba(0, 0, 0, 0.98)',
                }}
              >
                <span style={{fontSize: 40, fontWeight: 900, color: '#4ADE80'}}>
                  🥗 Salada?
                </span>
              </div>
            )}
            {frame >= 162 && (
              <div
                style={{
                  opacity: tag3Pop,
                  transform: `scale(${0.85 + tag3Pop * 0.15})`,
                  background: '#140308',
                  border: '3.5px solid #E11D48',
                  borderRadius: 20,
                  padding: '12px 24px',
                  boxShadow: '0 12px 28px rgba(0, 0, 0, 0.98)',
                }}
              >
                <span style={{fontSize: 40, fontWeight: 900, color: '#FFFFFF'}}>
                  🍟 Guarnição?
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
