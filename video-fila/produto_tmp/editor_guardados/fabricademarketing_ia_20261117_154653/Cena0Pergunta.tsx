import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena0Props {
  fontFamily: string;
}

export const Cena0Pergunta: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo suave (1.00 -> 1.08)
  const bgScale = interpolate(frame, [0, 169], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição final (frames 155-169)
  const cenaOpacity = interpolate(frame, [155, 169], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Topo: Badge "DÚVIDA FREQUENTE" (entra no frame 4)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Card da Dor: gancho forte em 0-2s (entra no frame 6, reduz suavemente no frame 70 para dar espaço ao texto)
  const cardEntrada = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const cardScale = interpolate(frame, [65, 80], [1.0, 0.92], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardOpacity = interpolate(frame, [65, 80], [1.0, 0.85], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardFloat = Math.sin(frame / 14) * 4;

  // Frase cinética sincronizada com a fala da pergunta:
  // "Como responder" -> frame 10 (0.32s)
  // "comentários nos posts" -> frame 33 (1.10s)
  // "enquanto estou atendendo" -> frame 69 (2.31s)
  // "clientes?" -> frame 105 (3.51s)
  const f1Spring = spring({frame: frame - 10, fps, config: {damping: 14, stiffness: 160}});
  const f2Spring = spring({frame: frame - 33, fps, config: {damping: 13, stiffness: 170}});
  const f3Spring = spring({frame: frame - 69, fps, config: {damping: 14, stiffness: 160}});
  const f4Spring = spring({frame: frame - 105, fps, config: {damping: 13, stiffness: 170}});

  // Gancho Fixo do Briefing ("Comentários sem resposta nos posts?") entra no frame 125
  const ganchoSpring = spring({frame: frame - 125, fps, config: {damping: 12, stiffness: 150}});
  const ganchoPulse = Math.sin(frame / 8) * 0.03 + 1;

  // Contador de minutos sem resposta
  const tempoMinutos = Math.floor(
    interpolate(frame, [6, 160], [35, 120], {
      extrapolateRight: 'clamp',
    })
  );

  return (
    <AbsoluteFill style={{opacity: cenaOpacity, overflow: 'hidden'}}>
      {/* Imagem de Fundo com Zoom Contínuo */}
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
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Camada sutil de ambientação escura */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(17, 24, 39, 0.45) 0%, rgba(11, 15, 25, 0.9) 100%)',
          }}
        />
      </div>

      {/* Orbs de luz dinâmica no fundo */}
      <div
        style={{
          position: 'absolute',
          top: 320 + Math.sin(frame / 20) * 25,
          left: 80,
          width: 440,
          height: 440,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(244,114,182,0.18) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 380 + Math.cos(frame / 20) * 25,
          right: 60,
          width: 440,
          height: 440,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(219,39,119,0.16) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Informativo Enxuto: y = 175 a 240 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `translateY(${(1 - badgeSpring) * -15}px)`,
          zIndex: 50,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: '1.5px solid rgba(244, 114, 182, 0.35)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.6)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: CORES.marca,
              boxShadow: `0 0 10px ${CORES.marca}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: CORES.textoPrincipal,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            DÚVIDA FREQUENTE
          </span>
        </div>
      </div>

      {/* Card da Dor: Gancho Visual dos Primeiros 2 Segundos (y = 255 a 460) */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 60,
          right: 60,
          opacity: Math.max(0, Math.min(1, cardEntrada * cardOpacity)),
          transform: `translateY(${(1 - cardEntrada) * 30 + cardFloat}px) scale(${cardScale})`,
          zIndex: 40,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            borderRadius: 24,
            padding: '20px 26px',
            border: '1.5px solid rgba(244, 114, 182, 0.4)',
            boxShadow: '0 16px 40px rgba(0,0,0,0.6), 0 0 25px rgba(244, 114, 182, 0.18)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 12,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #F472B6 0%, #9333EA 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 22,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                C
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  @cliente_interessado
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 24,
                    color: CORES.textoMutado,
                  }}
                >
                  Novo comentário no post
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 14px',
                borderRadius: 18,
                backgroundColor: 'rgba(245, 158, 11, 0.2)',
                border: '1px solid rgba(245, 158, 11, 0.5)',
              }}
            >
              <span style={{fontSize: 22}}>⏳</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 24,
                  fontWeight: 800,
                  color: '#FBBF24',
                }}
              >
                +{tempoMinutos}min sem resposta
              </span>
            </div>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              lineHeight: 1.3,
              color: '#F8FAFC',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              borderRadius: 14,
              padding: '12px 18px',
              borderLeft: `4px solid ${CORES.marca}`,
            }}
          >
            "Olá! Vocês ainda têm vaga para atendimento esta semana? Quero contratar!"
          </div>
        </div>
      </div>

      {/* Centro Focal: Texto Cinético da Pergunta (y = 510 a 1180) */}
      <div
        style={{
          position: 'absolute',
          top: 510,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 18,
          textAlign: 'center',
          zIndex: 45,
        }}
      >
        {/* Bloco 1: "Como responder" */}
        {frame >= 10 && (
          <div
            style={{
              opacity: Math.max(0, Math.min(1, f1Spring)),
              transform: `translateY(${(1 - f1Spring) * 20}px) scale(${0.92 + f1Spring * 0.08})`,
              fontFamily,
              fontSize: 48,
              fontWeight: 800,
              color: CORES.textoSecundario,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            Como responder
          </div>
        )}

        {/* Bloco 2: "COMENTÁRIOS NOS POSTS" (destaque rosa marca-texto) */}
        {frame >= 33 && (
          <div
            style={{
              opacity: Math.max(0, Math.min(1, f2Spring)),
              transform: `translateY(${(1 - f2Spring) * 25}px) scale(${0.9 + f2Spring * 0.1})`,
              display: 'inline-block',
              padding: '12px 28px',
              borderRadius: 20,
              background: `linear-gradient(135deg, ${CORES.marca} 0%, #DB2777 100%)`,
              boxShadow: `0 8px 30px ${CORES.marcaGlow}`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.5)',
              }}
            >
              COMENTÁRIOS NOS POSTS
            </span>
          </div>
        )}

        {/* Bloco 3: "enquanto estou atendendo" */}
        {frame >= 69 && (
          <div
            style={{
              opacity: Math.max(0, Math.min(1, f3Spring)),
              transform: `translateY(${(1 - f3Spring) * 20}px)`,
              fontFamily,
              fontSize: 44,
              fontWeight: 800,
              color: CORES.textoPrincipal,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            enquanto estou atendendo
          </div>
        )}

        {/* Bloco 4: "CLIENTES?" (destaque neon) */}
        {frame >= 105 && (
          <div
            style={{
              opacity: Math.max(0, Math.min(1, f4Spring)),
              transform: `translateY(${(1 - f4Spring) * 25}px) scale(${0.9 + f4Spring * 0.1})`,
              display: 'inline-block',
              padding: '10px 32px',
              borderRadius: 18,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: `2px solid ${CORES.marca}`,
              boxShadow: `0 0 25px ${CORES.marcaGlow}`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: CORES.marca,
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              CLIENTES?
            </span>
          </div>
        )}

        {/* Gancho Fixo do Briefing que entra no fim da cena */}
        {frame >= 125 && (
          <div
            style={{
              marginTop: 16,
              opacity: Math.max(0, Math.min(1, ganchoSpring)),
              transform: `scale(${ganchoSpring * ganchoPulse})`,
              padding: '12px 26px',
              borderRadius: 30,
              backgroundColor: 'rgba(239, 68, 68, 0.18)',
              border: '1.5px solid rgba(239, 68, 68, 0.6)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: '0 8px 24px rgba(239, 68, 68, 0.3)',
            }}
          >
            <span style={{fontSize: 28}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FCA5A5',
              }}
            >
              Comentários sem resposta nos posts?
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
