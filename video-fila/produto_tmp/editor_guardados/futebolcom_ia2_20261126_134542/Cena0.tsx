import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {fontFamily} from './fontes';

const CORES = {
  marca: '#E11D48',
  apoio: '#FACC15',
  fundo_escuro: '#31060F',
  card_fundo: 'rgba(18, 4, 8, 0.94)',
};

export const Cena0: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in de câmera contínuo no fundo
  const bgScale = interpolate(frame, [0, 4.69 * fps], [1.0, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Push-in contínuo do celular para reter o usuário logo no início
  const phoneScale = interpolate(frame, [0, 4.69 * fps], [0.99, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entradas rápidas e ágeis desde o frame 0 (retenção imediata do Reels)
  const sprBadge = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  const sprTitle = spring({frame: frame - 2, fps, config: {damping: 14, stiffness: 140}});
  const sprMsg1 = spring({frame: frame + 3, fps, config: {damping: 16, stiffness: 220}});
  const sprWait = spring({frame: frame - 14, fps, config: {damping: 16, stiffness: 160}});
  const sprMsg2 = spring({frame: frame - 28, fps, config: {damping: 16, stiffness: 180}});
  const sprGiveUp = spring({frame: frame - 44, fps, config: {damping: 14, stiffness: 190}});

  // Pulso do relógio de espera
  const waitPulse = 1 + Math.sin(frame * 0.25) * 0.05;
  const cancelPulse = 1 + Math.sin(frame * 0.22) * 0.04;

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundo_escuro, overflow: 'hidden'}}>
      {/* Fundo com imagem e vinheta */}
      <img
        src={staticFile('img_0.jpg')}
        alt="Fundo"
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
          opacity: 0.35,
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at 50% 35%, rgba(225, 29, 72, 0.35) 0%, rgba(35, 4, 10, 0.96) 75%)`,
        }}
      />

      {/* Top HUD: Frase de gancho unificada e limpa (y = 165 a 310) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          zIndex: 40,
        }}
      >
        {/* Rótulo superior */}
        {sprBadge > 0.01 && (
          <div
            style={{
              padding: '6px 22px',
              backgroundColor: CORES.marca,
              borderRadius: 30,
              boxShadow: '0 4px 18px rgba(225, 29, 72, 0.5)',
              transform: `scale(${sprBadge})`,
              opacity: sprBadge,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              ⚠️ DEMORA NO ATENDIMENTO
            </span>
          </div>
        )}

        {/* Título de Pergunta unificado e impactante */}
        {sprTitle > 0.01 && (
          <div
            style={{
              padding: '10px 24px',
              backgroundColor: CORES.card_fundo,
              borderRadius: 18,
              border: `2px solid ${CORES.apoio}`,
              boxShadow: '0 8px 25px rgba(0,0,0,0.85)',
              transform: `scale(${sprTitle})`,
              opacity: sprTitle,
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
              }}
            >
              CLIENTE DESISTE DE COMPRAR?
            </span>
          </div>
        )}
      </div>

      {/* Mockup do Celular com WhatsApp espaçado com folga (y = 365 a 1180, cabeçalho 100% livre) */}
      <div
        style={{
          position: 'absolute',
          top: 365,
          left: 60,
          right: 60,
          height: 810,
          backgroundColor: '#0F172A',
          borderRadius: 38,
          border: '2.5px solid rgba(255, 255, 255, 0.22)',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(225, 29, 72, 0.25)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          transform: `scale(${phoneScale})`,
          zIndex: 30,
        }}
      >
        {/* Header do WhatsApp simulado */}
        <div
          style={{
            padding: '16px 24px',
            backgroundColor: '#075E54',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 26,
                backgroundColor: CORES.marca,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 26,
              }}
            >
              🍔
            </div>
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                Hamburgueria & Delivery
              </span>
              <span style={{fontFamily, fontSize: 26, fontWeight: 600, color: '#A7F3D0'}}>
                Online
              </span>
            </div>
          </div>

          {/* Selo Simulação */}
          <div
            style={{
              padding: '6px 14px',
              backgroundColor: 'rgba(0, 0, 0, 0.35)',
              borderRadius: 14,
              border: '1px solid rgba(255, 255, 255, 0.25)',
            }}
          >
            <span style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#CBD5E1'}}>
              Simulação
            </span>
          </div>
        </div>

        {/* Área de mensagens */}
        <div
          style={{
            flex: 1,
            padding: '24px 26px',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            backgroundColor: '#0B141B',
          }}
        >
          {/* Mensagem 1 do cliente (entra logo no início) */}
          {sprMsg1 > 0.01 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '85%',
                padding: '14px 22px',
                backgroundColor: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                transform: `scale(${sprMsg1})`,
                opacity: sprMsg1,
              }}
            >
              <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.25}}>
                Boa noite! Gostaria de fazer um pedido de lanche.
              </div>
              <div style={{textAlign: 'right', marginTop: 6, fontFamily, fontSize: 24, color: '#94A3B8'}}>
                20:15 ✓✓
              </div>
            </div>
          )}

          {/* Alerta de espera factual (SEM números ou prazos inventados) */}
          {sprWait > 0.01 && (
            <div
              style={{
                alignSelf: 'center',
                padding: '12px 26px',
                backgroundColor: 'rgba(250, 204, 21, 0.15)',
                border: `2px solid ${CORES.apoio}`,
                borderRadius: 24,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                transform: `scale(${waitPulse * sprWait})`,
                opacity: sprWait,
              }}
            >
              <span style={{fontSize: 28}}>⏳</span>
              <span style={{fontFamily, fontSize: 30, fontWeight: 800, color: CORES.apoio}}>
                Aguardando resposta...
              </span>
            </div>
          )}

          {/* Mensagem 2 de desistência: entra ágil antes de 1.1s (sem escala minúscula) */}
          {frame >= 28 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '85%',
                padding: '14px 22px',
                backgroundColor: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                opacity: interpolate(frame, [28, 32], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
                transform: `translateY(${(1 - Math.min(1, sprMsg2)) * 15}px)`,
              }}
            >
              <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.25}}>
                Demorou muito, vou pedir em outro lugar. 😟
              </div>
              <div style={{textAlign: 'right', marginTop: 6, fontFamily, fontSize: 24, color: '#94A3B8'}}>
                20:30 ✓✓
              </div>
            </div>
          )}

          {/* Aviso de cancelamento interno do WhatsApp: entra antes de 1.8s (gerando retenção imediata) */}
          {sprGiveUp > 0.01 && (
            <div
              style={{
                alignSelf: 'center',
                padding: '12px 28px',
                backgroundColor: 'rgba(225, 29, 72, 0.95)',
                borderRadius: 20,
                border: '2px solid #FFFFFF',
                boxShadow: '0 8px 24px rgba(225, 29, 72, 0.6)',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                transform: `scale(${cancelPulse * sprGiveUp})`,
                opacity: sprGiveUp,
              }}
            >
              <span style={{fontSize: 28}}>❌</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                }}
              >
                Cliente cancelou a compra
              </span>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
