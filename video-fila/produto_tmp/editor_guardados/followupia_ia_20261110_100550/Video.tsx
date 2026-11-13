import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import briefing from '../../../trabalhos/followupia_ia_20261110_100550/public/briefing.json';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

const COR = {
  marca: '#4ECDC4',
  apoio: '#111827',
  fundo: '#0B1120',
  card: 'rgba(17, 24, 39, 0.94)',
  cardClaro: 'rgba(30, 41, 59, 0.94)',
  textoSobreMarca: '#121216',
  branco: '#FFFFFF',
  cinzaClaro: '#E2E8F0',
  alerta: '#EF4444',
  whatsVerde: '#054D44',
  whatsCliente: '#1F2C34',
};

// ============================================================================
// CENA 0 — PERGUNTA (0.00s -> 5.07s | 153 frames)
// Composição (a) + (e): Fala principal cinética + Gancho da tela + Simulação
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const bgScale = interpolate(frame, [0, 155], [1.02, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgX = interpolate(frame, [0, 155], [0, -25], {
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [140, 152], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const categoryIn = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  const titleIn = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // gancho_tela entra aos ~1.4s (frame 42) quando a locução diz "parou de falar"
  const ganchoIn = spring({
    frame: Math.max(0, frame - 40),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Chat de simulação entra aos ~1.4s (frame 41)
  const chatIn = spring({
    frame: Math.max(0, frame - 42),
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const floatY = Math.sin(frame * 0.1) * 7;

  return (
    <AbsoluteFill style={{opacity: fadeOut, backgroundColor: COR.fundo}}>
      {/* Foto de fundo img_0.jpg em movimento contínuo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 20%',
            transform: `scale(${bgScale}) translateX(${bgX}px)`,
            filter: 'brightness(0.48) contrast(1.1)',
          }}
        />
      </AbsoluteFill>

      {/* Gradiente escuro para legibilidade sem esconder o ambiente */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.92) 0%, rgba(11,17,32,0.48) 45%, rgba(11,17,32,0.92) 100%)',
        }}
      />

      {/* Conteúdo na Safe Zone (y=165..1280, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}
      >
        {/* Topo: Categoria inicial (0s) + Gancho fixo que acende na hora da dor (1.4s) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(78, 205, 196, 0.18)',
              border: `2px solid ${COR.marca}`,
              color: COR.marca,
              padding: '10px 24px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              transform: `scale(${categoryIn})`,
            }}
          >
            DÚVIDA DO VENDEDOR
          </div>

          {frame >= 38 && (
            <div
              style={{
                backgroundColor: COR.marca,
                color: COR.textoSobreMarca,
                padding: '10px 24px',
                borderRadius: 999,
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                boxShadow: '0 10px 28px rgba(78, 205, 196, 0.4)',
                transform: `scale(${ganchoIn})`,
              }}
            >
              ⚡ {briefing.gancho_tela}
            </div>
          )}
        </div>

        {/* Pergunta principal = FALA DA CENA 0 (cinética com destaque nas palavras-chave) */}
        <div
          style={{
            backgroundColor: COR.card,
            border: `3px solid rgba(78, 205, 196, 0.5)`,
            borderRadius: 30,
            padding: '30px 36px',
            boxShadow: '0 20px 48px rgba(0,0,0,0.55)',
            transform: `translateY(${(1 - titleIn) * 35 + floatY * 0.4}px) scale(${0.95 + 0.05 * titleIn})`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              lineHeight: 1.18,
              color: COR.branco,
              textWrap: 'balance',
            }}
          >
            Como vender para quem{' '}
            <span
              style={{
                backgroundColor: t >= 1.38 ? COR.marca : 'rgba(78,205,196,0.2)',
                color: t >= 1.38 ? COR.textoSobreMarca : COR.marca,
                padding: '2px 14px',
                borderRadius: 12,
                display: 'inline-block',
                transition: 'all 0.2s ease',
              }}
            >
              parou de falar
            </span>{' '}
            comigo{' '}
            <span
              style={{
                color: t >= 2.58 ? COR.marca : COR.branco,
                textDecoration: t >= 2.58 ? 'underline' : 'none',
              }}
            >
              sem perder tempo?
            </span>
          </div>
        </div>

        {/* Card de Simulação de Orçamento sem resposta (entra em 1.4s) */}
        <div
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.96)',
            borderRadius: 28,
            padding: '24px 30px',
            border: '2px solid rgba(255,255,255,0.16)',
            boxShadow: '0 18px 42px rgba(0,0,0,0.55)',
            transform: `translateY(${(1 - chatIn) * 50}px) scale(${0.94 + 0.06 * chatIn})`,
            opacity: chatIn,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '2px solid rgba(255,255,255,0.1)',
              paddingBottom: 12,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 26,
                  backgroundColor: COR.marca,
                  color: COR.textoSobreMarca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                }}
              >
                CL
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: COR.branco,
                }}
              >
                Lead • Orçamento enviado
              </div>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: COR.marca,
                backgroundColor: 'rgba(78,205,196,0.16)',
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Mensagem do cliente antes de sumir */}
          <div
            style={{
              alignSelf: 'flex-start',
              backgroundColor: COR.whatsCliente,
              padding: '16px 24px',
              borderRadius: '20px 20px 20px 6px',
              fontFamily,
              fontSize: 34,
              fontWeight: 700,
              color: COR.branco,
            }}
          >
            &ldquo;Me manda a proposta que já te retorno!&rdquo;
          </div>

          {/* Alerta de status evoluindo com a locução */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor:
                t >= 2.58 ? 'rgba(78,205,196,0.2)' : 'rgba(239, 68, 68, 0.18)',
              border: `2px solid ${t >= 2.58 ? COR.marca : 'rgba(239, 68, 68, 0.55)'}`,
              borderRadius: 18,
              padding: '14px 22px',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: t >= 2.58 ? COR.marca : '#FCA5A5',
              }}
            >
              {t >= 2.58
                ? '⚡ A IA recupera sem esforço manual'
                : '⚠️ Visualizado • Sumiu depois do orçamento'}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1 — O PROBLEMA / DONO (4.72s -> 11.76s | 212 frames)
