import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena4Cartao: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duration of scene: 119 frames
  const sceneDuration = 119;

  // Camera slow push-in zoom throughout entire CTA scene (prevents visual deceleration)
  const cameraScale = interpolate(frame, [0, sceneDuration], [1.0, 1.10], {
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, sceneDuration], [1.03, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Floating micro-motion for brand elements
  const floatY = Math.sin(frame / 10) * 5;

  // Continuous magnetic button pulse: loops smoothly between 1.00x and 1.07x throughout entire final card
  const buttonPulse = 1.03 + Math.sin(frame * 0.22) * 0.04;

  // Arrow bouncing animation inside button
  const arrowX = Math.sin(frame * 0.28) * 8;

  // Continuous shimmer sweep running smoothly across the 820px button with vivid reflection
  const shimmerCycle = (frame % 40) / 40;
  const shimmerX = interpolate(shimmerCycle, [0, 1], [-250, 1000]);

  // Card breathing scale
  const cardBreathe = 1.0 + Math.sin(frame / 14) * 0.015;

  // Handle micro-animation (floating & subtle pulse so the arroba is magnetic and never static)
  const handleFloatY = Math.sin((frame + 12) / 8) * 4;
  const handlePulse = 1.02 + Math.sin((frame + 8) * 0.20) * 0.02;

  // Staggered cascade entrance from bottom up (stagger de baixo para cima com spring)
  // 1. Top Brand Header (frame 0)
  const brandSpring = spring({
    frame,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // 2. Features Card Container (frame 3)
  const cardSpring = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 3. Staggered tags pop
  const tag1Spring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: {damping: 11, stiffness: 160},
  });

  const tag2Spring = spring({
    frame: Math.max(0, frame - 7),
    fps,
    config: {damping: 11, stiffness: 160},
  });

  const tag3Spring = spring({
    frame: Math.max(0, frame - 9),
    fps,
    config: {damping: 11, stiffness: 160},
  });

  // 4. CTA Button Entrance (frame 10 - ready right as speech starts)
  const buttonEntrance = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 5. Handle Entrance (frame 14)
  const handleSpring = spring({
    frame: Math.max(0, frame - 14),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background with continuous slow zoom */}
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
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Dark brand veil */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.90) 0%, rgba(17, 24, 39, 0.94) 50%, rgba(6, 78, 59, 0.92) 100%)',
          }}
        />
        {/* Floating animated depth glow particles in background */}
        {[
          {x: 100, y: 350, size: 180, color: 'rgba(16, 185, 129, 0.22)'},
          {x: 820, y: 550, size: 220, color: 'rgba(16, 185, 129, 0.16)'},
          {x: 150, y: 1100, size: 240, color: 'rgba(16, 185, 129, 0.25)'},
          {x: 800, y: 1350, size: 200, color: 'rgba(5, 150, 105, 0.22)'},
        ].map((p, idx) => {
          const driftY = Math.sin((frame + idx * 30) * 0.08) * 20;
          const driftX = Math.cos((frame + idx * 25) * 0.07) * 16;
          return (
            <div
              key={idx}
              style={{
                position: 'absolute',
                left: p.x,
                top: p.y,
                width: p.size,
                height: p.size,
                borderRadius: '50%',
                background: `radial-gradient(circle, ${p.color} 0%, transparent 70%)`,
                transform: `translate(${driftX}px, ${driftY}px)`,
                pointerEvents: 'none',
              }}
            />
          );
        })}
      </div>

      {/* Main Content Container with continuous slow camera push-in zoom */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${cameraScale})`,
          transformOrigin: '50% 50%',
          pointerEvents: 'none',
        }}
      >
        {/* Top Brand Header (y ≈ 260 to 440) */}
        <div
          style={{
            position: 'absolute',
            top: 260,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            opacity: brandSpring,
            transform: `translateY(${(1 - brandSpring) * 35 + floatY}px)`,
            zIndex: 30,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 24px',
              borderRadius: 999,
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1.5px solid rgba(16, 185, 129, 0.5)',
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: '#10B981',
                boxShadow: '0 0 10px #10B981',
              }}
            />
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#A7F3D0',
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              Agentes de IA
            </span>
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: 56,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: -1,
              textAlign: 'center',
              lineHeight: 1.1,
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.6)',
            }}
          >
            Agente Pessoal IA
          </h1>
        </div>

        {/* Features / Facts Card (y ≈ 510 to 880) with staggered tags */}
        <div
          style={{
            position: 'absolute',
            top: 510,
            left: 70,
            right: 70,
            opacity: cardSpring,
            transform: `scale(${cardSpring * cardBreathe}) translateY(${(1 - cardSpring) * 45}px)`,
            zIndex: 30,
          }}
        >
          <div
            style={{
              padding: '38px 34px',
              borderRadius: 32,
              background: 'rgba(17, 24, 39, 0.90)',
              border: '2px solid rgba(16, 185, 129, 0.4)',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5)',
              backdropFilter: 'blur(16px)',
              display: 'flex',
              flexDirection: 'column',
              gap: 26,
              textAlign: 'center',
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: 40,
                fontWeight: 800,
                color: '#F9FAFB',
                lineHeight: 1.25,
              }}
            >
              Delegue tarefas reais a um agente IA
            </p>

            {/* 3 Pills from Briefing Facts: Staggered Entrance */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: 14,
              }}
            >
              {/* Tag 1: Pesquisa */}
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '10px 22px',
                  borderRadius: 999,
                  background: 'rgba(16, 185, 129, 0.2)',
                  border: '1px solid rgba(52, 211, 153, 0.6)',
                  opacity: tag1Spring,
                  transform: `scale(${tag1Spring}) translateY(${(1 - tag1Spring) * 20}px)`,
                }}
              >
                <span style={{color: '#34D399', fontWeight: 900, fontSize: 32}}>✓</span>
                <span style={{color: '#FFFFFF', fontWeight: 700, fontSize: 32}}>
                  Pesquisa
                </span>
              </div>

              {/* Tag 2: Agendamento */}
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '10px 22px',
                  borderRadius: 999,
                  background: 'rgba(16, 185, 129, 0.2)',
                  border: '1px solid rgba(52, 211, 153, 0.6)',
                  opacity: tag2Spring,
                  transform: `scale(${tag2Spring}) translateY(${(1 - tag2Spring) * 20}px)`,
                }}
              >
                <span style={{color: '#34D399', fontWeight: 900, fontSize: 32}}>✓</span>
                <span style={{color: '#FFFFFF', fontWeight: 700, fontSize: 32}}>
                  Agendamento
                </span>
              </div>

              {/* Tag 3: Follow-up */}
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '10px 22px',
                  borderRadius: 999,
                  background: 'rgba(16, 185, 129, 0.2)',
                  border: '1px solid rgba(52, 211, 153, 0.6)',
                  opacity: tag3Spring,
                  transform: `scale(${tag3Spring}) translateY(${(1 - tag3Spring) * 20}px)`,
                }}
              >
                <span style={{color: '#34D399', fontWeight: 900, fontSize: 32}}>✓</span>
                <span style={{color: '#FFFFFF', fontWeight: 700, fontSize: 32}}>
                  Follow-up
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Button: Constrained width (820px, margins 130px >= 60px), continuous pulse, vivid shimmer & animated arrow */}
        <div
          style={{
            position: 'absolute',
            top: 1040,
            left: 0,
            right: 0,
            display: 'flex',
            justifyContent: 'center',
            opacity: buttonEntrance,
            transform: `scale(${buttonEntrance * buttonPulse}) translateY(${(1 - buttonEntrance) * 60}px)`,
            zIndex: 35,
          }}
        >
          <div
            style={{
              position: 'relative',
              width: 820,
              padding: '26px 36px',
              borderRadius: 32,
              background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
              boxShadow: `0 14px 40px rgba(5, 150, 105, 0.6), 0 0 ${20 + Math.sin(frame * 0.22) * 15}px rgba(16, 185, 129, 0.45)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              overflow: 'hidden',
              border: '1.5px solid rgba(52, 211, 153, 0.55)',
            }}
          >
            {/* Vivid Shimmer sweep reflection */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 160,
                transform: `translateX(${shimmerX}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 1,
                lineHeight: 1,
                textShadow: '0 2px 8px rgba(0, 0, 0, 0.55)',
              }}
            >
              Chame no direct
            </span>
            <span
              style={{
                fontSize: 40,
                color: '#FFFFFF',
                fontWeight: 900,
                textShadow: '0 2px 8px rgba(0, 0, 0, 0.55)',
                transform: `translateX(${arrowX}px)`,
              }}
            >
              ➜
            </span>
          </div>
        </div>

        {/* Official Handle @agentesdeia.ia (y ≈ 1380 to 1460, enters by frame 14 with micro-floating & breathing) */}
        <div
          style={{
            position: 'absolute',
            top: 1380,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            opacity: handleSpring,
            transform: `scale(${handlePulse}) translateY(${(1 - handleSpring) * 50 + handleFloatY}px)`,
            zIndex: 30,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 28px',
              borderRadius: 999,
              background: 'rgba(17, 24, 39, 0.90)',
              border: '1.5px solid rgba(52, 211, 153, 0.35)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
            }}
          >
            <span style={{fontSize: 34}}>💬</span>
            <span
              style={{
                fontSize: 40,
                fontWeight: 800,
                color: '#F9FAFB',
                letterSpacing: -0.5,
              }}
            >
              @agentesdeia.ia
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
