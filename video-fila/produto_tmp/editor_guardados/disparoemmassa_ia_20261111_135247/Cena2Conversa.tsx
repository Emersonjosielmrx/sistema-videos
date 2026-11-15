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

type Msg = {
  de: 'cliente' | 'empresa';
  texto: string;
};

export const Cena2Conversa: React.FC<{
  fontFamily: string;
  conversa: Msg[];
}> = ({fontFamily, conversa}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Cena 2: ini = 10.43s, fim = 19.27s (duração local = 8.84s = 265 frames)
  const absT = 10.43 + frame / fps;

  // Fundo contextualizado de rotina comercial de loja (img_0.jpg com ambient blur e movimento vivo)
  const bgScale = interpolate(frame, [0, 265], [1.02, 1.10], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 265], [0, -20], {extrapolateRight: 'clamp'});

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(absT, [18.95, 19.25], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const phonePop = spring({frame: frame - 2, fps, config: {damping: 15, stiffness: 130}});
  const tiltY = interpolate(Math.sin(frame * 0.08), [-1, 1], [-2, 2]);
  const floatY = Math.cos(frame * 0.1) * 4;

  // Sincronia exata com cada trecho falado:
  // 1) "configuro mensagens personalizadas" -> 10.43s a 15.54s
  // 2) "com envio automático" -> 15.54s a 16.78s
  // 3) "e rotação de números" -> 16.78s em diante
  const isEtapa1 = absT < 15.54;
  const isEtapa2 = absT >= 15.54 && absT < 16.78;
  const isEtapa3 = absT >= 16.78;

  const step1Prog = spring({
    frame: frame - Math.round((10.9 - 10.43) * fps),
    fps,
    config: {damping: 14},
  });
  const step2Prog = spring({
    frame: frame - Math.round((15.54 - 10.43) * fps),
    fps,
    config: {damping: 14},
  });
  const step3Prog = spring({
    frame: frame - Math.round((16.78 - 10.43) * fps),
    fps,
    config: {damping: 14},
  });

  const headerStatusText = isEtapa3
    ? 'Rotação de números ativa'
    : isEtapa2
      ? 'Envio automático ativo'
      : 'Personalização ativa';

  const bottomCardPop = spring({frame: frame - 10, fps, config: {damping: 14}});

  // Mensagens do chat entrando em sincronia com o fluxo
  const msg0Pop = spring({
    frame: frame - Math.round((11.05 - 10.43) * fps),
    fps,
    config: {damping: 14},
  });
  const msg1Pop = spring({
    frame: frame - Math.round((13.75 - 10.43) * fps),
    fps,
    config: {damping: 14},
  });
  const digitando = absT >= 15.2 && absT < 16.15;
  const msg2Pop = spring({
    frame: frame - Math.round((16.15 - 10.43) * fps),
    fps,
    config: {damping: 14},
  });

  return (
    <AbsoluteFill style={{backgroundColor: ESCURO, opacity: enterOp * exitOp}}>
      {/* Fundo contextualizado de rotina comercial/loja com véu dinâmico escuro */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 15%',
            filter: 'blur(20px) brightness(0.28)',
            transform: `scale(${bgScale}) translateY(${bgY}px)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(34, 197, 94, 0.16) 0%, rgba(17, 24, 39, 0.94) 75%)',
          }}
        />
      </AbsoluteFill>

      {/* Topo dentro da Safe Zone (y=165): Rótulo "COMO FUNCIONA" + Selo Simulação */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
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
            padding: '10px 24px',
            borderRadius: 999,
            textTransform: 'uppercase',
            boxShadow: '0 8px 24px rgba(34,197,94,0.45)',
          }}
        >
          COMO FUNCIONA
        </div>
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid rgba(255,255,255,0.45)',
            color: '#FFFFFF',
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            padding: '8px 22px',
            borderRadius: 999,
          }}
        >
          Simulação
        </div>
      </div>

      {/* Abas Superiores das 3 Etapas sincronizadas dinamicamente com o áudio (y=245) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          display: 'flex',
          gap: 12,
          justifyContent: 'space-between',
          zIndex: 20,
        }}
      >
        {[
          {
            label: isEtapa1 ? '1. Personalizar' : '✓ Personalizar',
            foco: isEtapa1,
            concluido: !isEtapa1,
            prog: step1Prog,
          },
          {
            label: isEtapa3 ? '✓ Automático' : '2. Automático',
            foco: isEtapa2,
            concluido: isEtapa3,
            prog: step2Prog,
          },
          {
            label: '3. Rotação',
            foco: isEtapa3,
            concluido: false,
            prog: step3Prog,
          },
        ].map((etapa, idx) => {
          const bg = etapa.foco
            ? VERDE
            : etapa.concluido
              ? 'rgba(34, 197, 94, 0.22)'
              : 'rgba(17, 24, 39, 0.92)';
          const textCor = etapa.foco
            ? TEXTO_ESCURO
            : etapa.concluido
              ? '#86EFAC'
              : '#CBD5E1';
          const borderCor = etapa.foco
            ? VERDE
            : etapa.concluido
              ? 'rgba(34, 197, 94, 0.65)'
              : 'rgba(255, 255, 255, 0.24)';

          return (
            <div
              key={idx}
              style={{
                flex: 1,
                background: bg,
                color: textCor,
                border: `3px solid ${borderCor}`,
                borderRadius: 18,
                padding: '12px 6px',
                textAlign: 'center',
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                whiteSpace: 'nowrap',
                transform: `scale(${etapa.foco ? 1 + etapa.prog * 0.04 : 1})`,
                boxShadow: etapa.foco ? '0 10px 26px rgba(34,197,94,0.5)' : 'none',
                transition: 'background 0.3s, color 0.3s, border 0.3s',
              }}
            >
              {etapa.label}
            </div>
          );
        })}
      </div>

      {/* Frame Expandido da Simulação de WhatsApp ocupando o centro da tela (y=335..1170) */}
      <div
        style={{
          position: 'absolute',
          top: 335,
          left: 60,
          right: 60,
          perspective: 1200,
          transform: `translateY(${interpolate(phonePop, [0, 1], [40, 0]) + floatY}px)`,
          opacity: phonePop,
          zIndex: 15,
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.98)',
            border: `4px solid ${VERDE}`,
            borderRadius: 34,
            overflow: 'hidden',
            boxShadow: '0 26px 55px rgba(0,0,0,0.75)',
            transform: `rotateY(${tiltY}deg)`,
          }}
        >
          {/* Cabeçalho do Chat */}
          <div
            style={{
              background: '#075E54',
              padding: '16px 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '2px solid rgba(255,255,255,0.15)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: '50%',
                  background: VERDE,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: TEXTO_ESCURO,
                  boxShadow: '0 4px 14px rgba(0,0,0,0.3)',
                }}
              >
                IA
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  Disparo em Massa IA
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#A7F3D0',
                  }}
                >
                  {headerStatusText}
                </span>
              </div>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: TEXTO_ESCURO,
                background: VERDE,
                padding: '6px 16px',
                borderRadius: 999,
              }}
            >
              WhatsApp
            </span>
          </div>

          {/* Mensagens do Chat com balões nítidos e legibilidade impecável */}
          <div
            style={{
              padding: '22px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              background:
                'radial-gradient(circle at top right, rgba(34,197,94,0.15), rgba(15,23,42,0.98) 70%)',
            }}
          >
            {/* Mensagem 1: Empresa */}
            {absT >= 10.9 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '92%',
                  background: '#1E293B',
                  border: `2px solid ${VERDE}`,
                  borderRadius: '20px 20px 20px 6px',
                  padding: '16px 20px',
                  opacity: msg0Pop,
                  transform: `translateY(${interpolate(msg0Pop, [0, 1], [20, 0])}px)`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 33,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Olá, Mariana! Preparamos uma novidade especial para você hoje na loja.
                </div>
              </div>
            )}

            {/* Mensagem 2: Cliente */}
            {absT >= 13.75 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  background: VERDE,
                  borderRadius: '20px 20px 6px 20px',
                  padding: '16px 20px',
                  opacity: msg1Pop,
                  transform: `translateY(${interpolate(msg1Pop, [0, 1], [20, 0])}px)`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 33,
                    fontWeight: 800,
                    color: TEXTO_ESCURO,
                    lineHeight: 1.25,
                  }}
                >
                  Oi! Que ótimo, quero ver as opções disponíveis.
                </div>
              </div>
            )}

            {/* Indicador digitando... */}
            {digitando && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  background: '#1E293B',
                  border: '2px solid rgba(34,197,94,0.55)',
                  borderRadius: 18,
                  padding: '12px 22px',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#86EFAC',
                }}
              >
                digitando...
              </div>
            )}

            {/* Mensagem 3: Empresa com concordância em 1ª pessoa padronizada */}
            {absT >= 16.15 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '92%',
                  background: '#1E293B',
                  border: `2px solid ${VERDE}`,
                  borderRadius: '20px 20px 20px 6px',
                  padding: '16px 22px',
                  opacity: msg2Pop,
                  transform: `translateY(${interpolate(msg2Pop, [0, 1], [20, 0])}px)`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 33,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Vou te mostrar as opções e também vou enviar a chave Pix por aqui.
                </div>
              </div>
            )}
          </div>

          {/* Rodapé interno da simulação com status de entrega */}
          <div
            style={{
              background: '#0F172A',
              borderTop: '2px solid rgba(34,197,94,0.35)',
              padding: '14px 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#E2E8F0'}}>
              {isEtapa3
                ? '✓ Rotação de instâncias'
                : isEtapa2
                  ? '✓ Envio automático'
                  : '✓ Mensagens personalizadas'}
            </span>
            <span style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#86EFAC'}}>
              Ativo
            </span>
          </div>
        </div>

        {/* Cards flutuantes de métricas e status preenchendo a metade inferior (y=1190..1360) */}
        <div
          style={{
            marginTop: 18,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            opacity: bottomCardPop,
            transform: `translateY(${interpolate(bottomCardPop, [0, 1], [24, 0])}px)`,
          }}
        >
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.95)',
              border: `2px solid ${VERDE}`,
              borderRadius: 22,
              padding: '14px 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              boxShadow: '0 16px 36px rgba(0,0,0,0.6)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
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
              <span style={{fontFamily, fontSize: 33, fontWeight: 800, color: '#FFFFFF'}}>
                {isEtapa3
                  ? 'Alternando números da campanha'
                  : isEtapa2
                    ? 'Disparo automático em andamento'
                    : 'Personalizando nome do contato'}
              </span>
            </div>
            <span style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#86EFAC'}}>
              Operando
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
