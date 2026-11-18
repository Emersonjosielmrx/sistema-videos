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
import {BotIcon, CheckIcon} from './Icons';

interface Cena2Props {
  fontFamily: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena 2: 11.86s a 18.92s = 7.06s (212 frames a 30 fps)
  // Transição dinâmica de entrada: conectando a Cena 1 à Cena 2 com scale-in/spring suave
  // e slide lateral ágil (eliminando o corte seco / hard cut)
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.65, stiffness: 125},
  });
  const enterScale = interpolate(enterSpring, [0, 1], [0.85, 1.0]);
  const enterSlideX = interpolate(enterSpring, [0, 1], [70, 0]);
  const enterOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Zoom contínuo e pan sutil no fundo: 1.00 -> 1.12
  const bgScale = interpolate(frame, [0, 212], [1.0, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 212], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Movimento 3D contínuo do smartphone (rotateY sutil de 8deg para 1deg)
  const phoneRotateY = interpolate(frame, [0, 212], [8, 1], {
    extrapolateRight: 'clamp',
  });
  const phoneFloatY = Math.sin((frame / 30) * Math.PI * 1.5) * 6;

  // Rótulo "Como funciona": entra no frame 0
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 130},
  });

  // Título entra aos ~0.15s (frame 5)
  const titleSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, mass: 0.7, stiffness: 125},
  });

  // Balão 1 (Empresa / Notificação Bot Sentinela): entra aos ~0.6s (frame 18)
  const b1Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 125},
  });

  // Balão 2 (Cliente): entra aos ~2.8s (frame 84)
  const b2Spring = spring({
    frame: frame - 84,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 125},
  });

  // Balão 3 (Empresa / Monitoramento): entra aos ~4.5s (frame 135)
  const b3Spring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 125},
  });

  // Pulso sutil no indicador de status ativo
  const livePulse = interpolate(
    Math.sin((frame / 30) * Math.PI * 4),
    [-1, 1],
    [0.85, 1.15]
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0B1120',
        opacity: enterOpacity,
      }}
    >
      {/* Fundo com img_2.jpg com zoom dinâmico e grafismos de servidores e linhas de conexão */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.3) contrast(1.15)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(14, 165, 233, 0.25) 0%, rgba(11, 17, 32, 0.96) 75%)',
          }}
        />
        {/* Linhas tech de background com grid cibernético */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(14, 165, 233, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.08) 1px, transparent 1px)',
            backgroundSize: '50px 50px',
            opacity: 0.6,
          }}
        />

        {/* Linhas verticais de conexão luminosa de servidores ancorando o espaço */}
        <div
          style={{
            position: 'absolute',
            left: '15%',
            top: 0,
            bottom: 0,
            width: 1,
            background:
              'linear-gradient(to bottom, transparent, rgba(14, 165, 233, 0.4), transparent)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            right: '15%',
            top: 0,
            bottom: 0,
            width: 1,
            background:
              'linear-gradient(to bottom, transparent, rgba(14, 165, 233, 0.4), transparent)',
          }}
        />
      </AbsoluteFill>

      {/* Topo dentro da Safe Zone (y 165 a 330) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 50,
        }}
      >
        {/* Rótulo de contexto oficial do briefing */}
        <div
          style={{
            transform: `scale(${Math.max(0, badgeSpring)})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 24,
            backgroundColor: 'rgba(14, 165, 233, 0.22)',
            border: '2px solid #0EA5E9',
            boxShadow: '0 0 20px rgba(14, 165, 233, 0.45)',
            backdropFilter: 'blur(8px)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: 7,
              backgroundColor: '#10B981',
              boxShadow: '0 0 10px #10B981',
              transform: `scale(${livePulse})`,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#38BDF8',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA
          </span>
        </div>

        {/* Título de Destaque da Solução */}
        {frame >= 5 && (
          <div
            style={{
              marginTop: 14,
              textAlign: 'center',
              transform: `scale(${titleSpring})`,
              opacity: titleSpring,
            }}
          >
            <div
              style={{
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textTransform: 'uppercase',
                textShadow: '0 4px 15px rgba(0,0,0,0.85)',
              }}
            >
              BOT SENTINELA{' '}
              <span
                style={{
                  color: '#FFFFFF',
                  backgroundColor: '#0284C7',
                  padding: '3px 14px',
                  borderRadius: 12,
                  boxShadow: '0 0 20px rgba(14, 165, 233, 0.5)',
                }}
              >
                ATIVO
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Mockup Realista de Smartphone Vertical preenchendo elegantemente o Centro Focal (y = 340 a 1300)
          com transição de entrada suave em scale-in e leve slide lateral */}
      <div
        style={{
          position: 'absolute',
          top: 340,
          left: 70,
          right: 70,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 40,
          transform: `translateX(${enterSlideX}px) translateY(${phoneFloatY}px) scale(${enterScale})`,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: 880,
            height: 940,
            borderRadius: 48,
            backgroundColor: '#0B132B',
            border: '4px solid rgba(14, 165, 233, 0.65)',
            boxShadow:
              '0 30px 80px rgba(0, 0, 0, 0.85), 0 0 45px rgba(14, 165, 233, 0.35)',
            padding: '24px 28px',
            transform: `rotateY(${phoneRotateY}deg)`,
            transformOrigin: 'center center',
            fontFamily,
            display: 'flex',
            flexDirection: 'column',
            boxSizing: 'border-box',
          }}
        >
          {/* Notch / Speaker bar superior do celular */}
          <div
            style={{
              alignSelf: 'center',
              width: 150,
              height: 6,
              borderRadius: 3,
              backgroundColor: 'rgba(255, 255, 255, 0.25)',
              marginBottom: 16,
            }}
          />

          {/* Header da conversa */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255, 255, 255, 0.12)',
              paddingBottom: 16,
              marginBottom: 16,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 28,
                  backgroundColor: 'rgba(14, 165, 233, 0.25)',
                  border: '2px solid #0EA5E9',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 15px rgba(14, 165, 233, 0.5)',
                }}
              >
                <BotIcon size={34} color="#38BDF8" />
              </div>
              <div>
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  Bot Sentinela
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#34D399',
                      backgroundColor: 'rgba(16, 185, 129, 0.2)',
                      padding: '2px 10px',
                      borderRadius: 10,
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                    }}
                  >
                    ● Online
                  </span>
                </div>
                <div style={{fontSize: 32, color: '#94A3B8', fontWeight: 600}}>
                  Monitoramento Ativo
                </div>
              </div>
            </div>

            {/* Selo Simulação Obrigatório (font 32px, bold, alto contraste) */}
            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                border: '1.5px solid rgba(255, 255, 255, 0.3)',
                padding: '6px 14px',
                borderRadius: 12,
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 900,
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              Simulação
            </div>
          </div>

          {/* Selo de Notificação do Sistema: Alto contraste clareando a cor da fonte e corpo confortável */}
          <div
            style={{
              alignSelf: 'center',
              backgroundColor: 'rgba(14, 165, 233, 0.22)',
              border: '1.5px solid #0EA5E9',
              boxShadow: '0 0 16px rgba(14, 165, 233, 0.35)',
              padding: '8px 22px',
              borderRadius: 16,
              marginBottom: 16,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{fontSize: 26}}>🔒</span>
            <span style={{color: '#F8FAFC', fontSize: 34, fontWeight: 800}}>
              Servidor conectado ao Bot Sentinela
            </span>
          </div>

          {/* Lista de Mensagens dinâmicas */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
              justifyContent: 'flex-start',
              flex: 1,
            }}
          >
            {/* Balão 1 - Empresa (Notificação oficial sem repetição de "Alerta") */}
            {frame >= 18 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '92%',
                  backgroundColor: 'rgba(30, 41, 59, 0.95)',
                  border: '2px solid rgba(14, 165, 233, 0.6)',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '16px 22px',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.4)',
                  transform: `translateY(${(1 - b1Spring) * 30}px) scale(${0.92 + b1Spring * 0.08})`,
                  opacity: b1Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#38BDF8',
                    marginBottom: 6,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span>⚡ NOTIFICAÇÃO DO SISTEMA</span>
                </div>
                <div
                  style={{
                    fontSize: 36,
                    fontWeight: 700,
                    color: '#F8FAFC',
                    lineHeight: 1.35,
                  }}
                >
                  Alerta: o Bot Sentinela detectou uma falha no fluxo de automação.
                </div>
              </div>
            )}

            {/* Indicador de Digitação: Cliente digitando (entre frame 30 e 84) com 3 pontos exatos */}
            {frame >= 30 && frame < 84 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(3, 105, 161, 0.45)',
                  border: '1.5px solid rgba(14, 165, 233, 0.5)',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '12px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span style={{color: '#BAE6FD', fontSize: 32, fontWeight: 700}}>
                  Cliente digitando...
                </span>
              </div>
            )}

            {/* Balão 2 - Cliente (Resposta imediata) */}
            {frame >= 84 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '90%',
                  backgroundColor: '#0284C7',
                  border: '1.5px solid rgba(255, 255, 255, 0.25)',
                  borderRadius: '24px 24px 6px 24px',
                  padding: '16px 22px',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.4)',
                  transform: `translateY(${(1 - b2Spring) * 30}px) scale(${0.92 + b2Spring * 0.08})`,
                  opacity: b2Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 36,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.35,
                  }}
                >
                  Obrigado pelo aviso, já estamos corrigindo o processo.
                </div>
              </div>
            )}

            {/* Indicador de Digitação: Bot Sentinela digitando (entre frame 92 e 135) com 3 pontos exatos */}
            {frame >= 92 && frame < 135 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  backgroundColor: 'rgba(6, 78, 59, 0.92)',
                  border: '2px solid #34D399',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '12px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  boxShadow: '0 6px 20px rgba(16, 185, 129, 0.35)',
                }}
              >
                <BotIcon size={28} color="#34D399" />
                <span style={{color: '#FFFFFF', fontSize: 32, fontWeight: 800}}>
                  Bot Sentinela digitando...
                </span>
              </div>
            )}

            {/* Balão 3 - Empresa (Confirmação de Segurança) */}
            {frame >= 135 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '92%',
                  backgroundColor: 'rgba(16, 185, 129, 0.22)',
                  border: '2px solid #10B981',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '16px 22px',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.4)',
                  transform: `translateY(${(1 - b3Spring) * 30}px) scale(${0.92 + b3Spring * 0.08})`,
                  opacity: b3Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#34D399',
                    marginBottom: 6,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <CheckIcon size={28} color="#34D399" />
                  <span>STATUS: OPERAÇÃO ESTÁVEL</span>
                </div>
                <div
                  style={{
                    fontSize: 36,
                    fontWeight: 700,
                    color: '#ECFDF5',
                    lineHeight: 1.35,
                  }}
                >
                  Servidor seguro, estável e sob monitoramento constante.
                </div>
              </div>
            )}
          </div>

          {/* Barra de Input realista na base do celular */}
          <div
            style={{
              marginTop: 'auto',
              marginBottom: 8,
              padding: '14px 20px',
              borderRadius: 24,
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              border: '1.5px solid rgba(255, 255, 255, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{fontSize: 32, color: '#64748B', fontWeight: 600}}>
              Mensagem...
            </span>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 19,
                backgroundColor: '#0EA5E9',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                fontSize: 22,
                fontWeight: 900,
              }}
            >
              ➤
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
