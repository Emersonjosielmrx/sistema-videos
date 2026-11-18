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

interface Cena2Props {
  fontFamily: string;
  corMarca: string;
  corFundo: string;
  corTextoMarca: string;
}

export const Cena2: React.FC<Cena2Props> = ({
  fontFamily,
  corMarca,
  corFundo,
  corTextoMarca,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((19.92 - 11.73) * fps);
  const absTime = 11.73 + frame / fps;

  const enter = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  const exit = interpolate(absTime, [19.57, 19.92], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Push-in contínuo na cena para manter dinamismo visual constante
  const sceneScale = interpolate(frame, [0, durFrames], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Estados de ativação das abas rigorosamente sincronizados com o áudio:
  // - 12.67s até 15.15s: "A IA envia mensagens no WhatsApp" -> Etapa 1 ativa
  // - 15.15s até 17.15s: "para trazer esse público de volta" -> Etapa 2 ativa (Aba 1 desativa)
  // - 17.15s em diante: "e nunca desiste." -> Etapa 3 ativa com realce (Aba 2 desativa)
  const isEtapa2 = absTime >= 15.15 && absTime < 17.15;
  const isEtapa3 = absTime >= 17.15;
  const isEtapa1 = absTime >= 12.67 && !isEtapa2 && !isEtapa3;

  // Linha de progresso do Stepper animada continuamente
  const progressLine = interpolate(
    absTime,
    [12.67, 15.15, 17.15, 18.5],
    [16, 50, 85, 100],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Molas para a entrada dos balões no mockup
  const msg1Spring = spring({
    frame: frame - Math.round((12.67 - 11.73) * fps),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  const msg2Spring = spring({
    frame: frame - Math.round((15.15 - 11.73) * fps),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  const badge3Spring = spring({
    frame: frame - Math.round((17.15 - 11.73) * fps),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  // Micro-movimentos
  const floatY = Math.sin(frame / 10) * 4;
  const pulseS3 = isEtapa3 ? 1 + Math.sin(frame / 6) * 0.04 : 1;

  // Transição suave de entrada com slide lateral conectando à fala do apresentador
  const enterSlideX = interpolate(enter, [0, 1], [40, 0]);
  const exitSlideX = interpolate(absTime, [19.57, 19.92], [0, -30], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        opacity: enter * exit,
        backgroundColor: corFundo,
        overflow: 'hidden',
        transform: `translateX(${enterSlideX + exitSlideX}px)`,
      }}
    >
      {/* Vídeo do fundador em plano médio lateral (mantém contato visual humano, autoridade e dinamismo) */}
      <AbsoluteFill
        style={{
          transform: `scale(${sceneScale * 1.04}) translateX(135px) translateY(40px)`,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Vinheta superior suave para legibilidade do Stepper */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 420,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.9) 0%, rgba(17,24,39,0.5) 60%, transparent 100%)',
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

      {/* Top HUD posicionado em y: 175 (livre do traço da barra de progresso em y: 150) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          backgroundColor: 'rgba(17, 24, 39, 0.94)',
          border: `2px solid ${corMarca}`,
          borderRadius: 22,
          padding: '14px 20px',
          boxShadow: '0 18px 45px rgba(0,0,0,0.65)',
          transform: `translateY(${interpolate(enter, [0, 1], [-25, 0])}px) scale(${interpolate(enter, [0, 1], [0.96, 1.0])})`,
          zIndex: 40,
        }}
      >
        {/* Cabeçalho do HUD */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 12,
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
            COMO FUNCIONA
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 30,
              fontWeight: 800,
              color: corMarca,
            }}
          >
            Automação com IA
          </span>
        </div>

        {/* Linha de conexão do Stepper */}
        <div
          style={{
            position: 'relative',
            height: 4,
            backgroundColor: 'rgba(255,255,255,0.14)',
            borderRadius: 2,
            marginBottom: 12,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progressLine}%`,
              height: '100%',
              backgroundColor: corMarca,
              boxShadow: `0 0 10px ${corMarca}`,
            }}
          />
        </div>

        {/* 3 Etapas conectadas com alternância exclusiva e alto contraste */}
        <div style={{display: 'flex', gap: 10}}>
          {/* Etapa 1: Ativa exclusivamente durante a primeira fala */}
          <div
            style={{
              flex: 1,
              backgroundColor: isEtapa1 ? corMarca : 'rgba(17, 24, 39, 0.82)',
              borderRadius: 14,
              padding: '10px 6px',
              textAlign: 'center',
              border: `2px solid ${isEtapa1 ? corMarca : 'rgba(255,255,255,0.22)'}`,
              boxShadow: isEtapa1 ? `0 0 20px rgba(78,205,196,0.6)` : 'none',
              transition: 'all 0.2s ease',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 30,
                fontWeight: 900,
                color: isEtapa1 ? corTextoMarca : '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              1. Envia no WhatsApp
            </div>
          </div>

          {/* Etapa 2: Ativa exclusivamente ao falar 'trazer esse público de volta' */}
          <div
            style={{
              flex: 1,
              backgroundColor: isEtapa2 ? corMarca : 'rgba(17, 24, 39, 0.82)',
              borderRadius: 14,
              padding: '10px 6px',
              textAlign: 'center',
              border: `2px solid ${isEtapa2 ? corMarca : 'rgba(255,255,255,0.22)'}`,
              boxShadow: isEtapa2 ? `0 0 20px rgba(78,205,196,0.6)` : 'none',
              transition: 'all 0.2s ease',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 30,
                fontWeight: 900,
                color: isEtapa2 ? corTextoMarca : '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              2. Traz de volta
            </div>
          </div>

          {/* Etapa 3: Ativa exclusivamente ao falar 'nunca desiste' */}
          <div
            style={{
              flex: 1,
              backgroundColor: isEtapa3 ? '#10B981' : 'rgba(17, 24, 39, 0.82)',
              borderRadius: 14,
              padding: '10px 6px',
              textAlign: 'center',
              border: `2px solid ${isEtapa3 ? '#10B981' : 'rgba(255,255,255,0.22)'}`,
              boxShadow: isEtapa3 ? `0 0 22px rgba(16,185,129,0.7)` : 'none',
              transform: isEtapa3 ? `scale(${pulseS3})` : 'none',
              transition: 'all 0.2s ease',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 30,
                fontWeight: 900,
                color: isEtapa3 ? '#0F172A' : '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              3. Nunca desiste
            </div>
          </div>
        </div>
      </div>

      {/* Mockup Dinâmico de WhatsApp em Overlay Flutuante na Lateral Esquerda (y: 410 - 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 410,
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
            boxShadow: '0 24px 65px rgba(0,0,0,0.75), 0 0 30px rgba(78,205,196,0.2)',
            transform: `translateY(${floatY}px)`,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Barra do WhatsApp Business */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.14)',
              paddingBottom: 14,
              marginBottom: 16,
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
                IA
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
                  Follow-up IA
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 600,
                    color: corMarca,
                  }}
                >
                  ● Automação ativa
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

          {/* Histórico anterior: Orçamento esquecido semanas atrás (alto contraste garantido com texto branco puro) */}
          <div
            style={{
              alignSelf: 'center',
              backgroundColor: 'rgba(255, 255, 255, 0.22)',
              border: '1px solid rgba(255, 255, 255, 0.45)',
              borderRadius: 12,
              padding: '6px 20px',
              marginBottom: 16,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.3,
                textShadow: '0 2px 4px rgba(0,0,0,0.6)',
              }}
            >
              Lead inativo há semanas
            </span>
          </div>

          {/* Balão 1: Follow-up disparado pela IA aos 12.67s ("A IA envia mensagens no WhatsApp") */}
          {absTime >= 12.67 && (
            <div
              style={{
                marginLeft: 'auto',
                backgroundColor: '#065F46',
                border: '1px solid rgba(78,205,196,0.4)',
                borderRadius: '20px 20px 6px 20px',
                padding: '14px 18px',
                marginBottom: 14,
                maxWidth: '94%',
                transform: `scale(${interpolate(msg1Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(msg1Spring, [0, 1], [20, 0])}px)`,
                opacity: msg1Spring,
                boxShadow: '0 6px 20px rgba(6,95,70,0.4)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 4,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 900,
                    color: corMarca,
                  }}
                >
                  ⚡ DISPARO AUTOMÁTICO IA
                </span>
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Olá! Notei que seu orçamento ficou pendente. Quer retomar o atendimento?
              </div>
              <div
                style={{
                  textAlign: 'right',
                  fontFamily,
                  fontSize: 26,
                  fontWeight: 700,
                  color: corMarca,
                  marginTop: 4,
                }}
              >
                ✓✓ Enviado no WhatsApp
              </div>
            </div>
          )}

          {/* Balão 2: Resposta do Lead aos 15.15s ("para trazer esse público de volta") */}
          {absTime >= 15.15 && (
            <div
              style={{
                alignSelf: 'flex-start',
                backgroundColor: '#334155',
                border: '1px solid rgba(255,255,255,0.22)',
                borderRadius: '20px 20px 20px 6px',
                padding: '14px 18px',
                marginBottom: 14,
                maxWidth: '92%',
                transform: `scale(${interpolate(msg2Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(msg2Spring, [0, 1], [20, 0])}px)`,
                opacity: msg2Spring,
                boxShadow: '0 6px 20px rgba(0,0,0,0.3)',
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
                Oi! Que bom que chamou, quero fechar sim!
              </div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  marginTop: 6,
                  backgroundColor: 'rgba(78,205,196,0.25)',
                  padding: '4px 10px',
                  borderRadius: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 900,
                    color: corMarca,
                  }}
                >
                  ✓ Lead trazido de volta
                </span>
              </div>
            </div>
          )}

          {/* Alerta de Confirmação Hero aos 17.15s ("e nunca desiste.") */}
          {absTime >= 17.15 && (
            <div
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.28)',
                border: '2px solid #10B981',
                borderRadius: 16,
                padding: '12px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transform: `scale(${interpolate(badge3Spring, [0, 1], [0.88, 1]) * pulseS3})`,
                opacity: badge3Spring,
                boxShadow: '0 8px 25px rgba(16,185,129,0.4)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textAlign: 'center',
                }}
              >
                ✓ Follow-up contínuo que nunca desiste
              </span>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
