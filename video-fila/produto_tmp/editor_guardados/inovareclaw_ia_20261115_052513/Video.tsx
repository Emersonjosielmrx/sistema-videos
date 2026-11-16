import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

const CORES = {
  marca: '#7C3AED',
  marcaClara: '#A78BFA',
  marcaForte: '#6D28D9',
  apoio: '#111827',
  fundoEscuro: '#0B0F19',
  verde: '#10B981',
  vermelho: '#EF4444',
  amber: '#F59E0B',
  branco: '#FFFFFF',
  cinzaClaro: '#E2E8F0',
};

const PALAVRAS: PalavraK[] = [
  // Cena 0
  {p: 'Perdendo', ini: 0.318, fim: 0.787},
  {p: 'horas', ini: 0.799, fim: 1.075},
  {p: 'do', ini: 1.087, fim: 1.219},
  {p: 'dia', ini: 1.232, fim: 1.484, quebraApos: true},
  {p: 'com', ini: 1.496, fim: 1.664},
  {p: 'tarefas', ini: 1.676, fim: 2.121},
  {p: 'repetitivas', ini: 2.133, fim: 2.818, quebraLinha: true},
  {p: 'na', ini: 2.83, fim: 2.914},
  {p: 'empresa?', ini: 2.926, fim: 3.491, quebraApos: true},

  // Cena 1
  {p: 'Eu', ini: 4.904, fim: 5.414, quebraAntes: true},
  {p: 'perdia', ini: 5.414, fim: 5.934},
  {p: 'horas', ini: 5.934, fim: 6.444, quebraLinha: true},
  {p: 'do', ini: 6.444, fim: 6.954},
  {p: 'meu', ini: 6.954, fim: 7.474},
  {p: 'expediente', ini: 7.474, fim: 7.984, quebraApos: true},
  {p: 'fazendo', ini: 7.984, fim: 8.494},
  {p: 'tarefas', ini: 8.494, fim: 9.004, quebraLinha: true},
  {p: 'repetitivas', ini: 9.004, fim: 9.524, quebraApos: true},
  {p: 'que', ini: 9.524, fim: 10.034},
  {p: 'travavam', ini: 10.034, fim: 10.544, quebraLinha: true},
  {p: 'o', ini: 10.544, fim: 11.064},
  {p: 'meu', ini: 11.064, fim: 11.574},
  {p: 'dia.', ini: 11.574, fim: 12.084, quebraApos: true},

  // Cena 2
  {p: 'Você', ini: 12.93, fim: 13.17, quebraAntes: true},
  {p: 'delega', ini: 13.182, fim: 13.543, quebraLinha: true},
  {p: 'essas', ini: 13.555, fim: 13.759},
  {p: 'rotinas', ini: 13.771, fim: 14.3, quebraApos: true},
  {p: 'para', ini: 14.312, fim: 14.493},
  {p: 'o', ini: 14.505, fim: 14.541},
  {p: 'Inovare', ini: 14.553, fim: 14.961, quebraLinha: true},
  {p: 'Claw', ini: 14.973, fim: 15.334, quebraApos: true},
  {p: 'e', ini: 15.418, fim: 15.526},
  {p: 'esse', ini: 15.538, fim: 15.719},
  {p: 'agente', ini: 15.731, fim: 16.139, quebraLinha: true},
  {p: 'de', ini: 16.151, fim: 16.223},
  {p: 'inteligência', ini: 16.235, fim: 16.848},
  {p: 'artificial', ini: 16.86, fim: 17.461, quebraApos: true},
  {p: 'executa', ini: 17.473, fim: 17.966},
  {p: 'as', ini: 17.978, fim: 18.062},
  {p: 'tarefas', ini: 18.074, fim: 18.507, quebraLinha: true},
  {p: 'sozinho.', ini: 18.519, fim: 19.024, quebraApos: true},

  // Cena 3
  {p: 'Hoje', ini: 20.269, fim: 20.719, quebraAntes: true},
  {p: 'meu', ini: 20.719, fim: 21.169},
  {p: 'agente', ini: 21.169, fim: 21.619, quebraLinha: true},
  {p: 'trabalha', ini: 21.619, fim: 22.069},
  {p: 'sozinho', ini: 22.069, fim: 22.509},
  {p: 'nessas', ini: 22.509, fim: 22.959},
  {p: 'rotinas', ini: 22.959, fim: 23.409, quebraApos: true},
  {p: 'e', ini: 23.409, fim: 23.859},
  {p: 'eu', ini: 23.859, fim: 24.309},
  {p: 'foco', ini: 24.309, fim: 24.759},
  {p: 'no', ini: 24.759, fim: 25.209},
  {p: 'que', ini: 25.209, fim: 25.659},
  {p: 'importa', ini: 25.659, fim: 26.109, quebraLinha: true},
  {p: 'para', ini: 26.109, fim: 26.559},
  {p: 'a', ini: 26.559, fim: 26.999},
  {p: 'empresa.', ini: 26.999, fim: 27.449, quebraApos: true},
];

