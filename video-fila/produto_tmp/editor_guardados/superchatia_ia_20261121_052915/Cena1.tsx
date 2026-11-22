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

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (> 8% variação)
  const scale = interpolate(frame, [0, 212], [1.06, 1.20], {
    extrapolateRight: 'clamp',
  });

  // Entrada do título (0.2s -> frame 6)
  const titleSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada escalonada dos cards logo no início (0.2s e 0.4s)
  const cardInstaSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const cardWhatsSpring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Sincronização da fala
  // Fala cita Instagram: 8.666s -> local frame ~101
  const isFalaInsta = frame >= 101 && frame < 125;
  // Fala cita WhatsApp: 9.447s -> local frame ~125
  const isFalaWhats = frame >= 125 && frame < 146;
  // Fala cita "ao mesmo tempo" (10.156s -> local frame 146)
  const isMesmoTempo = frame >= 146;

  // Efeito dinâmico de alternância contínua entre abas ("alternando telas", caos visual)
  // Ciclo rápido de troca a cada 18 frames com leve tremor
  const switchCycle = Math.sin((frame / 9) * Math.PI);
  const isTabSwitching = frame >= 30 && frame < 146;
  const shakeX = isTabSwitching ? Math.sin(frame * 1.6) * 3 : 0;

  // Alerta de sobrecarga aos 4.8s (frame 146, "ao mesmo tempo") com entrada suave em slide-up + overshoot
  const alertaSpring = spring({
    frame: frame - 146,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const alertaSlideY = interpolate(alertaSpring, [0, 1], [40, 0]);
  const alertaPulse = 1.0 + 0.03 * Math.sin(((frame - 146) / 12) * Math.PI * 2);

  // Transições de entrada/saída de cena
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 202, 212],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Fundo com foto em zoom e desfoque profissional */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
          filter: 'blur(16px)',
        }}
      >
        <Img
          src={staticFile('img_1.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(15,23,42,0.85) 0%, rgba(11,13,19,0.96) 100%)',
          }}
        />
      </div>

      {/* Área Segura: y=150 a y=1580, x=60 a x=1020 */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
        }}
      >
        {/* Badge "O PROBLEMA" com fundo vermelho de alerta (opacidade >= 90%) */}
        <div
          style={{
            alignSelf: 'flex-start',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 22px',
            borderRadius: 30,
            background: '#DC2626',
            boxShadow: '0 8px 24px rgba(220, 38, 38, 0.45)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>

        {/* Título de dor dramática */}
        <div
          style={{
            width: '100%',
            padding: '20px 26px',
            borderRadius: 22,
            background: 'rgba(17, 24, 39, 0.95)',
            border: '2px solid rgba(239, 68, 68, 0.35)',
            boxShadow: '0 15px 40px rgba(0, 0, 0, 0.8)',
            transform: `scale(${titleSpring})`,
            transformOrigin: 'top center',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.2,
              color: '#FFFFFF',
              textWrap: 'balance',
            }}
          >
            Alternando telas para responder clientes
          </div>
        </div>

        {/* Comparativo de Telas Divididas preenchendo o espaço vertical (y=380 a y=1200) */}
        <div
          style={{
            width: '100%',
            marginTop: 6,
            display: 'flex',
            justifyContent: 'space-between',
            gap: 20,
            transform: `translateX(${shakeX}px)`,
          }}
        >
          {/* Card Esquerdo: Instagram Direct */}
          <div
            style={{
              flex: 1,
              borderRadius: 24,
              background: 'rgba(23, 27, 44, 0.96)',
              border:
                isFalaInsta || (isTabSwitching && switchCycle > 0)
                  ? '3px solid #FF5483'
                  : '2px solid rgba(255, 84, 131, 0.3)',
              boxShadow:
                isFalaInsta || (isTabSwitching && switchCycle > 0)
                  ? '0 0 35px rgba(255, 84, 131, 0.45)'
                  : '0 12px 30px rgba(0,0,0,0.7)',
              padding: '22px 18px',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              transform: `scale(${cardInstaSpring}) scale(${
                isTabSwitching && switchCycle > 0 ? 1.025 : 1.0
              })`,
              transition: 'border 0.15s, box-shadow 0.15s, transform 0.15s',
            }}
          >
            {/* Header Instagram */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: 12,
                borderBottom: '1.5px solid rgba(255,255,255,0.1)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FF5483',
                }}
              >
                Instagram
              </span>
              <div
                style={{
                  background: '#DC2626',
                  color: '#FFFFFF',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  padding: '4px 12px',
                  borderRadius: 12,
                }}
              >
                Não lidas
              </div>
            </div>

            {/* Mensagem 1 */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.07)',
                borderRadius: 14,
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Direct de anúncio
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#F1F5F9',
                }}
              >
                Vi o anúncio e quero orçamento
              </span>
            </div>

            {/* Mensagem 2 */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 14,
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Lead sem resposta
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Aguardando retorno da equipe
              </span>
            </div>

            {/* Mensagem 3 (Preenche o terço central da tela) */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 14,
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Mensagem recente
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Cliente esperando resposta
              </span>
            </div>
          </div>

          {/* Card Direito: WhatsApp */}
          <div
            style={{
              flex: 1,
              borderRadius: 24,
              background: 'rgba(20, 32, 28, 0.96)',
              border:
                isFalaWhats || (isTabSwitching && switchCycle < 0)
                  ? '3px solid #25D366'
                  : '2px solid rgba(37, 211, 102, 0.3)',
              boxShadow:
                isFalaWhats || (isTabSwitching && switchCycle < 0)
                  ? '0 0 35px rgba(37, 211, 102, 0.45)'
                  : '0 12px 30px rgba(0,0,0,0.7)',
              padding: '22px 18px',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              transform: `scale(${cardWhatsSpring}) scale(${
                isTabSwitching && switchCycle < 0 ? 1.025 : 1.0
              })`,
              transition: 'border 0.15s, box-shadow 0.15s, transform 0.15s',
            }}
          >
            {/* Header WhatsApp */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: 12,
                borderBottom: '1.5px solid rgba(255,255,255,0.1)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#25D366',
                }}
              >
                WhatsApp
              </span>
              <div
                style={{
                  background: '#DC2626',
                  color: '#FFFFFF',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  padding: '4px 12px',
                  borderRadius: 12,
                }}
              >
                Acumuladas
              </div>
            </div>

            {/* Mensagem 1 */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.07)',
                borderRadius: 14,
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Cliente aguardando
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#F1F5F9',
                }}
              >
                Mandei mensagem aqui também
              </span>
            </div>

            {/* Mensagem 2 */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 14,
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Fila de espera
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Aguardando atendente livre
              </span>
            </div>

            {/* Mensagem 3 (Preenche o terço central da tela) */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 14,
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Conversa pendente
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Atraso na resposta manual
              </span>
            </div>
          </div>
        </div>

        {/* Alerta de perda de tempo com entrada dinâmica suave em slide-up + overshoot sincronizado */}
        {frame >= 146 && (
          <div
            style={{
              width: '100%',
              padding: '18px 24px',
              borderRadius: 20,
              background: '#991B1B',
              border: '2px solid #EF4444',
              boxShadow: `0 8px 30px rgba(239, 68, 68, 0.65), 0 0 ${15 + 10 * Math.sin((frame - 146) / 8)}px rgba(239, 68, 68, 0.4)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 14,
              transform: `translateY(${alertaSlideY}px) scale(${alertaSpring * alertaPulse})`,
              marginTop: 10,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
                textAlign: 'center',
              }}
            >
              Sobrecarga: abas separadas geram atraso
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
