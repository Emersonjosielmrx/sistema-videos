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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo e mais amplo (movimento >= 4%)
  const bgScale = interpolate(frame, [0, 163], [1.02, 1.25], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 163], [0, -60], {
    extrapolateRight: 'clamp',
  });

  // Gancho / Badge: entra imediatamente em 0s com 100% opacidade e pop-in rápido
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // Pergunta falada: entra imediatamente em 0s com 100% opacidade e pop-in ágil
  const titleSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Destaque em marca-texto esmeralda: presente desde o início com pop vibrante
  const highlightSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Entrada em cascata acelerada logo no 1º segundo (frames 6, 16 e 26)
  // Preenche o centro da tela imediatamente aos 1.0s retendo o scroll
  const card1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const card2Spring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const card3Spring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Destaques dinâmicos em cascata acompanhando a fala ao longo da cena (frames 50, 75, 100)
  const card1Active = frame >= 50;
  const card2Active = frame >= 75;
  const card3Active = frame >= 100;

  // Banner inferior de automação entrando aos 3.6s (frame 108) ilustrando "para ele?"
  const statusSpring = spring({
    frame: frame - 108,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Floating sutil contínuo nos cards
  const floatY = Math.sin(frame / 12) * 8;

  // Transição de saída suave
  const exitOpacity = interpolate(frame, [150, 163], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0F19', opacity: exitOpacity}}>
      {/* Imagem de fundo com zoom dinâmico */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
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
        {/* Camada de escurecimento e vinheta cinematográfica */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(16, 185, 129, 0.12) 0%, rgba(11, 15, 25, 0.88) 60%, rgba(11, 15, 25, 0.98) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo principal dentro da Safe Zone (y: 150 a 1580, x: 60 a 1020) */}
      <AbsoluteFill style={{padding: '0 60px'}}>
        {/* Gancho secundário / Selo fixo: visível desde 0s com alto contraste */}
        <div
          style={{
            position: 'absolute',
            top: 180,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: 1,
            transform: `scale(${interpolate(badgeSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 28px',
              borderRadius: 30,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid #10B981',
              boxShadow: '0 0 25px rgba(16, 185, 129, 0.4)',
            }}
          >
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#34D399',
                boxShadow: '0 0 10px #34D399',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 2,
              }}
            >
              Microtarefas acumuladas no dia?
            </span>
          </div>
        </div>

        {/* Cartão Central com a Pergunta Principal: 100% opacidade no frame 0 com pop-in ágil */}
        <div
          style={{
            position: 'absolute',
            top: 275,
            left: 60,
            right: 60,
            padding: '28px 32px',
            borderRadius: 32,
            background: 'rgba(17, 24, 39, 0.95)',
            border: '1.5px solid rgba(16, 185, 129, 0.45)',
            boxShadow:
              '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(16, 185, 129, 0.2)',
            opacity: 1,
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.2,
              textWrap: 'balance',
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            Posso transferir essas
          </div>

          {/* Destaque em marca-texto / caixa esmeralda vibrante desde o frame 0 */}
          <div
            style={{
              position: 'relative',
              margin: '14px 0',
              padding: '12px 28px',
              borderRadius: 18,
              background: '#10B981',
              boxShadow: '0 10px 30px rgba(16, 185, 129, 0.5)',
              transform: `scale(${interpolate(highlightSpring, [0, 1], [0.95, 1], {extrapolateRight: 'clamp'})}) rotate(-0.5deg)`,
            }}
          >
            <span
              style={{
                position: 'relative',
                zIndex: 2,
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#0B0F19',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              pequenas tarefas chatas
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 46,
              fontWeight: 800,
              color: '#E2E8F0',
              lineHeight: 1.2,
              textShadow: '0 4px 15px rgba(0,0,0,0.7)',
            }}
          >
            do dia a dia para ele?
          </div>
        </div>

        {/* Pilha de cards de microtarefas ilustrando a pergunta */}
        <div
          style={{
            position: 'absolute',
            top: 730,
            left: 70,
            right: 70,
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            transform: `translateY(${floatY}px)`,
          }}
        >
          {/* Card 1 */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '22px 30px',
              borderRadius: 24,
              background: card1Active ? 'rgba(17, 30, 45, 0.96)' : 'rgba(17, 24, 39, 0.94)',
              border: card1Active
                ? '2px solid #10B981'
                : '1.5px solid rgba(255, 255, 255, 0.12)',
              boxShadow: card1Active
                ? '0 15px 40px rgba(0, 0, 0, 0.7), 0 0 25px rgba(16, 185, 129, 0.35)'
                : '0 15px 35px rgba(0, 0, 0, 0.6)',
              opacity: card1Spring,
              transform: `translateX(${interpolate(card1Spring, [0, 1], [-80, 0])}px) scale(${card1Active ? 1.02 : 1.0})`,
              transition: 'transform 0.2s ease',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background: card1Active ? 'rgba(16, 185, 129, 0.35)' : 'rgba(16, 185, 129, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                }}
              >
                🔍
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Pesquisa de mercado
              </span>
            </div>
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 20,
                background: card1Active ? '#10B981' : 'rgba(16, 185, 129, 0.2)',
                border: '1px solid #10B981',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: card1Active ? '#0B0F19' : '#10B981',
                boxShadow: card1Active ? '0 0 15px rgba(16, 185, 129, 0.7)' : 'none',
              }}
            >
              Delegável ✓
            </div>
          </div>

          {/* Card 2 */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '22px 30px',
              borderRadius: 24,
              background: card2Active ? 'rgba(17, 30, 45, 0.96)' : 'rgba(17, 24, 39, 0.94)',
              border: card2Active
                ? '2px solid #10B981'
                : '1.5px solid rgba(255, 255, 255, 0.12)',
              boxShadow: card2Active
                ? '0 15px 40px rgba(0, 0, 0, 0.7), 0 0 25px rgba(16, 185, 129, 0.35)'
                : '0 15px 35px rgba(0, 0, 0, 0.6)',
              opacity: card2Spring,
              transform: `translateX(${interpolate(card2Spring, [0, 1], [80, 0])}px) scale(${card2Active ? 1.02 : 1.0})`,
              transition: 'transform 0.2s ease',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background: card2Active ? 'rgba(16, 185, 129, 0.35)' : 'rgba(16, 185, 129, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                }}
              >
                📅
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Agendamento de reuniões
              </span>
            </div>
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 20,
                background: card2Active ? '#10B981' : 'rgba(16, 185, 129, 0.2)',
                border: '1px solid #10B981',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: card2Active ? '#0B0F19' : '#10B981',
                boxShadow: card2Active ? '0 0 15px rgba(16, 185, 129, 0.7)' : 'none',
              }}
            >
              Delegável ✓
            </div>
          </div>

          {/* Card 3 */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '22px 30px',
              borderRadius: 24,
              background: card3Active ? 'rgba(17, 30, 45, 0.96)' : 'rgba(17, 24, 39, 0.94)',
              border: card3Active
                ? '2px solid #10B981'
                : '1.5px solid rgba(255, 255, 255, 0.12)',
              boxShadow: card3Active
                ? '0 15px 40px rgba(0, 0, 0, 0.7), 0 0 25px rgba(16, 185, 129, 0.35)'
                : '0 15px 35px rgba(0, 0, 0, 0.6)',
              opacity: card3Spring,
              transform: `translateX(${interpolate(card3Spring, [0, 1], [-80, 0])}px) scale(${card3Active ? 1.02 : 1.0})`,
              transition: 'transform 0.2s ease',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background: card3Active ? 'rgba(16, 185, 129, 0.35)' : 'rgba(16, 185, 129, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                }}
              >
                ✉️
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Follow-up de contatos
              </span>
            </div>
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 20,
                background: card3Active ? '#10B981' : 'rgba(16, 185, 129, 0.2)',
                border: '1px solid #10B981',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: card3Active ? '#0B0F19' : '#10B981',
                boxShadow: card3Active ? '0 0 15px rgba(16, 185, 129, 0.7)' : 'none',
              }}
            >
              Delegável ✓
            </div>
          </div>

          {/* Tag de automação entrando aos 3.6s (frame 108) completando o gancho */}
          <div
            style={{
              opacity: statusSpring,
              transform: `scale(${interpolate(statusSpring, [0, 1], [0.88, 1])}) translateY(${interpolate(statusSpring, [0, 1], [20, 0])}px)`,
              display: 'flex',
              justifyContent: 'center',
              marginTop: 6,
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 28px',
                borderRadius: 20,
                background: 'rgba(16, 185, 129, 0.18)',
                border: '1.5px solid #10B981',
                boxShadow: '0 0 25px rgba(16, 185, 129, 0.4)',
              }}
            >
              <span style={{fontSize: 26}}>⚡</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#34D399',
                  textTransform: 'uppercase',
                  letterSpacing: 1.5,
                }}
              >
                Agente IA assume tudo
              </span>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
