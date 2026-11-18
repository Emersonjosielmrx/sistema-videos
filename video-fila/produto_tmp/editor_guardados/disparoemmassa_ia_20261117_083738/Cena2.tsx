import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena2Props {
  fontFamily: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo
  const zoom = interpolate(frame, [0, 240], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Movimento de flutuação contínua do celular (motion design)
  const floatY = Math.sin((frame / 30) * Math.PI * 1.5) * 8;

  // Entrada do Topo (y=165 a 290)
  const sprBadge = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const sprTitulo = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Celular + Balão 1 entram juntos aos ~frame 30 (1.0s, "faz disparo em massa")
  const sprPhone = spring({
    frame: frame - 28,
    fps,
    config: {damping: 15, stiffness: 100},
  });

  // Balão 1 (empresa)
  const sprBalao1 = spring({
    frame: frame - 32,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Indicador de "digitando..." (frame 78 a 96)
  const isTyping = frame >= 76 && frame < 94;

  // Balão 2 (cliente) aos ~frame 94 (quando a fala diz "WhatsApp")
  const sprBalao2 = spring({
    frame: frame - 94,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Badge 1: "Rotação de Instâncias" aos ~frame 114 (3.8s)
  const sprRotacao = spring({
    frame: frame - 114,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Balão 3 (empresa) aos ~frame 145 (4.8s)
  const sprBalao3 = spring({
    frame: frame - 145,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Badge 2: "Mensagens Personalizadas" aos ~frame 152 (5.0s)
  const sprPersonalizadas = spring({
    frame: frame - 152,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: '#0D141C',
      }}
    >
      {/* Imagem de Fundo com zoom e escurecimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${zoom})`,
          transformOrigin: 'center center',
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
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(13, 20, 28, 0.75) 0%, rgba(13, 20, 28, 0.96) 100%)',
          }}
        />
      </div>

      {/* Top Zone: Rótulo e Título da Etapa (y=165 a 290) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 25,
        }}
      >
        {frame >= 4 && (
          <div
            style={{
              opacity: sprBadge,
              transform: `scale(${0.85 + sprBadge * 0.15}) translateY(${
                (1 - sprBadge) * 15
              }px)`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 24px',
              borderRadius: 24,
              background: 'rgba(34, 197, 94, 0.18)',
              border: '2px solid rgba(34, 197, 94, 0.5)',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
            }}
          >
            <span style={{fontSize: 26}}>⚙️</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#22C55E',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              COMO FUNCIONA
            </span>
          </div>
        )}

        {frame >= 10 && (
          <div
            style={{
              opacity: sprTitulo,
              transform: `scale(${0.9 + sprTitulo * 0.1}) translateY(${
                (1 - sprTitulo) * 15
              }px)`,
              fontFamily,
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textTransform: 'uppercase',
              textAlign: 'center',
              textShadow: '0 4px 16px rgba(0, 0, 0, 0.8)',
            }}
          >
            DISPARO EM MASSA{' '}
            <span style={{color: '#22C55E'}}>INTELIGENTE</span>
          </div>
        )}
      </div>

      {/* Mockup de Celular WhatsApp 3D (y=310 a 1100) */}
      {frame >= 26 && (
        <div
          style={{
            position: 'absolute',
            top: 310,
            left: 100,
            width: 880,
            height: 790,
            borderRadius: 44,
            background: '#0B141A',
            border: '3px solid rgba(255, 255, 255, 0.16)',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.75), 0 0 35px rgba(34, 197, 94, 0.15)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 30,
            opacity: sprPhone,
            transform: `perspective(1000px) rotateY(-2deg) rotateX(1deg) translateY(${
              (1 - sprPhone) * 40 + floatY
            }px) scale(${0.92 + sprPhone * 0.08})`,
            transformOrigin: 'center center',
          }}
        >
          {/* Header do WhatsApp */}
          <div
            style={{
              height: 100,
              background: '#202C33',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 28px',
            }}
          >
            {/* Usuário Mariana */}
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #22C55E, #15803D)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  boxShadow: '0 0 12px rgba(34, 197, 94, 0.4)',
                }}
              >
                M
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#E9EDEF',
                  }}
                >
                  Mariana Silva
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#22C55E',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      background: '#22C55E',
                      display: 'inline-block',
                    }}
                  />
                  online
                </span>
              </div>
            </div>

            {/* Selo Simulação Obrigatório */}
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 16,
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#94A3B8',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Área de Conversa / Balões de Mensagem */}
          <div
            style={{
              flex: 1,
              padding: '32px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 22,
              background: '#0B141A',
            }}
          >
            {/* Balão 1: Empresa */}
            {frame >= 30 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '85%',
                  background: '#005C4B',
                  borderRadius: '24px 24px 6px 24px',
                  padding: '18px 24px',
                  boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                  opacity: sprBalao1,
                  transform: `scale(${0.85 + sprBalao1 * 0.15}) translateY(${
                    (1 - sprBalao1) * 20
                  }px)`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.35,
                  }}
                >
                  Oi, Mariana! Separamos novidades exclusivas para você hoje.
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: 6,
                    marginTop: 8,
                    fontFamily,
                    fontSize: 32,
                    color: '#8696A0',
                    fontWeight: 600,
                  }}
                >
                  10:14 <span style={{color: '#53BDEB'}}>✓✓</span>
                </div>
              </div>
            )}

            {/* Digitando animado antes do Balão 2 */}
            {isTyping && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  background: '#202C33',
                  borderRadius: '20px 20px 20px 6px',
                  padding: '14px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    color: '#8696A0',
                    fontStyle: 'italic',
                  }}
                >
                  Mariana digitando...
                </span>
              </div>
            )}

            {/* Balão 2: Cliente */}
            {frame >= 92 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  background: '#202C33',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '18px 24px',
                  boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                  opacity: sprBalao2,
                  transform: `scale(${0.85 + sprBalao2 * 0.15}) translateY(${
                    (1 - sprBalao2) * 20
                  }px)`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.35,
                  }}
                >
                  Que ótimo! Estava mesmo querendo conferir.
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    marginTop: 8,
                    fontFamily,
                    fontSize: 32,
                    color: '#8696A0',
                    fontWeight: 600,
                  }}
                >
                  10:15
                </div>
              </div>
            )}

            {/* Balão 3: Empresa */}
            {frame >= 142 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '85%',
                  background: '#005C4B',
                  borderRadius: '24px 24px 6px 24px',
                  padding: '18px 24px',
                  boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                  opacity: sprBalao3,
                  transform: `scale(${0.85 + sprBalao3 * 0.15}) translateY(${
                    (1 - sprBalao3) * 20
                  }px)`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.35,
                  }}
                >
                  Perfeito, vou te enviar os detalhes por aqui!
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: 6,
                    marginTop: 8,
                    fontFamily,
                    fontSize: 32,
                    color: '#8696A0',
                    fontWeight: 600,
                  }}
                >
                  10:15 <span style={{color: '#53BDEB'}}>✓✓</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Badges de Destaque das Features que acendem na hora falada (y=1125 a 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 1125,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          zIndex: 40,
          pointerEvents: 'none',
        }}
      >
        {frame >= 112 && (
          <div
            style={{
              opacity: sprRotacao,
              transform: `scale(${0.85 + sprRotacao * 0.15}) translateY(${
                (1 - sprRotacao) * 15
              }px)`,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid #22C55E',
              padding: '12px 28px',
              borderRadius: 24,
              boxShadow: '0 8px 25px rgba(0, 0, 0, 0.7)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 32}}>🔄</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#22C55E',
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              ROTAÇÃO DE INSTÂNCIAS
            </span>
          </div>
        )}

        {frame >= 150 && (
          <div
            style={{
              opacity: sprPersonalizadas,
              transform: `scale(${0.85 + sprPersonalizadas * 0.15}) translateY(${
                (1 - sprPersonalizadas) * 15
              }px)`,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid #4ADE80',
              padding: '12px 28px',
              borderRadius: 24,
              boxShadow: '0 8px 25px rgba(0, 0, 0, 0.7)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 32}}>✨</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              MENSAGENS PERSONALIZADAS
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
