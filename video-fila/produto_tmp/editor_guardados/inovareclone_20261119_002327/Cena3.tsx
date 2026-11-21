import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no vídeo do dono
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const entryOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [235, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Tag do HUD Superior
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Sub-fases da fala:
  // Fase 1 (frames 0 a 110): Hoje meu avatar posta todo dia nas redes
  const fase1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Fase 2 (frames 110 a 190): e eu não preciso montar cenário
  const fase2Spring = spring({
    frame: frame - 110,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fase 3 (frames 190 a 245): Sigo cuidando do negócio
  const fase3Spring = spring({
    frame: frame - 190,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const subFase = frame < 110 ? 1 : frame < 190 ? 2 : 3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: CORES.fundoEscuro,
        opacity: entryOpacity * exitOpacity,
        fontFamily,
      }}
    >
      {/* Vídeo do dono com push-in suave */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Sombra sutil no topo (y=0 a 380) para contraste do HUD */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.75) 0%, rgba(15, 23, 42, 0.4) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* HUD SUPERIOR: FAIXA RESTRITA y=165 a 420 (Rosto do dono protegido) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Tag da Etapa: 03 • O RESULTADO */}
        <div
          style={{
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `scale(${badgeSpring})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.88)',
            border: '1.5px solid #10B981',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#10B981',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            03 • O Resultado
          </span>
        </div>

        {/* Card Dinâmico no Topo */}
        <div
          style={{
            marginTop: 14,
            width: '100%',
            maxWidth: 920,
            backgroundColor: 'rgba(15, 23, 42, 0.88)',
            backdropFilter: 'blur(10px)',
            borderRadius: 20,
            padding: '16px 24px',
            border: '1.5px solid rgba(16, 185, 129, 0.4)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 10,
            minHeight: 145,
            justifyContent: 'center',
          }}
        >
          {subFase === 1 && (
            // Fase 1: Postando todo dia nas redes
            <div
              style={{
                opacity: interpolate(fase1Spring, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(fase1Spring, [0, 1], [15, 0])}px)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                width: '100%',
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  textAlign: 'center',
                  letterSpacing: '-0.5px',
                }}
              >
                Postando Todo Dia nas Redes
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: 12,
                  justifyContent: 'center',
                  flexWrap: 'wrap',
                }}
              >
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 14px',
                    borderRadius: 10,
                    backgroundColor: 'rgba(16, 185, 129, 0.25)',
                    border: '1px solid #10B981',
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#6EE7B7',
                  }}
                >
                  <span>📱</span>
                  <span>Conteúdo Ativo</span>
                </div>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 14px',
                    borderRadius: 10,
                    backgroundColor: 'rgba(139, 92, 246, 0.25)',
                    border: '1px solid #8B5CF6',
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#C4B5FD',
                  }}
                >
                  <span>🔥</span>
                  <span>Presença Diária</span>
                </div>
              </div>
            </div>
          )}

          {subFase === 2 && (
            // Fase 2: Sem precisar montar cenário
            <div
              style={{
                opacity: interpolate(fase2Spring, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(fase2Spring, [0, 1], [15, 0])}px)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                width: '100%',
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#6EE7B7',
                  textTransform: 'uppercase',
                  textAlign: 'center',
                  letterSpacing: '-0.5px',
                }}
              >
                Zero Montagem de Cenário
              </div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '4px 16px',
                  borderRadius: 10,
                  backgroundColor: 'rgba(16, 185, 129, 0.3)',
                  border: '1px solid #10B981',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                }}
              >
                <span>⚡</span>
                <span>Produção Automática</span>
              </div>
            </div>
          )}

          {subFase === 3 && (
            // Fase 3: Sigo cuidando do negócio
            <div
              style={{
                opacity: interpolate(fase3Spring, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(fase3Spring, [0, 1], [15, 0])}px)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                width: '100%',
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#C4B5FD',
                  textTransform: 'uppercase',
                  textAlign: 'center',
                  letterSpacing: '-0.5px',
                }}
              >
                Foco Total no Negócio
              </div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '4px 16px',
                  borderRadius: 10,
                  backgroundColor: 'rgba(139, 92, 246, 0.35)',
                  border: '1px solid #8B5CF6',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                }}
              >
                <span>💼</span>
                <span>Tempo Livre Para Crescer</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
