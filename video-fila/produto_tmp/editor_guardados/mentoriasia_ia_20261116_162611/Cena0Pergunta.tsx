import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {BRIEFING} from './data';

export const Cena0Pergunta: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom contínuo suave de câmera (1.00 -> 1.07)
  const bgScale = interpolate(frame, [0, 156], [1.0, 1.07], {
    extrapolateRight: 'clamp'
  });

  // Entrada do badge no topo aos primeiros quadros
  const badgeSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 130}
  });

  // Entrada do cartão dinâmico de priorização em lower-third aos ~1.8s (frame 52),
  // quando a locução avança para "mas não sabe por onde começar?"
  // Mantém os primeiros 2 segundos do gancho 100% limpos e focados no apresentador!
  const cardEntryFrame = 52;
  const cardSpring = spring({
    frame: frame - cardEntryFrame,
    fps,
    config: {damping: 15, stiffness: 110}
  });

  const cardPulse = Math.sin((frame - cardEntryFrame) / 6) * 0.02;

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: BRIEFING.cores.fundo_escuro}}>
      {/* 1. B-roll Humano no segundo 0: Enquadramento limpo do apresentador (sem poluição no peito) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(-190px) scale(${bgScale})`,
          transformOrigin: '50% 25%'
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.92) contrast(1.08)'
          }}
        />
      </div>

      {/* 2. Vinheta gradiente: mantém o rosto nítido e escurece a base para legibilidade */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(10, 15, 30, 0.70) 0%, rgba(10, 15, 30, 0.10) 22%, rgba(10, 15, 30, 0.18) 45%, rgba(10, 15, 30, 0.85) 68%, rgba(5, 8, 16, 0.98) 100%)',
          pointerEvents: 'none'
        }}
      />

      {/* 3. Topo: Pílula temática fixada em 'DÚVIDA COMUM' por toda a cena 0 (y: 168) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          fontFamily,
          zIndex: 60
        }}
      >
        <div
          style={{
            transform: `scale(${badgeSpring}) translateY(${interpolate(badgeSpring, [0, 1], [-20, 0])}px)`,
            opacity: badgeSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            borderRadius: 30,
            backgroundColor: 'rgba(37, 99, 235, 0.28)',
            border: '2px solid #60A5FA',
            boxShadow: '0 6px 24px rgba(37, 99, 235, 0.4)'
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#60A5FA',
              boxShadow: '0 0 10px #60A5FA'
            }}
          />
          <span
            style={{
              color: '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '1px',
              textTransform: 'uppercase'
            }}
          >
            DÚVIDA COMUM
          </span>
        </div>
      </div>

      {/* 4. Elemento Gráfico Dinâmico em Lower-Third Único (entra aos 1.8s) */}
      {/* Posicionado estritamente acima de y=1400 (base em y=1360), garantindo folga total para a legenda em y=1440..1560 */}
      {frame >= cardEntryFrame && (
        <div
          style={{
            position: 'absolute',
            left: 70,
            right: 70,
            bottom: 560,
            fontFamily,
            zIndex: 50,
            transform: `scale(${cardSpring * (1 + cardPulse)}) translateY(${interpolate(cardSpring, [0, 1], [30, 0])}px)`,
            opacity: cardSpring,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 22,
            padding: '16px 22px',
            border: '2px solid rgba(59, 130, 246, 0.45)',
            boxShadow: '0 16px 44px rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            flexDirection: 'column',
            gap: 10
          }}
        >
          {/* Header do dilema */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingBottom: 8,
              borderBottom: '1px solid rgba(255, 255, 255, 0.12)'
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span style={{fontSize: 34}}>❓</span>
              <span
                style={{
                  fontSize: 33,
                  fontWeight: 900,
                  color: '#93C5FD',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}
              >
                QUAL TAREFA PRIORIZAR?
              </span>
            </div>
            <div
              style={{
                padding: '4px 12px',
                borderRadius: 10,
                backgroundColor: 'rgba(239, 68, 68, 0.22)',
                border: '1px solid #EF4444',
                fontSize: 32,
                fontWeight: 800,
                color: '#FECACA'
              }}
            >
              Dilema
            </div>
          </div>

          {/* 3 Opções Compactas de Processos */}
          <div style={{display: 'flex', flexDirection: 'column', gap: 8}}>
            {[
              {icone: '⚡', nome: 'Atendimento e Vendas', sub: 'Gargalo comum', cor: '#EF4444'},
              {icone: '⚙️', nome: 'Operação e Cadastros', sub: 'Tempo manual', cor: '#F59E0B'},
              {icone: '📊', nome: 'Geração de Relatórios', sub: 'Retrabalho', cor: '#3B82F6'}
            ].map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  backgroundColor: 'rgba(30, 41, 59, 0.9)',
                  padding: '10px 16px',
                  borderRadius: 14,
                  border: '1px solid rgba(255, 255, 255, 0.12)'
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <span style={{fontSize: 32}}>{item.icone}</span>
                  <span style={{fontSize: 33, fontWeight: 800, color: '#FFFFFF'}}>
                    {item.nome}
                  </span>
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                  <span style={{fontSize: 32, fontWeight: 700, color: '#94A3B8'}}>
                    {item.sub}
                  </span>
                  <span style={{fontSize: 32, color: item.cor, fontWeight: 900}}>→</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
