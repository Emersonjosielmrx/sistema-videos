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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de aproximação no fundo (1.00 -> 1.09)
  const bgScale = interpolate(frame, [0, 120], [1.0, 1.09], {
    extrapolateRight: 'clamp',
  });

  // Entrada imediata no primeiro segundo com stagger rápido de 0.1s (3 frames) e opacidade legível desde o frame 0
  const topoSpring = spring({
    frame,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  const cardSpring = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 13, mass: 0.7},
  });

  const ctaSpring = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 12, mass: 0.65},
  });

  const arrobaSpring = spring({
    frame: Math.max(0, frame - 9),
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Microanimação de pulso contínuo no botão CTA (1.00 a 1.055 até o último frame)
  const pulsoBotao = 1.025 + Math.sin(frame / 5) * 0.032;
  const pulsoCard = 1 + Math.sin(frame / 7) * 0.015;

  // Brilho passando pelo botão (shimmer effect)
  const shimmerPos = interpolate(frame % 40, [0, 40], [-150, 450]);

  // Flutuação contínua suave
  const flutuacao = Math.sin(frame / 8) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F172A',
      }}
    >
      {/* Fundo dinâmico com fotografia preservada e zoom suave */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
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
            filter: 'blur(4px)',
          }}
        />
        {/* Véu escuro da marca para prestígio e legibilidade absoluta */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(255, 169, 77, 0.22) 0%, rgba(31, 41, 55, 0.90) 55%, rgba(15, 23, 42, 0.97) 100%)',
          }}
        />
      </div>

      {/* Topo: Selo Institucional (y=200) */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${interpolate(topoSpring, [0, 1], [-18, 0])}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 26px',
            borderRadius: 99,
            backgroundColor: 'rgba(31, 41, 55, 0.92)',
            border: '1.5px solid rgba(255, 169, 77, 0.55)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.35)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#FFA94D',
              boxShadow: '0 0 10px #FFA94D',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFA94D',
              textTransform: 'uppercase',
              letterSpacing: 1.5,
            }}
          >
            Agendamentos Automáticos 24h
          </span>
        </div>
      </div>

      {/* Marca Principal (y=305 a 465) */}
      <div
        style={{
          position: 'absolute',
          top: 305,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          transform: `translateY(${interpolate(topoSpring, [0, 1], [20, flutuacao])}px)`,
        }}
      >
        <span
          style={{
            fontFamily,
            fontSize: 92,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.05,
            textTransform: 'uppercase',
            letterSpacing: 2,
            textShadow:
              '0 0 35px rgba(255, 169, 77, 0.55), 0 4px 20px rgba(0,0,0,0.85)',
          }}
        >
          Agenda IA
        </span>
        <span
          style={{
            fontFamily,
            fontSize: 36,
            fontWeight: 700,
            color: '#F3F4F6',
            textAlign: 'center',
            lineHeight: 1.25,
          }}
        >
          IA agenda, confirma e reagenda sozinha no WhatsApp
        </span>
      </div>

      {/* Card Único de Proposta de Valor de Alto Contraste e Impacto (y=520 a 835) */}
      <div
        style={{
          position: 'absolute',
          top: 525,
          left: 65,
          right: 65,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${interpolate(cardSpring, [0, 1], [24, 0])}px) scale(${pulsoCard})`,
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 900,
            padding: '28px 34px',
            borderRadius: 28,
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            border: '2.5px solid #FFA94D',
            boxShadow:
              '0 16px 42px rgba(0, 0, 0, 0.65), 0 0 32px rgba(255, 169, 77, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            textAlign: 'center',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Trabalha 24 horas no WhatsApp
          </span>

          <div
            style={{
              padding: '10px 28px',
              borderRadius: 18,
              backgroundColor: '#FFA94D',
              boxShadow: '0 6px 20px rgba(255, 169, 77, 0.4)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#1F2937',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              A partir de R$ 199/mês
            </span>
          </div>

          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 700,
              color: '#E5E7EB',
              lineHeight: 1.25,
            }}
          >
            Sem conflito e sem duplo agendamento
          </span>
        </div>
      </div>

      {/* Botão CTA Principal Pulsante — Visível desde o início da cena (y=915 a 1045) */}
      <div
        style={{
          position: 'absolute',
          top: 915,
          left: 70,
          right: 70,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${pulsoBotao * interpolate(ctaSpring, [0, 1], [0.92, 1])}) translateY(${interpolate(ctaSpring, [0, 1], [22, 0])}px)`,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 880,
            padding: '26px 36px',
            borderRadius: 26,
            backgroundColor: '#FFA94D',
            boxShadow:
              '0 14px 44px rgba(255, 169, 77, 0.55), 0 4px 16px rgba(0,0,0,0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            overflow: 'hidden',
          }}
        >
          {/* Efeito Shimmer de Brilho */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 130,
              transform: `skewX(-25deg) translateX(${shimmerPos}%)`,
              background:
                'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.5) 50%, rgba(255,255,255,0) 100%)',
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              color: '#1F2937',
              textTransform: 'uppercase',
              letterSpacing: 1.5,
            }}
          >
            Chame no Direct
          </span>

          <svg
            width="44"
            height="44"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#1F2937"
            strokeWidth="3.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </div>
      </div>

      {/* Arroba da Conta (y=1120 a 1210) */}
      <div
        style={{
          position: 'absolute',
          top: 1120,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${interpolate(arrobaSpring, [0, 1], [18, 0])}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '14px 36px',
            borderRadius: 99,
            backgroundColor: 'rgba(31, 41, 55, 0.92)',
            border: '2px solid rgba(255, 169, 77, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 46,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.2,
            }}
          >
            @sintetizerisada
          </span>
        </div>
      </div>

      {/* Rodapé Seguro com Fonte Ampliada (40px) e Branco Translúcido (rgba(255,255,255,0.85)) (y=1290) */}
      <div
        style={{
          position: 'absolute',
          top: 1290,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <span
          style={{
            fontFamily,
            fontSize: 40,
            fontWeight: 700,
            color: 'rgba(255, 255, 255, 0.85)',
            textAlign: 'center',
            letterSpacing: 0.8,
            textShadow: '0 2px 10px rgba(0,0,0,0.7)',
          }}
        >
          Clínicas • Consultórios • Salões • Profissionais
        </span>
      </div>
    </div>
  );
};
