import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {CORES} from './constants';

interface CenaProps {
  fontFamily: string;
}

export const Cena0: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo: push-in contínuo e expressivo
  const bgScale = interpolate(frame, [0, 180], [1.02, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 180], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Molas da cena - Pergunta completa visível desde o frame 0 para impacto imediato
  const tagSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const questionSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Notificações da Dor com entrada ágil no 1º segundo (impacto imediato para retenção)
  const notif1Spring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const notif2Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Flutuação contínua e micro-shake/pulso de alerta no badge para eliminar qualquer estática
  const float1 = Math.sin(frame * 0.09) * 5;
  const float2 = Math.cos(frame * 0.09) * 5;
  const alertPulse = 1.0 + 0.08 * Math.sin(frame * 0.25);
  const alertShake = Math.sin(frame * 0.6) * 2.5;
  const alertGlow = 14 + 8 * Math.sin(frame * 0.25);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: CORES.fundo_escuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
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
        {/* Véu e iluminação com contraste aprimorado */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 30%, rgba(17, 24, 39, 0.65) 0%, rgba(17, 24, 39, 0.92) 100%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 15%, rgba(255, 169, 77, 0.15) 0%, transparent 65%)',
          }}
        />
      </div>

      {/* Faixa Superior: Tag de Contexto (y ~ 178) */}
      <div
        style={{
          position: 'absolute',
          top: 178,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: tagSpring,
          transform: `scale(${Math.max(0.7, tagSpring)})`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            backgroundColor: 'rgba(31, 41, 55, 0.94)',
            border: `2px solid ${CORES.marca}`,
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.5)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: CORES.marca,
              boxShadow: `0 0 10px ${CORES.marca}`,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: CORES.texto_claro,
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Pergunta do Cliente
          </span>
        </div>
      </div>

      {/* Título Cinético: Pergunta Central Completa desde o Frame 0 */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          textAlign: 'center',
          opacity: questionSpring,
          transform: `translateY(${(1 - questionSpring) * 20}px)`,
        }}
      >
        {/* Linha 1 */}
        <div
          style={{
            fontSize: 52,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
          }}
        >
          UMA INTELIGÊNCIA ARTIFICIAL
        </div>

        {/* Linha 2 com destaque */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 14,
            flexWrap: 'wrap',
          }}
        >
          <span
            style={{
              backgroundColor: CORES.marca,
              color: CORES.texto_sobre_marca,
              padding: '6px 20px',
              borderRadius: 14,
              fontSize: 54,
              fontWeight: 900,
              boxShadow: `0 8px 25px rgba(255, 169, 77, 0.45)`,
            }}
          >
            DÁ CONTA
          </span>
          <span
            style={{
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              textShadow: '0 4px 18px rgba(0,0,0,0.85)',
            }}
          >
            DE ORGANIZAR
          </span>
        </div>

        {/* Linha 3 */}
        <div
          style={{
            fontSize: 54,
            fontWeight: 900,
            color: CORES.marca,
            lineHeight: 1.15,
            textShadow: '0 4px 20px rgba(0,0,0,0.9)',
          }}
        >
          TODA A SUA AGENDA?
        </div>
      </div>

      {/* Área Central: Notificações Visuais da Dor (y: 610 a 1240) */}
      <div
        style={{
          position: 'absolute',
          top: 610,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}
      >
        {/* Notificação 1: Mensagens sem resposta no WhatsApp com Urgência Imediata */}
        {frame >= 2 && (
          <div
            style={{
              opacity: notif1Spring,
              transform: `translateY(${(1 - notif1Spring) * 30 + float1}px)`,
              backgroundColor: 'rgba(31, 41, 55, 0.96)',
              border: '2px solid #25D366',
              borderRadius: 26,
              padding: '24px 28px',
              boxShadow: '0 15px 40px rgba(37, 211, 102, 0.25), 0 20px 45px rgba(0, 0, 0, 0.7)',
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
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    boxShadow: '0 0 12px rgba(37, 211, 102, 0.7)',
                  }}
                >
                  ✓
                </div>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  WhatsApp • Cliente aguardando
                </span>
              </div>
              <span
                style={{
                  fontSize: 28,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  backgroundColor: '#DC2626',
                  padding: '6px 16px',
                  borderRadius: 12,
                  boxShadow: '0 4px 12px rgba(220, 38, 38, 0.4)',
                }}
              >
                Sem resposta
              </span>
            </div>

            <div
              style={{
                fontSize: 33,
                fontWeight: 600,
                color: '#FFFFFF',
                lineHeight: 1.3,
                backgroundColor: 'rgba(17, 24, 39, 0.8)',
                padding: '14px 20px',
                borderRadius: 14,
                borderLeft: '4px solid #25D366',
              }}
            >
              &ldquo;Olá! Quero marcar meu horário para hoje, tem vaga?&rdquo;
            </div>
          </div>
        )}

        {/* Notificação 2: Conflito de Agendamento com Alto Contraste e Micro-shake / Pulsar contínuo de Alerta */}
        {frame >= 14 && (
          <div
            style={{
              opacity: notif2Spring,
              transform: `translateY(${(1 - notif2Spring) * 30 + float2}px)`,
              backgroundColor: 'rgba(31, 41, 55, 0.96)',
              border: '2px solid rgba(239, 68, 68, 0.85)',
              borderRadius: 26,
              padding: '24px 28px',
              boxShadow: `0 15px 40px rgba(239, 68, 68, 0.35), 0 20px 45px rgba(0, 0, 0, 0.7)`,
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
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    backgroundColor: '#EF4444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    boxShadow: `0 0 ${alertGlow}px rgba(239, 68, 68, 0.9)`,
                  }}
                >
                  !
                </div>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Alerta de Conflito de Horário
                </span>
              </div>
              <span
                style={{
                  fontSize: 28,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  backgroundColor: '#DC2626',
                  padding: '6px 16px',
                  borderRadius: 12,
                  boxShadow: '0 4px 15px rgba(220, 38, 38, 0.5)',
                  textTransform: 'uppercase',
                  transform: `scale(${alertPulse}) translateX(${alertShake}px)`,
                  display: 'inline-block',
                }}
              >
                Duplo Agendamento
              </span>
            </div>

            <div
              style={{
                fontSize: 33,
                fontWeight: 600,
                color: '#FFFFFF',
                lineHeight: 1.3,
                backgroundColor: 'rgba(17, 24, 39, 0.8)',
                padding: '14px 20px',
                borderRadius: 14,
                borderLeft: '4px solid #EF4444',
              }}
            >
              Dois clientes marcados no mesmo horário por falha manual.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
