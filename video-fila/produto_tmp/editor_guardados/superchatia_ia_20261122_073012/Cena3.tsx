import React from 'react';
import {
  AbsoluteFill,
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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transição gráfica fluida na entrada da cena (wipe direcional com blur suave de HUD)
  const transitionProgress = interpolate(frame, [0, 14], [1, 0], {
    extrapolateRight: 'clamp',
  });
  const transitionTranslateX = interpolate(frame, [0, 14], [80, 0], {
    extrapolateRight: 'clamp',
  });
  const transitionBlur = interpolate(frame, [0, 14], [8, 0], {
    extrapolateRight: 'clamp',
  });

  // Enquadramento mais fechado e focado na ação de acompanhamento no computador (zoom 1.16x a 1.22x)
  const videoScale = interpolate(frame, [0, 246], [1.16, 1.22], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = interpolate(frame, [0, 246], [40, 50], {
    extrapolateRight: 'clamp',
  });

  // Entradas sincronizadas dos benefícios alcançados
  // Item 1 ("cada contato fica organizado no CRM"): ativa aos 21.83s (frame 55 da cena)
  const isItem1Active = frame >= 55;
  const springItem1 = spring({
    frame: frame - 55,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Item 2 ("minha equipe acompanha todos os clientes"): ativa aos 24.65s (frame 139 da cena)
  const isItem2Active = frame >= 139;
  const springItem2 = spring({
    frame: frame - 139,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Brilho contínuo percorrendo as tags ativas
  const shineProgress = interpolate((frame % 55), [0, 55], [-120, 220]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
        filter: transitionBlur > 0 ? `blur(${transitionBlur}px)` : 'none',
        transform: `translateX(${transitionTranslateX}px)`,
        opacity: 1 - transitionProgress * 0.4,
      }}
    >
      {/* Vídeo do dono com enquadramento mais fechado e focado */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: 'center 35%',
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

        {/* Gradiente escuro reforçado no topo para garantir alto contraste mesmo sobre a janela/parede clara */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.98) 0%, rgba(11, 13, 19, 0.85) 200px, rgba(11, 13, 19, 0.4) 290px, transparent 380px)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa segura superior: y=156 a y=310 (respiro seguro acima da cabeça do apresentador) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 156,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Rótulo de contexto */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 24px',
            borderRadius: 9999,
            background: 'rgba(17, 24, 39, 0.96)',
            border: '1.5px solid rgba(16, 185, 129, 0.6)',
            boxShadow: '0 6px 18px rgba(0, 0, 0, 0.7)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#A7F3D0',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            O Resultado • Controle Total
          </span>
        </div>

        {/* Grade / Checklist de benefícios reais do CRM com contraste garantido mesmo no estado inativo */}
        <div
          style={{
            marginTop: 14,
            width: '100%',
            maxWidth: 960,
            display: 'flex',
            flexDirection: 'row',
            gap: 16,
            justifyContent: 'center',
          }}
        >
          {/* Card Benefício 1: Contato no CRM */}
          <div
            style={{
              flex: 1,
              background: isItem1Active
                ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.22) 0%, rgba(17, 24, 39, 0.96) 100%)'
                : 'rgba(17, 24, 39, 0.96)',
              border: isItem1Active
                ? '2px solid #10B981'
                : '1.5px solid rgba(255, 255, 255, 0.28)',
              borderRadius: 22,
              padding: '14px 20px',
              boxShadow: isItem1Active
                ? '0 12px 30px rgba(0, 0, 0, 0.85), 0 0 25px rgba(16, 185, 129, 0.4)'
                : '0 8px 24px rgba(0, 0, 0, 0.8)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              transform: isItem1Active
                ? `scale(${Math.max(1, springItem1)})`
                : 'scale(1)',
              position: 'relative',
              overflow: 'hidden',
              transition: 'all 0.25s',
            }}
          >
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                backgroundColor: isItem1Active
                  ? '#10B981'
                  : 'rgba(255, 255, 255, 0.12)',
                border: isItem1Active
                  ? '1.5px solid #34D399'
                  : '1.5px solid rgba(255, 255, 255, 0.3)',
                boxShadow: isItem1Active ? '0 0 12px #10B981' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: isItem1Active ? '#FFFFFF' : 'rgba(255, 255, 255, 0.75)',
                fontSize: 22,
                fontWeight: 900,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: isItem1Active ? '#FFFFFF' : 'rgba(255, 255, 255, 0.85)',
                lineHeight: 1.15,
                textShadow: '0 2px 8px rgba(0,0,0,0.8)',
              }}
            >
              Contato no CRM
            </span>

            {/* Brilho dinâmico no acendimento */}
            {isItem1Active && (
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: `${shineProgress}%`,
                  width: 45,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent)',
                  transform: 'skewX(-20deg)',
                }}
              />
            )}
          </div>

          {/* Card Benefício 2: Equipe Alinhada */}
          <div
            style={{
              flex: 1,
              background: isItem2Active
                ? 'linear-gradient(135deg, rgba(91, 108, 255, 0.22) 0%, rgba(17, 24, 39, 0.96) 100%)'
                : 'rgba(17, 24, 39, 0.96)',
              border: isItem2Active
                ? '2px solid #5B6CFF'
                : '1.5px solid rgba(255, 255, 255, 0.28)',
              borderRadius: 22,
              padding: '14px 20px',
              boxShadow: isItem2Active
                ? '0 12px 30px rgba(0, 0, 0, 0.85), 0 0 25px rgba(91, 108, 255, 0.4)'
                : '0 8px 24px rgba(0, 0, 0, 0.8)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              transform: isItem2Active
                ? `scale(${Math.max(1, springItem2)})`
                : 'scale(1)',
              position: 'relative',
              overflow: 'hidden',
              transition: 'all 0.25s',
            }}
          >
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                backgroundColor: isItem2Active
                  ? '#5B6CFF'
                  : 'rgba(255, 255, 255, 0.12)',
                border: isItem2Active
                  ? '1.5px solid #818CF8'
                  : '1.5px solid rgba(255, 255, 255, 0.3)',
                boxShadow: isItem2Active ? '0 0 12px #5B6CFF' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: isItem2Active ? '#FFFFFF' : 'rgba(255, 255, 255, 0.75)',
                fontSize: 22,
                fontWeight: 900,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: isItem2Active ? '#FFFFFF' : 'rgba(255, 255, 255, 0.85)',
                lineHeight: 1.15,
                textShadow: '0 2px 8px rgba(0,0,0,0.8)',
              }}
            >
              Equipe Alinhada
            </span>

            {/* Brilho dinâmico no acendimento */}
            {isItem2Active && (
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: `${shineProgress}%`,
                  width: 45,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent)',
                  transform: 'skewX(-20deg)',
                }}
              />
            )}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
