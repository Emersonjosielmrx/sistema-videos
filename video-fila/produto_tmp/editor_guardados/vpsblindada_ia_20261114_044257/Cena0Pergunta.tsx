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
};

export const Cena0Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo
  const bgScale = interpolate(frame, [0, 150], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 150], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Gancho: Badge entra rápido aos 0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Linha 1: "SEU NEGÓCIO FICA" entra aos ~0.32s (frame 10)
  const line1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Linha 2 (DOR FORTE): "DESPROTEGIDO?" entra aos ~1.33s (frame 40) com impacto
  const line2Spring = spring({
    frame: frame - 40,
    fps,
    config: {damping: 10, stiffness: 160},
  });

  // Linha 3: "SE O SERVIDOR CAIR HOJE" entra aos ~2.28s (frame 68)
  const line3Spring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Card do servidor entra aos 0.8s (frame 24)
  const cardSpring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 14, stiffness: 90},
  });

  // Linha de laser escaneando o rack continuamente
  const scanY = interpolate(frame % 75, [0, 75], [0, 520]);

  // Alerta de vulnerabilidade ativado após frame 40 ("desprotegido")
  const alertActive = frame >= 40;
  const alertPulse = Math.sin(frame * 0.25) * 0.5 + 0.5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
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
        {/* Grid cibernético e vinheta */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(14, 165, 233, 0.18) 0%, rgba(15, 23, 42, 0.75) 60%, rgba(15, 23, 42, 0.95) 100%)',
          }}
        />
      </div>

      {/* Partículas sutis no fundo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          opacity: 0.4,
          background:
            'radial-gradient(circle at 20% 40%, rgba(14, 165, 233, 0.15) 0%, transparent 40%), radial-gradient(circle at 80% 60%, rgba(2, 132, 199, 0.15) 0%, transparent 40%)',
        }}
      />

      {/* ================= TOPO INFORMATIVO (y: 170 a 460) ================= */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        {/* Badge do Gancho */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `scale(${badgeSpring})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.85)',
            border: '2px solid rgba(14, 165, 233, 0.6)',
            boxShadow: '0 4px 20px rgba(14, 165, 233, 0.25)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#0EA5E9',
              boxShadow: '0 0 10px #0EA5E9',
            }}
          />
          <span
            style={{
              color: '#38BDF8',
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            PERGUNTA CRUCIAL
          </span>
        </div>

        {/* Título Cinético Sincronizado */}
        <div
          style={{
            marginTop: 22,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 10,
          }}
        >
          {/* Linha 1: "SEU NEGÓCIO FICA" */}
          <div
            style={{
              opacity: line1Spring,
              transform: `translateY(${(1 - line1Spring) * 20}px)`,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -0.5,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            SEU NEGÓCIO FICA
          </div>

          {/* Linha 2: "DESPROTEGIDO?" em destaque */}
          <div
            style={{
              opacity: line2Spring,
              transform: `scale(${interpolate(line2Spring, [0, 1], [0.8, 1])})`,
              display: 'inline-block',
              padding: '6px 28px',
              borderRadius: 16,
              background: alertActive
                ? `rgba(239, 68, 68, ${0.85 + alertPulse * 0.15})`
                : 'rgba(239, 68, 68, 0.85)',
              border: '2px solid #F87171',
              boxShadow: alertActive
                ? `0 0 ${20 + alertPulse * 20}px rgba(239, 68, 68, 0.6)`
                : '0 6px 24px rgba(239, 68, 68, 0.4)',
            }}
          >
            <span
              style={{
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
              }}
            >
              DESPROTEGIDO?
            </span>
          </div>

          {/* Linha 3: "SE O SERVIDOR CAIR HOJE" */}
          <div
            style={{
              opacity: line3Spring,
              transform: `translateY(${(1 - line3Spring) * 15}px)`,
              fontSize: 42,
              fontWeight: 800,
              color: '#38BDF8',
              letterSpacing: 0.5,
              textShadow: '0 2px 10px rgba(0,0,0,0.8)',
            }}
          >
            SE O SERVIDOR CAIR HOJE
          </div>
        </div>
      </div>

      {/* ================= CENTRO FOCAL (y: 500 a 1150) ================= */}
      {/* Dashboard Card de Infraestrutura & Servidor */}
      <div
        style={{
          position: 'absolute',
          top: 500,
          left: 70,
          right: 70,
          height: 620,
          opacity: cardSpring,
          transform: `translateY(${(1 - cardSpring) * 50}px)`,
          borderRadius: 32,
          background: 'rgba(15, 23, 42, 0.92)',
          border: alertActive
            ? '2px solid rgba(239, 68, 68, 0.6)'
            : '2px solid rgba(14, 165, 233, 0.4)',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 15,
        }}
      >
        {/* Linha de Scanner Contínuo */}
        <div
          style={{
            position: 'absolute',
            top: scanY,
            left: 0,
            right: 0,
            height: 3,
            background:
              'linear-gradient(90deg, transparent 0%, rgba(56, 189, 248, 0.8) 50%, transparent 100%)',
            boxShadow: '0 0 12px rgba(56, 189, 248, 0.9)',
            pointerEvents: 'none',
          }}
        />

        {/* Topo do Card / Header do Servidor */}
        <div
          style={{
            padding: '20px 28px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'rgba(30, 41, 59, 0.6)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                backgroundColor: alertActive ? '#EF4444' : '#10B981',
                boxShadow: alertActive
                  ? `0 0 ${12 + alertPulse * 8}px #EF4444`
                  : '0 0 10px #10B981',
              }}
            />
            <span
              style={{
                color: '#F8FAFC',
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 0.5,
              }}
            >
              SERVIDOR DE PRODUÇÃO
            </span>
          </div>

          <span
            style={{
              padding: '6px 16px',
              borderRadius: 12,
              background: alertActive
                ? 'rgba(239, 68, 68, 0.2)'
                : 'rgba(16, 185, 129, 0.2)',
              color: alertActive ? '#FCA5A5' : '#6EE7B7',
              fontSize: 32,
              fontWeight: 700,
            }}
          >
            {alertActive ? 'VULNERÁVEL' : 'ONLINE'}
          </span>
        </div>

        {/* Corpo do Card com 3 Métricas Visuais */}
        <div
          style={{
            padding: '22px 28px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            flex: 1,
            justifyContent: 'space-between',
          }}
        >
          {/* Módulo 1: Aplicações & Automações */}
          <div
            style={{
              padding: '16px 22px',
              borderRadius: 18,
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{color: '#94A3B8', fontSize: 32, fontWeight: 600}}>
                SISTEMAS & SITES
              </div>
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 36,
                  fontWeight: 800,
                  marginTop: 4,
                }}
              >
                Automações Críticas
              </div>
            </div>
            <div
              style={{
                color: '#38BDF8',
                fontSize: 34,
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>●</span> Ativo
            </div>
          </div>

          {/* Módulo 2: Status do Backup (Muda com o Alerta) */}
          <div
            style={{
              padding: '16px 22px',
              borderRadius: 18,
              background: alertActive
                ? 'rgba(239, 68, 68, 0.18)'
                : 'rgba(30, 41, 59, 0.6)',
              border: alertActive
                ? '2px solid rgba(239, 68, 68, 0.5)'
                : '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              transition: 'all 0.3s ease',
            }}
          >
            <div>
              <div
                style={{
                  color: alertActive ? '#FCA5A5' : '#94A3B8',
                  fontSize: 32,
                  fontWeight: 600,
                }}
              >
                CÓPIA DE SEGURANÇA
              </div>
              <div
                style={{
                  color: alertActive ? '#FEF2F2' : '#FFFFFF',
                  fontSize: 36,
                  fontWeight: 800,
                  marginTop: 4,
                }}
              >
                {alertActive ? 'Sem Backup Configurado' : 'Aguardando Verificação'}
              </div>
            </div>
            <div
              style={{
                color: alertActive ? '#EF4444' : '#E2E8F0',
                fontSize: 34,
                fontWeight: 800,
              }}
            >
              {alertActive ? '⚠️ RISCO' : '—'}
            </div>
          </div>

          {/* Módulo 3: Alertas e Monitoramento */}
          <div
            style={{
              padding: '16px 22px',
              borderRadius: 18,
              background: alertActive
                ? 'rgba(239, 68, 68, 0.15)'
                : 'rgba(30, 41, 59, 0.6)',
              border: alertActive
                ? '2px solid rgba(239, 68, 68, 0.4)'
                : '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div
                style={{
                  color: alertActive ? '#FCA5A5' : '#94A3B8',
                  fontSize: 32,
                  fontWeight: 600,
                }}
              >
                SISTEMA DE ALERTA
              </div>
              <div
                style={{
                  color: alertActive ? '#FEF2F2' : '#FFFFFF',
                  fontSize: 36,
                  fontWeight: 800,
                  marginTop: 4,
                }}
              >
                {alertActive ? 'Nenhum Robô Vigiando' : 'Monitoramento Desligado'}
              </div>
            </div>
            <div
              style={{
                color: alertActive ? '#F87171' : '#94A3B8',
                fontSize: 34,
                fontWeight: 800,
              }}
            >
              {alertActive ? 'SEM VIGIA' : 'AUSENTE'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