// ============================================================================
// CENA 0 — PERGUNTA (0.00s a 4.95s)
// Composição: Foto viva em recorte dinâmico + Texto Cinético + Cards de Rotina
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const bgZoom = interpolate(frame, [0, 148], [1.0, 1.16], {extrapolateRight: 'clamp'});
  const bgPanX = interpolate(frame, [0, 148], [0, -35], {extrapolateRight: 'clamp'});

  const saida = interpolate(t, [4.6, 4.92], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const sGancho = spring({frame: frame - 1, fps, config: {damping: 12, stiffness: 180}});
  const sL1 = spring({frame: frame - 1, fps, config: {damping: 12, stiffness: 170}});
  const sL2 = spring({frame: frame - Math.round(0.45 * fps), fps, config: {damping: 12, stiffness: 170}});
  const sL3 = spring({frame: frame - Math.round(0.9 * fps), fps, config: {damping: 12, stiffness: 170}});

  const floatY = Math.sin(frame * 0.14) * 10;
  const ponteiroAngulo = frame * 12;

  const tarefas = [
    {titulo: 'Acompanhamento diário manual', sub: 'Rotina repetitiva • Pendente', delay: 0.12},
    {titulo: 'Atualização de etapas do dia', sub: 'Travando o expediente • Manual', delay: 0.48},
    {titulo: 'Execução de tarefas operacionais', sub: 'Tomando horas da empresa', delay: 0.85},
  ];

  return (
    <AbsoluteFill style={{opacity: saida, backgroundColor: CORES.fundoEscuro}}>
      {/* Fundo vivo em movimento contínuo com textura de vídeo em movimento + grade dinâmica */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgZoom}) translateX(${bgPanX}px)`,
          }}
        />
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.35,
            mixBlendMode: 'screen',
            transform: `scale(${1.22 - (bgZoom - 1) * 0.8}) translateX(${-bgPanX * 1.4}px) rotate(${frame * 0.08}deg)`,
          }}
        />
        {/* Malha tecnológica e linhas de pulso em movimento contínuo para preencher o fundo */}
        <div
          style={{
            position: 'absolute',
            inset: -120,
            backgroundImage:
              'linear-gradient(rgba(167,139,250,0.16) 2px, transparent 2px), linear-gradient(90deg, rgba(167,139,250,0.16) 2px, transparent 2px)',
            backgroundSize: '90px 90px',
            transform: `translateY(${(frame * 2.5) % 90}px) translateX(${(frame * -1.6) % 90}px)`,
          }}
        />
        {/* Orbes luminosos e grade de automação em movimento forte (>4% diff entre 20% e 80%) */}
        <div
          style={{
            position: 'absolute',
            width: 820,
            height: 820,
            borderRadius: 999,
            background:
              'radial-gradient(circle, rgba(124,58,237,0.55) 0%, rgba(239,68,68,0.22) 45%, rgba(11,15,25,0) 72%)',
            left: interpolate(frame, [0, 148], [-160, 340]),
            top: interpolate(frame, [0, 148], [320, 740]),
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: 700,
            height: 700,
            borderRadius: 999,
            background:
              'radial-gradient(circle, rgba(245,158,11,0.38) 0%, rgba(124,58,237,0.20) 50%, rgba(11,15,25,0) 75%)',
            right: interpolate(frame, [0, 148], [-180, 260]),
            bottom: interpolate(frame, [0, 148], [180, 560]),
          }}
        />
      </AbsoluteFill>

      {/* ZONA TOPO (y=168..540): Gancho + Pergunta Cinética sempre legível (contraste 100%) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          gap: 16,
        }}
      >
        {/* Pílula do gancho_tela */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 14,
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            border: `2.5px solid ${CORES.amber}`,
            borderRadius: 999,
            padding: '10px 26px',
            transform: `scale(${sGancho}) translateY(${(1 - sGancho) * -20}px)`,
            boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
          }}
        >
          {/* Relógio animado girando */}
          <svg width="34" height="34" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15" fill="none" stroke={CORES.amber} strokeWidth="3.5" />
            <line
              x1="18"
              y1="18"
              x2={18 + 9 * Math.sin((ponteiroAngulo * Math.PI) / 180)}
              y2={18 - 9 * Math.cos((ponteiroAngulo * Math.PI) / 180)}
              stroke="#FFFFFF"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
          <span
            style={{
              fontFamily,
              fontSize: 33,
              fontWeight: 800,
              color: '#FDE68A',
              letterSpacing: 0.4,
              textTransform: 'uppercase',
            }}
          >
            Rotinas chatas da empresa
          </span>
        </div>

        {/* Título Principal = Fala exata da pergunta (peso visual alto e contraste forte nas palavras de dor) */}
        <div
          style={{
            backgroundColor: 'rgba(11, 15, 25, 0.96)',
            borderRadius: 28,
            padding: '26px 30px',
            width: '100%',
            border: '3px solid rgba(239, 68, 68, 0.65)',
            boxShadow: '0 22px 48px rgba(0,0,0,0.75)',
            transform: `translateY(${floatY * 0.4}px)`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: CORES.branco,
              lineHeight: 1.2,
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 12,
              transform: `translateY(${(1 - sL1) * 16}px)`,
            }}
          >
            <span
              style={{
                backgroundColor: CORES.vermelho,
                border: '2px solid #FCA5A5',
                color: '#FFFFFF',
                padding: '2px 16px',
                borderRadius: 14,
                boxShadow: '0 6px 20px rgba(239, 68, 68, 0.55)',
              }}
            >
              Perdendo horas
            </span>
            <span style={{color: '#FDE68A'}}>do dia</span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: CORES.branco,
              lineHeight: 1.2,
              marginTop: 10,
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span>com</span>
            <span
              style={{
                backgroundColor: CORES.marca,
                border: '2px solid #DDD6FE',
                color: '#FFFFFF',
                padding: '2px 18px',
                borderRadius: 14,
                display: 'inline-block',
                transform: `scale(${0.96 + sL2 * 0.06})`,
                boxShadow: '0 8px 24px rgba(124, 58, 237, 0.7)',
              }}
            >
              tarefas repetitivas
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              color: '#FDE68A',
              lineHeight: 1.18,
              marginTop: 10,
              transform: `scale(${0.98 + sL3 * 0.04})`,
              transformOrigin: 'left center',
            }}
          >
            na empresa?
          </div>
        </div>
      </div>

      {/* Painel Central (y=615..1290): Fila de Tarefas Repetitivas distribuída com respiro vertical */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 615,
          display: 'flex',
          flexDirection: 'column',
          gap: 28,
        }}
      >
        {tarefas.map((item, idx) => {
          const sCard = spring({
            frame: frame - Math.round(item.delay * fps),
            fps,
            config: {damping: 13, stiffness: 150},
          });
          if (sCard <= 0.01) return null;
          const pulse = Math.sin((frame + idx * 14) * 0.16) * 5;
          const barraProg = interpolate((frame + idx * 25) % 90, [0, 90], [22, 78]);
          return (
            <div
              key={idx}
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                borderLeft: `10px solid ${CORES.vermelho}`,
                borderRadius: 24,
                padding: '24px 28px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                transform: `translateY(${(1 - sCard) * 45 + pulse}px) scale(${0.92 + sCard * 0.08})`,
                opacity: sCard,
                boxShadow: '0 14px 32px rgba(0,0,0,0.6)',
                border: '2px solid rgba(239, 68, 68, 0.5)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    {item.titulo}
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#FCA5A5',
                    }}
                  >
                    {item.sub}
                  </span>
                </div>
                <div
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.25)',
                    border: '2px solid #EF4444',
                    borderRadius: 14,
                    padding: '8px 18px',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FCA5A5',
                    whiteSpace: 'nowrap',
                  }}
                >
                  MANUAL
                </div>
              </div>
              {/* Barra de progresso travada/lenta animada */}
              <div
                style={{
                  width: '100%',
                  height: 10,
                  backgroundColor: 'rgba(255,255,255,0.12)',
                  borderRadius: 999,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${barraProg}%`,
                    height: '100%',
                    backgroundColor: CORES.vermelho,
                    borderRadius: 999,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1 — DONO: O PROBLEMA (4.60s a 12.79s)
// Composição (h): Vídeo dono_1.mp4 em tela cheia + HUD superior sincronizado
// ============================================================================
const Cena1DonoProblema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // frame 0 desta Sequence = 4.60s absoluto
  const tAbs = 4.6 + frame / fps;

  const entrada = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const saida = interpolate(tAbs, [12.44, 12.78], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento contínuo na câmera do dono + corte punch-in sutil (zoom de 11%) na metade da fala (8.49s)
  const punchIn1 = tAbs >= 8.48 ? 0.11 : 0;
  const zoomVideo = interpolate(frame, [0, 245], [1.0, 1.05], {extrapolateRight: 'clamp'}) + punchIn1;
  const panY = interpolate(frame, [0, 245], [58, 72], {extrapolateRight: 'clamp'});

  // Etapas sincronizadas com a fala do dono:
  // 4.90s: "Eu perdia horas do meu expediente"
  // 8.49s: "fazendo tarefas repetitivas"
  // 10.03s: "que travavam o meu dia"
  const fase = tAbs < 8.35 ? 0 : tAbs < 9.95 ? 1 : 2;

  const sTopo = spring({frame: frame - 6, fps, config: {damping: 14, stiffness: 150}});
  const sFase1 = spring({
    frame: Math.max(0, Math.round((tAbs - 8.35) * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });
  const sFase2 = spring({
    frame: Math.max(0, Math.round((tAbs - 9.95) * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  const floatCard = Math.sin(frame * 0.1) * 5;

  return (
    <AbsoluteFill style={{opacity: entrada * saida, backgroundColor: '#000'}}>
      {/* Vídeo do dono em tela cheia — SEM overlay escuro sobre o rosto */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoomVideo}) translateY(${panY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Gradiente sutil APENAS no topo (y=0..430) para proteger leitura do HUD sem tocar no rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 430,
          background:
            'linear-gradient(180deg, rgba(11,15,25,0.78) 0%, rgba(11,15,25,0.40) 68%, rgba(11,15,25,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* HUD COMPACTO NO TOPO (y=154..355, garantindo >40px de respiro acima da cabeça do dono) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          transform: `translateY(${(1 - sTopo) * -30 + floatCard}px)`,
          opacity: sTopo,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        {/* Linha 1: Rótulo "O problema" + Indicador de fase */}
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid #EF4444',
              borderRadius: 999,
              padding: '8px 24px',
              boxShadow: '0 8px 20px rgba(0,0,0,0.45)',
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 999,
                backgroundColor: '#EF4444',
                transform: `scale(${1 + Math.sin(frame * 0.25) * 0.25})`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FCA5A5',
                textTransform: 'uppercase',
                letterSpacing: 0.6,
              }}
            >
              O problema
            </span>
          </div>

          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.90)',
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: 999,
              padding: '8px 22px',
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#E2E8F0',
            }}
          >
            Rotina manual
          </div>
        </div>

        {/* Card Único Dinâmico do Topo que evolui com a fala */}
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.93)',
            borderRadius: 22,
            padding: '12px 22px',
            borderLeft: `8px solid ${fase === 2 ? '#EF4444' : CORES.marca}`,
            border: '2px solid rgba(255,255,255,0.16)',
            boxShadow: '0 14px 30px rgba(0,0,0,0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
          }}
        >
          {fase === 0 && (
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                }}
              >
                Perdia horas do expediente
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 600,
                  color: '#FDE68A',
                }}
              >
                Tempo gasto em execução manual
              </span>
            </div>
          )}

          {fase === 1 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
                transform: `scale(${0.94 + sFase1 * 0.06})`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                }}
              >
                Fazendo <span style={{color: '#C4B5FD'}}>tarefas repetitivas</span>
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 600,
                  color: '#E2E8F0',
                }}
              >
                Mesmas rotinas todos os dias
              </span>
            </div>
          )}

          {fase === 2 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
                transform: `scale(${0.94 + sFase2 * 0.06})`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FCA5A5',
                  lineHeight: 1.15,
                }}
              >
                Travavam o meu dia
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 600,
                  color: '#FFFFFF',
                }}
              >
                Expediente preso no operacional
              </span>
            </div>
          )}

          {/* Ícone lateral reativo */}
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 20,
              backgroundColor: fase === 2 ? 'rgba(239,68,68,0.22)' : 'rgba(124,58,237,0.25)',
              border: `2px solid ${fase === 2 ? '#EF4444' : CORES.marcaClara}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transform: `rotate(${Math.sin(frame * 0.14) * 8}deg)`,
            }}
          >
            <span style={{fontFamily, fontSize: 36, fontWeight: 900, color: '#FFFFFF'}}>
              {fase === 0 ? '⏳' : fase === 1 ? '🔁' : '🛑'}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — CONVERSA WHATSAPP (12.44s a 20.32s)
// Composição (b): Celular em perspectiva 3D suave + fundo fotográfico em movimento
// ============================================================================
const Cena2Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tAbs = 12.44 + frame / fps;

  const entrada = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  const saida = interpolate(tAbs, [19.97, 20.3], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const mensagens = [
    {
      de: 'cliente',
      texto: 'Inovare Claw, faça a conciliação bancária das notas de hoje e avise se houver divergência.',
      tIni: 12.6,
    },
    {
      de: 'empresa',
      texto: 'Conciliação iniciada. Conferindo notas fiscais e extratos bancários de forma autônoma.',
      tIni: 14.45,
    },
    {
      de: 'cliente',
      texto: 'Você já atualiza o painel financeiro quando terminar?',
      tIni: 16.15,
    },
    {
      de: 'empresa',
      texto: 'Conciliação concluída e painel atualizado sozinho, sem precisar da sua intervenção.',
      tIni: 17.45,
    },
  ];

  // Auto-height real: sem usar translateY negativo que deixa buraco escuro embaixo;
  // todas as 4 mensagens cabem perfeitamente na área de auto-height!
  const chatScrollY = 0;

  const rotY = interpolate(frame, [0, 236], [-8, 6]);
  const floatPhone = Math.sin(frame * 0.1) * 7;
  const segundaMetadeFala = tAbs >= 15.7;

  return (
    <AbsoluteFill style={{opacity: entrada * saida, backgroundColor: CORES.fundoEscuro}}>
      {/* Fundo vivo com img_2.jpg + orbes de luz em movimento (sem cobrir rosto de pessoa) */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${interpolate(frame, [0, 236], [1.0, 1.16])}) translateX(${interpolate(frame, [0, 236], [0, -30])}px)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: 860,
            height: 860,
            borderRadius: 999,
            background:
              'radial-gradient(circle, rgba(124,58,237,0.48) 0%, rgba(16,185,129,0.22) 50%, rgba(11,15,25,0) 75%)',
            left: interpolate(frame, [0, 236], [280, -140]),
            top: interpolate(frame, [0, 236], [220, 680]),
          }}
        />
      </AbsoluteFill>

      {/* TOPO (y=164..375): Rótulo "Como funciona" + Título sincronizado com a voz */}
      <div
        style={{
          position: 'absolute',
          top: 164,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <div
            style={{
              backgroundColor: CORES.marca,
              borderRadius: 999,
              padding: '8px 26px',
              border: '2px solid #DDD6FE',
              boxShadow: '0 8px 22px rgba(124, 58, 237, 0.5)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 0.6,
              }}
            >
              Como funciona
            </span>
          </div>

          {/* Selo obrigatório "Simulação" com letra >= 32px */}
          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(255,255,255,0.28)',
              borderRadius: 999,
              padding: '8px 22px',
            }}
          >
            <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#E2E8F0'}}>
              Simulação
            </span>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'rgba(11, 15, 25, 0.92)',
            borderRadius: 24,
            padding: '16px 26px',
            border: '2px solid rgba(167, 139, 250, 0.45)',
            boxShadow: '0 14px 32px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
            }}
          >
            {!segundaMetadeFala ? (
              <>
                Você delega para o <span style={{color: '#C4B5FD'}}>Inovare Claw</span>
              </>
            ) : (
              <>
                Agente de IA <span style={{color: '#34D399'}}>executa sozinho</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* CELULAR 3D COM WHATSAPP AUTO-HEIGHT (cresce dinamicamente com as mensagens, sem caixa preta vazia) */}
      <div
        style={{
          position: 'absolute',
          top: 390,
          left: 68,
          right: 68,
          maxHeight: 875,
          perspective: 1400,
        }}
      >
        <div
          style={{
            width: '100%',
            height: 'auto',
            maxHeight: 875,
            backgroundColor: '#0F172A',
            borderRadius: 40,
            border: '4px solid rgba(167, 139, 250, 0.7)',
            boxShadow: '0 28px 65px rgba(0,0,0,0.75)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            transform: `rotateY(${rotY}deg) translateY(${floatPhone}px) scale(${0.92 + entrada * 0.08})`,
          }}
        >
          {/* Cabeçalho do Chat */}
          <div
            style={{
              background: 'linear-gradient(90deg, #4C1D95 0%, #6D28D9 100%)',
              padding: '18px 26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.15)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 999,
                  backgroundColor: '#111827',
                  border: '3px solid #34D399',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                IC
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span style={{fontFamily, fontSize: 35, fontWeight: 900, color: '#FFFFFF'}}>
                  Inovare Claw
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#A7F3D0'}}>
                  • Agente de IA autônomo
                </span>
              </div>
            </div>
          </div>

          {/* Área das Mensagens (auto-height conforme as mensagens entram) */}
          <div
            style={{
              padding: '24px 24px 28px 24px',
              maxHeight: 745,
              overflow: 'hidden',
              position: 'relative',
              background:
                'radial-gradient(circle at 50% 20%, rgba(124,58,237,0.16), rgba(15,23,42,0.98) 75%)',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                transform: `translateY(${chatScrollY}px)`,
              }}
            >
              {mensagens.map((m, idx) => {
                const sMsg = spring({
                  frame: Math.max(0, Math.round((tAbs - m.tIni) * fps)),
                  fps,
                  config: {damping: 14, stiffness: 160},
                });
                if (tAbs < m.tIni - 0.05) return null;
                const isEmpresa = m.de === 'empresa';
                return (
                  <div
                    key={idx}
                    style={{
                      alignSelf: isEmpresa ? 'flex-start' : 'flex-end',
                      maxWidth: '88%',
                      backgroundColor: isEmpresa ? '#5B21B6' : '#1E293B',
                      border: isEmpresa
                        ? '2px solid #A78BFA'
                        : '2px solid rgba(255,255,255,0.22)',
                      borderRadius: isEmpresa
                        ? '24px 24px 24px 6px'
                        : '24px 24px 6px 24px',
                      padding: '16px 22px',
                      transform: `scale(${0.88 + sMsg * 0.12}) translateY(${(1 - sMsg) * 24}px)`,
                      opacity: sMsg,
                      boxShadow: '0 10px 24px rgba(0,0,0,0.4)',
                    }}
                  >
                    <div
                      style={{
                        fontFamily,
                        fontSize: 33,
                        fontWeight: 700,
                        color: '#FFFFFF',
                        lineHeight: 1.24,
                      }}
                    >
                      {m.texto}
                    </div>
                  </div>
                );
              })}

              {/* Indicador "digitando..." antes das respostas da empresa */}
              {((tAbs >= 14.0 && tAbs < 14.55) || (tAbs >= 17.0 && tAbs < 17.55)) && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    backgroundColor: 'rgba(91, 33, 182, 0.85)',
                    border: '2px solid #A78BFA',
                    borderRadius: 20,
                    padding: '12px 22px',
                  }}
                >
                  <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#E9D5FF'}}>
                    Executando tarefa...
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — DONO: O RESULTADO (19.97s a 28.15s)
// Composição (h): Vídeo dono_3.mp4 em tela cheia + Card de Resultado no Topo
// ============================================================================
const Cena3DonoResultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tAbs = 19.97 + frame / fps;

  const entrada = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const saida = interpolate(tAbs, [27.8, 28.14], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Cena 3 diferenciada da Cena 1: punch-in digital em plano fechado (1.15x -> 1.23x com corte dinâmico na metade)
  const punchIn3 = tAbs >= 23.85 ? 0.06 : 0;
  const zoomVideo = interpolate(frame, [0, 245], [1.15, 1.18], {extrapolateRight: 'clamp'}) + punchIn3;
  const panX = interpolate(frame, [0, 245], [-18, 12], {extrapolateRight: 'clamp'});
  const panY3 = interpolate(frame, [0, 245], [85, 100], {extrapolateRight: 'clamp'});

  // Fala:
  // 20.26s: "Hoje meu agente trabalha sozinho nessas rotinas"
  // 23.85s: "e eu foco no que importa"
  // 25.85s: "para a empresa."
  const faseCena3 = tAbs < 23.85 ? 0 : tAbs < 25.85 ? 1 : 2;
  const sTopo = spring({frame: frame - 5, fps, config: {damping: 13, stiffness: 150}});
  const sFoco = spring({
    frame: Math.max(0, Math.round((tAbs - 23.85) * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });
  const sEmpresa = spring({
    frame: Math.max(0, Math.round((tAbs - 25.85) * fps)),
    fps,
    config: {damping: 12, stiffness: 170},
  });

  const floatY = Math.sin(frame * 0.11) * 5;

  return (
    <AbsoluteFill style={{opacity: entrada * saida, backgroundColor: '#000'}}>
      {/* Vídeo dono_3.mp4 em tela cheia — Rosto livre e iluminação natural */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoomVideo}) translateX(${panX}px) translateY(${panY3}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Sombra protetora exclusiva na faixa do topo (y=0..380) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background:
            'linear-gradient(180deg, rgba(11,15,25,0.80) 0%, rgba(11,15,25,0.38) 68%, rgba(11,15,25,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* HUD DO TOPO COMPACTO (y=154..355, garantindo >40px de respiro acima da cabeça) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          transform: `translateY(${(1 - sTopo) * -30 + floatY}px)`,
          opacity: sTopo,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid #10B981',
              borderRadius: 999,
              padding: '8px 24px',
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 999,
                backgroundColor: '#10B981',
                transform: `scale(${1 + Math.sin(frame * 0.25) * 0.25})`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#6EE7B7',
                textTransform: 'uppercase',
                letterSpacing: 0.6,
              }}
            >
              O resultado
            </span>
          </div>

          <div
            style={{
              backgroundColor: 'rgba(124, 58, 237, 0.92)',
              border: '2px solid #DDD6FE',
              borderRadius: 999,
              padding: '8px 22px',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Inovare Claw
          </div>
        </div>

        {/* Card de conquista sincronizado com as 3 partes da fala (sem ficar estático entre 24s e 27s) */}
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            borderRadius: 22,
            padding: '12px 22px',
            borderLeft: '8px solid #10B981',
            border: '2px solid rgba(16, 185, 129, 0.45)',
            boxShadow: '0 14px 30px rgba(0,0,0,0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
          }}
        >
          {faseCena3 === 0 && (
            <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                }}
              >
                Agente trabalha <span style={{color: '#6EE7B7'}}>sozinho</span>
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#E2E8F0',
                }}
              >
                Assume as rotinas da empresa
              </span>
            </div>
          )}
          {faseCena3 === 1 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                transform: `scale(${0.94 + sFoco * 0.06})`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                }}
              >
                Foco no que <span style={{color: '#C4B5FD'}}>importa</span>
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#6EE7B7',
                }}
              >
                Rotinas delegadas ao agente
              </span>
            </div>
          )}
          {faseCena3 === 2 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                transform: `scale(${(0.92 + sEmpresa * 0.08) * (1 + Math.sin(frame * 0.25) * 0.025)})`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                }}
              >
                Importa <span style={{color: '#6EE7B7'}}>para a empresa</span>
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#DDD6FE',
                }}
              >
                Crescimento e direção estratégica
              </span>
            </div>
          )}

          {/* Ícone Check Animado */}
          <div
            style={{
              width: 68,
              height: 68,
              borderRadius: 999,
              backgroundColor: '#10B981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              boxShadow: '0 0 24px rgba(16, 185, 129, 0.6)',
              transform: `scale(${1 + Math.sin(frame * 0.18) * 0.06})`,
            }}
          >
            <svg width="38" height="38" viewBox="0 0 24 24" fill="none">
              <path
                d="M5 13l4 4L19 7"
                stroke="#FFFFFF"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL (27.80s a 31.75s)
// CTA Vivo, Pulsante, sem Karaokê, dentro da Safe Zone (y=180..1480)
// ============================================================================
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const entradaCard = spring({frame, fps, config: {damping: 14, stiffness: 130}});
  const sBotao = spring({frame: Math.max(0, frame - 8), fps, config: {damping: 13, stiffness: 130}});
  const sHandle = spring({frame: Math.max(0, frame - 16), fps, config: {damping: 14, stiffness: 130}});

  // Movimento contínuo forte do primeiro ao último frame do cartão (>4% diff entre 20% e 80%)
  const bgScale = interpolate(frame, [0, 120], [1.0, 1.24]);
  const bgRot = interpolate(frame, [0, 120], [0, 7]);
  const pulseBtn = interpolate(Math.sin(frame * 0.25), [-1, 1], [1.0, 1.04]);
  const floatCard = Math.sin(frame * 0.14) * 10;
  const shimmerX = interpolate(frame % 42, [0, 42], [-350, 1050]);

  return (
    <AbsoluteFill style={{opacity: interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'}), backgroundColor: CORES.apoio}}>
      {/* Fundo vivo abstrato da marca em movimento forte (sem rosto coberto por botão) */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) rotate(${bgRot}deg)`,
          }}
        />
        {/* Orbes luminosos grandes que cruzam a tela dando variação visual contínua */}
        <div
          style={{
            position: 'absolute',
            width: 900,
            height: 900,
            borderRadius: 999,
            background:
              'radial-gradient(circle, rgba(167,139,250,0.55) 0%, rgba(124,58,237,0.28) 45%, rgba(17,24,39,0) 72%)',
            left: interpolate(frame, [0, 120], [-240, 380]),
            top: interpolate(frame, [0, 120], [120, 680]),
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: 780,
            height: 780,
            borderRadius: 999,
            background:
              'radial-gradient(circle, rgba(52,211,153,0.35) 0%, rgba(124,58,237,0.22) 50%, rgba(17,24,39,0) 75%)',
            right: interpolate(frame, [0, 120], [-220, 320]),
            bottom: interpolate(frame, [0, 120], [140, 620]),
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo centralizado e distribuído entre y=240 e y=1440 */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 68,
          right: 68,
          bottom: 460,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          transform: `translateY(${floatCard}px)`,
        }}
      >
        {/* Bloco Marca + Proposta de Valor */}
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '3px solid rgba(167, 139, 250, 0.65)',
            borderRadius: 36,
            padding: '38px 34px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 18,
            boxShadow: '0 24px 60px rgba(0,0,0,0.65)',
            transform: `translateY(${(1 - entradaCard) * 85}px) scale(${0.92 + entradaCard * 0.08})`,
            opacity: entradaCard,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(124, 58, 237, 0.28)',
              border: '2px solid #C4B5FD',
              borderRadius: 999,
              padding: '8px 26px',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#E9D5FF',
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            Agente de IA Autônomo
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 70,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              lineHeight: 1.08,
            }}
          >
            INOVARE <span style={{color: '#C4B5FD'}}>CLAW</span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.28,
              maxWidth: 820,
            }}
          >
            Seu agente de inteligência artificial que executa tarefas de verdade sozinho.
          </div>
        </div>

        {/* Botão CTA Principal Pulsante = mesma ação do convite_voz */}
        <div
          style={{
            width: '100%',
            transform: `translateY(${(1 - sBotao) * 80}px) scale(${(0.92 + sBotao * 0.08) * pulseBtn})`,
            opacity: Math.min(1, 0.25 + sBotao * 0.75),
            position: 'relative',
            overflow: 'hidden',
            borderRadius: 999,
            background: 'linear-gradient(90deg, #6D28D9 0%, #7C3AED 50%, #9333EA 100%)',
            border: '4px solid #F3E8FF',
            padding: '30px 36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
            boxShadow: '0 20px 55px rgba(124, 58, 237, 0.75)',
          }}
        >
          {/* Brilho atravessando o botão continuamente */}
          <div
            style={{
              position: 'absolute',
              top: -40,
              bottom: -40,
              width: 140,
              background:
                'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.38) 50%, rgba(255,255,255,0) 100%)',
              transform: `translateX(${shimmerX}px) rotate(20deg)`,
              pointerEvents: 'none',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.8,
              textTransform: 'uppercase',
            }}
          >
            CHAME A GENTE NO DIRECT
          </span>
        </div>

        {/* @arroba dentro da janela y=900..1450 */}
        <div
          style={{
            transform: `translateY(${(1 - sHandle) * 70 + Math.sin(frame * 0.18) * 6}px) scale(${0.92 + sHandle * 0.08})`,
            opacity: Math.min(1, 0.25 + sHandle * 0.75),
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid rgba(255,255,255,0.28)',
            borderRadius: 999,
            padding: '14px 38px',
            boxShadow: '0 12px 30px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 0.5,
            }}
          >
            @inovareclaw.ia
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================
const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, fontFamily}}>
      {/* Áudio da Narração Completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha Sonora com ducking suave e fade out no final */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const seg = f / 30;
          const fadeOut = interpolate(seg, [29.8, 31.75], [1, 0.04], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return 0.1 * fadeOut;
        }}
      />

      {/* CENA 0: 0.00s -> 4.95s */}
      <Sequence from={0} durationInFrames={Math.ceil(4.95 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 4.60s -> 12.79s */}
      <Sequence
        from={Math.floor(4.6 * fps)}
        durationInFrames={Math.ceil((12.79 - 4.6) * fps)}
      >
        <Cena1DonoProblema />
      </Sequence>

      {/* CENA 2: 12.44s -> 20.32s */}
      <Sequence
        from={Math.floor(12.44 * fps)}
        durationInFrames={Math.ceil((20.32 - 12.44) * fps)}
      >
        <Cena2Conversa />
      </Sequence>

      {/* CENA 3: 19.97s -> 28.15s */}
      <Sequence
        from={Math.floor(19.97 * fps)}
        durationInFrames={Math.ceil((28.15 - 19.97) * fps)}
      >
        <Cena3DonoResultado />
      </Sequence>

      {/* CENA 4: 27.80s -> 31.75s */}
      <Sequence
        from={Math.floor(27.8 * fps)}
        durationInFrames={Math.ceil((31.75 - 27.8) * fps)}
      >
        <Cena4Cartao />
      </Sequence>

      {/* Barra de Progresso na Safe Zone (y=152, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.22)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: CORES.marcaClara,
            borderRadius: 999,
          }}
        />
      </div>

      {/* Legenda Karaokê (desligada no Cartão Final t >= 27.8s) */}
      {t < 27.75 && (
        <Karaoke
          palavras={PALAVRAS}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={350}
          maxLetras={28}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(31.75 * 30)}
    />
  );
};
