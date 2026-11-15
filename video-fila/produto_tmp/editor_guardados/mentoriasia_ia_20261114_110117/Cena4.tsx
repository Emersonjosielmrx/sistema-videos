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

export const Cena4: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: push-in contínuo (1.00 -> 1.08)
  const bgScale = interpolate(frame, [0, 118], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Entrada dos blocos com molas escalonadas
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const cardsSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const ctaSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso contínuo ininterrupto no botão principal (1.00 a 1.06 até o último frame!)
  const btnPulse = 1.03 + Math.sin(frame * 0.18) * 0.03;

  // Efeito de brilho (shimmer) varrendo o botão
  const shimmerPos = interpolate(frame % 45, [0, 45], [-200, 500]);

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
      {/* Imagem de Fundo com Movimento e Blur */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(10px)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
            opacity: 0.8,
          }}
        />
      </div>

      {/* Véu escuro da marca para alto contraste e foco */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(17, 24, 39, 0.7) 0%, rgba(11, 15, 25, 0.95) 100%)',
        }}
      />

      {/* Grid tech sutil com leve movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(circle, rgba(59, 130, 246, 0.22) 1.5px, transparent 1.5px)',
          backgroundSize: '48px 48px',
          opacity: 0.6,
          transform: `translateY(${frame * 0.4}px)`,
        }}
      />

      {/* Topo: Marca e Autoridade (y=190 a 440) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          zIndex: 20,
          transform: `scale(${Math.min(1, Math.max(0, logoSpring))})`,
          textAlign: 'center',
        }}
      >
        {/* Badge de Categoria */}
        <div
          style={{
            padding: '10px 28px',
            borderRadius: 24,
            background: 'rgba(37, 99, 235, 0.25)',
            border: `2px solid ${COLORS.marcaClara}`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 4px 18px rgba(37,99,235,0.45)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: COLORS.marcaClara,
              boxShadow: `0 0 10px ${COLORS.marcaClara}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#93C5FD',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            Mentoria & Consultoria IA
          </span>
        </div>

        {/* Nome Oficial da Marca */}
        <h1
          style={{
            margin: 0,
            fontFamily,
            fontSize: 54,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: '0.02em',
            textShadow: '0 4px 20px rgba(0,0,0,0.85)',
            maxWidth: 920,
            lineHeight: 1.15,
          }}
        >
          Treinamentos e Mentorias IA
        </h1>

        {/* 1 Frase Clara do Produto (Fatos Permitidos) */}
        <p
          style={{
            margin: 0,
            fontFamily,
            fontSize: 40,
            fontWeight: 700,
            color: '#60A5FA',
            letterSpacing: '0.01em',
            textShadow: '0 2px 12px rgba(0,0,0,0.7)',
          }}
        >
          Aprenda a criar automações com IA
        </p>
      </div>

      {/* Centro: Os 3 Pilares Entregues (y=490 a 980) */}
      <div
        style={{
          position: 'absolute',
          top: 490,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 22,
          zIndex: 20,
          transform: `scale(${Math.min(1, Math.max(0, cardsSpring))})`,
        }}
      >
        {/* Item 1: Treinamento Vibe Coding */}
        <div
          style={{
            padding: '24px 32px',
            borderRadius: 24,
            background: 'rgba(15, 23, 42, 0.9)',
            border: '2px solid rgba(59, 130, 246, 0.4)',
            boxShadow: '0 10px 28px rgba(0,0,0,0.45)',
            display: 'flex',
            alignItems: 'center',
            gap: 22,
          }}
        >
          <div
            style={{
              width: 58,
              height: 58,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #1E3A8A, #2563EB)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(37,99,235,0.7)',
            }}
          >
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="16 18 22 12 16 6" />
              <polyline points="8 6 2 12 8 18" />
            </svg>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Treinamento de Vibe Coding
          </span>
        </div>

        {/* Item 2: Consultoria de Otimização */}
        <div
          style={{
            padding: '24px 32px',
            borderRadius: 24,
            background: 'rgba(15, 23, 42, 0.9)',
            border: '2px solid rgba(59, 130, 246, 0.4)',
            boxShadow: '0 10px 28px rgba(0,0,0,0.45)',
            display: 'flex',
            alignItems: 'center',
            gap: 22,
          }}
        >
          <div
            style={{
              width: 58,
              height: 58,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #065F46, #10B981)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(16,185,129,0.6)',
            }}
          >
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Consultoria de Otimização
          </span>
        </div>

        {/* Item 3: Pack de Prompts Validados + Mapa Mental */}
        <div
          style={{
            padding: '24px 32px',
            borderRadius: 24,
            background: 'rgba(15, 23, 42, 0.9)',
            border: '2px solid rgba(59, 130, 246, 0.4)',
            boxShadow: '0 10px 28px rgba(0,0,0,0.45)',
            display: 'flex',
            alignItems: 'center',
            gap: 22,
          }}
        >
          <div
            style={{
              width: 58,
              height: 58,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #92400E, #F59E0B)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(245,158,11,0.6)',
            }}
          >
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Pack de Prompts & Mapa Mental
          </span>
        </div>
      </div>

      {/* CTA: Botão Pulsante e Handle (y=1040 a 1480) */}
      <div
        style={{
          position: 'absolute',
          top: 1040,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 28,
          zIndex: 30,
          transform: `scale(${Math.min(1, Math.max(0, ctaSpring))})`,
        }}
      >
        {/* Botão de Ação com Pulso Contínuo */}
        <div
          style={{
            position: 'relative',
            width: 820,
            height: 120,
            borderRadius: 36,
            background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)',
            border: '3px solid #93C5FD',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 20,
            boxShadow:
              '0 16px 50px rgba(37, 99, 235, 0.75), inset 0 2px 4px rgba(255,255,255,0.4)',
            transform: `scale(${btnPulse})`,
            overflow: 'hidden',
          }}
        >
          {/* Shimmer sweep */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: shimmerPos,
              width: 100,
              background:
                'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
              transform: 'skewX(-25deg)',
            }}
          />

          <span
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              textShadow: '0 2px 10px rgba(0,0,0,0.6)',
            }}
          >
            Chame no Direct
          </span>

          <svg
            width="44"
            height="44"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </div>

        {/* Handle do Instagram */}
        <div
          style={{
            padding: '18px 42px',
            borderRadius: 26,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid rgba(148, 163, 184, 0.5)',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            boxShadow: '0 8px 28px rgba(0,0,0,0.5)',
          }}
        >
          <svg
            width="38"
            height="38"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#60A5FA"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
          </svg>
          <span
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#F8FAFC',
              letterSpacing: '0.02em',
            }}
          >
            @mentoriasia.ia
          </span>
        </div>

        {/* Frase de Apoio Discreta na Base da Safe Zone */}
        <span
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 600,
            color: '#94A3B8',
            letterSpacing: '0.02em',
          }}
        >
          Consultoria & Automações com IA
        </span>
      </div>
    </div>
  );
};
