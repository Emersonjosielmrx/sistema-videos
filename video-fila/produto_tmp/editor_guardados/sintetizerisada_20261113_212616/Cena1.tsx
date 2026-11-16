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

export const Cena1: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento Ken Burns contínuo e expressivo no fundo (garante > 4% de movimento contínuo)
  const bgScale = interpolate(frame, [0, 199], [1.02, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 199], [0, -45], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 199], [0, 35], {
    extrapolateRight: 'clamp',
  });

  // BEAT 1 (frames 0 a 105): Revelação exclusiva da dor / limitações da Recepção Convencional
  const tag1Spring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const header1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const card1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Bullets escalonados do Bloco 1 (para movimento constante ao longo de toda a cena)
  const bullet1Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const bullet2Spring = spring({
    frame: frame - 42,
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const bullet3Spring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Transição do Bloco 1 saindo por volta do frame 105 (~9.1s)
  const beat1Exit = interpolate(frame, [100, 114], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const beat1ExitY = interpolate(frame, [100, 114], [0, -40], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // BEAT 2 (frames 106 a 199): Entrada triunfal do alívio com Agenda IA
  const beat2Spring = spring({
    frame: frame - 108,
    fps,
    config: {damping: 14, stiffness: 125},
  });

  const beat2Bullet1 = spring({
    frame: frame - 120,
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const beat2Bullet2 = spring({
    frame: frame - 142,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Flutuação orgânica sutil
  const floatY = Math.sin(frame * 0.08) * 4;

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
      {/* Imagem de Fundo com Movimento Ken Burns contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translate(${bgTranslateX}px, ${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_1.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Iluminação ambiente dourada/âmbar com gradiente dinâmico */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at 50% 25%, rgba(255, 169, 77, 0.22) 0%, rgba(17, 24, 39, 0.94) 75%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.85) 0%, rgba(17, 24, 39, 0.70) 45%, rgba(17, 24, 39, 0.95) 100%)',
          }}
        />
      </div>

      {/* ============================================================== */}
      {/* BATIDA 1: O PROBLEMA DA RECEPÇÃO CONVENCIONAL (frames 0 a 114) */}
      {/* ============================================================== */}
      {frame < 116 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: beat1Exit,
            transform: `translateY(${beat1ExitY + floatY}px)`,
          }}
        >
          {/* Topo: Tag de Contexto (y ~ 175) */}
          <div
            style={{
              position: 'absolute',
              top: 175,
              left: 60,
              right: 60,
              display: 'flex',
              justifyContent: 'center',
              opacity: tag1Spring,
              transform: `scale(${Math.max(0.7, tag1Spring)})`,
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 24px',
                borderRadius: 30,
                backgroundColor: 'rgba(31, 41, 55, 0.94)',
                border: `2px solid ${CORES.marca}`,
                boxShadow: '0 8px 25px rgba(0, 0, 0, 0.5)',
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: CORES.marca,
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                O Problema
              </span>
            </div>
          </div>

          {/* Título Principal Beat 1 (y: 245 a 410) */}
          <div
            style={{
              position: 'absolute',
              top: 245,
              left: 60,
              right: 60,
              textAlign: 'center',
              opacity: header1Spring,
              transform: `translateY(${(1 - header1Spring) * 20}px)`,
            }}
          >
            <div
              style={{
                fontSize: 50,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
                textShadow: '0 4px 18px rgba(0,0,0,0.85)',
              }}
            >
              SÓ UMA RECEPÇÃO DÁ CONTA?
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 700,
                color: '#F87171',
                marginTop: 8,
              }}
            >
              O custo e as limitações do modelo tradicional
            </div>
          </div>

          {/* Card Principal: Recepção Convencional (y: 435 a 1150) */}
          <div
            style={{
              position: 'absolute',
              top: 435,
              left: 60,
              right: 60,
              opacity: card1Spring,
              transform: `translateY(${(1 - card1Spring) * 35}px)`,
              backgroundColor: 'rgba(31, 41, 55, 0.97)',
              border: '2px solid rgba(239, 68, 68, 0.8)',
              borderRadius: 30,
              padding: '36px 36px',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.75), 0 0 30px rgba(239, 68, 68, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: 22,
            }}
          >
            {/* Cabeçalho do Card com Preço Gigante em Destaque */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                paddingBottom: 20,
              }}
            >
              <span style={{fontSize: 40, fontWeight: 900, color: '#FFFFFF'}}>
                Recepção Convencional
              </span>
              <span
                style={{
                  backgroundColor: '#DC2626',
                  color: '#FFFFFF',
                  padding: '10px 22px',
                  borderRadius: 16,
                  fontSize: 34,
                  fontWeight: 900,
                  boxShadow: '0 6px 20px rgba(220, 38, 38, 0.55)',
                }}
              >
                R$ 2.500 / mês
              </span>
            </div>

            {/* Lista Escalonada de Dores (Alta Legibilidade, Branco + Ícone Vermelho) */}
            <div style={{display: 'flex', flexDirection: 'column', gap: 18, marginTop: 4}}>
              {/* Bullet 1 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  opacity: bullet1Spring,
                  transform: `translateX(${(1 - bullet1Spring) * -20}px)`,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    backgroundColor: '#DC2626',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    flexShrink: 0,
                  }}
                >
                  ✕
                </div>
                <span
                  style={{
                    fontSize: 35,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Salário fixo todo mês
                </span>
              </div>

              {/* Bullet 2 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  opacity: bullet2Spring,
                  transform: `translateX(${(1 - bullet2Spring) * -20}px)`,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    backgroundColor: '#DC2626',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    flexShrink: 0,
                  }}
                >
                  ✕
                </div>
                <span
                  style={{
                    fontSize: 35,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Atendimento limitado ao horário comercial
                </span>
              </div>

              {/* Bullet 3 (Texto 100% Branco e Alto Contraste para Celular) */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  opacity: bullet3Spring,
                  transform: `translateX(${(1 - bullet3Spring) * -20}px)`,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    backgroundColor: '#DC2626',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    flexShrink: 0,
                  }}
                >
                  ✕
                </div>
                <span
                  style={{
                    fontSize: 35,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Mensagens e clientes acumulados fora do expediente
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* BATIDA 2: O ALÍVIO COM AGENDA IA (frames 106 a 199)            */}
      {/* ============================================================== */}
      {frame >= 104 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: beat2Spring,
            transform: `translateY(${(1 - beat2Spring) * 35 + floatY}px)`,
          }}
        >
          {/* Topo: Tag de Solução (y ~ 175) */}
          <div
            style={{
              position: 'absolute',
              top: 175,
              left: 60,
              right: 60,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 24px',
                borderRadius: 30,
                backgroundColor: 'rgba(31, 41, 55, 0.94)',
                border: `2px solid #25D366`,
                boxShadow: '0 8px 25px rgba(37, 211, 102, 0.35)',
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#25D366',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                A Alternativa com IA
              </span>
            </div>
          </div>

          {/* Título Principal Beat 2 (y: 245 a 410) */}
          <div
            style={{
              position: 'absolute',
              top: 245,
              left: 60,
              right: 60,
              textAlign: 'center',
            }}
          >
            <div
              style={{
                fontSize: 50,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
                textShadow: '0 4px 18px rgba(0,0,0,0.85)',
              }}
            >
              ORGANIZAÇÃO COM AGENDA IA
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 700,
                color: CORES.marca,
                marginTop: 8,
              }}
            >
              Atendimento automático 24 horas no WhatsApp
            </div>
          </div>

          {/* Card Principal: Agenda IA 24h (y: 435 a 1150) */}
          <div
            style={{
              position: 'absolute',
              top: 435,
              left: 60,
              right: 60,
              backgroundColor: 'rgba(31, 41, 55, 0.97)',
              border: `2px solid ${CORES.marca}`,
              borderRadius: 30,
              padding: '36px 36px',
              boxShadow: `0 20px 50px rgba(0, 0, 0, 0.75), 0 0 35px rgba(255, 169, 77, 0.35)`,
              display: 'flex',
              flexDirection: 'column',
              gap: 22,
            }}
          >
            {/* Cabeçalho do Card com Preço em Destaque */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                paddingBottom: 20,
              }}
            >
              <span
                style={{
                  fontSize: 40,
                  fontWeight: 900,
                  color: CORES.marca,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                Agenda IA 24h
              </span>
              <span
                style={{
                  backgroundColor: CORES.marca,
                  color: CORES.texto_sobre_marca,
                  padding: '10px 22px',
                  borderRadius: 16,
                  fontSize: 34,
                  fontWeight: 900,
                  boxShadow: '0 6px 20px rgba(255, 169, 77, 0.5)',
                }}
              >
                A partir de R$ 199 / mês
              </span>
            </div>

            {/* Lista Escalonada de Vantagens da IA */}
            <div style={{display: 'flex', flexDirection: 'column', gap: 18, marginTop: 4}}>
              {/* Bullet 1 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  opacity: beat2Bullet1,
                  transform: `translateX(${(1 - beat2Bullet1) * -20}px)`,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    flexShrink: 0,
                    boxShadow: '0 0 12px rgba(37, 211, 102, 0.6)',
                  }}
                >
                  ✓
                </div>
                <span
                  style={{
                    fontSize: 35,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Atende, confirma e reagenda 24h no WhatsApp
                </span>
              </div>

              {/* Bullet 2 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  opacity: beat2Bullet2,
                  transform: `translateX(${(1 - beat2Bullet2) * -20}px)`,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    flexShrink: 0,
                    boxShadow: '0 0 12px rgba(37, 211, 102, 0.6)',
                  }}
                >
                  ✓
                </div>
                <span
                  style={{
                    fontSize: 35,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Sem conflito e sem duplo agendamento
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
