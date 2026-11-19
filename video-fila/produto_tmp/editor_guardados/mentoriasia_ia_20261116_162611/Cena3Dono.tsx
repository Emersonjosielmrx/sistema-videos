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

export const Cena3Dono: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fala na Cena 3:
  // 21.15s: "Hoje planejo cada etapa no mapa mental"
  // 24.65s (frame 125): "antes de montar minhas próprias automações com IA."
  const viradaFrame = 120;
  const isFase2 = frame >= viradaFrame;

  // Entrada do container
  const introSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 120}
  });

  // Leve flutuação do canvas
  const boardFloatY = Math.cos(frame / 14) * 4;

  // Pulso contínuo para o status de execução na Fase 2
  const pulse = 1 + Math.sin(frame / 5) * 0.035;

  // Timings das etapas do Mapa Mental
  // Nó 1 (Raiz - Mapeamento): ativo logo no início (f=8)
  const node1Spring = spring({frame: frame - 8, fps, config: {damping: 14, stiffness: 120}});
  const isNode1Active = frame >= 8;

  // Nós 2 e 3 (Ramificações - Prompts Validados e Vibe Coding): f=40 e f=70
  const node2Spring = spring({frame: frame - 40, fps, config: {damping: 14, stiffness: 120}});
  const isNode2Active = frame >= 40;

  const node3Spring = spring({frame: frame - 70, fps, config: {damping: 14, stiffness: 120}});
  const isNode3Active = frame >= 70;

  // Nó 4 (Convergência - Automações Próprias com IA): atinge pico na virada (f=115)
  const node4Spring = spring({frame: frame - 115, fps, config: {damping: 14, stiffness: 120}});
  const isNode4Active = frame >= 115;

  return (
    <AbsoluteFill style={{backgroundColor: '#070B19', overflow: 'hidden', fontFamily}}>
      {/* 1. Fundo Tecnológico de Canvas de Automação */}
      <img
        src={staticFile('img_0.jpg')}
        alt="Canvas"
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'brightness(0.35) contrast(1.2)'
        }}
      />

      {/* 2. Grade Pontilhada Estilo Miro / Canvas de Fluxo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(96, 165, 250, 0.22) 2px, transparent 2px)',
          backgroundSize: '36px 36px',
          transform: `translateY(${(frame * 0.6) % 36}px)`,
          pointerEvents: 'none'
        }}
      />

      {/* 3. Safe Zone Container (x: 60..1020, y: 165..1380) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 165,
          bottom: 535,
          display: 'flex',
          flexDirection: 'column',
          gap: 12
        }}
      >
        {/* TOPO: Split / PiP com Apresentador em Close-Up + Título de Autoridade */}
        <div
          style={{
            transform: `scale(${introSpring})`,
            opacity: introSpring,
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 24,
            padding: '10px 18px',
            border: isFase2 ? '2px solid #10B981' : '2px solid #3B82F6',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(12px)'
          }}
        >
          {/* Círculo PiP do Dono em Close-up — Rosto nítido */}
          <div
            style={{
              width: 135,
              height: 135,
              borderRadius: '50%',
              overflow: 'hidden',
              border: isFase2 ? '3px solid #10B981' : '3px solid #60A5FA',
              boxShadow: isFase2
                ? '0 0 16px rgba(16, 185, 129, 0.55)'
                : '0 0 16px rgba(59, 130, 246, 0.55)',
              flexShrink: 0,
              position: 'relative',
              backgroundColor: '#000'
            }}
          >
            <OffthreadVideo
              src={staticFile('dono_3.mp4')}
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: 'scale(1.45) translateY(6%)',
                transformOrigin: '50% 28%'
              }}
            />
          </div>

          {/* Texto Lateral de Contexto */}
          <div style={{display: 'flex', flexDirection: 'column', gap: 4, flex: 1}}>
            <div
              style={{
                display: 'inline-flex',
                alignSelf: 'flex-start',
                alignItems: 'center',
                gap: 8,
                padding: '4px 12px',
                borderRadius: 12,
                backgroundColor: isFase2 ? 'rgba(16, 185, 129, 0.22)' : 'rgba(37, 99, 235, 0.25)',
                border: isFase2 ? '1.5px solid #10B981' : '1.5px solid #60A5FA'
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: isFase2 ? '#A7F3D0' : '#93C5FD',
                  textTransform: 'uppercase'
                }}
              >
                {isFase2 ? '✓ FLUXO EXECUTANDO' : '• NA PRÁTICA'}
              </span>
            </div>

            <div
              style={{
                fontSize: 33,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
                textTransform: 'uppercase'
              }}
            >
              {isFase2
                ? 'AUTOMAÇÕES PRÓPRIAS COM IA'
                : 'DO MAPA MENTAL PARA A EXECUÇÃO'}
            </div>
          </div>
        </div>

        {/* CENTRO: Canvas de Mapa Mental Estruturado (Diagramação em Nós Ramificados) */}
        <div
          style={{
            flex: 1,
            transform: `translateY(${boardFloatY}px)`,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            borderRadius: 26,
            padding: '14px 20px',
            border: isFase2
              ? '2px solid rgba(16, 185, 129, 0.65)'
              : '2px solid rgba(96, 165, 250, 0.45)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.85)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            backdropFilter: 'blur(16px)'
          }}
        >
          {/* Barra de Título: Badge em linha única sem quebra ou estouro vertical */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingBottom: 10,
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
              gap: 12
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0}}>
              <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#EF4444'}} />
              <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#F59E0B'}} />
              <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#10B981'}} />
              <span style={{fontSize: 32, fontWeight: 800, color: '#CBD5E1', marginLeft: 8}}>
                mapa_mental.flow
              </span>
            </div>
            <div
              style={{
                padding: '4px 14px',
                borderRadius: 12,
                backgroundColor: isFase2 ? 'rgba(16, 185, 129, 0.25)' : 'rgba(37, 99, 235, 0.25)',
                border: isFase2 ? '1.5px solid #10B981' : '1.5px solid #60A5FA',
                fontSize: 30,
                fontWeight: 800,
                color: isFase2 ? '#6EE7B7' : '#93C5FD',
                whiteSpace: 'nowrap',
                flexShrink: 0
              }}
            >
              {isFase2 ? '● Rodando em Tempo Real' : '● Estruturando'}
            </div>
          </div>

          {/* DIAGRAMA EM NÓS RAMIFICADOS DE MAPA MENTAL */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              margin: '10px 0',
              position: 'relative'
            }}
          >
            {/* NÓ CENTRAL 1 (RAIZ DO MAPA MENTAL): Topo Largo */}
            <div
              style={{
                transform: `scale(${isNode1Active ? node1Spring : 0.98})`,
                opacity: isNode1Active ? node1Spring : 0.5,
                backgroundColor: isNode1Active ? 'rgba(37, 99, 235, 0.25)' : 'rgba(30, 41, 59, 0.55)',
                border: isNode1Active ? '2px solid #3B82F6' : '1.5px solid rgba(255, 255, 255, 0.25)',
                borderRadius: 18,
                padding: '12px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: isNode1Active ? '0 6px 20px rgba(37, 99, 235, 0.35)' : 'none'
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 36}}>🧠</span>
                <div>
                  <div style={{fontSize: 32, fontWeight: 800, color: '#93C5FD'}}>
                    ETAPA 1 · MAPA MENTAL
                  </div>
                  <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Estruturação de Ideias e Fluxos
                  </div>
                </div>
              </div>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: isNode1Active ? '#2563EB' : 'rgba(255, 255, 255, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                  color: '#FFFFFF',
                  fontWeight: 900
                }}
              >
                ✓
              </div>
            </div>

            {/* RAMIFICAÇÃO VISUAL: Conectores SVG bifurcados */}
            <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: 28}}>
              <svg width="600" height="28" viewBox="0 0 600 28" fill="none">
                <path
                  d="M 300 0 L 300 12 L 150 12 L 150 28"
                  stroke={isNode2Active ? '#8B5CF6' : 'rgba(255,255,255,0.3)'}
                  strokeWidth="2.5"
                  strokeDasharray={isNode2Active ? 'none' : '4 4'}
                />
                <path
                  d="M 300 0 L 300 12 L 450 12 L 450 28"
                  stroke={isNode3Active ? '#3B82F6' : 'rgba(255,255,255,0.3)'}
                  strokeWidth="2.5"
                  strokeDasharray={isNode3Active ? 'none' : '4 4'}
                />
              </svg>
            </div>

            {/* NÓS RAMIFICADOS LATERAIS (2 COLUNAS): Prompts Validados e Vibe Coding */}
            <div style={{display: 'flex', gap: 14}}>
              {/* Ramo Esquerdo: Pack de Prompts Validados */}
              <div
                style={{
                  flex: 1,
                  transform: `scale(${isNode2Active ? node2Spring : 0.98})`,
                  opacity: isNode2Active ? Math.max(0.9, node2Spring) : 0.52,
                  backgroundColor: isNode2Active ? 'rgba(139, 92, 246, 0.22)' : 'rgba(30, 41, 59, 0.55)',
                  border: isNode2Active ? '2px solid #8B5CF6' : '1.5px solid rgba(255, 255, 255, 0.25)',
                  borderRadius: 18,
                  padding: '12px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  boxShadow: isNode2Active ? '0 6px 20px rgba(139, 92, 246, 0.35)' : 'none'
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                  <span style={{fontSize: 32}}>🎯</span>
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      backgroundColor: isNode2Active ? '#8B5CF6' : 'rgba(255,255,255,0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 22,
                      color: '#FFFFFF',
                      fontWeight: 900
                    }}
                  >
                    {isNode2Active ? '✓' : '•'}
                  </div>
                </div>
                <div style={{fontSize: 32, fontWeight: 800, color: '#C4B5FD'}}>
                  ETAPA 2
                </div>
                <div style={{fontSize: 33, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.2}}>
                  Pack de Prompts Validados
                </div>
              </div>

              {/* Ramo Direito: Treinamento Vibe Coding */}
              <div
                style={{
                  flex: 1,
                  transform: `scale(${isNode3Active ? node3Spring : 0.98})`,
                  opacity: isNode3Active ? Math.max(0.9, node3Spring) : 0.52,
                  backgroundColor: isNode3Active ? 'rgba(59, 130, 246, 0.22)' : 'rgba(30, 41, 59, 0.55)',
                  border: isNode3Active ? '2px solid #3B82F6' : '1.5px solid rgba(255, 255, 255, 0.25)',
                  borderRadius: 18,
                  padding: '12px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  boxShadow: isNode3Active ? '0 6px 20px rgba(59, 130, 246, 0.35)' : 'none'
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                  <span style={{fontSize: 32}}>💻</span>
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      backgroundColor: isNode3Active ? '#3B82F6' : 'rgba(255,255,255,0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 22,
                      color: '#FFFFFF',
                      fontWeight: 900
                    }}
                  >
                    {isNode3Active ? '✓' : '•'}
                  </div>
                </div>
                <div style={{fontSize: 32, fontWeight: 800, color: '#93C5FD'}}>
                  ETAPA 3
                </div>
                <div style={{fontSize: 33, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.2}}>
                  Treinamento Vibe Coding
                </div>
              </div>
            </div>

            {/* CONVERGÊNCIA VISUAL: Conectores SVG convergindo para a saída */}
            <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: 28}}>
              <svg width="600" height="28" viewBox="0 0 600 28" fill="none">
                <path
                  d="M 150 0 L 150 16 L 300 16 L 300 28"
                  stroke={isNode4Active ? '#10B981' : 'rgba(255,255,255,0.3)'}
                  strokeWidth="2.5"
                  strokeDasharray={isNode4Active ? 'none' : '4 4'}
                />
                <path
                  d="M 450 0 L 450 16 L 300 16 L 300 28"
                  stroke={isNode4Active ? '#10B981' : 'rgba(255,255,255,0.3)'}
                  strokeWidth="2.5"
                  strokeDasharray={isNode4Active ? 'none' : '4 4'}
                />
              </svg>
            </div>

            {/* NÓ DE CONVERGÊNCIA 4 (SAÍDA / EXECUÇÃO): Automações com IA */}
            <div
              style={{
                transform: `scale(${isNode4Active ? node4Spring * (isFase2 ? pulse : 1) : 0.98})`,
                opacity: isNode4Active ? Math.max(0.9, node4Spring) : 0.52,
                backgroundColor: isFase2 ? 'rgba(16, 185, 129, 0.24)' : 'rgba(30, 41, 59, 0.55)',
                border: isFase2 ? '2px solid #10B981' : '1.5px solid rgba(255, 255, 255, 0.25)',
                borderRadius: 18,
                padding: '12px 18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: isFase2 ? '0 8px 24px rgba(16, 185, 129, 0.45)' : 'none'
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 36}}>⚡</span>
                <div>
                  <div style={{fontSize: 32, fontWeight: 800, color: isFase2 ? '#A7F3D0' : '#94A3B8'}}>
                    RESULTADO · FLUXO ATIVO
                  </div>
                  <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Automações Próprias com IA
                  </div>
                </div>
              </div>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: isFase2 ? '#10B981' : 'rgba(255, 255, 255, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                  color: '#FFFFFF',
                  fontWeight: 900,
                  boxShadow: isFase2 ? '0 0 10px #10B981' : 'none'
                }}
              >
                {isFase2 ? '✓' : '•'}
              </div>
            </div>
          </div>

          {/* Console / Terminal de Status em Tempo Real no Rodapé do Canvas */}
          <div
            style={{
              backgroundColor: 'rgba(2, 6, 23, 0.85)',
              borderRadius: 14,
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              border: '1px solid rgba(255, 255, 255, 0.12)'
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
              <span style={{fontSize: 32, color: '#38BDF8', fontWeight: 900}}>&gt;_</span>
              <span style={{fontSize: 32, fontWeight: 700, color: '#E2E8F0'}}>
                {isFase2
                  ? 'Automações ativas e rodando com sucesso'
                  : 'Estruturando nós do mapa mental...'}
              </span>
            </div>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: isFase2 ? '#10B981' : '#3B82F6',
                boxShadow: isFase2 ? '0 0 10px #10B981' : '0 0 10px #3B82F6'
              }}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
