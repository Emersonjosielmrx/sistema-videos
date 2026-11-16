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
import briefing from '../../../trabalhos/followupia_ia_20261116_052420/public/briefing.json';

interface Cena0Props {
  fontFamily: string;
  corMarca: string;
  corFundo: string;
  corTextoMarca: string;
}

export const Cena0: React.FC<Cena0Props> = ({
  fontFamily,
  corMarca,
  corFundo,
  corTextoMarca,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  // Zoom contínuo na câmera durante toda a cena para reter atenção
  const pushIn = interpolate(frame, [0, 154], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrada do título
  const titlePop = spring({
    frame: frame - 1,
    fps,
    config: {damping: 14, stiffness: 160},
  });

  // Entrada do card de mockup logo no início como pop-up flutuante dinâmico
  const cardEnter = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 150},
  });

  // Mensagem 2 (Empresa): entra ágil aos 1.35s
  const showMsg2 = t >= 1.35;
  const msg2Enter = spring({
    frame: frame - Math.round(1.35 * fps),
    fps,
    config: {damping: 14, stiffness: 160},
  });

  // Alerta de vácuo / não comprou: entra aos 2.6s
  const showAlert = t >= 2.6;
  const alertEnter = spring({
    frame: frame - Math.round(2.6 * fps),
    fps,
    config: {damping: 13, stiffness: 170},
  });

  // Transição de saída com zoom-through cinematográfico em direção à mesa do apresentador
  const zoomThrough = interpolate(t, [4.7, 5.12], [1.0, 1.45], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(t, [4.85, 5.12], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Micro-flutuação orgânica
  const floatY = Math.sin(frame / 11) * 5;
  const tiltY = interpolate(frame, [0, 154], [-4, 3], {
    extrapolateRight: 'clamp',
  });

  // Destaques de palavras em sincronia exata com a fala
  // Aplicados diretamente na cor da fonte com glow em ciano neon, sem caixas recortadas
  const highlightPreco = t >= 1.37;
  const highlightMes = t >= 2.16;
  const highlightNaoComprou = t >= 2.91;

  return (
    <AbsoluteFill
      style={{
        opacity: exitOpacity,
        backgroundColor: corFundo,
        transform: `scale(${zoomThrough})`,
        transformOrigin: 'center center',
      }}
    >
      {/* Vídeo do apresentador nítido, bem iluminado e em primeiro plano falando diretamente com o público */}
      <AbsoluteFill
        style={{
          transform: `scale(${pushIn * 1.04}) translateX(135px) translateY(35px)`,
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
            filter: 'brightness(1.02) contrast(1.04)',
          }}
        />
      </AbsoluteFill>

      {/* Vinheta superior suave para legibilidade do gancho */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 440,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.85) 0%, rgba(17,24,39,0.45) 50%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Vinheta inferior para o Karaokê */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(0deg, rgba(17,24,39,0.92) 0%, rgba(17,24,39,0.5) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Seguro (y: 175 - 410): Pergunta do cliente */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          transform: `scale(${interpolate(titlePop, [0, 1], [0.94, 1])}) translateY(${interpolate(titlePop, [0, 1], [20, 0])}px)`,
          opacity: titlePop,
          zIndex: 40,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            backgroundColor: 'rgba(17, 24, 39, 0.88)',
            border: `2px solid ${corMarca}`,
            borderRadius: 999,
            padding: '6px 20px',
            marginBottom: 12,
            boxShadow: '0 4px 15px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: 6,
              backgroundColor: corMarca,
              boxShadow: `0 0 10px ${corMarca}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 30,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 0.5,
            }}
          >
            DÚVIDA DE VENDEDOR
          </span>
        </div>

        {/* Título unificado sem fragmentação de caixas e sem espaços duplos */}
        <div
          style={{
            fontFamily,
            fontSize: 48,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.25,
            textShadow: '0 4px 20px rgba(0,0,0,0.95)',
            textWrap: 'balance',
            backgroundColor: 'rgba(17, 24, 39, 0.65)',
            padding: '10px 18px',
            borderRadius: 18,
            border: '1px solid rgba(255,255,255,0.12)',
            boxShadow: '0 8px 25px rgba(0,0,0,0.4)',
          }}
        >
          Dá para resgatar quem{' '}
          <span
            style={{
              color: highlightPreco ? corMarca : '#FFFFFF',
              textShadow: highlightPreco
                ? `0 0 20px ${corMarca}, 0 0 35px ${corMarca}`
                : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            pediu preço
          </span>{' '}
          <span
            style={{
              color: highlightMes ? corMarca : '#FFFFFF',
              textShadow: highlightMes
                ? `0 0 20px ${corMarca}, 0 0 35px ${corMarca}`
                : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            no mês passado
          </span>{' '}
          <span
            style={{
              color: highlightNaoComprou ? corMarca : '#FFFFFF',
              textShadow: highlightNaoComprou
                ? `0 0 20px ${corMarca}, 0 0 35px ${corMarca}`
                : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            e não comprou?
          </span>
        </div>
      </div>

      {/* Pop-up flutuante dinâmico e compacto na lateral esquerda (y: 450 - 1050), deixando o apresentador 100% livre na direita */}
      <div
        style={{
          position: 'absolute',
          top: 450,
          left: 45,
          width: 440,
          perspective: 1200,
          zIndex: 30,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(30, 41, 59, 0.94)',
            backdropFilter: 'blur(16px)',
            borderRadius: 26,
            border: `2px solid rgba(78, 205, 196, 0.5)`,
            padding: '18px 20px',
            boxShadow: '0 24px 60px rgba(0,0,0,0.75), 0 0 30px rgba(78,205,196,0.2)',
            transform: `scale(${cardEnter}) translateY(${floatY}px) rotateY(${tiltY}deg)`,
            opacity: cardEnter,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Cabeçalho do chat WhatsApp */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.14)',
              paddingBottom: 14,
              marginBottom: 18,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 29,
                  backgroundColor: corMarca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 28,
                  fontWeight: 900,
                  color: corTextoMarca,
                  boxShadow: `0 4px 14px rgba(78,205,196,0.35)`,
                }}
              >
                CL
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
                  Cliente Orçamento
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 600,
                    color: '#94A3B8',
                  }}
                >
                  Lead inativo
                </div>
              </div>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 26,
                fontWeight: 700,
                color: '#CBD5E1',
                backgroundColor: 'rgba(255,255,255,0.1)',
                padding: '6px 14px',
                borderRadius: 10,
                border: '1px solid rgba(255,255,255,0.2)',
              }}
            >
              Simulação
            </div>
          </div>

          {/* Mensagem 1: Cliente (presente desde o início) */}
          <div
            style={{
              alignSelf: 'flex-start',
              backgroundColor: '#334155',
              borderRadius: '20px 20px 20px 6px',
              padding: '16px 20px',
              marginBottom: showMsg2 ? 14 : 0,
              maxWidth: '92%',
              boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#FFFFFF',
                lineHeight: 1.25,
              }}
            >
              Oi! Qual o valor do orçamento?
            </div>
          </div>

          {/* Mensagem 2: Empresa (surge com mola ágil aos 1.35s) */}
          {showMsg2 && (
            <div
              style={{
                marginLeft: 'auto',
                backgroundColor: '#065F46',
                border: '1px solid rgba(78,205,196,0.35)',
                borderRadius: '20px 20px 6px 20px',
                padding: '16px 20px',
                marginBottom: showAlert ? 16 : 0,
                maxWidth: '92%',
                transform: `scale(${interpolate(msg2Enter, [0, 1], [0.85, 1])}) translateY(${interpolate(msg2Enter, [0, 1], [15, 0])}px)`,
                opacity: msg2Enter,
                boxShadow: '0 4px 15px rgba(6,95,70,0.4)',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Enviei a proposta completa! Vamos fechar?
              </div>
            </div>
          )}

          {/* Alerta de vácuo + Gancho (surge aos 2.6s com altíssimo contraste e brilho) */}
          {showAlert && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                transform: `scale(${interpolate(alertEnter, [0, 1], [0.88, 1])})`,
                opacity: alertEnter,
              }}
            >
              <div
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.95)',
                  border: '2px solid #EF4444',
                  borderRadius: 14,
                  padding: '10px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 6px 20px rgba(239, 68, 68, 0.5)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textShadow: '0 2px 6px rgba(0,0,0,0.7)',
                    letterSpacing: 0.3,
                  }}
                >
                  ⚠️ Sem resposta há semanas
                </span>
              </div>
              <div
                style={{
                  backgroundColor: corMarca,
                  borderRadius: 14,
                  padding: '10px 16px',
                  textAlign: 'center',
                  boxShadow: `0 4px 16px rgba(78,205,196,0.45)`,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: corTextoMarca,
                  }}
                >
                  {briefing.gancho_tela}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
