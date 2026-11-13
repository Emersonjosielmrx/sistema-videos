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

const VERDE = '#22C55E';
const ESCURO = '#111827';
const TEXTO_ESCURO = '#121216';

export const Cena3Resultado: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Cena 3: ini = 18.92s, fim = 26.30s (duração local = 7.38s = 221 frames)
  const absT = 18.92 + frame / fps;

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(absT, [25.98, 26.28], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento de câmera contínuo (slow push-in + pan)
  const bgScale = interpolate(frame, [0, 221], [1.02, 1.10], {extrapolateRight: 'clamp'});
  const progressPct = interpolate(frame, [5, 210], [22, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(frame * 0.12) * 4;

  // Sincronia perfeita com a fala:
  // "Hoje eu envio campanhas" -> 19.42s..20.71s
  // "para milhares de contatos no WhatsApp" -> 20.73s..22.77s
  // "através do disparo em massa inteligente" -> 22.78s..25.00s
  const headerPop = spring({frame: frame - 2, fps, config: {damping: 14}});
  const item1Pop = spring({
    frame: frame - Math.round((19.45 - 18.92) * fps),
    fps,
    config: {damping: 14},
  });
  const item2Pop = spring({
    frame: frame - Math.round((20.75 - 18.92) * fps),
    fps,
    config: {damping: 14},
  });
  const item3Pop = spring({
    frame: frame - Math.round((22.80 - 18.92) * fps),
    fps,
    config: {damping: 14},
  });
  const metricsPop = spring({
    frame: frame - Math.round((21.5 - 18.92) * fps),
    fps,
    config: {damping: 14},
  });

  const item1Ativo = absT >= 19.45;
  const item2Ativo = absT >= 20.75;
  const item3Ativo = absT >= 22.80;

  return (
    <AbsoluteFill style={{backgroundColor: ESCURO, opacity: enterOp * exitOp}}>
      {/* Fundo contextualizado de resultados (painel tecnológico de disparo com ambient glow verde, sem repetir a foto da Cena 1) */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 20%',
            filter: 'blur(22px) brightness(0.24)',
            transform: `scale(${bgScale})`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 30%, rgba(34,197,94,0.22) 0%, rgba(15,23,42,0.96) 65%, #111827 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Topo dentro da Safe Zone (y=162): Rótulo "O RESULTADO" + Milhares de contatos */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          opacity: headerPop,
          transform: `translateY(${interpolate(headerPop, [0, 1], [-25, 0])}px)`,
          zIndex: 20,
        }}
      >
        <div
          style={{
            background: VERDE,
            color: TEXTO_ESCURO,
            fontFamily,
            fontSize: 34,
            fontWeight: 900,
            padding: '10px 26px',
            borderRadius: 999,
            textTransform: 'uppercase',
            boxShadow: '0 8px 24px rgba(34,197,94,0.45)',
          }}
        >
          O RESULTADO
        </div>
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.94)',
            border: `2px solid ${VERDE}`,
            color: '#FFFFFF',
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            padding: '8px 22px',
            borderRadius: 999,
          }}
        >
          Milhares de contatos
        </div>
      </div>

      {/* Painel de Campanhas em Tempo Real (y=235..450) */}
      <div
        style={{
          position: 'absolute',
          top: 235,
          left: 60,
          right: 60,
          zIndex: 15,
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.96)',
            border: `3px solid ${VERDE}`,
            borderRadius: 28,
            padding: '18px 24px',
            boxShadow: '0 20px 45px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  background: VERDE,
                  boxShadow: `0 0 14px ${VERDE}`,
                  transform: `scale(${1 + Math.sin(frame * 0.25) * 0.25})`,
                }}
              />
              <span style={{fontFamily, fontSize: 33, fontWeight: 900, color: '#FFFFFF'}}>
                Painel de Campanhas IA
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: TEXTO_ESCURO,
                background: VERDE,
                padding: '4px 18px',
                borderRadius: 999,
              }}
            >
              Enviando
            </span>
          </div>

          {/* Cards de campanhas ativas operando disparos em massa */}
          <div style={{display: 'flex', gap: 10, justifyContent: 'space-between'}}>
            {[
              {rotulo: 'Campanha Loja', status: '✓ Enviado'},
              {rotulo: 'Aviso VIP', status: '✓ Enviado'},
              {rotulo: 'Chave Pix', status: '✓ Ativo'},
            ].map((p, i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  background: 'rgba(34, 197, 94, 0.16)',
                  border: '2px solid rgba(34, 197, 94, 0.55)',
                  borderRadius: 16,
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                  transform: `translateY(${Math.sin(frame * 0.15 + i * 1.3) * 3}px)`,
                }}
              >
                <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                  {p.rotulo}
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#86EFAC'}}>
                  {p.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Barra de Progresso do Disparo Ativo (y=470..555) */}
      <div
        style={{
          position: 'absolute',
          top: 470,
          left: 60,
          right: 60,
          background: 'rgba(17, 24, 39, 0.95)',
          border: `2px solid ${VERDE}`,
          borderRadius: 22,
          padding: '14px 24px',
          boxShadow: '0 14px 32px rgba(0,0,0,0.55)',
          zIndex: 15,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 10}}>
          <span style={{fontFamily, fontSize: 33, fontWeight: 900, color: '#FFFFFF'}}>
            Disparo em Massa Ativo
          </span>
          <span style={{fontFamily, fontSize: 33, fontWeight: 900, color: VERDE}}>
            WhatsApp
          </span>
        </div>
        <div
          style={{
            width: '100%',
            height: 14,
            background: 'rgba(255,255,255,0.15)',
            borderRadius: 999,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progressPct}%`,
              height: '100%',
              background: `linear-gradient(90deg, ${VERDE}, #86EFAC)`,
              borderRadius: 999,
            }}
          />
        </div>
      </div>

      {/* Checklist de 3 benefícios sincronizado com a voz (y=575..1045) com alta luminosidade em itens pendentes */}
      <div
        style={{
          position: 'absolute',
          top: 575,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          transform: `translateY(${floatY}px)`,
          zIndex: 15,
        }}
      >
        {[
          {
            pop: item1Pop,
            ativo: item1Ativo,
            titulo: 'Campanhas em Massa',
            sub: 'Envio automático no WhatsApp',
          },
          {
            pop: item2Pop,
            ativo: item2Ativo,
            titulo: 'Milhares de Contatos',
            sub: 'Rotação de números e instâncias',
          },
          {
            pop: item3Pop,
            ativo: item3Ativo,
            titulo: 'Disparo Inteligente',
            sub: 'Cartão de aniversário e envio de Pix',
          },
        ].map((item, idx) => {
          const bg = item.ativo ? 'rgba(15, 23, 42, 0.98)' : 'rgba(30, 41, 59, 0.95)';
          const borderCor = item.ativo ? VERDE : 'rgba(255, 255, 255, 0.35)';
          const titleCor = '#FFFFFF'; // sempre branco brilhante para legibilidade perfeita
          const subCor = item.ativo ? '#86EFAC' : '#E2E8F0'; // cinza neutro claro quando inativo

          return (
            <div
              key={idx}
              style={{
                background: bg,
                border: `3px solid ${borderCor}`,
                borderRadius: 24,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: item.ativo
                  ? '0 14px 32px rgba(34,197,94,0.3)'
                  : '0 8px 20px rgba(0,0,0,0.4)',
                opacity: Math.max(0.85, item.pop),
                transform: `translateX(${interpolate(item.pop, [0, 1], [-25, 0])}px)`,
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  background: item.ativo ? VERDE : 'rgba(255,255,255,0.2)',
                  color: item.ativo ? TEXTO_ESCURO : '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  flexShrink: 0,
                  boxShadow: item.ativo ? `0 0 16px ${VERDE}` : 'none',
                }}
              >
                ✓
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 900,
                    color: titleCor,
                    lineHeight: 1.15,
                  }}
                >
                  {item.titulo}
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: subCor,
                    lineHeight: 1.15,
                  }}
                >
                  {item.sub}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Card Flutuante de Métricas no terço inferior eliminando qualquer vazio escuro (y=1065..1230) */}
      <div
        style={{
          position: 'absolute',
          top: 1065,
          left: 60,
          right: 60,
          background: 'rgba(17, 24, 39, 0.96)',
          border: `2px solid ${VERDE}`,
          borderRadius: 24,
          padding: '16px 24px',
          boxShadow: '0 16px 36px rgba(0,0,0,0.6)',
          opacity: metricsPop,
          transform: `translateY(${interpolate(metricsPop, [0, 1], [24, 0])}px)`,
          zIndex: 15,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          {[
            {label: 'Alcance', valor: 'Milhares'},
            {label: 'Envio', valor: 'Automático'},
            {label: 'Instâncias', valor: 'Com Rotação'},
          ].map((m, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: i === 0 ? 'flex-start' : i === 1 ? 'center' : 'flex-end',
              }}
            >
              <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#94A3B8'}}>
                {m.label}
              </span>
              <span style={{fontFamily, fontSize: 33, fontWeight: 900, color: '#86EFAC'}}>
                {m.valor}
              </span>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