// Composição (h): Vídeo cheio dono_1.mp4 + UI compacta estritamente no topo (y=156..280)
// Rosto do dono protegido: cabeça inicia em y >= 334 (respiro > 50 px)
// ============================================================================
const Cena1Dono: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absSec = 4.72 + frame / fps;

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [198, 211], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const videoScale = interpolate(frame, [0, 211], [1.02, 1.08], {
    extrapolateRight: 'clamp',
  });

  const headerIn = spring({frame, fps, config: {damping: 14, stiffness: 130}});
  // "venda sempre escapava" @ 8.24s (frame ~106 local)
  const fase2 = absSec >= 8.24;
  const card2In = spring({
    frame: Math.max(0, frame - 105),
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const floatY = Math.sin(frame * 0.1) * 4;

  return (
    <AbsoluteFill
      style={{opacity: fadeIn * fadeOut, backgroundColor: COR.fundo}}
    >
      {/* Vídeo do dono deslocado verticalmente para blindar a cabeça e dar respiro > 50px do topo */}
      <div
        style={{
          position: 'absolute',
          top: 85,
          left: 0,
          right: 0,
          bottom: -85,
          overflow: 'hidden',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${videoScale})`,
          }}
        />
      </div>

      {/* Vinheta suave no topo para contraste sem encobrir o apresentador */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.88) 0%, rgba(11,17,32,0.0) 22%, rgba(11,17,32,0.0) 72%, rgba(11,17,32,0.78) 100%)',
        }}
      />

      {/* Faixa superior estrita: y=154 a y=278 (cabeça do dono inicia em y >= 340) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          transform: `translateY(${(1 - headerIn) * -25 + floatY}px)`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              backgroundColor: COR.alerta,
              color: COR.branco,
              padding: '10px 24px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              letterSpacing: 0.5,
              boxShadow: '0 8px 24px rgba(239, 68, 68, 0.35)',
            }}
          >
            01 • O PROBLEMA
          </div>
          <div
            style={{
              backgroundColor: COR.card,
              color: COR.marca,
              padding: '10px 24px',
              borderRadius: 999,
              border: `2px solid ${COR.marca}`,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
            }}
          >
            Follow-up manual
          </div>
        </div>

        {/* Headline dinâmico compacto que evolui exatamente na mudança da fala */}
        {!fase2 ? (
          <div
            style={{
              backgroundColor: COR.card,
              borderRadius: 20,
              padding: '16px 26px',
              borderLeft: `8px solid ${COR.marca}`,
              boxShadow: '0 14px 32px rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 34}}>⏳</span>
            <div
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: COR.branco,
                lineHeight: 1.2,
              }}
            >
              Horas correndo atrás de quem sumiu
            </div>
          </div>
        ) : (
          <div
            style={{
              backgroundColor: 'rgba(28, 16, 24, 0.95)',
              borderRadius: 20,
              padding: '16px 26px',
              borderLeft: `8px solid ${COR.alerta}`,
              boxShadow: '0 14px 32px rgba(239, 68, 68, 0.3)',
              transform: `scale(${0.96 + 0.04 * card2In})`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 34}}>⚠️</span>
            <div
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: '#FCA5A5',
                lineHeight: 1.2,
              }}
            >
              No fim, a venda sempre escapava
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — COMO FUNCIONA (11.41s -> 19.20s | 234 frames)
// Composição (b): Vídeo contextual ao fundo (mulher no notebook à esquerda)
// + Mockup WhatsApp 3D dinâmico com etapas 01-02-03 em balões reais
// ============================================================================
const Cena2ComoFunciona: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absSec = 11.41 + frame / fps;

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [220, 234], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, 234], [1.02, 1.1], {
    extrapolateRight: 'clamp',
  });

  // Sincronia exata com as palavras da Cena 2:
  // "follow-up automático" @ 13.53s (frame 64 local)
  // "reativar o contato" @ 15.94s (frame 136 local)
  // "conduzir a negociação" @ 17.17s (frame 173 local)
  const step1In = spring({
    frame: Math.max(0, frame - 18),
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const step2In = spring({
    frame: Math.max(0, frame - Math.round((15.9 - 11.41) * fps)),
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const step3In = spring({
    frame: Math.max(0, frame - Math.round((17.15 - 11.41) * fps)),
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const phoneFloat = Math.sin(frame * 0.09) * 8;
  const phoneTilt = interpolate(frame, [0, 234], [-9, -4]);

  return (
    <AbsoluteFill
      style={{opacity: fadeIn * fadeOut, backgroundColor: COR.fundo}}
    >
      {/* Vídeo Veo de fundo posicionado à esquerda para manter a pessoa no notebook 100% visível */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '114%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: '0% center',
            transform: `scale(${bgScale})`,
            filter: 'brightness(0.44) contrast(1.1)',
          }}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.92) 0%, rgba(11,17,32,0.48) 50%, rgba(11,17,32,0.94) 100%)',
        }}
      />

      {/* Topo: Rótulo + Título na Safe Zone (y=165..330) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div
          style={{
            alignSelf: 'flex-start',
            backgroundColor: COR.marca,
            color: COR.textoSobreMarca,
            padding: '10px 26px',
            borderRadius: 999,
            fontFamily,
            fontSize: 34,
            fontWeight: 900,
            boxShadow: '0 8px 24px rgba(78, 205, 196, 0.35)',
          }}
        >
          02 • COMO FUNCIONA
        </div>
        <div
          style={{
            fontFamily,
            fontSize: 50,
            fontWeight: 900,
            color: COR.branco,
            lineHeight: 1.15,
          }}
        >
          Follow-up automático no{' '}
          <span style={{color: COR.marca}}>WhatsApp</span>
        </div>
      </div>

      {/* Centro Nobre: Mockup Celular WhatsApp 3D (x=175..1020, largura 845px >= 820px) */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 175,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          perspective: 1200,
        }}
      >
        <div
          style={{
            backgroundColor: '#0F172A',
            borderRadius: 36,
            border: `3px solid ${COR.marca}`,
            padding: '24px 28px',
            boxShadow: '0 26px 65px rgba(0,0,0,0.7)',
            transform: `rotateY(${phoneTilt}deg) translateY(${phoneFloat}px)`,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* Barra Superior WhatsApp */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.14)',
              paddingBottom: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 27,
                  backgroundColor: COR.marca,
                  color: COR.textoSobreMarca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                }}
              >
                IA
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: COR.branco,
                  }}
                >
                  Follow-up IA
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: COR.marca,
                  }}
                >
                  Automático • Ativo
                </div>
              </div>
            </div>
            <div
              style={{
                backgroundColor: 'rgba(78,205,196,0.18)',
                color: COR.marca,
                padding: '6px 20px',
                borderRadius: 999,
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Mensagem 01 — IA envia o follow-up no WhatsApp (à direita) */}
          <div
            style={{
              alignSelf: 'flex-end',
              backgroundColor: '#054D44',
              border: `2px solid rgba(78, 205, 196, 0.45)`,
              padding: '16px 22px',
              borderRadius: '20px 20px 6px 20px',
              transform: `scale(${0.92 + 0.08 * step1In})`,
              opacity: step1In,
              maxWidth: '92%',
              boxShadow: '0 10px 24px rgba(0,0,0,0.3)',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#6EE7B7',
                marginBottom: 6,
              }}
            >
              01 • Follow-up automático
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: COR.branco,
                lineHeight: 1.22,
              }}
            >
              Olá! Ficou alguma dúvida sobre o orçamento que enviamos?
            </div>
            <div
              style={{
                textAlign: 'right',
                fontFamily,
                fontSize: 34,
                color: '#A7F3D0',
                marginTop: 4,
              }}
            >
              10:14 ✓✓
            </div>
          </div>

          {/* Mensagem 02 — Cliente reativa o contato (à esquerda) */}
          {absSec >= 15.6 && (
            <div
              style={{
                alignSelf: 'flex-start',
                backgroundColor: COR.whatsCliente,
                border: '2px solid rgba(255,255,255,0.15)',
                padding: '16px 22px',
                borderRadius: '20px 20px 20px 6px',
                transform: `scale(${0.92 + 0.08 * step2In})`,
                opacity: step2In,
                maxWidth: '92%',
                boxShadow: '0 10px 24px rgba(0,0,0,0.3)',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#94A3B8',
                  marginBottom: 6,
                }}
              >
                02 • Contato reativado
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: COR.branco,
                  lineHeight: 1.22,
                }}
              >
                Oi! Correria aqui, mas quero fechar sim. Como fazemos?
              </div>
              <div
                style={{
                  textAlign: 'right',
                  fontFamily,
                  fontSize: 34,
                  color: '#94A3B8',
                  marginTop: 4,
                }}
              >
                10:16
              </div>
            </div>
          )}

          {/* Mensagem 03 — IA conduz a negociação (à direita) */}
          {absSec >= 17.0 && (
            <div
              style={{
                alignSelf: 'flex-end',
                backgroundColor: '#064E3B',
                border: `3px solid ${COR.marca}`,
                padding: '16px 22px',
                borderRadius: '20px 20px 6px 20px',
                transform: `scale(${0.92 + 0.08 * step3In})`,
                opacity: step3In,
                maxWidth: '92%',
                boxShadow: '0 12px 30px rgba(78, 205, 196, 0.3)',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: COR.marca,
                  marginBottom: 6,
                }}
              >
                03 • Conduz a negociação
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: COR.branco,
                  lineHeight: 1.22,
                }}
              >
                Perfeito! Já separei os dados para concluir seu pedido agora.
              </div>
              <div
                style={{
                  textAlign: 'right',
                  fontFamily,
                  fontSize: 34,
                  color: '#A7F3D0',
                  marginTop: 4,
                }}
              >
                10:17 ✓✓
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — O RESULTADO (18.85s -> 26.01s | 215 frames)
// Composição (g): Checklist de 3 benefícios com ✓ animado + Comparativo oficial
// Foto: img_3.jpg em tela cheia com push-in cinematográfico e visual corporativo
// ============================================================================
const Cena3Resultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absSec = 18.85 + frame / fps;

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [200, 215], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, 215], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 215], [0, -28], {
    extrapolateRight: 'clamp',
  });

  // Sincronia exata com a fala:
  // "recupero leads inativos" -> 19.75s (frame 27 local)
  // "fecho negócios pelo WhatsApp" -> 21.27s (frame 73 local)
  // "sem depender de esforço manual" -> 22.95s (frame 123 local)
  const item1In = spring({
    frame: Math.max(0, frame - 22),
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const item2In = spring({
    frame: Math.max(0, frame - 70),
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const item3In = spring({
    frame: Math.max(0, frame - 120),
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const floatY = Math.sin(frame * 0.1) * 6;

  const itens = [
    {
      num: '01',
      texto: 'Recupera leads inativos',
      ativo: absSec >= 19.4,
      anim: item1In,
    },
    {
      num: '02',
      texto: 'Fecha negócios pelo WhatsApp',
      ativo: absSec >= 21.15,
      anim: item2In,
    },
    {
      num: '03',
      texto: 'Sem depender de esforço manual',
      ativo: absSec >= 22.85,
      anim: item3In,
    },
  ];

  return (
    <AbsoluteFill
      style={{opacity: fadeIn * fadeOut, backgroundColor: COR.fundo}}
    >
      {/* Foto img_3 em tela cheia com push-in e contraste corporativo elegante */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translateY(${bgY}px)`,
            filter: 'brightness(0.48) contrast(1.1)',
          }}
        />
      </AbsoluteFill>

      {/* Gradiente escuro para legibilidade sem esconder a profundidade arquitetônica */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.92) 0%, rgba(11,17,32,0.55) 45%, rgba(11,17,32,0.92) 100%)',
        }}
      />

      {/* Topo: Rótulo + Título na Safe Zone (y=165..320) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              backgroundColor: COR.marca,
              color: COR.textoSobreMarca,
              padding: '10px 26px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              boxShadow: '0 8px 24px rgba(78, 205, 196, 0.35)',
            }}
          >
            03 • O RESULTADO
          </div>
          <div
            style={{
              backgroundColor: COR.card,
              color: COR.branco,
              padding: '10px 24px',
              borderRadius: 999,
              border: `2px solid ${COR.marca}`,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
            }}
          >
            Ela nunca desiste
          </div>
        </div>

        <div
          style={{
            fontFamily,
            fontSize: 48,
            fontWeight: 900,
            color: COR.branco,
            lineHeight: 1.15,
          }}
        >
          Conversão ativa no <span style={{color: COR.marca}}>WhatsApp</span>
        </div>
      </div>

      {/* Centro Nobre: Checklist de 3 benefícios bem espaçado e proporcional (y=345..900) */}
      <div
        style={{
          position: 'absolute',
          top: 345,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {itens.map((it) => (
          <div
            key={it.num}
            style={{
              backgroundColor: it.ativo ? COR.card : 'rgba(17,24,39,0.7)',
              border: `3px solid ${it.ativo ? COR.marca : 'rgba(255,255,255,0.14)'}`,
              borderRadius: 24,
              padding: '22px 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transform: `translateX(${(1 - it.anim) * -45}px) scale(${0.95 + 0.05 * it.anim})`,
              boxShadow: it.ativo
                ? '0 16px 36px rgba(0,0,0,0.5)'
                : 'none',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  backgroundColor: it.ativo ? COR.marca : '#334155',
                  color: it.ativo ? COR.textoSobreMarca : COR.branco,
                  padding: '8px 18px',
                  borderRadius: 14,
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                }}
              >
                {it.num}
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: COR.branco,
                }}
              >
                {it.texto}
              </div>
            </div>
            <div
              style={{
                width: 50,
                height: 50,
                borderRadius: 25,
                backgroundColor: it.ativo ? COR.marca : 'rgba(255,255,255,0.12)',
                color: COR.textoSobreMarca,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
              }}
            >
              ✓
            </div>
          </div>
        ))}

        {/* Comparativo oficial do briefing (entra com o item 3) */}
        {absSec >= 22.85 && (
          <div
            style={{
              display: 'flex',
              gap: 16,
              marginTop: 6,
              transform: `scale(${item3In})`,
            }}
          >
            <div
              style={{
                flex: 1,
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                border: '2px solid rgba(239, 68, 68, 0.6)',
                borderRadius: 20,
                padding: '16px 20px',
                textAlign: 'center',
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FCA5A5',
              }}
            >
              SDR humano: R$ 2.500 (desiste)
            </div>
            <div
              style={{
                flex: 1,
                backgroundColor: COR.marca,
                borderRadius: 20,
                padding: '16px 20px',
                textAlign: 'center',
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: COR.textoSobreMarca,
                boxShadow: '0 8px 24px rgba(78, 205, 196, 0.4)',
              }}
            >
              Follow-up IA: a partir de R$ 199
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL / CTA (25.66s -> 29.61s | 119 frames)
// Sem legenda Karaokê, movimento contínuo > 10% até o último frame
// Equilíbrio vertical na Safe Zone (y=175..1420), fundo com blur profundo e glow ciano
// ============================================================================
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, 119], [1.06, 1.2]);
  const bgPanY = interpolate(frame, [0, 119], [0, -40]);
  const cardIn = spring({frame, fps, config: {damping: 13, stiffness: 130}});
  const btnPulse = 1 + Math.sin(frame * 0.25) * 0.045;
  const floatY = Math.sin(frame * 0.12) * 8;
  const glowX = interpolate(frame % 60, [0, 60], [-120, 1100]);

  return (
    <AbsoluteFill style={{opacity: fadeIn, backgroundColor: COR.fundo}}>
      {/* Fundo com blur profundo (36px) para textura luminosa que não repete o cenário da Cena 0 */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 85%',
            transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
            filter: 'blur(36px) brightness(0.24)',
          }}
        />
      </AbsoluteFill>

      {/* Halo dinâmico da marca em movimento ativo (> 10%) */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${50 + Math.sin(frame * 0.08) * 16}% ${40 + Math.cos(frame * 0.08) * 12}%, rgba(78, 205, 196, 0.26) 0%, rgba(11, 17, 32, 0.95) 75%)`,
        }}
      />

      {/* Conteúdo distribuído com harmonia espacial em toda a Safe Zone (y=175..1420) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(${(1 - cardIn) * 35 + floatY}px)`,
        }}
      >
        {/* Bloco Superior: Categoria + Marca (y=175..380) */}
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 18,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(78, 205, 196, 0.18)',
              border: `2px solid ${COR.marca}`,
              color: COR.marca,
              padding: '12px 34px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              boxShadow: '0 8px 24px rgba(78, 205, 196, 0.25)',
            }}
          >
            ⚡ Automação Comercial no WhatsApp
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 88,
              fontWeight: 900,
              color: COR.branco,
              textAlign: 'center',
              letterSpacing: -1,
              lineHeight: 1.05,
              textShadow: '0 14px 40px rgba(0,0,0,0.7)',
            }}
          >
            Follow-up <span style={{color: COR.marca}}>IA</span>
          </div>
        </div>

        {/* Bloco Central Nobre: Card de Proposta de Valor e Fatos Oficiais (y=430..830) */}
        <div
          style={{
            position: 'absolute',
            top: 430,
            left: 60,
            right: 60,
            backgroundColor: COR.card,
            borderRadius: 32,
            padding: '38px 42px',
            border: `2px solid rgba(78, 205, 196, 0.35)`,
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            boxShadow: '0 24px 60px rgba(0,0,0,0.65)',
            boxSizing: 'border-box',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.marca,
              letterSpacing: 0.5,
            }}
          >
            A IA QUE RECUPERA VENDAS PERDIDAS
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              color: COR.branco,
              lineHeight: 1.25,
              textWrap: 'balance',
            }}
          >
            Recupera leads inativos e converte no WhatsApp sozinha
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 16,
              flexWrap: 'wrap',
              marginTop: 6,
            }}
          >
            <div
              style={{
                backgroundColor: 'rgba(78,205,196,0.18)',
                color: COR.marca,
                padding: '10px 24px',
                borderRadius: 999,
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
              }}
            >
              ✓ A partir de R$ 199
            </div>
            <div
              style={{
                backgroundColor: 'rgba(78,205,196,0.18)',
                color: COR.marca,
                padding: '10px 24px',
                borderRadius: 999,
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
              }}
            >
              ✓ Ela nunca desiste
            </div>
          </div>
        </div>

        {/* Bloco de Ação Inferior: CTA + @handle (y=940..1420) */}
        <div
          style={{
            position: 'absolute',
            top: 940,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
          }}
        >
          {/* Botão CTA Pulsante com Shine (alinhado com convite_voz: "Chame a gente no direct.") */}
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              backgroundColor: COR.marca,
              color: COR.textoSobreMarca,
              padding: '30px 68px',
              borderRadius: 999,
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              letterSpacing: 0.6,
              transform: `scale(${btnPulse})`,
              boxShadow: '0 22px 55px rgba(78, 205, 196, 0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
            }}
          >
            <span style={{fontSize: 48}}>💬</span>
            <span>CHAME NO DIRECT</span>
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: glowX,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.65), transparent)',
                transform: 'skewX(-20deg)',
              }}
            />
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#CBD5E1',
              textAlign: 'center',
            }}
          >
            Pare de perder vendas por esquecimento
          </div>

          {/* @handle ancorado com respiro em y ~ 1280 */}
          <div
            style={{
              marginTop: 8,
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              border: `2px solid ${COR.marca}`,
              padding: '16px 46px',
              borderRadius: 999,
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: COR.branco,
              boxShadow: '0 12px 30px rgba(0,0,0,0.55)',
            }}
          >
            {briefing.arroba}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================
