import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

interface Cena2Props {
  fontFamily: string;
  destaque: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo
  const bgScale = interpolate(frame, [0, 204], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 204], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Entrada do celular em 3D aos 0.2s (frame 6)
  const phoneSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Flutuação contínua 3D do celular
  const phoneRotY = interpolate(frame, [0, 204], [-7, -3]);
  const phoneRotX = interpolate(frame, [0, 204], [3, 1]);
  const phoneFloatY = Math.sin(frame * 0.08) * 6;

  // Mensagem 1 (Cliente) - entra no frame 16 (0.53s na cena, ~13.15s)
  const msg1Spring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Digitando... (Empresa) - ativo entre frame 65 e frame 92
  const isTyping = frame >= 65 && frame < 92;

  // Mensagem 2 (Empresa) - entra no frame 92 (3.06s na cena, ~15.7s)
  const msg2Spring = spring({
    frame: frame - 92,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Mensagem 3 (Cliente) - entra no frame 138 (4.6s na cena, ~17.2s)
  const msg3Spring = spring({
    frame: frame - 138,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo com zoom e escurecimento */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          filter: 'brightness(0.4) contrast(1.15)',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Degradê dark de contraste */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 30%, rgba(17, 24, 39, 0.4) 0%, rgba(10, 14, 23, 0.92) 80%)',
        }}
      />

      {/* Topo Informativo (y=165 a 290) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
        }}
      >
        {/* Badge: COMO FUNCIONA */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 24,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: `2px solid ${destaque}`,
            boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: destaque,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        {/* Título da cena */}
        <h2
          style={{
            margin: 0,
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            textWrap: 'balance',
            textShadow: '0 4px 12px rgba(0,0,0,0.8)',
          }}
        >
          Página Pronta & Vídeo Demo
        </h2>
      </div>

      {/* Mockup de Smartphone 3D (y=305 a 1270) */}
      <div
        style={{
          position: 'absolute',
          top: 305,
          left: 60,
          width: 960,
          display: 'flex',
          justifyContent: 'center',
          perspective: 1200,
        }}
      >
        <div
          style={{
            width: 860,
            height: 955,
            borderRadius: 40,
            backgroundColor: '#0F172A',
            border: '4px solid rgba(255, 255, 255, 0.16)',
            boxShadow:
              '0 30px 80px rgba(0,0,0,0.8), 0 0 30px rgba(245, 158, 11, 0.2)',
            transform: `scale(${phoneSpring}) rotateY(${phoneRotY}deg) rotateX(${phoneRotX}deg) translateY(${phoneFloatY}px)`,
            opacity: phoneSpring,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header do WhatsApp */}
          <div
            style={{
              height: 110,
              backgroundColor: '#1E293B',
              padding: '0 26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: destaque,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#111827',
                  fontWeight: 900,
                  fontSize: 32,
                }}
              >
                LP
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                  Estrutura Comercial
                </span>
                <span style={{fontSize: 32, fontWeight: 600, color: '#22C55E'}}>
                  Online agora
                </span>
              </div>
            </div>

            {/* Selo Simulação */}
            <div
              style={{
                padding: '6px 14px',
                borderRadius: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#CBD5E1',
                  textTransform: 'uppercase',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Área de Mensagens */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#0B1120',
              padding: '24px 22px',
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
              justifyContent: 'flex-start',
            }}
          >
            {/* Divisor de data e contexto no topo do chat */}
            <div
              style={{
                alignSelf: 'center',
                padding: '4px 16px',
                borderRadius: 10,
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                color: '#94A3B8',
                fontSize: 32,
                fontWeight: 600,
              }}
            >
              Hoje • Conversa comercial
            </div>

            {/* Preview da Página & Vídeo de Demonstração */}
            <div
              style={{
                alignSelf: 'center',
                width: '92%',
                padding: '12px 18px',
                borderRadius: 16,
                backgroundColor: 'rgba(245, 158, 11, 0.12)',
                border: '1.5px solid rgba(245, 158, 11, 0.35)',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 10,
                  backgroundColor: destaque,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#111827',
                  fontSize: 32,
                  fontWeight: 900,
                }}
              >
                ▶
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span style={{fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                  Vídeo de Demonstração
                </span>
                <span style={{fontSize: 32, fontWeight: 500, color: '#FCD34D'}}>
                  Apresentação comercial do produto
                </span>
              </div>
            </div>

            {/* Mensagem 1: Cliente */}
            {frame >= 16 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '84%',
                  padding: '18px 22px',
                  borderRadius: '22px 22px 22px 6px',
                  backgroundColor: '#FFFFFF',
                  color: '#0F172A',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.4)',
                  transform: `scale(${msg1Spring}) translateX(${(1 - msg1Spring) * -30}px)`,
                  opacity: msg1Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#64748B',
                    marginBottom: 4,
                  }}
                >
                  Visitante
                </div>
                <div style={{fontSize: 36, fontWeight: 700, lineHeight: 1.3}}>
                  Vi o vídeo demonstrando o produto na página.
                </div>
              </div>
            )}

            {/* Digitando... */}
            {isTyping && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  padding: '12px 22px',
                  borderRadius: '20px 20px 6px 20px',
                  backgroundColor: '#064E3B',
                  color: '#A7F3D0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span style={{fontSize: 32, fontWeight: 700}}>Digitando</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 900,
                    letterSpacing: 2,
                  }}
                >
                  ...
                </span>
              </div>
            )}

            {/* Mensagem 2: Empresa */}
            {frame >= 92 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '86%',
                  padding: '18px 22px',
                  borderRadius: '22px 22px 6px 22px',
                  backgroundColor: '#065F46',
                  border: `2px solid ${destaque}`,
                  color: '#FFFFFF',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                  transform: `scale(${msg2Spring}) translateX(${(1 - msg2Spring) * 30}px)`,
                  opacity: msg2Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: destaque,
                    marginBottom: 4,
                  }}
                >
                  Atendimento
                </div>
                <div style={{fontSize: 36, fontWeight: 700, lineHeight: 1.3}}>
                  Perfeito! A apresentação tirou todas as suas dúvidas?
                </div>
              </div>
            )}

            {/* Mensagem 3: Cliente */}
            {frame >= 138 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '86%',
                  padding: '18px 22px',
                  borderRadius: '22px 22px 22px 6px',
                  backgroundColor: '#FFFFFF',
                  border: '3px solid #22C55E',
                  color: '#0F172A',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.4)',
                  transform: `scale(${msg3Spring}) translateX(${(1 - msg3Spring) * -30}px)`,
                  opacity: msg3Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#15803D',
                    marginBottom: 4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span>✓ Decisão de compra</span>
                </div>
                <div style={{fontSize: 36, fontWeight: 800, lineHeight: 1.3}}>
                  Sim, ficou muito claro. Quero fechar agora.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
