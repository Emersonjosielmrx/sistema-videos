import React from 'react';
import {
  Img,
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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transição de entrada suave (fade cruzado rápido nos primeiros 6 frames)
  const entryFade = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento contínuo de push-in no fundo até o último frame
  const bgScale = interpolate(frame, [0, 119], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Entrada com spring do logo e topo
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Flutuação contínua suave no logo
  const logoFloat = Math.sin(frame * 0.08) * 6;

  // Entrada em cascata com slide-right e fade
  const pill1Spring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const pill2Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const pill3Spring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Entrada do botão CTA rápida aos ~0.7s (frame 22)
  const ctaSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 135},
  });

  // Pulso contínuo sutil de conversão no botão (1.0 -> 1.035 -> 1.0)
  const ctaPulse = 1.0 + Math.sin(frame * 0.16) * 0.035;

  // Brilho dinâmico contínuo passando pelo botão
  const shimmerPos = interpolate(frame % 40, [0, 40], [-120, 240]);

  // Entrada do bloco @inovareagenda logo após o botão CTA (frame 28)
  const arrobaSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Variação de iluminação radial âmbar contínua
  const glowY = interpolate(frame, [0, 119], [25, 40]);
  const glowOpacity = interpolate(
    Math.sin(frame * 0.1),
    [-1, 1],
    [0.32, 0.48]
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        opacity: entryFade,
      }}
    >
      {/* Vídeo do dono em segundo plano escurecido com leve desfoque para preservar o elemento humano */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(40px)`,
          transformOrigin: '50% 40%',
          opacity: 0.28,
          filter: 'blur(8px) brightness(0.6)',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          startFrom={230}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Imagem de fundo com textura complementar */}
      <Img
        src={staticFile('img_4.jpg')}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
          opacity: 0.55,
          filter: 'brightness(0.55) saturate(1.35)',
        }}
      />

      {/* Iluminação radial âmbar com movimento contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at 50% ${glowY}%, rgba(245, 158, 11, 0.4) 0%, rgba(15, 23, 42, 0.85) 60%, rgba(10, 15, 25, 0.98) 100%)`,
          opacity: glowOpacity,
          pointerEvents: 'none',
        }}
      />

      {/* Topo / Marca Principal (y=210 a 430) centralizado com harmonia */}
      <div
        style={{
          position: 'absolute',
          top: 210,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          opacity: logoSpring,
          transform: `translateY(${(1 - logoSpring) * -25 + logoFloat}px)`,
        }}
      >
        {/* Ícone de Marca com Glow */}
        <div
          style={{
            width: 86,
            height: 86,
            borderRadius: 26,
            background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 48,
            boxShadow:
              '0 10px 28px rgba(245, 158, 11, 0.5), 0 0 20px rgba(245, 158, 11, 0.35)',
            marginBottom: 14,
          }}
        >
          📅
        </div>

        {/* Nome da Marca */}
        <span
          style={{
            fontFamily,
            fontSize: 58,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: 2,
            lineHeight: 1.1,
            textShadow: '0 4px 20px rgba(0,0,0,0.95)',
          }}
        >
          INOVARE AGENDA
        </span>

        {/* Frase de Posicionamento */}
        <span
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 700,
            color: '#FDE68A',
            marginTop: 8,
            letterSpacing: 0.5,
          }}
        >
          Agenda Inteligente com IA no WhatsApp
        </span>
      </div>

      {/* Benefícios com Entrada em Cascata escalonada e slide-right (y=470 a 760) */}
      <div
        style={{
          position: 'absolute',
          top: 470,
          left: 80,
          right: 80,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          alignItems: 'center',
        }}
      >
        {/* Chip 1: 24h no WhatsApp (entra frame 4 com slide-right) */}
        {frame >= 4 && (
          <div
            style={{
              width: '100%',
              opacity: pill1Spring,
              transform: `translateX(${(1 - pill1Spring) * -35}px)`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: '16px 26px',
                borderRadius: 20,
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(245, 158, 11, 0.45)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
              }}
            >
              <span style={{fontSize: 34}}>⚡</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#F8FAFC',
                }}
              >
                Agendamentos automáticos 24h
              </span>
            </div>
          </div>
        )}

        {/* Chip 2: Zero conflito (entra frame 10 com slide-right) */}
        {frame >= 10 && (
          <div
            style={{
              width: '100%',
              opacity: pill2Spring,
              transform: `translateX(${(1 - pill2Spring) * -35}px)`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: '16px 26px',
                borderRadius: 20,
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(34, 197, 94, 0.45)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
              }}
            >
              <span style={{fontSize: 34}}>💬</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#F8FAFC',
                }}
              >
                Agenda, confirma e reagenda sozinha
              </span>
            </div>
          </div>
        )}

        {/* Chip 3: Preço a partir de R$ 199 (entra frame 16 com slide-right) */}
        {frame >= 16 && (
          <div
            style={{
              width: '100%',
              opacity: pill3Spring,
              transform: `translateX(${(1 - pill3Spring) * -35}px)`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: '16px 26px',
                borderRadius: 20,
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(245, 158, 11, 0.45)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
              }}
            >
              <span style={{fontSize: 34}}>💰</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FDE68A',
                }}
              >
                Planos a partir de R$ 199/mês
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Botão CTA Principal Pulsando Ativamente (y=800 a 920) */}
      {frame >= 22 && (
        <div
          style={{
            position: 'absolute',
            top: 800,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: ctaSpring,
            transform: `scale(${interpolate(ctaSpring, [0, 1], [0.85, 1]) * ctaPulse})`,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              width: '100%',
              maxWidth: 920,
              padding: '24px 38px',
              borderRadius: 28,
              background:
                'linear-gradient(135deg, #F59E0B 0%, #EA580C 100%)',
              boxShadow:
                '0 14px 40px rgba(245, 158, 11, 0.5), 0 4px 12px rgba(0, 0, 0, 0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
            }}
          >
            {/* Brilho dinâmico contínuo passando pelo botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.45) 50%, transparent 100%)',
                transform: `translateX(${shimmerPos}%) skewX(-20deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#121216',
                textTransform: 'uppercase',
                letterSpacing: 2,
              }}
            >
              CHAME NO DIRECT ➔
            </span>
          </div>
        </div>
      )}

      {/* Perfil Oficial (@marca) — Perfeitamente posicionado em y=960 a 1120 */}
      {frame >= 28 && (
        <div
          style={{
            position: 'absolute',
            top: 960,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
            opacity: arrobaSpring,
            transform: `scale(${interpolate(arrobaSpring, [0, 1], [0.9, 1])}) translateY(${(1 - arrobaSpring) * 15}px)`,
            zIndex: 20,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '16px 40px',
              borderRadius: 999,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid rgba(245, 158, 11, 0.6)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
            }}
          >
            {/* Ícone Vetorial Oficial SVG do Instagram */}
            <svg
              width="38"
              height="38"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#F59E0B"
              strokeWidth="2.2"
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
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
              }}
            >
              @inovareagenda
            </span>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 600,
              color: '#94A3B8',
              letterSpacing: 0.5,
            }}
          >
            Envie uma mensagem e teste agora
          </span>
        </div>
      )}
    </div>
  );
};

