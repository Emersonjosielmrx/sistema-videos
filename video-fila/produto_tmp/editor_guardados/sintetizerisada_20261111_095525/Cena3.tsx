import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
  cores: {
    marca: string;
    destaque: string;
    apoio: string;
    fundo_escuro: string;
  };
};

export const Cena3: React.FC<Props> = ({fontFamily, cores}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de push-in no b-roll da barbearia
  const bgScale = interpolate(frame, [0, 176], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 176], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Topo animado
  const topAnim = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada base de cada card (escalonada no início da cena para preencher o terço central)
  const card1Base = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const card2Base = spring({
    frame: frame - 9,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const card3Base = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const progressBase = spring({
    frame: frame - 18,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Ativação dinâmica no milissegundo exato da narração
  // Item 1: "Hoje minha recepção trabalha" (~19.5s -> local frame 15)
  const item1Ativo = frame >= 15;
  const punch1 = spring({
    frame: frame - 15,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Item 2: "vinte e quatro horas" (~21.0s -> local frame 62)
  const item2Ativo = frame >= 62;
  const punch2 = spring({
    frame: frame - 62,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Item 3: "com a agenda sempre em dia" (~22.3s -> local frame 100)
  const item3Ativo = frame >= 100;
  const punch3 = spring({
    frame: frame - 100,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Progresso dinâmico sincronizado
  const gradeProgresso = interpolate(frame, [15, 62, 110], [45, 75, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento de respiração sutil nos cards
  const floatCard1 = Math.sin(frame * 0.08) * 4;
  const floatCard2 = Math.sin(frame * 0.08 + 1) * 4;
  const floatCard3 = Math.sin(frame * 0.08 + 2) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: cores.fundo_escuro,
        overflow: 'hidden',
      }}
    >
      {/* Imagem de Fundo com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(3px)',
          opacity: 0.4,
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Véu Escuro com Vinheta */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 40%, rgba(15, 23, 42, 0.75) 0%, rgba(10, 15, 28, 0.95) 100%)',
        }}
      />

      {/* Conteúdo Gráfico */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 10,
        }}
      >
        {/* Badge do Rótulo "O RESULTADO" */}
        <div
          style={{
            opacity: topAnim,
            transform: `scale(${topAnim})`,
            backgroundColor: 'rgba(31, 41, 55, 0.95)',
            border: `2px solid ${cores.destaque}`,
            borderRadius: 24,
            padding: '6px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: `0 4px 16px rgba(0,0,0,0.6), 0 0 12px rgba(255, 169, 77, 0.3)`,
            marginBottom: 12,
          }}
        >
          <span style={{fontSize: 34}}>🚀</span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: cores.destaque,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Título Principal */}
        <div
          style={{
            opacity: topAnim,
            transform: `translateY(${interpolate(topAnim, [0, 1], [20, 0])}px)`,
            fontSize: 50,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.15,
            textShadow: '0 3px 12px rgba(0,0,0,0.85)',
            marginBottom: 34,
          }}
        >
          Recepção Ativa 24 Horas
        </div>

        {/* Grade de 3 Cards de Benefícios / Resultados (Sempre presentes, sincronizados com a narração) */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* Card 1: Recepção 24h */}
          <div
            style={{
              opacity: card1Base * (item1Ativo ? 1 : 0.6),
              transform: `translateX(${interpolate(card1Base, [0, 1], [-40, 0])}px) translateY(${floatCard1}px) scale(${item1Ativo ? interpolate(punch1, [0, 1], [0.96, 1]) : 0.98})`,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: item1Ativo
                ? '2px solid #22C55E'
                : '2px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 22,
              padding: '18px 26px',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              boxShadow: item1Ativo
                ? '0 8px 30px rgba(0,0,0,0.6), 0 0 20px rgba(34, 197, 94, 0.25)'
                : '0 8px 30px rgba(0,0,0,0.6)',
            }}
          >
            <div
              style={{
                width: 68,
                height: 68,
                borderRadius: 18,
                backgroundColor: item1Ativo
                  ? 'rgba(34, 197, 94, 0.25)'
                  : 'rgba(255, 255, 255, 0.08)',
                border: item1Ativo
                  ? '2px solid #22C55E'
                  : '1.5px solid rgba(255, 255, 255, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 36,
                flexShrink: 0,
              }}
            >
              🟢
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  fontSize: 38,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Recepção Automática 24/7
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 500,
                  color: item1Ativo ? '#D1D5DB' : '#9CA3AF',
                  marginTop: 4,
                }}
              >
                Atendimento ativo dia e noite
              </div>
            </div>
            <div
              style={{
                backgroundColor: item1Ativo ? '#22C55E' : 'rgba(255,255,255,0.15)',
                color: item1Ativo ? '#0F172A' : '#E5E7EB',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 14px',
                borderRadius: 12,
                textTransform: 'uppercase',
              }}
            >
              24h
            </div>
          </div>

          {/* Card 2: Zero Duplo Agendamento */}
          <div
            style={{
              opacity: card2Base * (item2Ativo ? 1 : 0.55),
              transform: `translateX(${interpolate(card2Base, [0, 1], [40, 0])}px) translateY(${floatCard2}px) scale(${item2Ativo ? interpolate(punch2, [0, 1], [0.96, 1]) : 0.98})`,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: item2Ativo
                ? `2px solid ${cores.destaque}`
                : '2px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 22,
              padding: '18px 26px',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              boxShadow: item2Ativo
                ? `0 8px 30px rgba(0,0,0,0.6), 0 0 25px rgba(255, 169, 77, 0.3)`
                : '0 8px 30px rgba(0,0,0,0.6)',
            }}
          >
            <div
              style={{
                width: 68,
                height: 68,
                borderRadius: 18,
                backgroundColor: item2Ativo
                  ? 'rgba(255, 169, 77, 0.25)'
                  : 'rgba(255, 255, 255, 0.08)',
                border: item2Ativo
                  ? `2px solid ${cores.destaque}`
                  : '1.5px solid rgba(255, 255, 255, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 36,
                flexShrink: 0,
              }}
            >
              ⚡
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  fontSize: 38,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Zero Conflito de Horários
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 500,
                  color: item2Ativo ? '#D1D5DB' : '#9CA3AF',
                  marginTop: 4,
                }}
              >
                Sem duplo agendamento na grade
              </div>
            </div>
            <div
              style={{
                backgroundColor: item2Ativo ? cores.destaque : 'rgba(255,255,255,0.15)',
                color: item2Ativo ? cores.apoio : '#E5E7EB',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 14px',
                borderRadius: 12,
                textTransform: 'uppercase',
              }}
            >
              IA
            </div>
          </div>

          {/* Card 3: Agenda Sempre em Dia */}
          <div
            style={{
              opacity: card3Base * (item3Ativo ? 1 : 0.55),
              transform: `translateX(${interpolate(card3Base, [0, 1], [-40, 0])}px) translateY(${floatCard3}px) scale(${item3Ativo ? interpolate(punch3, [0, 1], [0.96, 1]) : 0.98})`,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: item3Ativo
                ? '2px solid #3B82F6'
                : '2px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 22,
              padding: '18px 26px',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              boxShadow: item3Ativo
                ? '0 8px 30px rgba(0,0,0,0.6), 0 0 25px rgba(59, 130, 246, 0.3)'
                : '0 8px 30px rgba(0,0,0,0.6)',
            }}
          >
            <div
              style={{
                width: 68,
                height: 68,
                borderRadius: 18,
                backgroundColor: item3Ativo
                  ? 'rgba(59, 130, 246, 0.25)'
                  : 'rgba(255, 255, 255, 0.08)',
                border: item3Ativo
                  ? '2px solid #3B82F6'
                  : '1.5px solid rgba(255, 255, 255, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 36,
                flexShrink: 0,
              }}
            >
              📅
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  fontSize: 38,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Agenda Sempre em Dia
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 500,
                  color: item3Ativo ? '#D1D5DB' : '#9CA3AF',
                  marginTop: 4,
                }}
              >
                Reagendamentos no WhatsApp
              </div>
            </div>
            <div
              style={{
                backgroundColor: item3Ativo ? '#3B82F6' : 'rgba(255,255,255,0.15)',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 14px',
                borderRadius: 12,
                textTransform: 'uppercase',
              }}
            >
              100%
            </div>
          </div>

          {/* Barra de Ocupação da Grade */}
          <div
            style={{
              opacity: progressBase,
              transform: `translateY(${interpolate(progressBase, [0, 1], [20, 0])}px)`,
              backgroundColor: 'rgba(17, 24, 39, 0.88)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 20,
              padding: '16px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#E5E7EB',
                }}
              >
                Grade Otimizada
              </span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: cores.destaque,
                }}
              >
                {Math.round(gradeProgresso)}%
              </span>
            </div>
            <div
              style={{
                width: '100%',
                height: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: 6,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${gradeProgresso}%`,
                  height: '100%',
                  backgroundColor: cores.destaque,
                  borderRadius: 6,
                  boxShadow: `0 0 12px ${cores.destaque}`,
                }}
              />
            </div>
          </div>
              <div
                style={{
                  width: '100%',
                  height: 12,
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: 6,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${interpolate(progressAnim, [0, 1], [65, 100])}%`,
                    height: '100%',
                    backgroundColor: cores.destaque,
                    borderRadius: 6,
                    boxShadow: `0 0 12px ${cores.destaque}`,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
