import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
  staticFile,
} from 'remotion';
import {CORES} from './types';

export const Cena0: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com vídeo do restaurante em movimento contínuo (zoom dinâmico 1.05 -> 1.20)
  const bgScale = interpolate(frame, [0, 140], [1.06, 1.20], {
    extrapolateRight: 'clamp',
  });
  const lightX = interpolate(frame, [0, 140], [30, 70], {
    extrapolateRight: 'clamp',
  });

  // Título cinético sincronizado com a fala (1 único bloco no topo)
  const isPhase2 = frame >= 45;
  const titleSpring1 = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const titleSpring2 = spring({
    frame: frame - 45,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Entrada do Elemento Focal Central (Card de Sobrecarga do WhatsApp)
  const hubSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const hubY = interpolate(hubSpring, [0, 1], [60, 0]);

  // Transições suaves com spring, slide vertical e fade para cada notificação
  const item1Progress = spring({
    frame: frame - 16,
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const item1Y = interpolate(item1Progress, [0, 1], [35, 0]);

  const item2Progress = spring({
    frame: frame - 46,
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const item2Y = interpolate(item2Progress, [0, 1], [35, 0]);

  const alertProgress = spring({
    frame: frame - 72,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const alertY = interpolate(alertProgress, [0, 1], [30, 0]);

  // Efeito de tremor sutil no momento da desistência
  const shake =
    frame >= 48 && frame <= 70
      ? Math.sin((frame - 48) * 1.6) * 5
      : 0;

  // Pulso contínuo do alerta de urgência
  const pulseAlert =
    frame >= 72 ? 1 + Math.sin((frame - 72) * 0.22) * 0.03 : 1;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do restaurante ao fundo em movimento contínuo e enquadramento superior com rosto 100% livre */}
      <div
        style={{
          position: 'absolute',
          inset: -30,
          transform: `scale(${bgScale}) translateY(-40px)`,
          transformOrigin: '50% 30%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Overlay com iluminação dinâmica suave sem apagar o apresentador */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at ${lightX}% 35%, rgba(225,29,72,0.18) 0%, rgba(35,6,12,0.5) 60%, #110206 100%)`,
        }}
      />

      {/* Gradiente superior para garantir contraste do título cinético */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 360,
          background:
            'linear-gradient(to bottom, rgba(15, 2, 5, 0.94) 0%, rgba(15, 2, 5, 0.45) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Informativo Enxuto (y: 175 a 350) — Respiro seguro >= 25px abaixo da barra em y=152 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          height: 170,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          zIndex: 25,
        }}
      >
        {!isPhase2 ? (
          <div
            style={{
              transform: `scale(${Math.max(0, titleSpring1)})`,
              opacity: Math.min(1, titleSpring1),
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.2,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              whiteSpace: 'nowrap',
            }}
          >
            MENSAGENS{' '}
            <span
              style={{
                background: CORES.marca,
                padding: '4px 18px',
                borderRadius: 14,
                color: '#FFFFFF',
                boxShadow: `0 0 30px ${CORES.marca}`,
              }}
            >
              ACUMULANDO?
            </span>
          </div>
        ) : (
          <div
            style={{
              transform: `scale(${Math.max(0, titleSpring2)})`,
              opacity: Math.min(1, titleSpring2),
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.2,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              whiteSpace: 'nowrap',
            }}
          >
            CLIENTES{' '}
            <span
              style={{
                background: '#DC2626',
                padding: '4px 18px',
                borderRadius: 14,
                color: '#FFFFFF',
                boxShadow: '0 0 30px rgba(220,38,38,0.85)',
              }}
            >
              DESISTINDO
            </span>{' '}
            DO PEDIDO?
          </div>
        )}
      </div>

      {/* Elemento Focal Posicionado no Terço Inferior (y: 1120 a 1480) — ROSTO DO APRESENTADOR 100% LIVRE NO CENTRO */}
      <div
        style={{
          position: 'absolute',
          top: 1120,
          left: 60,
          right: 60,
          transform: `translateX(${shake}px) translateY(${hubY}px) scale(${Math.max(
            0,
            hubSpring
          )})`,
          opacity: Math.min(1, hubSpring),
          background: 'rgba(20, 8, 14, 0.94)',
          border: '3px solid rgba(244, 63, 94, 0.45)',
          borderRadius: 30,
          padding: '18px 24px',
          boxShadow:
            '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 45px rgba(225, 29, 72, 0.3)',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          zIndex: 20,
        }}
      >
        {/* Cabeçalho do Hub WhatsApp (Sem números ou prazos inventados) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '2px solid rgba(255,255,255,0.12)',
            paddingBottom: 12,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 16,
                background: CORES.whatsappVerde,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                boxShadow: '0 0 20px rgba(37, 211, 102, 0.5)',
              }}
            >
              💬
            </div>
            <div>
              <div style={{color: '#94A3B8', fontSize: 32, fontWeight: 600}}>
                WhatsApp Business
              </div>
              <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 900}}>
                Muitas Mensagens no WhatsApp
              </div>
            </div>
          </div>
          <div
            style={{
              background: '#EF4444',
              color: '#FFFFFF',
              borderRadius: 999,
              padding: '4px 16px',
              fontSize: 32,
              fontWeight: 900,
              boxShadow: '0 0 15px rgba(239, 68, 68, 0.7)',
              letterSpacing: 0.5,
              textTransform: 'uppercase',
            }}
          >
            Fila Cheia
          </div>
        </div>

        {/* Mensagem dinâmica: Lucas aguardando (frame 14 a 45) -> Camila desistindo (frame 45 em diante) */}
        {frame < 45 ? (
          <div
            style={{
              transform: `translateY(${item1Y}px) scale(${Math.max(
                0,
                item1Progress
              )})`,
              opacity: Math.min(1, item1Progress),
              background: 'rgba(35, 18, 24, 0.92)',
              border: '2px solid rgba(250, 204, 21, 0.45)',
              borderRadius: 20,
              padding: '14px 20px',
              boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: 6,
              }}
            >
              <span style={{color: CORES.apoio, fontSize: 32, fontWeight: 700}}>
                Cliente Lucas
              </span>
              <span style={{color: '#F87171', fontSize: 32, fontWeight: 700}}>
                Aguardando resposta ⏳
              </span>
            </div>
            <div style={{color: '#F1F5F9', fontSize: 34, fontWeight: 500}}>
              "Oi, boa noite! Manda o cardápio por favor?"
            </div>
          </div>
        ) : (
          <div
            style={{
              transform: `translateY(${item2Y}px) scale(${Math.max(
                0,
                item2Progress
              )})`,
              opacity: Math.min(1, item2Progress),
              background: 'rgba(48, 10, 18, 0.96)',
              border: '2px solid #EF4444',
              borderRadius: 20,
              padding: '14px 20px',
              boxShadow: '0 8px 25px rgba(239, 68, 68, 0.4)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: 6,
              }}
            >
              <span style={{color: '#FCA5A5', fontSize: 32, fontWeight: 700}}>
                Cliente Camila
              </span>
              <span
                style={{
                  color: '#EF4444',
                  fontSize: 32,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                }}
              >
                Desistência ❌
              </span>
            </div>
            <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 700}}>
              "Demorou para responder... acabei desistindo do pedido."
            </div>
          </div>
        )}

        {/* Alerta de Urgência no Horário de Pico */}
        {frame >= 68 && (
          <div
            style={{
              transform: `translateY(${alertY}px) scale(${
                pulseAlert * Math.max(0, alertProgress)
              })`,
              opacity: Math.min(1, alertProgress),
              background:
                'linear-gradient(135deg, rgba(225,29,72,0.96) 0%, rgba(159,18,57,0.96) 100%)',
              border: '2px solid #FECDD3',
              borderRadius: 18,
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
              boxShadow: '0 12px 35px rgba(225, 29, 72, 0.65)',
            }}
          >
            <span style={{fontSize: 34}}>🚨</span>
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 900,
                textAlign: 'center',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              MENSAGENS ACUMULANDO NO HORÁRIO DE PICO
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
