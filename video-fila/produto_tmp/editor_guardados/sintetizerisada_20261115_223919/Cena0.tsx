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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Slow zoom em toda a composição da cena 0 (1.00 -> 1.05) com aceleração direcional (zoom-in 1.15) no final para conexão fluida com a Cena 1
  const compScale = interpolate(
    frame,
    [0, 125, 141],
    [1.0, 1.05, 1.15],
    {extrapolateRight: 'clamp'}
  );

  // Movimento de câmera contínuo adicional no fundo
  const bgScale = interpolate(frame, [0, 141], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });

  // Entrada imediata no frame 0 (~0.0s) para eliminar vazio escuro nos primeiros 2s
  const heroSpring = spring({
    frame,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Linha 2 ("À NOITE...") ganha ênfase extra quando falada (~1.2s = frame 36)
  const l2Pop = spring({
    frame: Math.max(0, frame - 34),
    fps,
    config: {damping: 11, mass: 0.65},
  });

  // Linha 4 ("RESOLVENDO?") está visível desde o início e ganha destaque extra aos 2.8s (frame 84) até o fim da cena
  const l4Emphasis = spring({
    frame: Math.max(0, frame - 82),
    fps,
    config: {damping: 10, mass: 0.6},
  });

  // Haptic feedback (vibração/pulso) no card do WhatsApp ao surgir e ao longo da cena
  const hapticShake =
    frame < 28
      ? Math.sin(frame * 2.2) * interpolate(frame, [0, 28], [7, 0], {extrapolateRight: 'clamp'})
      : Math.sin(frame / 5) * 2.5;
  const cardPulse = 1 + Math.sin(frame / 7) * 0.018;
  const flutuacao = Math.sin(frame / 9) * 6;
  const pulsoAlerta = 1 + Math.sin(frame / 6) * 0.032;

  // Segunda mensagem simulada entrando aos 2.1s (frame 63) para manter movimento contínuo entre q02 e q03
  const msg2Spring = spring({
    frame: Math.max(0, frame - 48),
    fps,
    config: {damping: 13, mass: 0.75},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
      }}
    >
      {/* Composição inteira com slow zoom 1.0 -> 1.06 */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${compScale})`,
          transformOrigin: 'center center',
        }}
      >
        {/* Imagem de Fundo com zoom contínuo */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            transform: `scale(${bgScale})`,
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
          {/* Camada de escurecimento e ambiência com brilho quente central */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'radial-gradient(circle at 50% 42%, rgba(255, 169, 77, 0.24) 0%, rgba(17, 24, 39, 0.78) 55%, rgba(10, 14, 26, 0.94) 100%)',
            }}
          />
        </div>

        {/* Selo Topo (Zona y=170) — Visível já no segundo 0.0 */}
        <div
          style={{
            position: 'absolute',
            top: 170,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `translateY(${interpolate(heroSpring, [0, 1], [-16, 0])}px)`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 99,
              backgroundColor: 'rgba(31, 41, 55, 0.92)',
              border: '1.5px solid rgba(255, 169, 77, 0.55)',
              boxShadow: '0 6px 22px rgba(0, 0, 0, 0.45)',
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#FFA94D',
                boxShadow: '0 0 10px #FFA94D',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFA94D',
                letterSpacing: 1.4,
                textTransform: 'uppercase',
              }}
            >
              Agenda IA • Para Consultórios e Clínicas
            </span>
          </div>
        </div>

        {/* Bloco Central de Pergunta Completa desde 0.0s (y=255 a 660) — Mantido até o fim da Cena 0 */}
        <div
          style={{
            position: 'absolute',
            top: 255,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
            textAlign: 'center',
            transform: `translateY(${interpolate(heroSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          {/* Linha 1 */}
          <div
            style={{
              fontFamily,
              fontSize: 56,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.12,
              textTransform: 'uppercase',
              letterSpacing: 1,
              textShadow: '0 4px 18px rgba(0,0,0,0.85)',
            }}
          >
            Cliente desmarca
          </div>

          {/* Linha 2 - Destaque Âmbar */}
          <div
            style={{
              transform: `scale(${1 + l2Pop * 0.05})`,
            }}
          >
            <div
              style={{
                display: 'inline-block',
                padding: '6px 28px',
                borderRadius: 18,
                backgroundColor: '#FFA94D',
                boxShadow: '0 6px 24px rgba(255, 169, 77, 0.45)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 62,
                  fontWeight: 900,
                  color: '#1F2937',
                  lineHeight: 1.1,
                  textTransform: 'uppercase',
                  letterSpacing: 1.2,
                }}
              >
                À noite...
              </span>
            </div>
          </div>

          {/* Linha 3 */}
          <div
            style={{
              fontFamily,
              fontSize: 50,
              fontWeight: 800,
              color: '#F3F4F6',
              lineHeight: 1.15,
              textTransform: 'uppercase',
              letterSpacing: 0.8,
              textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            }}
          >
            e você perde a manhã
          </div>

          {/* Linha 4 - Clímax da Pergunta SEMPRE VISÍVEL até a transição para a Cena 1 */}
          <div
            style={{
              transform: `scale(${pulsoAlerta + l4Emphasis * 0.06})`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 74,
                fontWeight: 900,
                color: '#FFA94D',
                lineHeight: 1.08,
                textTransform: 'uppercase',
                letterSpacing: 2,
                textShadow:
                  '0 0 28px rgba(255, 169, 77, 0.7), 0 4px 20px rgba(0,0,0,0.95)',
              }}
            >
              Resolvendo?
            </span>
          </div>
        </div>

        {/* Mockup de Smartphone / Notificação Noturna em Destaque Central desde 0.0s (y=690 a 1210) */}
        <div
          style={{
            position: 'absolute',
            top: 695,
            left: 70,
            right: 70,
            transform: `translateY(${interpolate(heroSpring, [0, 1], [35, flutuacao])}px) translateX(${hapticShake}px) scale(${cardPulse})`,
          }}
        >
          <div
            style={{
              padding: '22px 28px',
              borderRadius: 28,
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '2px solid rgba(255, 169, 77, 0.65)',
              boxShadow:
                '0 18px 45px rgba(0, 0, 0, 0.75), 0 0 30px rgba(255, 169, 77, 0.22)',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            {/* Barra de status do Mockup de Celular */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: 10,
                borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: '50%',
                    backgroundColor: '#EF4444',
                    boxShadow: '0 0 12px #EF4444',
                  }}
                />
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#F9FAFB',
                    textTransform: 'uppercase',
                  }}
                >
                  WhatsApp • 22:45
                </span>
              </div>
              <div
                style={{
                  padding: '4px 16px',
                  borderRadius: 99,
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid #F87171',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FCA5A5',
                  }}
                >
                  Aviso Noturno
                </span>
              </div>
            </div>

            {/* Balão 1 de Mensagem Noturna */}
            <div
              style={{
                padding: '16px 22px',
                borderRadius: '20px 20px 20px 6px',
                backgroundColor: '#1F2937',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                "Boa noite! Surgiu um imprevisto e não vou conseguir ir amanhã cedo..."
              </span>
            </div>

            {/* Balão 2 / Status dinâmico entrando para manter movimento vivo até o fim da cena */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 20px',
                borderRadius: 18,
                backgroundColor: 'rgba(255, 169, 77, 0.14)',
                border: '1.5px solid rgba(255, 169, 77, 0.45)',
                opacity: interpolate(msg2Spring, [0, 1], [0.85, 1]),
                transform: `translateX(${interpolate(msg2Spring, [0, 1], [-18, 0])}px)`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FFA94D',
                }}
              >
                Horário vago na manhã seguinte
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#E5E7EB',
                }}
              >
                Simulação
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
