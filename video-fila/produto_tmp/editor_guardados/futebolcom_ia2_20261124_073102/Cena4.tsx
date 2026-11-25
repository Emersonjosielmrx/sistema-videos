import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {COLORS, SAFE_ZONE} from './types';

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (scale 1.10 -> 1.24)
  const bgScale = interpolate(frame, [0, 116], [1.1, 1.24], {
    extrapolateRight: 'clamp',
  });

  // Pulso contínuo ininterrupto do botão de CTA (ciclo suave de 1.1s)
  const btnPulse = 1.04 + Math.sin((frame / fps) * Math.PI * 2 * 0.9) * 0.04;

  // Shimmer / brilho varrendo o botão diagonalmente
  const shimmerPos = interpolate(frame % 45, [0, 45], [-180, 520], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica de flutuação suave da marca
  const logoFloat = Math.sin(frame / 14) * 4;

  // Entrada com mola suave dos blocos principais
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const cardSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const btnSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const atSpring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: COLORS.dark,
        fontFamily,
      }}
    >
      {/* Imagem de Fundo Desfocada com Zoom Contínuo (Regra 23) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          filter: 'blur(24px)',
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
      </div>

      {/* Véu Escuro Profundo da Marca para Máximo Contraste */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(25,3,8,0.92) 0%, rgba(49,6,15,0.85) 45%, rgba(18,2,6,0.95) 100%)',
        }}
      />

      {/* Brilho radial de fundo na cor de destaque */}
      <div
        style={{
          position: 'absolute',
          top: '38%',
          left: '50%',
          width: 860,
          height: 860,
          transform: 'translate(-50%, -50%)',
          background:
            'radial-gradient(circle, rgba(225,29,72,0.30) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* CONTEÚDO DO CARTÃO FINAL DENTRO DA SAFE ZONE (y=150 a y=1580, perfeitamente distribuído) */}

      {/* 1. TOPO: ÍCONE E NOME DA MARCA (y=180 a y=420) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          transform: `translateY(${logoFloat}px)`,
        }}
      >
        {/* Ícone da Marca com Glow */}
        <div
          style={{
            width: 120,
            height: 120,
            borderRadius: '50%',
            backgroundColor: COLORS.primary,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 58,
            boxShadow:
              '0 12px 35px rgba(225, 29, 72, 0.65), 0 0 20px rgba(250, 204, 21, 0.4)',
            border: '3px solid #FFFFFF',
            transform: `scale(${Math.min(enterSpring, 1)})`,
            marginBottom: 16,
          }}
        >
          🍽️
        </div>

        <h1
          style={{
            margin: 0,
            fontSize: 66,
            fontWeight: 900,
            color: COLORS.white,
            letterSpacing: 2,
            textTransform: 'uppercase',
            textShadow: '0 6px 24px rgba(0,0,0,0.95)',
          }}
        >
          Cardápio Digital
        </h1>

        <div
          style={{
            display: 'inline-block',
            marginTop: 10,
            padding: '8px 26px',
            borderRadius: 999,
            backgroundColor: 'rgba(250, 204, 21, 0.2)',
            border: `1.5px solid ${COLORS.accent}`,
            color: COLORS.accent,
            fontSize: 28,
            fontWeight: 800,
            letterSpacing: 1.5,
            textTransform: 'uppercase',
          }}
        >
          Atendimento com Inteligência Artificial
        </div>
      </div>

      {/* 2. CARD CENTRAL DO PRODUTO (y=470 a y=730) */}
      <div
        style={{
          position: 'absolute',
          top: 470,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          opacity: Math.min(cardSpring, 1),
          transform: `scale(${Math.max(0.7, cardSpring)})`,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(20, 3, 8, 0.94)',
            borderRadius: 28,
            padding: '28px 34px',
            border: '2px solid rgba(255, 255, 255, 0.16)',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.8)',
            textAlign: 'center',
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 36,
              fontWeight: 600,
              color: COLORS.white,
              lineHeight: 1.38,
              textWrap: 'balance',
            }}
          >
            O cliente vê o cardápio com fotos no celular e faz o pedido direto pelo
            WhatsApp, com a IA respondendo dúvidas na hora.
          </p>
        </div>
      </div>

      {/* 3. PILLS DE BENEFÍCIOS (y=770 a y=900) */}
      <div
        style={{
          position: 'absolute',
          top: 770,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: 16,
        }}
      >
        <div
          style={{
            padding: '12px 24px',
            borderRadius: 16,
            backgroundColor: 'rgba(255, 255, 255, 0.10)',
            border: '1.5px solid rgba(255, 255, 255, 0.22)',
            fontSize: 32,
            fontWeight: 700,
            color: COLORS.white,
          }}
        >
          ⚡ Sem baixar app
        </div>
        <div
          style={{
            padding: '12px 24px',
            borderRadius: 16,
            backgroundColor: 'rgba(255, 255, 255, 0.10)',
            border: '1.5px solid rgba(255, 255, 255, 0.22)',
            fontSize: 32,
            fontWeight: 700,
            color: COLORS.white,
          }}
        >
          📸 Fotos no celular
        </div>
        <div
          style={{
            padding: '12px 24px',
            borderRadius: 16,
            backgroundColor: 'rgba(255, 255, 255, 0.10)',
            border: '1.5px solid rgba(255, 255, 255, 0.22)',
            fontSize: 32,
            fontWeight: 700,
            color: COLORS.white,
          }}
        >
          🤖 Pedido no WhatsApp
        </div>
      </div>

      {/* 4. BOTÃO DE CTA PRINCIPAL COM PULSO CONTÍNUO E SHIMMER (y=960 a y=1110) */}
      <div
        style={{
          position: 'absolute',
          top: 960,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            transform: `scale(${Math.min(btnSpring, 1) * btnPulse})`,
            display: 'inline-block',
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 20,
              padding: '24px 58px',
              borderRadius: 999,
              background: `linear-gradient(135deg, ${COLORS.primary} 0%, #BE123C 100%)`,
              border: `3px solid ${COLORS.accent}`,
              boxShadow:
                '0 18px 45px rgba(225, 29, 72, 0.65), 0 0 28px rgba(250, 204, 21, 0.35)',
            }}
          >
            {/* Raio de brilho diagonal animado (shimmer) */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 80,
                transform: `translateX(${shimmerPos}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 48,
                fontWeight: 900,
                color: COLORS.white,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 3px 10px rgba(0,0,0,0.6)',
              }}
            >
              Chame no Direct
            </span>

            {/* Ícone de aviãozinho / direct */}
            <svg
              width="44"
              height="44"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </div>
        </div>
      </div>

      {/* 5. PERFIL OFICIAL (@ARROBA) (y=1160 a y=1270) */}
      <div
        style={{
          position: 'absolute',
          top: 1160,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(atSpring, 1),
          transform: `translateY(${interpolate(atSpring, [0, 1], [20, 0])}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 14,
            padding: '14px 34px',
            borderRadius: 22,
            backgroundColor: 'rgba(255, 255, 255, 0.12)',
            border: '1.5px solid rgba(255, 255, 255, 0.28)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          }}
        >
          <span style={{fontSize: 34}}>💬</span>
          <span
            style={{
              fontSize: 38,
              fontWeight: 800,
              color: COLORS.accent,
              letterSpacing: 0.5,
            }}
          >
            @futebolcom.ia2
          </span>
        </div>
      </div>

      {/* 6. SELO DE CONVITE FINAL (y=1300 a y=1390) */}
      <div
        style={{
          position: 'absolute',
          top: 1300,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(atSpring, 1),
        }}
      >
        <div
          style={{
            padding: '10px 24px',
            borderRadius: 14,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.14)',
            color: COLORS.textMuted,
            fontSize: 28,
            fontWeight: 600,
          }}
        >
          Envie uma mensagem e tire suas dúvidas
        </div>
      </div>
    </div>
  );
};
