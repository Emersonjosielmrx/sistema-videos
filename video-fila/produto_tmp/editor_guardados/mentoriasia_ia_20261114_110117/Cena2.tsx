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

export const Cena2: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: push-in suave (1.00 -> 1.07)
  const bgScale = interpolate(frame, [0, 245], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Entrada do celular mockup (com mola viva)
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Rotação suave sutil em 3D para dar dinamismo
  const rotateY = interpolate(frame, [0, 245], [-2.5, 2.5], {
    extrapolateRight: 'clamp',
  });
  const translateY = interpolate(frame, [0, 245], [0, -12], {
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos balões de WhatsApp
  // Balão 1: Cliente (frame 4)
  const b1Spring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Digitando antes do balão 2 (frames 36 a 55)
  const isTyping = frame >= 36 && frame < 55;

  // Balão 2: Empresa (frame 55)
  const b2Spring = spring({
    frame: frame - 55,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Balão 3: Cliente (frame 105)
  const b3Spring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Balão 4: Empresa (frame 145)
  const b4Spring = spring({
    frame: frame - 145,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Destaques dos 3 entregáveis em sincronia com a voz:
  // "mapa mental" falado aos ~15.15s (frame local ~88)
  const highlightMapa = frame >= 88;
  // "pack de prompts validados" falado aos ~16.5s (frame local ~128)
  const highlightPrompts = frame >= 128;
  // "treinamento de Vibe Coding" falado aos ~17.6s (frame local ~161)
  const highlightVibe = frame >= 161;

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
      {/* Imagem de Fundo com Movimento */}
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
          src={staticFile('img_2.jpg')}
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
            opacity: 0.88,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.45) 0%, rgba(11, 15, 25, 0.9) 100%)',
          }}
        />
      </div>

      {/* Grid tech sutil */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(circle, rgba(59, 130, 246, 0.16) 1.5px, transparent 1.5px)',
          backgroundSize: '48px 48px',
          opacity: 0.5,
        }}
      />

      {/* Top Zone: Rótulo e Título (y=175 a 300) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 30,
        }}
      >
        <div
          style={{
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(15, 23, 42, 0.95)',
            border: `2px solid ${COLORS.destaque}`,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: COLORS.destaque,
              boxShadow: `0 0 10px ${COLORS.destaque}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        <span
          style={{
            fontFamily,
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: '0.02em',
            textShadow: '0 2px 12px rgba(0,0,0,0.8)',
          }}
        >
          Consultoria & Entregáveis
        </span>
      </div>

      {/* Celular / Mockup WhatsApp Grande (y=320 a 1340) */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 60,
          width: 960,
          height: 1010,
          borderRadius: 36,
          background: '#0F172A',
          border: '2px solid rgba(59, 130, 246, 0.45)',
          boxShadow:
            '0 25px 60px rgba(0,0,0,0.75), 0 0 35px rgba(37,99,235,0.3)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 25,
          transform: `perspective(1000px) rotateY(${rotateY}deg) translateY(${translateY}px) scale(${Math.min(
            1,
            Math.max(0, phoneSpring)
          )})`,
        }}
      >
        {/* Header do WhatsApp */}
        <div
          style={{
            height: 94,
            background: '#1E293B',
            borderBottom: '2px solid rgba(255, 255, 255, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            {/* Avatar */}
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: '50%',
                background: COLORS.marca,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 14px rgba(37,99,235,0.7)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 26,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                IA
              </span>
            </div>
            <div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#F8FAFC',
                }}
              >
                Mentoria & Consultoria IA
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#34D399',
                }}
              >
                Online
              </div>
            </div>
          </div>

          {/* Selo Simulação Obrigatório */}
          <div
            style={{
              padding: '6px 16px',
              borderRadius: 14,
              background: 'rgba(255, 255, 255, 0.12)',
              border: '1px solid rgba(255, 255, 255, 0.25)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#CBD5E1',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Simulação
            </span>
          </div>
        </div>

        {/* Corpo do Chat com Mensagens */}
        <div
          style={{
            flex: 1,
            padding: '28px 24px 20px 24px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start',
            gap: 22,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(11, 15, 25, 0.98) 100%)',
          }}
        >
          {/* Balão 1: Cliente */}
          {frame >= 4 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '85%',
                transform: `scale(${Math.min(1, Math.max(0, b1Spring))})`,
                transformOrigin: 'bottom right',
                padding: '16px 22px',
                borderRadius: '22px 22px 4px 22px',
                background: '#047857',
                border: '1px solid rgba(52, 211, 153, 0.45)',
                boxShadow: '0 4px 14px rgba(0,0,0,0.3)',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Vocês avaliam meus fluxos atuais que estão lentos?
              </span>
              <div
                style={{
                  alignSelf: 'flex-end',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    color: '#A7F3D0',
                    fontWeight: 600,
                  }}
                >
                  10:41
                </span>
                <span style={{fontSize: 24, color: '#38BDF8', fontWeight: 900}}>
                  ✓✓
                </span>
              </div>
            </div>
          )}

          {/* Indicador de Digitando */}
          {isTyping && (
            <div
              style={{
                alignSelf: 'flex-start',
                padding: '12px 22px',
                borderRadius: '20px 20px 20px 4px',
                background: '#1E293B',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: '#38BDF8',
                  boxShadow: '0 0 8px #38BDF8',
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#94A3B8',
                  fontStyle: 'italic',
                }}
              >
                digitando...
              </span>
            </div>
          )}

          {/* Balão 2: Empresa */}
          {frame >= 55 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '90%',
                transform: `scale(${Math.min(1, Math.max(0, b2Spring))})`,
                transformOrigin: 'bottom left',
                padding: '16px 22px',
                borderRadius: '22px 22px 22px 4px',
                background: '#1E3A8A',
                border: '1px solid rgba(147, 197, 253, 0.45)',
                boxShadow: '0 6px 18px rgba(37,99,235,0.35)',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Sim, na consultoria de otimização identificamos onde criar
                automações com IA.
              </span>
              <div style={{alignSelf: 'flex-end'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    color: '#BFDBFE',
                    fontWeight: 600,
                  }}
                >
                  10:41
                </span>
              </div>
            </div>
          )}

          {/* Balão 3: Cliente */}
          {frame >= 105 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '85%',
                transform: `scale(${Math.min(1, Math.max(0, b3Spring))})`,
                transformOrigin: 'bottom right',
                padding: '14px 22px',
                borderRadius: '22px 22px 4px 22px',
                background: '#047857',
                border: '1px solid rgba(52, 211, 153, 0.45)',
                boxShadow: '0 4px 14px rgba(0,0,0,0.3)',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                E eu mesmo consigo montar depois?
              </span>
              <div
                style={{
                  alignSelf: 'flex-end',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    color: '#A7F3D0',
                    fontWeight: 600,
                  }}
                >
                  10:42
                </span>
                <span style={{fontSize: 24, color: '#38BDF8', fontWeight: 900}}>
                  ✓✓
                </span>
              </div>
            </div>
          )}

          {/* Balão 4: Empresa */}
          {frame >= 145 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '90%',
                transform: `scale(${Math.min(1, Math.max(0, b4Spring))})`,
                transformOrigin: 'bottom left',
                padding: '16px 22px',
                borderRadius: '22px 22px 22px 4px',
                background: '#1E3A8A',
                border: '1px solid rgba(147, 197, 253, 0.45)',
                boxShadow: '0 6px 18px rgba(37,99,235,0.35)',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Sim, com o treinamento de Vibe Coding, mapa mental e pack de
                prompts validados.
              </span>
              <div style={{alignSelf: 'flex-end'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    color: '#BFDBFE',
                    fontWeight: 600,
                  }}
                >
                  10:42
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Barra de Entregáveis em Destaque no Rodapé do Mockup */}
        <div
          style={{
            height: 105,
            background: '#0B0F19',
            borderTop: '2px solid rgba(255, 255, 255, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-around',
            padding: '0 20px',
            gap: 12,
          }}
        >
          {/* Chip 1: Mapa Mental */}
          <div
            style={{
              flex: 1,
              padding: '12px 10px',
              borderRadius: 16,
              background: highlightMapa
                ? 'rgba(37, 99, 235, 0.4)'
                : 'rgba(30, 41, 59, 0.6)',
              border: `2px solid ${
                highlightMapa ? COLORS.marcaClara : 'rgba(148, 163, 184, 0.3)'
              }`,
              textAlign: 'center',
              boxShadow: highlightMapa
                ? '0 0 16px rgba(59, 130, 246, 0.6)'
                : 'none',
              transform: highlightMapa ? 'scale(1.05)' : 'scale(1)',
              transition: 'all 0.2s ease',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: highlightMapa ? '#FFFFFF' : '#94A3B8',
                whiteSpace: 'nowrap',
              }}
            >
              Mapa Mental
            </span>
          </div>

          {/* Chip 2: Pack Prompts */}
          <div
            style={{
              flex: 1,
              padding: '12px 10px',
              borderRadius: 16,
              background: highlightPrompts
                ? 'rgba(37, 99, 235, 0.4)'
                : 'rgba(30, 41, 59, 0.6)',
              border: `2px solid ${
                highlightPrompts ? COLORS.marcaClara : 'rgba(148, 163, 184, 0.3)'
              }`,
              textAlign: 'center',
              boxShadow: highlightPrompts
                ? '0 0 16px rgba(59, 130, 246, 0.6)'
                : 'none',
              transform: highlightPrompts ? 'scale(1.05)' : 'scale(1)',
              transition: 'all 0.2s ease',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: highlightPrompts ? '#FFFFFF' : '#94A3B8',
                whiteSpace: 'nowrap',
              }}
            >
              Pack Prompts
            </span>
          </div>

          {/* Chip 3: Vibe Coding */}
          <div
            style={{
              flex: 1,
              padding: '12px 10px',
              borderRadius: 16,
              background: highlightVibe
                ? 'rgba(37, 99, 235, 0.4)'
                : 'rgba(30, 41, 59, 0.6)',
              border: `2px solid ${
                highlightVibe ? COLORS.marcaClara : 'rgba(148, 163, 184, 0.3)'
              }`,
              textAlign: 'center',
              boxShadow: highlightVibe
                ? '0 0 16px rgba(59, 130, 246, 0.6)'
                : 'none',
              transform: highlightVibe ? 'scale(1.05)' : 'scale(1)',
              transition: 'all 0.2s ease',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: highlightVibe ? '#FFFFFF' : '#94A3B8',
                whiteSpace: 'nowrap',
              }}
            >
              Vibe Coding
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
