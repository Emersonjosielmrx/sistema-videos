import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração: ~196 frames (6.54s)
  // Badge do topo no frame 4
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Título da cena no frame 8
  const titleSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1 (Rotina com o Agente) entra no frame 14 (t_abs = 19.9s)
  const c1Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 2 (Equipe focada no negócio) entra no frame 75 (t_abs = 22.0s)
  const c2Spring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Floating idle contínuo suave (evita qualquer congelamento de quadro)
  const floatY = Math.sin(frame * 0.08) * 6;
  const pulseScale = 1 + Math.sin(frame * 0.12) * 0.02;

  // Fluxo de dados contínuo (partículas e neon percorrendo a tela)
  const dataFlowOffset = (frame * 4) % 120;
  const glowPulse = 14 + Math.sin(frame * 0.16) * 8;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#070A14',
      }}
    >
      {/* Motion Graphic estilizado representando fluxos de dados e automação (substitui a foto repetida de reunião) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at 50% 25%, #131238 0%, #0A0D1E 50%, #05070E 100%)',
        }}
      />

      {/* Grade tecnológica de fundo com perspectiva animada */}
      <svg
        width="1080"
        height="1920"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          opacity: 0.35,
        }}
      >
        <defs>
          <linearGradient id="streamGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7C3AED" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#A855F7" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#10B981" stopOpacity="0.9" />
          </linearGradient>
        </defs>

        {/* Linhas de conexão de dados em movimento contínuo */}
        <path
          d="M 120,400 Q 300,600 540,550 T 960,750"
          fill="none"
          stroke="url(#streamGrad)"
          strokeWidth="3"
          strokeDasharray="16, 12"
          strokeDashoffset={-frame * 3}
        />
        <path
          d="M 160,850 Q 400,750 540,900 T 920,1100"
          fill="none"
          stroke="url(#streamGrad)"
          strokeWidth="2.5"
          strokeDasharray="12, 10"
          strokeDashoffset={frame * 2.5}
        />
        <path
          d="M 540,300 L 540,1400"
          fill="none"
          stroke="rgba(124, 58, 237, 0.25)"
          strokeWidth="1.5"
          strokeDasharray="8, 8"
          strokeDashoffset={-frame * 2}
        />

        {/* Nós luminosos interativos de automação */}
        <circle cx="240" cy="520" r="6" fill="#A855F7" />
        <circle cx="240" cy="520" r={10 + Math.sin(frame * 0.2) * 5} fill="none" stroke="#A855F7" strokeWidth="1.5" opacity="0.6" />

        <circle cx="840" cy="680" r="6" fill="#10B981" />
        <circle cx="840" cy="680" r={10 + Math.sin(frame * 0.2 + 1) * 5} fill="none" stroke="#10B981" strokeWidth="1.5" opacity="0.6" />

        <circle cx="320" cy="980" r="6" fill="#7C3AED" />
        <circle cx="760" cy="1020" r="6" fill="#34D399" />
      </svg>

      {/* Brilho volumétrico ambiente roxo e esmeralda */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 100,
          width: 880,
          height: 650,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(124, 58, 237, 0.25) 0%, transparent 65%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 700,
          left: 200,
          width: 680,
          height: 550,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16, 185, 129, 0.18) 0%, transparent 65%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />

      {/* Badge Superior: Rótulo "03 • O RESULTADO" (y=165) */}
      {frame >= 4 && (
        <div
          style={{
            position: 'absolute',
            top: 165,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${badgeSpring})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 999,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1.5px solid #7C3AED',
              boxShadow: '0 8px 24px rgba(124, 58, 237, 0.45)',
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#10B981',
                boxShadow: '0 0 10px #10B981',
                transform: `scale(${1 + Math.sin(frame * 0.2) * 0.2})`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              03 • O RESULTADO
            </span>
          </div>
        </div>
      )}

      {/* Frase Imponente e Curta em Destaque (y=245 a y=360) */}
      {frame >= 8 && (
        <div
          style={{
            position: 'absolute',
            top: 245,
            left: 60,
            right: 60,
            textAlign: 'center',
            transform: `scale(${titleSpring})`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 50,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '0.02em',
              textTransform: 'uppercase',
              lineHeight: 1.15,
              textShadow: '0 6px 20px rgba(0,0,0,0.9)',
            }}
          >
            Sua equipe livre
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              background: 'linear-gradient(90deg, #A855F7 0%, #10B981 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '0.02em',
              textTransform: 'uppercase',
              lineHeight: 1.15,
              marginTop: 4,
            }}
          >
            para o que importa
          </div>
        </div>
      )}

      {/* Container dos Cards de Transformação com Floating Idle Contínuo */}
      <div
        style={{
          position: 'absolute',
          top: 410,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 30,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Card 1: Rotina Delegada ao Agente (Sem números inventados, sem '100% Autônomo') */}
        {frame >= 14 && (
          <div
            style={{
              transform: `scale(${c1Spring})`,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid #7C3AED',
                borderRadius: 28,
                padding: '24px 28px',
                boxShadow: `0 14px 40px rgba(124, 58, 237, 0.35), 0 0 ${glowPulse}px rgba(168, 85, 247, 0.25)`,
                display: 'flex',
                alignItems: 'center',
                gap: 20,
              }}
            >
              {/* Ícone de Automação */}
              <div
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: 20,
                  background: 'linear-gradient(135deg, #7C3AED 0%, #4C1D95 100%)',
                  border: '2px solid #8B5CF6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 6px 18px rgba(124, 58, 237, 0.5)',
                }}
              >
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h1v2a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2h1a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z" />
                  <circle cx="9" cy="13" r="1.5" fill="#FFFFFF" />
                  <circle cx="15" cy="13" r="1.5" fill="#FFFFFF" />
                </svg>
              </div>

              {/* Textos concisos sem enrolação */}
              <div style={{flex: 1}}>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    background: 'rgba(124, 58, 237, 0.2)',
                    border: '1px solid #8B5CF6',
                    borderRadius: 999,
                    padding: '4px 14px',
                    marginBottom: 8,
                  }}
                >
                  <span style={{fontFamily, fontSize: 30, fontWeight: 800, color: '#C084FC', textTransform: 'uppercase'}}>
                    Rotina Operacional
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 42,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Agente assume as tarefas
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#CBD5E1',
                    marginTop: 4,
                  }}
                >
                  Executa de forma independente pelo dono
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conector com fluxo de dados ativo */}
        {frame >= 50 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              margin: '-10px 0',
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid #8B5CF6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 16px rgba(139, 92, 246, 0.6)',
                transform: `scale(${pulseScale})`,
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#C084FC" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          </div>
        )}

        {/* Card 2: Equipe Focada no que Importa */}
        {frame >= 75 && (
          <div
            style={{
              transform: `scale(${c2Spring})`,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid #10B981',
                borderRadius: 28,
                padding: '24px 28px',
                boxShadow: `0 14px 40px rgba(16, 185, 129, 0.35), 0 0 ${glowPulse}px rgba(16, 185, 129, 0.25)`,
                display: 'flex',
                alignItems: 'center',
                gap: 20,
              }}
            >
              {/* Ícone de Sucesso / Equipe */}
              <div
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: 20,
                  background: 'linear-gradient(135deg, #065F46 0%, #047857 100%)',
                  border: '2px solid #34D399',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 6px 18px rgba(16, 185, 129, 0.5)',
                }}
              >
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
              </div>

              {/* Textos imponentes */}
              <div style={{flex: 1}}>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    background: 'rgba(16, 185, 129, 0.2)',
                    border: '1px solid #34D399',
                    borderRadius: 999,
                    padding: '4px 14px',
                    marginBottom: 8,
                  }}
                >
                  <span style={{fontFamily, fontSize: 30, fontWeight: 800, color: '#6EE7B7', textTransform: 'uppercase'}}>
                    Expediente Liberado
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 42,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Equipe focada no negócio
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#CBD5E1',
                    marginTop: 4,
                  }}
                >
                  Tempo dedicado ao crescimento real
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