const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const sec = frame / fps;

  // Palavras para o Karaoke (excluindo o cartão final, cena 4)
  const palavrasKaraoke = React.useMemo(
    () => briefing.palavras.filter((w) => w.cena !== 4),
    [],
  );

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: COR.fundo, fontFamily}}>
      {/* Áudio principal da narração */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha sonora com fade in/out e volume suave sob a fala */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const fadeIn = interpolate(f, [0, 25], [0, 0.1], {
            extrapolateRight: 'clamp',
          });
          const fadeOut = interpolate(
            f,
            [durationInFrames - 35, durationInFrames],
            [0.1, 0],
            {extrapolateLeft: 'clamp'},
          );
          return Math.min(fadeIn, fadeOut);
        }}
      />

      {/* Cena 0: 0.00s -> 5.07s (0..152) */}
      <Sequence from={0} durationInFrames={153}>
        <Cena0Pergunta />
      </Sequence>

      {/* Cena 1: 4.72s -> 11.76s (141..353) */}
      <Sequence from={141} durationInFrames={212}>
        <Cena1Dono />
      </Sequence>

      {/* Cena 2: 11.41s -> 19.20s (342..576) */}
      <Sequence from={342} durationInFrames={234}>
        <Cena2ComoFunciona />
      </Sequence>

      {/* Cena 3: 18.85s -> 26.01s (565..780) */}
      <Sequence from={565} durationInFrames={215}>
        <Cena3Resultado />
      </Sequence>

      {/* Cena 4: 25.66s -> 29.61s (770..889) */}
      <Sequence from={770} durationInFrames={119}>
        <Cena4Cartao />
      </Sequence>

      {/* Barra de progresso fina na Safe Zone (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255,255,255,0.18)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: COR.marca,
          }}
        />
      </div>

      {/* Legenda Karaokê (somente antes do cartão final) */}
      {sec < 25.66 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={COR.marca}
          textoDestaque={COR.textoSobreMarca}
          tamanho={44}
          base={350}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
