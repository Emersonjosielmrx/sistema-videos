import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2_ComoFunciona: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Crossfade suave
  const opacity = interpolate(frame, [0, 8, 232, 241], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Punch-in dinâmico para 1.15x na virada de bloco (quebra a repetição e jump cut)
  const videoScale = interpolate(frame, [0, 241], [1.15, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Entrada dos elementos do topo aos 0.15s
  const headerSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Sincronização rigorosa dos 3 módulos:
  // t_abs = 14.54s (rel 1.68s -> frame 50): automação full post
  const step1Spring = spring({
    frame: Math.max(0, frame - 50),
    fps,
    config: {damping: 13, stiffness: 150},
  });

  // t_abs = 16.84s (rel 3.98s -> frame 120): blog SEO
  const step2Spring = spring({
    frame: Math.max(0, frame - 120),
    fps,
    config: {damping: 13, stiffness: 150},
  });

  // t_abs = 18.84s (rel 5.98s -> frame 179): podcast
  const step3Spring = spring({
    frame: Math.max(0, frame - 179),
    fps,
    config: {damping: 13, stiffness: 150},
  });

  // Determina qual etapa da demonstração de produto está ativa
  const activeStep = frame >= 179 ? 3 : frame >= 120 ? 2 : 1;

  // Entrada do painel de demonstração aos ~1.2s (frame 36)
  const mockupEntrance = spring({
    frame: Math.max(0, frame - 36),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
        opacity,
      }}
    >
      {/* Topo Informativo Fixo (y=156 a 330) */}
      <div
        style={{
          position: 'absolute',
          top: 156,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 50,
        }}
      >
        {/* Rótulo da Etapa */}
        <div
          style={{
            transform: `scale(${headerSpring})`,
            padding: '8px 22px',
            borderRadius: 18,
            backgroundColor: 'rgba(244, 114, 182, 0.25)',
            border: '1.5px solid #F472B6',
            color: '#F472B6',
            fontSize: 32,
            fontWeight: 800,
            letterSpacing: 0.8,
            textTransform: 'uppercase',
            marginBottom: 10,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
          }}
        >
          ⚡ COMO FUNCIONA
        </div>

        {/* Título Cinético */}
        <div
          style={{
            transform: `scale(${headerSpring})`,
            fontSize: 42,
            fontWeight: 800,
            lineHeight: 1.2,
            color: '#FFFFFF',
            textAlign: 'center',
            textWrap: 'balance',
            textShadow: '0 4px 16px rgba(0,0,0,0.95)',
            marginBottom: 14,
          }}
        >
          Automação da ideia à postagem
        </div>

        {/* Stepper Tecnológico — ALTO CONTRASTE nos tópicos inativos (texto branco 85%) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            width: '100%',
          }}
        >
          {/* Módulo 1: Full Post */}
          <div
            style={{
              padding: '8px 18px',
              borderRadius: 14,
              backgroundColor:
                step1Spring > 0.05 ? '#F472B6' : 'rgba(255, 255, 255, 0.16)',
              border:
                step1Spring > 0.05
                  ? '1.5px solid #F472B6'
                  : '1.5px solid rgba(255, 255, 255, 0.35)',
              color: step1Spring > 0.05 ? '#111827' : '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow:
                step1Spring > 0.05 ? '0 4px 16px rgba(244, 114, 182, 0.55)' : 'none',
              transform: `scale(${step1Spring > 0.05 ? 1.04 : 1.0})`,
              transition: 'all 0.2s',
            }}
          >
            <span>✓</span> Full Post
          </div>

          <div
            style={{
              width: 16,
              height: 3,
              backgroundColor: step2Spring > 0.05 ? '#F472B6' : 'rgba(255,255,255,0.4)',
            }}
          />

          {/* Módulo 2: Blog SEO */}
          <div
            style={{
              padding: '8px 18px',
              borderRadius: 14,
              backgroundColor:
                step2Spring > 0.05 ? '#F472B6' : 'rgba(255, 255, 255, 0.16)',
              border:
                step2Spring > 0.05
                  ? '1.5px solid #F472B6'
                  : '1.5px solid rgba(255, 255, 255, 0.35)',
              color: step2Spring > 0.05 ? '#111827' : '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow:
                step2Spring > 0.05 ? '0 4px 16px rgba(244, 114, 182, 0.55)' : 'none',
              transform: `scale(${step2Spring > 0.05 ? 1.04 : 1.0})`,
              transition: 'all 0.2s',
            }}
          >
            <span>✓</span> Blog SEO
          </div>

          <div
            style={{
              width: 16,
              height: 3,
              backgroundColor: step3Spring > 0.05 ? '#F472B6' : 'rgba(255,255,255,0.4)',
            }}
          />

          {/* Módulo 3: Podcast */}
          <div
            style={{
              padding: '8px 18px',
              borderRadius: 14,
              backgroundColor:
                step3Spring > 0.05 ? '#F472B6' : 'rgba(255, 255, 255, 0.16)',
              border:
                step3Spring > 0.05
                  ? '1.5px solid #F472B6'
                  : '1.5px solid rgba(255, 255, 255, 0.35)',
              color: step3Spring > 0.05 ? '#111827' : '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow:
                step3Spring > 0.05 ? '0 4px 16px rgba(244, 114, 182, 0.55)' : 'none',
              transform: `scale(${step3Spring > 0.05 ? 1.04 : 1.0})`,
              transition: 'all 0.2s',
            }}
          >
            <span>✓</span> Podcast
          </div>
        </div>
      </div>

      {/* METADE SUPERIOR: Vídeo do Apresentador com Punch-In 1.15x (y=330 a 920) */}
      <div
        style={{
          position: 'absolute',
          top: 325,
          left: 60,
          right: 60,
          height: 590,
          borderRadius: 28,
          overflow: 'hidden',
          border: '1.5px solid rgba(244, 114, 182, 0.35)',
          boxShadow: '0 15px 40px rgba(0, 0, 0, 0.65)',
          zIndex: 30,
        }}
      >
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            transform: `scale(${videoScale})`,
            transformOrigin: '50% 28%',
          }}
        >
          <OffthreadVideo
            src={staticFile('dono_2.mp4')}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        </div>
      </div>

      {/* METADE INFERIOR: Demonstração Visual da Plataforma ('Show, don't tell') (y=935 a 1520) */}
      <div
        style={{
          position: 'absolute',
          top: 935,
          left: 60,
          right: 60,
          height: 580,
          borderRadius: 28,
          backgroundColor: 'rgba(17, 24, 39, 0.94)',
          border: '1.5px solid rgba(244, 114, 182, 0.4)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
          padding: '24px 28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          transform: `scale(${mockupEntrance})`,
          opacity: mockupEntrance,
          zIndex: 35,
        }}
      >
        {/* Barra de Status do Sistema da Plataforma */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            paddingBottom: 14,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: 6,
                backgroundColor: '#10B981',
                boxShadow: '0 0 10px #10B981',
              }}
            />
            <span style={{fontSize: 32, fontWeight: 800, color: '#F472B6'}}>
              Fábrica de Conteúdo
            </span>
          </div>
          <div
            style={{
              padding: '6px 14px',
              borderRadius: 12,
              backgroundColor: 'rgba(16, 185, 129, 0.18)',
              border: '1px solid #10B981',
              color: '#34D399',
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            ● AO VIVO
          </div>
        </div>

        {/* Conteúdo Dinâmico Conforme o Tópico Falado */}
        {activeStep === 1 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                ⚡ Automação Full Post
              </span>
              <span
                style={{
                  padding: '4px 12px',
                  borderRadius: 8,
                  backgroundColor: '#F472B6',
                  color: '#111827',
                  fontSize: 32,
                  fontWeight: 900,
                }}
              >
                Ideia ➔ Postagem
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                borderRadius: 18,
                padding: '18px 20px',
                border: '1px solid rgba(244, 114, 182, 0.25)',
              }}
            >
              <div style={{fontSize: 32, color: '#9CA3AF', marginBottom: 6}}>
                Multi-canais conectados:
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Post programado e publicado com arte e legenda oficial
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                fontSize: 32,
                color: '#34D399',
                fontWeight: 700,
              }}
            >
              <span>✓ Status:</span>
              <span style={{color: '#FFFFFF'}}>Tudo automatizado</span>
            </div>
          </div>
        )}

        {activeStep === 2 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                📝 Artigos para Blog com SEO
              </span>
              <span
                style={{
                  padding: '4px 12px',
                  borderRadius: 8,
                  backgroundColor: '#10B981',
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 900,
                }}
              >
                SEO 100%
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                borderRadius: 18,
                padding: '18px 20px',
                border: '1px solid rgba(16, 185, 129, 0.3)',
              }}
            >
              <div style={{fontSize: 32, color: '#9CA3AF', marginBottom: 6}}>
                Otimização para mecanismos de busca:
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Artigo completo estruturado com palavras-chave e SEO
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                fontSize: 32,
                color: '#34D399',
                fontWeight: 700,
              }}
            >
              <span>✓ Indexação:</span>
              <span style={{color: '#FFFFFF'}}>Artigo publicado no blog</span>
            </div>
          </div>
        )}

        {activeStep === 3 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                🎙️ Podcast em Áudio
              </span>
              <span
                style={{
                  padding: '4px 12px',
                  borderRadius: 8,
                  backgroundColor: '#F472B6',
                  color: '#111827',
                  fontSize: 32,
                  fontWeight: 900,
                }}
              >
                Áudio Gerado
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                borderRadius: 18,
                padding: '18px 20px',
                border: '1px solid rgba(244, 114, 182, 0.3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 10,
                }}
              >
                {[40, 75, 55, 90, 60, 85, 45, 95, 70, 80, 50, 65].map((h, idx) => (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      height: (h * (0.6 + Math.sin(frame * 0.3 + idx) * 0.35)),
                      backgroundColor: '#F472B6',
                      borderRadius: 4,
                    }}
                  />
                ))}
              </div>
              <div style={{fontSize: 32, fontWeight: 700, color: '#FFFFFF'}}>
                Áudio em formato podcast pronto para distribuição
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                fontSize: 32,
                color: '#34D399',
                fontWeight: 700,
              }}
            >
              <span>✓ Formato:</span>
              <span style={{color: '#FFFFFF'}}>Podcast completo automatizado</span>
            </div>
          </div>
        )}

        {/* Rodapé do Mockup */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            paddingTop: 12,
            fontSize: 32,
            color: '#9CA3AF',
            fontWeight: 600,
          }}
        >
          <span>Tecnologia de Automação</span>
          <span style={{color: '#F472B6', fontWeight: 800}}>Fábrica de Marketing IA</span>
        </div>
      </div>
    </div>
  );
};
