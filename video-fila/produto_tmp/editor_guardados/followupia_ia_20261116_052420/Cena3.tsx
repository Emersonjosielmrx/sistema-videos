import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena3Props {
  fontFamily: string;
  corMarca: string;
  corFundo: string;
  corTextoMarca: string;
}

export const Cena3: React.FC<Cena3Props> = ({
  fontFamily,
  corMarca,
  corFundo,
  corTextoMarca,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((27.75 - 19.57) * fps);
  const absTime = 19.57 + frame / fps;

  // Entrada e saída suaves da cena
  const enter = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  const exit = interpolate(absTime, [27.4, 27.75], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Transição suave direcional de saída para conectar com o cartão final (Cena 4)
  const exitSlideY = interpolate(absTime, [27.4, 27.75], [0, -35], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Punch-in dinâmico de close-up (escala 1.20x a 1.26x) com corte de impacto em q10
  const punchSnap = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 180},
  });
  const punchScale = interpolate(punchSnap, [0, 1], [1.3, 1.2]);
  const continuousZoom = interpolate(frame, [0, durFrames], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });
  const totalVideoScale = punchScale * continuousZoom;

  // Fracionamento da entrada dos dados em sincronia com o áudio
  const isVendas = absTime >= 20.3; // "Eu recupero vendas de semanas atrás"
  const isWhatsapp = absTime >= 22.8; // "direto no WhatsApp"
  const showPrice = absTime >= 24.61; // "a partir de cento e noventa e nove reais."

  const stepWhatsappEnter = spring({
    frame: frame - Math.round((22.8 - 19.57) * fps),
    fps,
    config: {damping: 14, stiffness: 160},
  });

  // Transição 3D animada suave na troca dos cards:
  // Card 1 sai com rotação e fade
  const card1Exit = spring({
    frame: frame - Math.round((24.3 - 19.57) * fps),
    fps,
    config: {damping: 14, stiffness: 150},
  });

  // Card 2 (Comparativo) entra com flip 3D suave
  const priceFlip = spring({
    frame: frame - Math.round((24.55 - 19.57) * fps),
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Animação de traçado (stroke-dashoffset de 0% a 100%) riscando o valor do SDR (R$ 2.500)
  // sincronizada no momento exato em que a locução contrapõe os custos
  const strikeProgress = interpolate(absTime, [24.75, 25.35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const pulse = 1 + Math.sin(frame / 7) * 0.02;

  return (
    <AbsoluteFill
      style={{
        opacity: enter * exit,
        backgroundColor: corFundo,
        transform: `translateY(${exitSlideY}px)`,
      }}
    >
      {/* Vídeo do apresentador com punch-in de close-up (1.20x) e rebaixado para respiro de headroom */}
      <AbsoluteFill
        style={{
          transform: `scale(${totalVideoScale}) translateY(85px)`,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Vinheta inferior para isolar e destacar o Karaokê sobre a roupa */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(to top, rgba(17,24,39,0.92) 0%, rgba(17,24,39,0.5) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top HUD seguro y: 175 - 400 com respiro livre */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          backgroundColor: 'rgba(17, 24, 39, 0.96)',
          border: `2px solid ${corMarca}`,
          borderRadius: 22,
          padding: '12px 20px',
          boxShadow: '0 20px 45px rgba(0,0,0,0.7)',
          transform: `scale(${pulse})`,
          zIndex: 40,
        }}
      >
        {!showPrice ? (
          /* Primeira metade (19.57s - 24.61s): Layout limpo e direto com transição de saída 3D */
          <div
            style={{
              perspective: 1000,
              transform: `rotateX(${interpolate(card1Exit, [0, 1], [0, -30])}deg) translateY(${interpolate(card1Exit, [0, 1], [0, -15])}px)`,
              opacity: interpolate(card1Exit, [0, 1], [1, 0]),
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 10,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 900,
                  color: corTextoMarca,
                  backgroundColor: corMarca,
                  padding: '3px 14px',
                  borderRadius: 8,
                  textTransform: 'uppercase',
                }}
              >
                O RESULTADO
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 800,
                  color: corMarca,
                }}
              >
                DIRETO NO WHATSAPP
              </span>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: isVendas ? '#FFFFFF' : '#94A3B8',
                lineHeight: 1.2,
                marginBottom: 8,
                textAlign: 'center',
                transition: 'color 0.2s ease',
              }}
            >
              Recupera vendas de semanas atrás
            </div>

            {isWhatsapp && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  transform: `scale(${interpolate(stepWhatsappEnter, [0, 1], [0.9, 1])})`,
                  opacity: stepWhatsappEnter,
                }}
              >
                <div
                  style={{
                    backgroundColor: 'rgba(78, 205, 196, 0.18)',
                    border: `2px solid ${corMarca}`,
                    borderRadius: 14,
                    padding: '8px 20px',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  ✓ Converte leads inativos no WhatsApp
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Segunda metade (24.61s - 27.75s): Comparativo Heroico com transição flip 3D e traço animado de risco */
          <div
            style={{
              perspective: 1000,
              transform: `rotateX(${interpolate(priceFlip, [0, 1], [30, 0])}deg) translateY(${interpolate(priceFlip, [0, 1], [15, 0])}px)`,
              opacity: priceFlip,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 10,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 28,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  backgroundColor: '#EF4444',
                  padding: '3px 14px',
                  borderRadius: 8,
                  textTransform: 'uppercase',
                }}
              >
                SDR HUMANO
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 28,
                  fontWeight: 900,
                  color: corTextoMarca,
                  backgroundColor: corMarca,
                  padding: '3px 14px',
                  borderRadius: 8,
                  textTransform: 'uppercase',
                }}
              >
                FOLLOW-UP IA
              </span>
            </div>

            <div style={{display: 'flex', gap: 12}}>
              {/* SDR Humano: R$ 2.500 com risco animado via SVG stroke-dashoffset */}
              <div
                style={{
                  flex: 1,
                  backgroundColor: 'rgba(239, 68, 68, 0.16)',
                  border: '2px solid rgba(239, 68, 68, 0.6)',
                  borderRadius: 16,
                  padding: '10px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <div style={{position: 'relative', display: 'inline-block'}}>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 48,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      lineHeight: 1.1,
                    }}
                  >
                    R$ 2.500
                  </span>
                  {/* Traçado animado riscando o valor com stroke-dashoffset */}
                  <svg
                    width="220"
                    height="28"
                    style={{
                      position: 'absolute',
                      top: 14,
                      left: -5,
                      pointerEvents: 'none',
                    }}
                  >
                    <line
                      x1="5"
                      y1="20"
                      x2="215"
                      y2="8"
                      stroke="#EF4444"
                      strokeWidth="6"
                      strokeLinecap="round"
                      strokeDasharray={230}
                      strokeDashoffset={interpolate(strikeProgress, [0, 1], [230, 0])}
                      style={{filter: 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.9))'}}
                    />
                  </svg>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    marginTop: 4,
                    textShadow: '0 2px 6px rgba(0,0,0,0.8)',
                  }}
                >
                  Custa mais e desiste
                </div>
              </div>

              {/* Follow-up IA: A partir de R$ 199 com destaque protagonista */}
              <div
                style={{
                  flex: 1.2,
                  backgroundColor: corMarca,
                  borderRadius: 16,
                  padding: '10px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  boxShadow: `0 8px 30px rgba(78, 205, 196, 0.5)`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 48,
                    fontWeight: 900,
                    color: corTextoMarca,
                    lineHeight: 1.1,
                  }}
                >
                  A partir de R$ 199
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#064E3B',
                    marginTop: 4,
                  }}
                >
                  ✓ Nunca desiste
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
