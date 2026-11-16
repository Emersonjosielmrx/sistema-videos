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

export const Cena2: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de fundo com pan
  const bgScale = interpolate(frame, [0, 270], [1.02, 1.10], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 270], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Molas da cena
  const tagSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const headerSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const phoneSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 16, stiffness: 110},
  });

  // Balões cronometrados com a narração
  // Balão 1 (Cliente): frame 16 (~0.53s)
  const b1Spring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 15, stiffness: 130},
  });

  // Digitando 1: do frame 52 ao frame 80
  const digitando1 = frame >= 52 && frame < 80;

  // Balão 2 (Empresa): frame 80 (~2.67s)
  const b2Spring = spring({
    frame: frame - 80,
    fps,
    config: {damping: 15, stiffness: 130},
  });

  // Balão 3 (Cliente): frame 130 (~4.33s)
  const b3Spring = spring({
    frame: frame - 130,
    fps,
    config: {damping: 15, stiffness: 130},
  });

  // Digitando 2: do frame 148 ao frame 172
  const digitando2 = frame >= 148 && frame < 172;

  // Balão 4 (Empresa): frame 172 (~5.73s)
  const b4Spring = spring({
    frame: frame - 172,
    fps,
    config: {damping: 15, stiffness: 130},
  });

  // Flutuação leve e perspectiva 3D do celular
  const phoneFloatY = Math.sin(frame * 0.06) * 5;
  const phoneRotateY = -7 + Math.sin(frame * 0.04) * 2;
  const phoneRotateX = 3 + Math.cos(frame * 0.05) * 1.5;

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
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(8px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 30%, rgba(37, 211, 102, 0.12) 0%, rgba(17, 24, 39, 0.92) 80%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.88) 0%, rgba(17, 24, 39, 0.78) 40%, rgba(17, 24, 39, 0.96) 100%)',
          }}
        />
      </div>

      {/* Topo: Tags de Contexto (y ~ 178) */}
      <div
        style={{
          position: 'absolute',
          top: 178,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          opacity: tagSpring,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 22px',
            borderRadius: 24,
            backgroundColor: 'rgba(31, 41, 55, 0.94)',
            border: `2px solid ${CORES.marca}`,
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.4)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: CORES.marca,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        {/* Selo Simulação Obrigatório */}
        <div
          style={{
            padding: '8px 20px',
            borderRadius: 20,
            backgroundColor: 'rgba(17, 24, 39, 0.88)',
            border: '1px solid rgba(255, 255, 255, 0.25)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 700,
              color: '#9CA3AF',
              textTransform: 'uppercase',
            }}
          >
            Simulação Real
          </span>
        </div>
      </div>

      {/* Título Principal (y: 250 a 390) */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 60,
          right: 60,
          textAlign: 'center',
          opacity: headerSpring,
          transform: `translateY(${(1 - headerSpring) * 20}px)`,
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
          }}
        >
          AGENDAMENTO AUTOMÁTICO 24H
        </div>
        <div
          style={{
            fontSize: 33,
            fontWeight: 700,
            color: CORES.marca,
            marginTop: 8,
          }}
        >
          Confirmações e reagendamentos no WhatsApp
        </div>
      </div>

      {/* Mockup de Celular 3D Realista com Moldura de Smartphone (y: 418 a 1288, largura 860px) */}
      <div
        style={{
          position: 'absolute',
          top: 418,
          left: 110,
          width: 860,
          height: 870,
          opacity: phoneSpring,
          transform: `perspective(1100px) rotateY(${phoneRotateY}deg) rotateX(${phoneRotateX}deg) translateY(${
            (1 - phoneSpring) * 50 + phoneFloatY
          }px)`,
          borderRadius: 48,
          backgroundColor: '#0B141A',
          border: '5px solid #374151',
          outline: '2px solid rgba(255, 255, 255, 0.1)',
          boxShadow:
            '0 0 35px rgba(37, 211, 102, 0.22), 0 25px 65px rgba(0, 0, 0, 0.9), inset 0 0 20px rgba(0, 0, 0, 0.8)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        {/* Dynamic Island / Entalhe Superior de Smartphone */}
        <div
          style={{
            position: 'absolute',
            top: 10,
            left: '50%',
            transform: 'translateX(-50%)',
            width: 140,
            height: 22,
            borderRadius: 12,
            backgroundColor: '#000000',
            zIndex: 30,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingRight: 14,
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#1E293B',
            }}
          />
        </div>

        {/* Header do WhatsApp */}
        <div
          style={{
            backgroundColor: '#202C33',
            padding: '22px 24px 14px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #2A3942',
            position: 'relative',
            zIndex: 20,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                backgroundColor: CORES.marca,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#111827',
                fontSize: 28,
                fontWeight: 900,
              }}
            >
              IA
            </div>
            <div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                Agenda IA
                <span style={{color: '#25D366', fontSize: 24}}>✓</span>
              </div>
              <div style={{fontSize: 26, color: '#25D366', fontWeight: 600}}>
                online 24 horas
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: 'rgba(37, 211, 102, 0.15)',
              padding: '6px 14px',
              borderRadius: 12,
              border: '1px solid rgba(37, 211, 102, 0.3)',
              color: '#25D366',
              fontSize: 26,
              fontWeight: 700,
            }}
          >
            WhatsApp Business
          </div>
        </div>

        {/* Corpo do Chat com Mensagens */}
        <div
          style={{
            flex: 1,
            padding: '20px 22px',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
            justifyContent: 'flex-start',
            backgroundColor: '#0B141A',
          }}
        >
          {/* Balão 1: Cliente com Alto Contraste (#FFFFFF) */}
          {frame >= 16 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '82%',
                backgroundColor: '#202C33',
                padding: '14px 18px',
                borderRadius: '18px 18px 18px 4px',
                opacity: b1Spring,
                transform: `translateX(${(1 - b1Spring) * -30}px)`,
                boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div
                style={{
                  fontSize: 33,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.28,
                }}
              >
                Olá, consigo remarcar meu corte de hoje para amanhã?
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: '#9CA3AF',
                  textAlign: 'right',
                  marginTop: 4,
                }}
              >
                10:14
              </div>
            </div>
          )}

          {/* Digitando 1 */}
          {digitando1 && (
            <div
              style={{
                alignSelf: 'flex-end',
                backgroundColor: '#005C4B',
                padding: '12px 20px',
                borderRadius: '18px 18px 4px 18px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span style={{fontSize: 28, color: '#E9EDEF', fontWeight: 600}}>
                Agenda IA digitando...
              </span>
            </div>
          )}

          {/* Balão 2: Empresa (Agenda IA) */}
          {frame >= 80 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '84%',
                backgroundColor: '#005C4B',
                padding: '14px 18px',
                borderRadius: '18px 18px 4px 18px',
                opacity: b2Spring,
                transform: `translateX(${(1 - b2Spring) * 30}px)`,
                boxShadow: '0 4px 14px rgba(0,0,0,0.45)',
                border: '1px solid rgba(255, 169, 77, 0.35)',
              }}
            >
              <div
                style={{
                  fontSize: 33,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.28,
                }}
              >
                Olá! Tenho às 14h ou 16h amanhã. Qual prefere?
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: '#A7F3D0',
                  textAlign: 'right',
                  marginTop: 4,
                }}
              >
                10:14 ✓✓
              </div>
            </div>
          )}

          {/* Balão 3: Cliente com Alto Contraste (#FFFFFF) */}
          {frame >= 130 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '82%',
                backgroundColor: '#202C33',
                padding: '14px 18px',
                borderRadius: '18px 18px 18px 4px',
                opacity: b3Spring,
                transform: `translateX(${(1 - b3Spring) * -30}px)`,
                boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div
                style={{
                  fontSize: 33,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.28,
                }}
              >
                Pode ser às 14h.
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: '#9CA3AF',
                  textAlign: 'right',
                  marginTop: 4,
                }}
              >
                10:15
              </div>
            </div>
          )}

          {/* Digitando 2 */}
          {digitando2 && (
            <div
              style={{
                alignSelf: 'flex-end',
                backgroundColor: '#005C4B',
                padding: '12px 20px',
                borderRadius: '18px 18px 4px 18px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span style={{fontSize: 28, color: '#E9EDEF', fontWeight: 600}}>
                Confirmando horário...
              </span>
            </div>
          )}

          {/* Balão 4: Empresa (Confirmação sem conflito) */}
          {frame >= 172 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '88%',
                backgroundColor: '#005C4B',
                padding: '14px 18px',
                borderRadius: '18px 18px 4px 18px',
                opacity: b4Spring,
                transform: `translateX(${(1 - b4Spring) * 30}px)`,
                boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
                border: `2px solid ${CORES.marca}`,
              }}
            >
              <div
                style={{
                  display: 'inline-block',
                  backgroundColor: CORES.marca,
                  color: '#111827',
                  padding: '3px 12px',
                  borderRadius: 8,
                  fontSize: 26,
                  fontWeight: 900,
                  marginBottom: 6,
                }}
              >
                ✓ REAGENDADO COM SUCESSO
              </div>
              <div
                style={{
                  fontSize: 33,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.28,
                }}
              >
                Perfeito! Horário reagendado para amanhã às 14h, sem conflito.
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: '#A7F3D0',
                  textAlign: 'right',
                  marginTop: 4,
                }}
              >
                10:15 ✓✓
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
