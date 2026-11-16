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

export const Cena2: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tRel = frame / fps;
  const tAbs = 11.98 + tRel; // 11.98s to 20.51s

  // Background: zoom into the left electronics shelves, product boxes & POS counter of the store (x=0..480 of dono_1.mp4)
  // so the B-roll shows the real electronics store counter and shelves in motion with ZERO face overlap!
  const bgScale = interpolate(tRel, [0, 8.53], [2.12, 2.34], {
    extrapolateRight: 'clamp',
  });
  const bgX = interpolate(tRel, [0, 8.53], [435, 395], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(tRel, [0, 8.53], [55, 15], {
    extrapolateRight: 'clamp',
  });

  // Entrance and exit
  const enterIn = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  const exitOut = interpolate(tAbs, [20.16, 20.48], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Staggered sequential timestamps in Cena 2:
  // 1) 12.25s (visible in q07 ~13.5s): Customer question bubble slides up + AI scanning store catalog
  // 2) 15.05s (visible in q08 ~16.5s): AI Bot reply bubble slides up & scales in
  // 3) 17.20s (on "recomenda opções ideais"): Product recommendation card (Fone Bluetooth ANC) slides up & scales in
  // 4) 18.75s (on "e vende", visible in q09 ~19.1s): Button click -> "✓ COMPRA CONCLUÍDA"
  const conhecimentoAtivo = tAbs >= 14.6;
  const msgClienteAtiva = tAbs >= 12.25;
  const respostaBotAtiva = tAbs >= 15.05;
  const cardProdutoAtivo = tAbs >= 17.2;
  const vendaConcluida = tAbs >= 18.75;

  const clienteIn = spring({
    frame: Math.max(0, frame - Math.round((12.25 - 11.98) * fps)),
    fps,
    config: {damping: 13, stiffness: 150},
  });
  const botIn = spring({
    frame: Math.max(0, frame - Math.round((15.05 - 11.98) * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });
  const prodIn = spring({
    frame: Math.max(0, frame - Math.round((17.2 - 11.98) * fps)),
    fps,
    config: {damping: 13, stiffness: 165},
  });
  const vendaPop = spring({
    frame: Math.max(0, frame - Math.round((18.75 - 11.98) * fps)),
    fps,
    config: {damping: 11, stiffness: 180},
  });

  const floatY = Math.sin(tRel * 3.2) * 8;
  const tiltY = -6 + Math.sin(tRel * 2.5) * 2.2;
  const btnPulse = 1 + Math.sin(tRel * 6.5) * 0.04;
  const scanProgress = interpolate((tRel * 0.85) % 1, [0, 1], [15, 95]);

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: exitOut}}>
      {/* Real Electronics Store Counter, Monitor & Product Shelves B-roll */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Subtle gradient keeping electronics shelves & counter visible on the left and high contrast on the right */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(90deg, rgba(17,24,39,0.18) 0%, rgba(17,24,39,0.58) 42%, rgba(17,24,39,0.88) 100%)',
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.88) 0%, rgba(17,24,39,0.16) 28%, rgba(17,24,39,0.18) 72%, rgba(17,24,39,0.88) 100%)',
        }}
      />

      {/* TOP HEADER (y=162..355) — 'COMO FUNCIONA' only (no duplicate 'Simulação' label) */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(enterIn, [0, 1], [-28, 0])}px)`,
          opacity: enterIn,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          gap: 12,
        }}
      >
        <div
          style={{
            backgroundColor: '#A78BFA',
            color: '#121216',
            fontFamily,
            fontSize: 32,
            fontWeight: 900,
            padding: '6px 22px',
            borderRadius: 999,
            textTransform: 'uppercase',
          }}
        >
          Como funciona
        </div>

        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            borderRadius: 24,
            padding: '16px 24px',
            border: '2px solid rgba(167, 139, 250, 0.5)',
            boxShadow: '0 14px 32px rgba(0,0,0,0.45)',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
            }}
          >
            Vitrine IA:{' '}
            <span
              style={{
                color: conhecimentoAtivo ? '#A78BFA' : '#FFFFFF',
              }}
            >
              conhecimento de toda a loja
            </span>
          </div>
        </div>
      </div>

      {/* STAGGERED CHAT INTERFACE (x=320..1020, y=485..1250) leaving left third open to show the electronics store shelves & counter */}
      <div
        style={{
          position: 'absolute',
          top: 485,
          right: 60,
          width: 700,
          perspective: 1200,
          transform: `translateY(${floatY}px)`,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.96)',
            borderRadius: 32,
            border: '3px solid #A78BFA',
            padding: '24px 28px',
            boxShadow: '0 24px 55px rgba(0,0,0,0.68)',
            transform: `rotateY(${tiltY}deg)`,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Chat Top Bar (only place with 'Simulação' label) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.1)',
              paddingBottom: 12,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  backgroundColor: '#22C55E',
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                Vitrine IA • Chat
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#A78BFA',
              }}
            >
              Simulação
            </span>
          </div>

          {/* STEP 1 (12.25s, visible in q07): Customer Question Bubble slides up */}
          {msgClienteAtiva && (
            <div
              style={{
                backgroundColor: 'rgba(255,255,255,0.1)',
                borderRadius: '22px 22px 22px 6px',
                padding: '16px 22px',
                alignSelf: 'flex-start',
                width: '100%',
                opacity: clienteIn,
                transform: `translateY(${interpolate(clienteIn, [0, 1], [28, 0])}px) scale(${interpolate(clienteIn, [0, 1], [0.9, 1])})`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 800,
                  color: '#F8FAFC',
                  lineHeight: 1.2,
                }}
              >
                “Qual fone isola bem o ruído?”
              </div>
            </div>
          )}

          {/* Searching Store Catalog Indicator before Bot Reply (12.25s..15.05s, visible in q07) */}
          {!respostaBotAtiva && (
            <div
              style={{
                backgroundColor: 'rgba(167, 139, 250, 0.16)',
                border: '2px dashed #A78BFA',
                borderRadius: 22,
                padding: '18px 22px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#E2E8F0',
                }}
              >
                Consultando estoque de eletrônicos...
              </span>
              <div
                style={{
                  width: '100%',
                  height: 10,
                  backgroundColor: 'rgba(255,255,255,0.12)',
                  borderRadius: 999,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${scanProgress}%`,
                    height: '100%',
                    backgroundColor: '#A78BFA',
                    borderRadius: 999,
                  }}
                />
              </div>
            </div>
          )}

          {/* STEP 2 (15.05s, visible in q08): AI Bot Reply Bubble slides up & scales in */}
          {respostaBotAtiva && (
            <div
              style={{
                backgroundColor: 'rgba(167, 139, 250, 0.24)',
                border: '2.5px solid #A78BFA',
                borderRadius: '22px 22px 6px 22px',
                padding: '16px 22px',
                opacity: botIn,
                transform: `translateY(${interpolate(botIn, [0, 1], [32, 0])}px) scale(${interpolate(botIn, [0, 1], [0.88, 1])})`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                “Esse modelo da loja é o ideal para você:”
              </div>
            </div>
          )}

          {/* Status while recommending (15.05s..17.20s, visible in q08 so q08 -> q09 also evolves!) */}
          {respostaBotAtiva && !cardProdutoAtivo && (
            <div
              style={{
                backgroundColor: 'rgba(30, 41, 59, 0.9)',
                borderRadius: 20,
                border: '2px solid rgba(167, 139, 250, 0.45)',
                padding: '16px 22px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#A78BFA',
                }}
              >
                Carregando Fone Bluetooth ANC...
              </span>
            </div>
          )}

          {/* STEP 3 (17.20s): Product Recommendation Card + STEP 4 (18.75s) Button Click */}
          {cardProdutoAtivo && (
            <div
              style={{
                backgroundColor: '#1E293B',
                borderRadius: 24,
                border: '2.5px solid #A78BFA',
                padding: '18px 22px',
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                opacity: prodIn,
                transform: `translateY(${interpolate(prodIn, [0, 1], [36, 0])}px) scale(${interpolate(prodIn, [0, 1], [0.86, 1])})`,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                <div
                  style={{
                    width: 96,
                    height: 96,
                    borderRadius: 20,
                    background:
                      'linear-gradient(135deg, #A78BFA 0%, #6D28D9 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    boxShadow: '0 8px 20px rgba(109,40,217,0.45)',
                  }}
                >
                  <svg width="58" height="58" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M4 13V12C4 7.58172 7.58172 4 12 4C16.4183 4 20 7.58172 20 12V13"
                      stroke="#FFFFFF"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    />
                    <rect
                      x="2"
                      y="12"
                      width="5"
                      height="8"
                      rx="2.5"
                      fill="#FFFFFF"
                    />
                    <rect
                      x="17"
                      y="12"
                      width="5"
                      height="8"
                      rx="2.5"
                      fill="#FFFFFF"
                    />
                  </svg>
                </div>

                <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      lineHeight: 1.15,
                    }}
                  >
                    Fone Bluetooth ANC
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 33,
                      fontWeight: 800,
                      color: '#A78BFA',
                    }}
                  >
                    ✓ Opção ideal em estoque
                  </span>
                </div>
              </div>

              {/* Checkout Action Button lighting up on "e vende" (18.75s) */}
              <div
                style={{
                  backgroundColor: vendaConcluida
                    ? '#A78BFA'
                    : 'rgba(167, 139, 250, 0.25)',
                  borderRadius: 18,
                  padding: '14px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transform: `scale(${vendaConcluida ? interpolate(vendaPop, [0, 0.5, 1], [0.92, 1.07, 1]) * btnPulse : 1})`,
                  boxShadow: vendaConcluida
                    ? '0 10px 25px rgba(167,139,250,0.45)'
                    : 'none',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: vendaConcluida ? '#121216' : '#FFFFFF',
                    letterSpacing: 0.4,
                  }}
                >
                  {vendaConcluida ? '✓ COMPRA CONCLUÍDA' : 'FECHAR COMPRA'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
