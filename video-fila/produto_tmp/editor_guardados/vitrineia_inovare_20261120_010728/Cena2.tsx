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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo
  const bgScale = interpolate(frame, [0, 247], [1.03, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 247], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída da cena
  const sceneOpacity = interpolate(frame, [0, 8, 238, 247], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Badge do Topo
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Celular entra com mola 3D suave aos ~0.2s = frame 6
  const phoneSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, mass: 0.9, stiffness: 100},
  });

  // Flutuação sutil do celular para manter o movimento constante
  const phoneTilt = Math.sin(frame / 12) * 1.5;

  // Sincronização dos Balões com a Fala:
  // Fala: "O cliente pergunta por uma sandália" -> frame 15 (12.8s)
  const msg1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 140},
  });

  // Digitando do Bot: aparece entre frame 46 e 70
  const isTyping = frame >= 46 && frame < 71;

  // Fala: "e o bot, que conhece os produtos da loja" -> frame 71 (14.7s)
  const msg2Spring = spring({
    frame: frame - 71,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 140},
  });

  // Fala: "responde na hora" -> frame 146 (17.18s) - Chip no chat
  const statusSpring = spring({
    frame: frame - 146,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 160},
  });

  // Fala: "e já indica o modelo" -> frame 165 e 176
  const msg3Spring = spring({
    frame: frame - 165,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  const msg4Spring = spring({
    frame: frame - 176,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 140},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Fundo Desfocado com Movimento Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          filter: 'blur(16px)',
          opacity: 0.45,
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu Escuro Elegante */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at center, rgba(30, 27, 75, 0.4) 0%, rgba(11, 13, 19, 0.95) 75%)',
        }}
      />

      {/* Topo: Tarja Chanfrada (Aprovado 7f4d41fc / 28a1924f) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.max(0, badgeSpring),
          transform: `translateY(${(1 - Math.max(0, badgeSpring)) * -25}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid #A78BFA',
            clipPath: 'polygon(0 0, 100% 0, 94% 100%, 0 100%)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#DDD6FE',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA · ATENDIMENTO INTELIGENTE
          </span>
        </div>
      </div>

      {/* Mockup do Celular em Perspectiva 3D (y = 250 a 1270, altura 1020px, largura 880px) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 100,
          width: 880,
          height: 1020,
          opacity: Math.max(0, phoneSpring),
          transform: `perspective(1200px) rotateY(${-6 + phoneTilt}deg) rotateX(3deg) scale(${Math.max(0.85, phoneSpring)})`,
          transformOrigin: 'center center',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.85)',
          borderRadius: 48,
          border: '10px solid #1E293B',
          backgroundColor: '#0F172A',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Dynamic Island / Notch */}
        <div
          style={{
            position: 'absolute',
            top: 10,
            left: '50%',
            transform: 'translateX(-50%)',
            width: 170,
            height: 26,
            backgroundColor: '#000000',
            borderRadius: 13,
            zIndex: 10,
          }}
        />

        {/* Cabeçalho do App (WhatsApp / Direct) */}
        <div
          style={{
            height: 110,
            backgroundColor: '#1E1B4B',
            borderBottom: '2px solid rgba(167, 139, 250, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '34px 24px 12px 24px',
            zIndex: 5,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            {/* Avatar do Bot */}
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                backgroundColor: '#A78BFA',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 12px rgba(167, 139, 250, 0.6)',
              }}
            >
              <svg
                width="34"
                height="34"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#121216"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="11" width="18" height="10" rx="2" />
                <circle cx="12" cy="5" r="2" />
                <path d="M12 7v4" />
                <line x1="8" y1="16" x2="8" y2="16" />
                <line x1="16" y1="16" x2="16" y2="16" />
              </svg>
            </div>
            <div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  lineHeight: 1.1,
                }}
              >
                Vitrine IA
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#34D399',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#34D399',
                    display: 'inline-block',
                    boxShadow: '0 0 8px #34D399',
                  }}
                />
                Atendendo online
              </div>
            </div>
          </div>

          {/* Selo "SIMULAÇÃO" (Fonte 32px para piso mínimo) */}
          <div
            style={{
              padding: '6px 14px',
              backgroundColor: 'rgba(255, 255, 255, 0.10)',
              border: '1.5px solid rgba(255, 255, 255, 0.25)',
              borderRadius: 12,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#CBD5E1',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              Simulação
            </span>
          </div>
        </div>

        {/* Área do Chat com Balões de Conversa */}
        <div
          style={{
            flex: 1,
            padding: '24px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Balão 1: Cliente pergunta pela sandália (entra em ~12.8s) */}
          {frame >= 15 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '82%',
                backgroundColor: '#1E293B',
                border: '1.5px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '20px 20px 20px 4px',
                padding: '14px 20px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
                opacity: Math.max(0, msg1Spring),
                transform: `translateX(${(1 - Math.max(0, msg1Spring)) * -30}px) scale(${Math.max(0.85, msg1Spring)})`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#F1F5F9',
                  lineHeight: 1.25,
                }}
              >
                Oi! Vocês têm sandália confortável para o dia a dia?
              </div>
            </div>
          )}

          {/* Digitando do Bot */}
          {isTyping && (
            <div
              style={{
                alignSelf: 'flex-end',
                backgroundColor: 'rgba(76, 29, 149, 0.5)',
                border: '1.5px solid #A78BFA',
                borderRadius: '20px 20px 4px 20px',
                padding: '10px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#DDD6FE',
                }}
              >
                Vitrine IA digitando
              </span>
              <div style={{display: 'flex', gap: 4}}>
                {[0, 1, 2].map((dot) => (
                  <div
                    key={dot}
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: '#A78BFA',
                      transform: `translateY(${Math.sin((frame + dot * 5) / 3) * 3}px)`,
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Balão 2: Empresa / Vitrine IA */}
          {frame >= 71 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '84%',
                backgroundColor: '#4C1D95',
                border: '2px solid #A78BFA',
                borderRadius: '20px 20px 4px 20px',
                padding: '14px 20px',
                boxShadow: '0 6px 20px rgba(167, 139, 250, 0.35)',
                opacity: Math.max(0, msg2Spring),
                transform: `translateX(${(1 - Math.max(0, msg2Spring)) * 30}px) scale(${Math.max(0.85, msg2Spring)})`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Temos sim! Conheço todos os modelos da loja. Prefere salto baixo
                ou rasteira?
              </div>
            </div>
          )}

          {/* Chip Central no Chat: ⚡ RESPOSTA NA HORA (Integrado ao fluxo, sem sobreposição) */}
          {frame >= 146 && (
            <div
              style={{
                alignSelf: 'center',
                margin: '4px 0',
                backgroundColor: 'rgba(6, 78, 59, 0.90)',
                border: '2px solid #10B981',
                padding: '8px 24px',
                borderRadius: 20,
                boxShadow: '0 6px 20px rgba(16, 185, 129, 0.45)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                opacity: Math.max(0, statusSpring),
                transform: `scale(${Math.max(0.7, statusSpring)})`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#A7F3D0',
                  letterSpacing: 1.5,
                  textTransform: 'uppercase',
                }}
              >
                ⚡ RESPOSTA NA HORA
              </span>
            </div>
          )}

          {/* Balão 3: Cliente prefere rasteira */}
          {frame >= 165 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '75%',
                backgroundColor: '#1E293B',
                border: '1.5px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '20px 20px 20px 4px',
                padding: '12px 18px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
                opacity: Math.max(0, msg3Spring),
                transform: `translateX(${(1 - Math.max(0, msg3Spring)) * -20}px)`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#F1F5F9',
                  lineHeight: 1.2,
                }}
              >
                Rasteira, de preferência.
              </div>
            </div>
          )}

          {/* Balão 4: Empresa indica modelo específico de rasteira */}
          {frame >= 176 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '84%',
                backgroundColor: '#4C1D95',
                border: '2px solid #A78BFA',
                borderRadius: '20px 20px 4px 20px',
                padding: '14px 20px',
                boxShadow: '0 6px 20px rgba(167, 139, 250, 0.35)',
                opacity: Math.max(0, msg4Spring),
                transform: `translateX(${(1 - Math.max(0, msg4Spring)) * 20}px)`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Então recomendo a rasteira de couro. Quer que eu separe o seu
                tamanho?
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
