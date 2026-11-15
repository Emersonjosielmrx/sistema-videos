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

  // Continuous push-in and pan across the ENTIRE scene (0 to 153 frames) to guarantee > 4% movement
  const bgScale = interpolate(frame, [0, 153], [1.02, 1.25], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 153], [0, -45], {
    extrapolateRight: 'clamp',
  });

  // Top Hook Badge: Urgent hook interrupting feed scroll
  const hookSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  // Kinetic Question springs synchronized with speech
  const q1Spring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, mass: 0.5},
  });

  const q2Spring = spring({
    frame: frame - 14, // on 'todas as mensagens'
    fps,
    config: {damping: 12, mass: 0.5},
  });

  const q3Spring = spring({
    frame: frame - 38, // on 'para saber o que rolou'
    fps,
    config: {damping: 13, mass: 0.5},
  });

  // Notifications entering staggered across entire scene
  const notif1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const notif2Spring = spring({
    frame: frame - 48,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const notif3Spring = spring({
    frame: frame - 82,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  // Climactic gancho banner: strictly enters at frame 105 (no early leak)
  const ganchoSpring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Urgency shakes on entry
  const shake1 =
    frame >= 12 && frame <= 24
      ? Math.sin((frame - 12) * 1.8) * 6 * (1 - (frame - 12) / 12)
      : 0;

  const shake2 =
    frame >= 48 && frame <= 60
      ? Math.sin((frame - 48) * 1.8) * 6 * (1 - (frame - 48) / 12)
      : 0;

  const shake3 =
    frame >= 82 && frame <= 94
      ? Math.sin((frame - 82) * 1.8) * 6 * (1 - (frame - 82) / 12)
      : 0;

  const pulse = 1.0 + Math.sin(frame * 0.25) * 0.05;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Background with continuous push-in and pan */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
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
        {/* Dark Slate & Crimson Gradient Overlay for urgency */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.90) 0%, rgba(15, 23, 42, 0.78) 45%, rgba(17, 24, 39, 0.95) 100%)',
          }}
        />
      </div>

      {/* Top Hook: Urgent call replacing the corporate 'Dúvida Comum' */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: hookSpring,
          transform: `translateY(${interpolate(hookSpring, [0, 1], [-20, 0])}px)`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            padding: '10px 26px',
            borderRadius: 999,
            backgroundColor: 'rgba(239, 68, 68, 0.20)',
            border: '2px solid rgba(239, 68, 68, 0.65)',
            boxShadow: '0 0 25px rgba(239, 68, 68, 0.35)',
            backdropFilter: 'blur(12px)',
            color: '#FCA5A5',
            fontSize: 32,
            fontWeight: 900,
            letterSpacing: 1.2,
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <span style={{fontSize: 28}}>⚠️</span>
          <span>Seus grupos estão fora de controle?</span>
        </div>
      </div>

      {/* Kinetic Question Section (y: 255 to 510) */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 70,
          right: 70,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          textAlign: 'center',
          zIndex: 10,
        }}
      >
        {/* Phrase 1: Preciso ler */}
        <div
          style={{
            opacity: q1Spring,
            transform: `scale(${interpolate(q1Spring, [0, 1], [0.85, 1])})`,
            fontSize: 48,
            fontWeight: 900,
            color: '#FFFFFF',
            textShadow: '0 4px 16px rgba(0, 0, 0, 0.8)',
            letterSpacing: -0.5,
          }}
        >
          Preciso ler
        </div>

        {/* Phrase 2: Todas as mensagens (High impact mark) */}
        <div
          style={{
            opacity: q2Spring,
            transform: `scale(${interpolate(q2Spring, [0, 1], [0.85, 1])})`,
            display: 'inline-block',
            padding: '8px 24px',
            borderRadius: 16,
            backgroundColor: 'rgba(20, 184, 166, 0.25)',
            border: '2px solid rgba(20, 184, 166, 0.8)',
            boxShadow: '0 0 30px rgba(20, 184, 166, 0.4)',
            fontSize: 50,
            fontWeight: 900,
            color: '#14B8A6',
            textTransform: 'uppercase',
            letterSpacing: -0.5,
          }}
        >
          Todas as mensagens
        </div>

        {/* Phrase 3: para saber o que rolou no grupo? */}
        <div
          style={{
            opacity: q3Spring,
            transform: `translateY(${interpolate(q3Spring, [0, 1], [15, 0])}px)`,
            fontSize: 40,
            fontWeight: 800,
            color: '#E2E8F0',
            textShadow: '0 4px 14px rgba(0, 0, 0, 0.8)',
            textWrap: 'balance',
            lineHeight: 1.25,
            maxWidth: 820,
          }}
        >
          para saber o que rolou no grupo?
        </div>
      </div>

      {/* Stacking WhatsApp Notification Cards in Forefront (NO INVENTED NUMBERS) */}
      <div
        style={{
          position: 'absolute',
          top: 550,
          left: 70,
          right: 70,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
          zIndex: 10,
        }}
      >
        {/* Card 1: enters frame 12 (~0.4s) */}
        <div
          style={{
            opacity: notif1Spring,
            transform: `translateX(${interpolate(notif1Spring, [0, 1], [-60, 0]) + shake1}px)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 28px',
            borderRadius: 22,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(14px)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 16,
                backgroundColor: '#25D366',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
              }}
            >
              👥
            </div>
            <div>
              <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                Grupo Diretoria & Sócios
              </div>
              <div style={{fontSize: 26, color: '#FCA5A5', fontWeight: 700}}>
                Mensagens não lidas acumuladas
              </div>
            </div>
          </div>
          <div
            style={{
              padding: '8px 20px',
              borderRadius: 999,
              backgroundColor: '#EF4444',
              color: '#FFFFFF',
              fontSize: 28,
              fontWeight: 900,
              boxShadow: '0 0 20px rgba(239, 68, 68, 0.8)',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              transform: `scale(${pulse})`,
            }}
          >
            Não Lidas
          </div>
        </div>

        {/* Card 2: enters frame 48 (~1.6s) */}
        <div
          style={{
            opacity: notif2Spring,
            transform: `translateX(${interpolate(notif2Spring, [0, 1], [60, 0]) + shake2}px)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 28px',
            borderRadius: 22,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(14px)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 16,
                backgroundColor: '#25D366',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
              }}
            >
              👥
            </div>
            <div>
              <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                Equipe Comercial & Vendas
              </div>
              <div style={{fontSize: 26, color: '#FCA5A5', fontWeight: 700}}>
                Discussões em andamento
              </div>
            </div>
          </div>
          <div
            style={{
              padding: '8px 20px',
              borderRadius: 999,
              backgroundColor: '#EF4444',
              color: '#FFFFFF',
              fontSize: 28,
              fontWeight: 900,
              boxShadow: '0 0 20px rgba(239, 68, 68, 0.8)',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              transform: `scale(${pulse})`,
            }}
          >
            Acumuladas
          </div>
        </div>

        {/* Card 3: enters frame 82 (~2.7s) */}
        <div
          style={{
            opacity: notif3Spring,
            transform: `translateX(${interpolate(notif3Spring, [0, 1], [-60, 0]) + shake3}px)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 28px',
            borderRadius: 22,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(14px)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 16,
                backgroundColor: '#25D366',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
              }}
            >
              👥
            </div>
            <div>
              <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                Suporte & Projetos Ativos
              </div>
              <div style={{fontSize: 26, color: '#94A3B8'}}>
                Conversas acumuladas nos grupos
              </div>
            </div>
          </div>
          <div
            style={{
              padding: '8px 20px',
              borderRadius: 999,
              backgroundColor: '#DC2626',
              color: '#FFFFFF',
              fontSize: 28,
              fontWeight: 900,
              boxShadow: '0 0 20px rgba(220, 38, 38, 0.8)',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            Alerta
          </div>
        </div>

        {/* Climactic Gancho Alert: enters frame 105 (3.5s) on 'no grupo' with crisp 100% opacity */}
        {frame >= 105 && (
          <div
            style={{
              marginTop: 10,
              opacity: ganchoSpring,
              transform: `scale(${interpolate(ganchoSpring, [0, 1], [0.6, 1]) * pulse})`,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                padding: '16px 36px',
                borderRadius: 999,
                backgroundColor: '#DC2626',
                border: '2px solid #FCA5A5',
                boxShadow: '0 0 40px rgba(220, 38, 38, 0.8)',
                color: '#FFFFFF',
                fontSize: 36,
                fontWeight: 900,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              <span>⚠️</span>
              <span>Centenas de mensagens acumuladas?</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
