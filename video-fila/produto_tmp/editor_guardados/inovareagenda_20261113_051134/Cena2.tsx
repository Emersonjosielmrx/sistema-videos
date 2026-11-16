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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Video smooth push-in
  const videoScale = interpolate(frame, [0, 281], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Top pill spring
  const topPillSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  const titleSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // Card 1: "A Agenda IA faz agendamentos automáticos" (~frame 22)
  const card1Spring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Card 2: "funciona 24h direto no WhatsApp" (~frame 118)
  const card2Spring = spring({
    frame: frame - 118,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Card 3: "sem conflito de horário" (~frame 190)
  const card3Spring = spring({
    frame: frame - 190,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Status pill at frame 225
  const statusSpring = spring({
    frame: frame - 225,
    fps,
    config: {damping: 12, mass: 0.5},
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
      {/* Background Video */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Dark gradient overlay for readability */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.78) 22%, rgba(15,23,42,0.60) 48%, rgba(15,23,42,0.80) 75%, rgba(15,23,42,0.96) 100%)',
        }}
      />

      {/* Top Badge: COMO FUNCIONA (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(1, Math.max(0, topPillSpring)),
          transform: `scale(${0.9 + 0.1 * Math.min(1, Math.max(0, topPillSpring))})`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(31, 41, 55, 0.90)',
            border: '2px solid rgba(245, 158, 11, 0.7)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          }}
        >
          <span style={{fontSize: 34}}>⚡</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>
      </div>

      {/* Headline (y=260) */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 60,
          right: 60,
          textAlign: 'center',
          opacity: Math.min(1, Math.max(0, titleSpring)),
          transform: `translateY(${(1 - Math.min(1, Math.max(0, titleSpring))) * 20}px)`,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 52,
            fontWeight: 800,
            color: '#FFFFFF',
            textShadow: '0 4px 18px rgba(0,0,0,0.95)',
          }}
        >
          Automação Completa no WhatsApp
        </h2>
      </div>

      {/* Card 1: Agendamento Automático (y=410) */}
      <div
        style={{
          position: 'absolute',
          top: 410,
          left: 60,
          right: 60,
          opacity: Math.min(1, Math.max(0, card1Spring)),
          transform: `translateX(${(1 - Math.min(1, Math.max(0, card1Spring))) * 30}px) translateY(${Math.sin(frame * 0.08) * 3}px)`,
        }}
      >
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(245, 158, 11, 0.6)',
            borderRadius: 22,
            padding: '22px 28px',
            boxShadow: '0 12px 35px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 38}}>📅</span>
              <span style={{fontSize: 44, fontWeight: 800, color: '#FFFFFF'}}>
                Agendamento Automático
              </span>
            </div>
            <div
              style={{
                background: 'rgba(245, 158, 11, 0.25)',
                border: '1px solid #F59E0B',
                color: '#FCD34D',
                fontSize: 32,
                fontWeight: 800,
                padding: '4px 16px',
                borderRadius: 14,
              }}
            >
              COM IA
            </div>
          </div>
          <div style={{fontSize: 34, fontWeight: 500, color: '#D1D5DB', lineHeight: 1.3}}>
            A inteligência artificial agenda clientes sozinha em poucos segundos
          </div>
        </div>
      </div>

      {/* Card 2: 24h Direto no WhatsApp (y=660) */}
      <div
        style={{
          position: 'absolute',
          top: 660,
          left: 60,
          right: 60,
          opacity: Math.min(1, Math.max(0, card2Spring)),
          transform: `translateX(${(1 - Math.min(1, Math.max(0, card2Spring))) * -30}px) translateY(${Math.cos(frame * 0.08) * 3}px)`,
        }}
      >
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(16, 185, 129, 0.6)',
            borderRadius: 22,
            padding: '22px 28px',
            boxShadow: '0 12px 35px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 38}}>💬</span>
              <span style={{fontSize: 44, fontWeight: 800, color: '#FFFFFF'}}>
                Atendimento 24 Horas
              </span>
            </div>
            <div
              style={{
                background: 'rgba(16, 185, 129, 0.25)',
                border: '1px solid #10B981',
                color: '#A7F3D0',
                fontSize: 32,
                fontWeight: 800,
                padding: '4px 16px',
                borderRadius: 14,
              }}
            >
              Simulação
            </div>
          </div>
          <div style={{fontSize: 34, fontWeight: 500, color: '#D1D5DB', lineHeight: 1.3}}>
            Funciona dia e noite direto no WhatsApp sem pausas
          </div>
        </div>
      </div>

      {/* Card 3: Sem Conflito de Horário (y=910) */}
      <div
        style={{
          position: 'absolute',
          top: 910,
          left: 60,
          right: 60,
          opacity: Math.min(1, Math.max(0, card3Spring)),
          transform: `translateX(${(1 - Math.min(1, Math.max(0, card3Spring))) * 30}px) translateY(${Math.sin(frame * 0.08 + 1) * 3}px)`,
        }}
      >
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(59, 130, 246, 0.6)',
            borderRadius: 22,
            padding: '22px 28px',
            boxShadow: '0 12px 35px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 38}}>🔒</span>
              <span style={{fontSize: 44, fontWeight: 800, color: '#FFFFFF'}}>
                Sem Conflito de Horário
              </span>
            </div>
            <div
              style={{
                background: 'rgba(59, 130, 246, 0.25)',
                border: '1px solid #3B82F6',
                color: '#BFDBFE',
                fontSize: 32,
                fontWeight: 800,
                padding: '4px 16px',
                borderRadius: 14,
              }}
            >
              ZERO DUPLO
            </div>
          </div>
          <div style={{fontSize: 34, fontWeight: 500, color: '#D1D5DB', lineHeight: 1.3}}>
            Trava inteligente impede duplicidade e conflitos na agenda
          </div>
        </div>
      </div>

      {/* Status Pill (y=1160) */}
      {frame >= 235 && (
        <div
          style={{
            position: 'absolute',
            top: 1160,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(1, Math.max(0, statusSpring)),
            transform: `scale(${0.92 + 0.08 * Math.min(1, Math.max(0, statusSpring))})`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 24px',
              borderRadius: 20,
              background: 'rgba(31, 41, 55, 0.92)',
              border: '2px solid rgba(245, 158, 11, 0.5)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            <span style={{fontSize: 34}}>✨</span>
            <span style={{fontSize: 34, fontWeight: 700, color: '#F59E0B'}}>
              Agenda sempre organizada em tempo real
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
