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
  marca: '#10B981',
  marcaBrilho: '#34D399',
  marcaEscura: '#065F46',
  apoio: '#111827',
  fundoEscuro: '#0B111E',
  cardSolido: 'rgba(17, 24, 39, 0.94)',
  cardSecundario: 'rgba(30, 41, 59, 0.92)',
  texto: '#FFFFFF',
  textoClaro: '#E2E8F0',
  alerta: '#EF4444',
  alertaSuave: 'rgba(239, 68, 68, 0.22)',
};

const DURACAO_S = 31.48;
const FPS = 30;
const TOTAL_FRAMES = Math.ceil(DURACAO_S * FPS); // 945

const PALAVRAS_K: PalavraK[] = [
  // Cena 0
  {p: 'Você', ini: 0.318, fim: 0.546},
  {p: 'esquece', ini: 0.558, fim: 1.003},
  {p: 'de', ini: 1.015, fim: 1.111, quebraLinha: true},
  {p: 'cobrar', ini: 1.123, fim: 1.496},
  {p: 'retorno', ini: 1.508, fim: 2.025, quebraApos: true},
  {p: 'de', ini: 2.037, fim: 2.145},
  {p: 'quem', ini: 2.157, fim: 2.325},
  {p: 'pediu', ini: 2.337, fim: 2.614},
  {p: 'orçamento?', ini: 2.626, fim: 3.299, quebraApos: true},
  // Cena 1
  {p: 'Eu', ini: 5.352, fim: 5.872, quebraAntes: true},
  {p: 'perdia', ini: 5.872, fim: 6.292},
  {p: 'vendas', ini: 6.292, fim: 6.712},
  {p: 'porque', ini: 6.712, fim: 6.972, quebraApos: true},
  {p: 'esquecia', ini: 6.972, fim: 7.432},
  {p: 'de', ini: 7.432, fim: 7.652},
  {p: 'cobrar', ini: 7.652, fim: 7.852, quebraApos: true},
  {p: 'resposta', ini: 8.092, fim: 8.372},
  {p: 'dos', ini: 8.372, fim: 8.572, quebraLinha: true},
  {p: 'orçamentos.', ini: 8.572, fim: 9.352, quebraApos: true},
  {p: 'Hoje', ini: 9.992, fim: 10.152, quebraAntes: true},
  {p: 'o', ini: 10.152, fim: 10.372},
  {p: 'agente', ini: 10.372, fim: 10.712},
  {p: 'IA', ini: 10.712, fim: 10.932, quebraApos: true},
  {p: 'faz', ini: 10.932, fim: 11.232},
  {p: 'esse', ini: 11.232, fim: 11.472},
  {p: 'follow-up.', ini: 11.472, fim: 12.052, quebraApos: true},
  // Cena 2
  {p: 'Você', ini: 12.738, fim: 12.978, quebraAntes: true},
  {p: 'delega', ini: 12.99, fim: 13.411},
  {p: 'o', ini: 13.423, fim: 13.471, quebraApos: true},
  {p: 'acompanhamento', ini: 13.483, fim: 14.253, quebraApos: true},
  {p: 'para', ini: 14.265, fim: 14.421},
  {p: 'o', ini: 14.433, fim: 14.469},
  {p: 'Agente', ini: 14.481, fim: 14.853},
  {p: 'Pessoal', ini: 14.865, fim: 15.298},
  {p: 'IA', ini: 15.31, fim: 16.62, quebraApos: true},
  {p: 'e', ini: 16.704, fim: 16.813},
  {p: 'ele', ini: 16.825, fim: 16.969},
  {p: 'faz', ini: 16.981, fim: 17.161},
  {p: 'essa', ini: 17.173, fim: 17.51, quebraApos: true},
  {p: 'tarefa', ini: 17.522, fim: 17.906},
  {p: 'real', ini: 17.918, fim: 18.231},
  {p: 'por', ini: 18.243, fim: 18.375},
  {p: 'você.', ini: 18.387, fim: 18.772, quebraApos: true},
  // Cena 3
  {p: 'Agora', ini: 19.885, fim: 20.745, quebraAntes: true},
  {p: 'eu', ini: 21.085, fim: 21.225},
  {p: 'delego', ini: 21.225, fim: 21.625, quebraApos: true},
  {p: 'o', ini: 21.625, fim: 21.765},
  {p: 'follow-up,', ini: 21.765, fim: 22.585, quebraApos: true},
  {p: 'o', ini: 22.585, fim: 22.725},
  {p: 'agendamento', ini: 22.725, fim: 23.345, quebraApos: true},
  {p: 'e', ini: 23.345, fim: 23.605},
  {p: 'a', ini: 23.605, fim: 23.785},
  {p: 'pesquisa', ini: 23.785, fim: 24.585, quebraApos: true},
  {p: 'para', ini: 24.585, fim: 24.985},
  {p: 'não', ini: 24.985, fim: 25.165},
  {p: 'deixar', ini: 25.165, fim: 25.485},
  {p: 'nenhum', ini: 25.485, fim: 25.805, quebraApos: true},
  {p: 'cliente', ini: 25.805, fim: 26.265},
  {p: 'sem', ini: 26.265, fim: 26.405},
  {p: 'retorno.', ini: 26.405, fim: 26.885},
];

const CONVERSA = [
  {
    de: 'cliente' as const,
    texto: 'Preciso fazer o follow-up dos orçamentos enviados que ainda não responderam.',
    tEntrada: 12.4,
  },
  {
    de: 'empresa' as const,
    texto: 'Certo. Vou enviar a mensagem de acompanhamento para esses contatos agora.',
    tEntrada: 13.75,
  },
  {
    de: 'empresa' as const,
    texto: '✓ Acompanhamento enviado: "Olá! Gostaria de saber se ficou alguma dúvida na proposta enviada."',
    tEntrada: 15.15,
    destaqueAcao: true,
  },
  {
    de: 'cliente' as const,
    texto: 'Me avise quando terminar e registre quem tiver interesse em avançar.',
    tEntrada: 16.55,
  },
  {
    de: 'empresa' as const,
    texto: 'Combinado. Tarefa de follow-up iniciada e retorno com as respostas.',
    tEntrada: 18.15,
  },
];

// Fundo vivo para cenas de imagem (zoom, pan, malha sutil)
const FundoFotoVivo: React.FC<{
  foto: string;
  duracaoFrames: number;
  blur?: number;
  escurecer?: number;
}> = ({foto, duracaoFrames, blur = 0, escurecer = 0.65}) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, duracaoFrames], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const tx = interpolate(frame, [0, duracaoFrames], [-14, 14], {
    extrapolateRight: 'clamp',
  });
  const ty = interpolate(frame, [0, duracaoFrames], [-10, 12], {
    extrapolateRight: 'clamp',
  });
  const orbShift = Math.sin(frame / 14) * 35;

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: CORES.fundoEscuro}}>
      <Img
        src={staticFile(foto)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${scale}) translate(${tx}px, ${ty}px)`,
          filter: blur > 0 ? `blur(${blur}px)` : undefined,
        }}
      />
      {/* Véu escuro de contraste */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, rgba(11,17,30,${escurecer + 0.08}) 0%, rgba(17,24,39,${escurecer}) 50%, rgba(11,17,30,${escurecer + 0.14}) 100%)`,
        }}
      />
      {/* Luzes vivas da marca em movimento */}
      <div
        style={{
          position: 'absolute',
          top: 240 + orbShift,
          right: -120,
          width: 520,
          height: 520,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16,185,129,0.26) 0%, rgba(16,185,129,0) 70%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 320 - orbShift,
          left: -140,
          width: 560,
          height: 560,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16,185,129,0.20) 0%, rgba(16,185,129,0) 70%)',
        }}
      />
      {/* Grade sutil em movimento */}
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
          backgroundSize: '72px 72px',
          backgroundPosition: `${frame * 0.6}px ${frame * 0.6}px`,
        }}
      />
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 0 — PERGUNTA (0.00s a 4.76s -> 143 frames)
// Composição (a) + (e): Texto cinético gigante já visível no 0s + cards de orçamentos pendentes
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const entradaCena = spring({frame: frame + 6, fps, config: {damping: 14, stiffness: 160}});
  const saidaCena = interpolate(t, [4.38, 4.72], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const zoomSaida = interpolate(t, [4.32, 4.74], [1, 1.24], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideSaidaX = interpolate(t, [4.35, 4.74], [0, -140], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Pergunta já presente e com alto contraste desde o frame 0, ganhando ênfase conforme a fala
  const sL1 = spring({frame: frame + 10, fps, config: {damping: 13, stiffness: 160}});
  const sL2 = spring({frame: frame + 8, fps, config: {damping: 13, stiffness: 160}});
  const sL3 = spring({frame: frame + 6, fps, config: {damping: 13, stiffness: 160}});

  const barraGrifo = interpolate(t, [0.55, 1.35], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const grifoAtivo = barraGrifo > 88;

  // Cascata rápida logo no primeiro segundo (0.06s, 0.36s, 0.66s) ocupando o centro sem qualquer sobreposição (y=575, 795, 1015)
  const orcamentos = [
    {
      titulo: 'Proposta — Reforma',
      subtitulo: 'Cliente aguardando contato',
      status: 'Sem resposta',
      cor: CORES.alerta,
      delayFrames: 2,
      top: 575,
    },
    {
      titulo: 'Orçamento — Consultoria',
      subtitulo: 'Cobrança de retorno pendente',
      status: 'Esquecido',
      cor: '#F59E0B',
      delayFrames: 11,
      top: 795,
    },
    {
      titulo: 'Cotação — Projeto',
      subtitulo: 'Risco de perder a venda',
      status: 'Sem retorno',
      cor: CORES.marca,
      delayFrames: 20,
      top: 1015,
    },
  ];

  return (
    <AbsoluteFill
      style={{
        opacity: saidaCena,
        transform: `scale(${zoomSaida}) translateX(${slideSaidaX}px)`,
        transformOrigin: '50% 50%',
      }}
    >
      <FundoFotoVivo foto="img_0.jpg" duracaoFrames={143} escurecer={0.62} />

      {/* TOPO: Pergunta cinética grande (y=170 a 560) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          gap: 14,
        }}
      >
        {/* Pílula de contexto imediato */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            backgroundColor: CORES.cardSolido,
            border: `2px solid ${CORES.alerta}`,
            transform: `scale(${entradaCena})`,
            boxShadow: '0 10px 25px rgba(239,68,68,0.35)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: CORES.alerta,
              boxShadow: `0 0 12px ${CORES.alerta}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 0.6,
            }}
          >
            ORÇAMENTOS SEM RESPOSTA
          </span>
        </div>

        {/* Pergunta principal completa desde o frame 0 com alto contraste */}
        <div
          style={{
            marginTop: 8,
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
            width: '100%',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 60,
              fontWeight: 900,
              color: CORES.texto,
              lineHeight: 1.08,
              transform: `translateY(${(1 - sL1) * 18}px)`,
              opacity: sL1,
              textShadow: '0 6px 18px rgba(0,0,0,0.85)',
            }}
          >
            Você esquece
          </div>

          <div
            style={{
              position: 'relative',
              display: 'inline-block',
              alignSelf: 'flex-start',
              padding: '6px 18px',
              borderRadius: 14,
              backgroundColor: 'rgba(17, 24, 39, 0.78)',
              border: `2px solid ${grifoAtivo ? CORES.marca : 'rgba(255,255,255,0.28)'}`,
              transform: `translateY(${(1 - sL2) * 18}px) scale(${grifoAtivo ? 1.03 : 1})`,
              opacity: sL2,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: `${barraGrifo}%`,
                backgroundColor: CORES.marca,
                boxShadow: '0 8px 24px rgba(16,185,129,0.45)',
              }}
            />
            <span
              style={{
                position: 'relative',
                fontFamily,
                fontSize: 60,
                fontWeight: 900,
                color: grifoAtivo ? '#052E16' : '#FFFFFF',
                textShadow: grifoAtivo ? 'none' : '0 4px 12px rgba(0,0,0,0.9)',
                lineHeight: 1.08,
              }}
            >
              de cobrar retorno
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 800,
              color: CORES.texto,
              lineHeight: 1.12,
              transform: `translateY(${(1 - sL3) * 18}px)`,
              opacity: sL3,
              textShadow: '0 6px 18px rgba(0,0,0,0.85)',
            }}
          >
            de quem pediu orçamento?
          </div>
        </div>
      </div>

      {/* CENTRO: Propostas pendentes entrando em stagger de baixo para cima (0.6s, 1.5s, 2.4s) */}
      {orcamentos.map((item, idx) => {
        if (frame < item.delayFrames) return null;

        const sCard = spring({
          frame: frame - item.delayFrames,
          fps,
          config: {damping: 10, stiffness: 140, mass: 0.8},
        });
        const floatY = Math.sin((frame + idx * 18) / 9) * 4;
        const pulseBadge = 1 + Math.sin((frame + idx * 11) / 5) * 0.08;
        const glowBadge = 0.4 + Math.sin((frame + idx * 11) / 5) * 0.3;

        return (
          <div
            key={idx}
            style={{
              position: 'absolute',
              top: item.top,
              left: 60,
              right: 60,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '18px 24px',
              borderRadius: 24,
              backgroundColor: CORES.cardSolido,
              border: `2px solid rgba(255,255,255,0.16)`,
              borderLeft: `10px solid ${item.cor}`,
              boxShadow: '0 16px 36px rgba(0,0,0,0.65)',
              transform: `translateY(${(1 - sCard) * 110 + floatY}px) scale(${0.88 + 0.12 * sCard})`,
              opacity: interpolate(sCard, [0, 0.3], [0, 1], {extrapolateRight: 'clamp'}),
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 20, flex: 1}}>
              {/* Ícone de documento/orçamento */}
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 18,
                  backgroundColor: 'rgba(255,255,255,0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"
                    stroke={item.cor}
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path d="M14 2V8H20" stroke={item.cor} strokeWidth="2.4" strokeLinecap="round" />
                  <path d="M8 13H16" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" />
                  <path d="M8 17H13" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" />
                </svg>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 800,
                    color: CORES.texto,
                    lineHeight: 1.18,
                  }}
                >
                  {item.titulo}
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: CORES.textoClaro,
                    lineHeight: 1.15,
                  }}
                >
                  {item.subtitulo}
                </span>
              </div>
            </div>

            <div
              style={{
                padding: '10px 20px',
                borderRadius: 14,
                backgroundColor:
                  item.cor === CORES.alerta
                    ? 'rgba(239,68,68,0.22)'
                    : item.cor === '#F59E0B'
                    ? 'rgba(245,158,11,0.22)'
                    : 'rgba(16,185,129,0.22)',
                border: `2px solid ${item.cor}`,
                boxShadow: `0 0 20px rgba(255,255,255,${glowBadge * 0.4})`,
                transform: `scale(${pulseBadge})`,
                flexShrink: 0,
                marginLeft: 16,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color:
                    item.cor === CORES.alerta
                      ? '#FCA5A5'
                      : item.cor === '#F59E0B'
                      ? '#FDE68A'
                      : CORES.marcaBrilho,
                }}
              >
                {item.status}
              </span>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// Véu escuro profundo na base que oculta completamente a borda inferior do tablet apagado, mantendo o centro livre e sem overlays no peito
const VinhetaBaseMesa: React.FC<{modoAtivo?: boolean; tAbs?: number}> = () => {
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        height: 820,
        background:
          'linear-gradient(180deg, rgba(11,17,30,0) 0%, rgba(11,17,30,0.68) 28%, rgba(11,17,30,0.97) 52%, rgba(11,17,30,1) 100%)',
        pointerEvents: 'none',
      }}
    />
  );
};

// ============================================================================
// CENA 1 — DONO / O PROBLEMA -> SOLUÇÃO (4.41s a 12.60s -> 246 frames)
// Composição (h): Vídeo cheio do dono + punch-in na virada da solução + card no topo
// ============================================================================
const Cena1DonoProblema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.round((12.6 - 4.41) * fps); // 246
  const tAbs = 4.41 + frame / fps;

  const entrada = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideEntradaX = interpolate(frame, [0, 12], [110, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const saida = interpolate(tAbs, [12.25, 12.58], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Em tAbs = 9.95s ("Hoje o agente IA faz esse follow-up"), o card do topo vira de Problema para Solução
  // e a câmera faz um punch-in dinâmico para quebrar a monotonia do plano
  const viradaSolucao = spring({
    frame: Math.round((tAbs - 9.85) * fps),
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const zoomBase = interpolate(frame, [0, duracaoFrames], [1.08, 1.13], {
    extrapolateRight: 'clamp',
  });
  const punchSolucao = viradaSolucao * 0.06;
  const zoomVideo = zoomBase + punchSolucao;
  const panYVideo = interpolate(frame, [0, duracaoFrames], [82, 68], {
    extrapolateRight: 'clamp',
  });
  const panXVideo = interpolate(frame, [0, duracaoFrames], [-32, -24], {
    extrapolateRight: 'clamp',
  });

  const cardEntrada = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 130},
  });
  const floatY = Math.sin(frame / 11) * 3;
  const modoSolucao = tAbs >= 9.85;

  return (
    <AbsoluteFill style={{opacity: entrada * saida, backgroundColor: CORES.fundoEscuro}}>
      {/* Vídeo cheio do dono com enquadramento limpo sem mockup falso 2D */}
      <AbsoluteFill
        style={{
          overflow: 'hidden',
          transform: `translateX(${slideEntradaX + panXVideo}px) translateY(${panYVideo}px) scale(${zoomVideo})`,
          transformOrigin: '50% 42%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>
      <VinhetaBaseMesa modoAtivo={modoSolucao} tAbs={tAbs} />

      {/* TOPO EXCLUSIVO (y=158 a 375) — Rosto e cabelo do dono com amplo headroom abaixo de y=490 */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          transform: `translateY(${(1 - cardEntrada) * -35 + floatY}px)`,
          opacity: cardEntrada,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {/* Linha superior: Rótulo + Gancho */}
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '8px 22px',
              borderRadius: 999,
              backgroundColor: modoSolucao ? CORES.marca : CORES.alerta,
              boxShadow: '0 8px 22px rgba(0,0,0,0.45)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: modoSolucao ? '#052E16' : '#FFFFFF',
                textTransform: 'uppercase',
              }}
            >
              {modoSolucao ? 'Solução ativa' : 'O problema'}
            </span>
          </div>

          <div
            style={{
              padding: '8px 20px',
              borderRadius: 999,
              backgroundColor: CORES.cardSolido,
              border: `2px solid ${CORES.marca}`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: CORES.texto,
              }}
            >
              Agente Pessoal IA
            </span>
          </div>
        </div>

        {/* Card principal compacto no alto com ícone alinhado ao topo (flex-start) e quebra equilibrada */}
        <div
          style={{
            padding: '16px 24px',
            borderRadius: 24,
            backgroundColor: CORES.cardSolido,
            border: `3px solid ${modoSolucao ? CORES.marca : CORES.alerta}`,
            boxShadow: '0 16px 36px rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 20,
            transform: `scale(${modoSolucao ? 0.96 + 0.04 * viradaSolucao : 1})`,
          }}
        >
          {/* Ícone dinâmico alinhado à primeira linha */}
          <div
            style={{
              width: 60,
              height: 60,
              marginTop: 2,
              borderRadius: 18,
              backgroundColor: modoSolucao ? 'rgba(16,185,129,0.22)' : CORES.alertaSuave,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {modoSolucao ? (
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
                <path
                  d="M20 6L9 17L4 12"
                  stroke={CORES.marcaBrilho}
                  strokeWidth="3.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 8V12M12 16H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
                  stroke="#FCA5A5"
                  strokeWidth="2.8"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </div>

          <div style={{display: 'flex', flexDirection: 'column', gap: 4, flex: 1}}>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: CORES.texto,
                lineHeight: 1.16,
              }}
            >
              {modoSolucao ? (
                'Hoje o Agente IA faz esse follow-up'
              ) : (
                <>
                  Perdia vendas esquecendo
                  <br />
                  de cobrar retorno
                </>
              )}
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: modoSolucao ? CORES.marcaBrilho : '#FCA5A5',
              }}
            >
              {modoSolucao
                ? 'Follow-up de orçamentos em dia'
                : 'Orçamentos ficavam sem resposta'}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — CONVERSA / COMO FUNCIONA (12.25s a 20.06s -> 235 frames)
// Composição (b): Celular em perspectiva 3D suave + balões de WhatsApp um a um
// ============================================================================
const Cena2Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.round((20.06 - 12.25) * fps); // 234
  const tAbs = 12.25 + frame / fps;

  const entrada = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const saida = interpolate(tAbs, [19.71, 20.04], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Leve inclinação 3D contínua
  const rotY = interpolate(frame, [0, duracaoFrames], [-7, 5], {
    extrapolateRight: 'clamp',
  });
  const rotX = interpolate(frame, [0, duracaoFrames], [3, -2], {
    extrapolateRight: 'clamp',
  });

  const floatPhone = Math.sin(frame / 10) * 6;

  return (
    <AbsoluteFill style={{opacity: saida}}>
      <FundoFotoVivo foto="img_2.jpg" duracaoFrames={duracaoFrames} escurecer={0.58} />

      {/* TOPO: Rótulo "Como funciona" + gancho_tela (y=154 a 256) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          transform: `translateY(${(1 - entrada) * -30}px)`,
          opacity: entrada,
        }}
      >
        <div
          style={{
            padding: '6px 24px',
            borderRadius: 999,
            backgroundColor: CORES.marca,
            boxShadow: '0 8px 20px rgba(16,185,129,0.4)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: '#052E16',
              textTransform: 'uppercase',
            }}
          >
            Como funciona
          </span>
        </div>

        <div
          style={{
            fontFamily,
            fontSize: 38,
            fontWeight: 900,
            color: CORES.texto,
            textAlign: 'center',
            lineHeight: 1.1,
            textShadow: '0 6px 18px rgba(0,0,0,0.65)',
          }}
        >
          Follow-up de orçamentos em dia
        </div>
      </div>

      {/* CENTRO VERTICAL: Moldura realista de smartphone centralizada preenchendo a tela 9:16 (y=292 a 1340) */}
      <div
        style={{
          position: 'absolute',
          top: 292,
          bottom: 580,
          left: 60,
          right: 60,
          perspective: 1400,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 44,
            backgroundColor: '#0F172A',
            border: `5px solid rgba(16,185,129,0.72)`,
            boxShadow: '0 30px 65px rgba(0,0,0,0.8), 0 0 35px rgba(16,185,129,0.18)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            transform: `translateY(${floatPhone}px) scale(${0.94 + 0.06 * entrada}) rotateY(${rotY}deg) rotateX(${rotX}deg)`,
          }}
        >
          {/* Topo de smartphone realista (speaker notch) */}
          <div
            style={{
              height: 26,
              backgroundColor: '#042F2E',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                width: 110,
                height: 7,
                borderRadius: 999,
                backgroundColor: 'rgba(255,255,255,0.22)',
              }}
            />
          </div>

          {/* Cabeçalho do chat */}
          <div
            style={{
              padding: '18px 28px',
              backgroundColor: '#064E3B',
              borderBottom: '2px solid rgba(16,185,129,0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 5,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: CORES.marca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#052E16',
                }}
              >
                IA
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: CORES.texto,
                  }}
                >
                  Agente Pessoal IA
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: CORES.marcaBrilho,
                  }}
                >
                  Tarefa real delegada
                </span>
              </div>
            </div>

            {/* Selo obrigatório "Simulação" >= 32px */}
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 12,
                backgroundColor: 'rgba(17,24,39,0.85)',
                border: '1.5px solid rgba(255,255,255,0.3)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: CORES.textoClaro,
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Corpo da conversa — preenche a tela do smartphone com rolagem vertical suave */}
          <div
            style={{
              flex: 1,
              padding: '22px 26px',
              overflow: 'hidden',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
              background:
                'radial-gradient(circle at 80% 20%, rgba(16,185,129,0.14), transparent 60%), #0B1324',
            }}
          >
            {(() => {
              // Rolagem em degraus inteiros: quando a 4ª mensagem chega (16.55s), oculta a 1ª mensagem inteira;
              // quando a 5ª mensagem chega (18.15s), mantém as últimas 4 mensagens 100% inteiras na tela sem cortar metade de balão.
              const inicioVisivel = tAbs >= 16.5 ? 1 : 0;
              const mensagensVisiveis = CONVERSA.slice(inicioVisivel);
              const sScroll = spring({
                frame: Math.round((tAbs - 16.5) * fps),
                fps,
                config: {damping: 15, stiffness: 140},
              });
              const offsetTransicao = tAbs >= 16.5 ? (1 - sScroll) * 45 : 0;

              return (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 16,
                    transform: `translateY(${offsetTransicao}px)`,
                  }}
                >
                  {mensagensVisiveis.map((msg, idxVis) => {
                    const i = inicioVisivel + idxVis;
                    const aparecer = tAbs >= msg.tEntrada;
                    const digitando =
                      msg.de === 'empresa' && tAbs >= msg.tEntrada - 0.65 && tAbs < msg.tEntrada;

                    if (digitando) {
                      return (
                        <div
                          key={`dig-${i}`}
                          style={{
                            alignSelf: 'flex-start',
                            padding: '16px 26px',
                            borderRadius: 24,
                            backgroundColor: '#065F46',
                            border: `2px solid ${CORES.marca}`,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 12,
                          }}
                        >
                          <span
                            style={{
                              fontFamily,
                              fontSize: 32,
                              fontWeight: 700,
                              color: CORES.marcaBrilho,
                            }}
                          >
                            digitando...
                          </span>
                        </div>
                      );
                    }

                    if (!aparecer) return null;

                    const sMsg = spring({
                      frame: Math.round((tAbs - msg.tEntrada) * fps),
                      fps,
                      config: {damping: 14, stiffness: 150},
                    });

                    const ehEmpresa = msg.de === 'empresa';
                    const ehDestaque = 'destaqueAcao' in msg && msg.destaqueAcao;

                    return (
                      <div
                        key={i}
                        style={{
                          alignSelf: ehEmpresa ? 'flex-start' : 'flex-end',
                          maxWidth: '92%',
                          padding: '18px 24px',
                          borderRadius: 24,
                          borderBottomLeftRadius: ehEmpresa ? 6 : 26,
                          borderBottomRightRadius: ehEmpresa ? 26 : 6,
                          backgroundColor: ehDestaque
                            ? 'rgba(6, 95, 70, 0.96)'
                            : ehEmpresa
                            ? '#065F46'
                            : '#1E293B',
                          border: `2.5px solid ${
                            ehDestaque
                              ? CORES.marcaBrilho
                              : ehEmpresa
                              ? CORES.marca
                              : 'rgba(255,255,255,0.22)'
                          }`,
                          boxShadow: ehDestaque
                            ? '0 12px 28px rgba(16,185,129,0.32)'
                            : '0 10px 24px rgba(0,0,0,0.4)',
                          transform: `translateY(${(1 - sMsg) * 32}px) scale(${0.92 + 0.08 * sMsg})`,
                          opacity: sMsg,
                        }}
                      >
                        <div
                          style={{
                            fontFamily,
                            fontSize: 33,
                            fontWeight: 700,
                            color: ehDestaque ? '#ECFDF5' : CORES.texto,
                            lineHeight: 1.24,
                          }}
                        >
                          {msg.texto}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })()}
          </div>

          {/* Barra inferior do chat para dar acabamento realista de app sem espaço vazio */}
          <div
            style={{
              padding: '14px 24px',
              backgroundColor: '#09101F',
              borderTop: '1.5px solid rgba(16,185,129,0.28)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 14,
            }}
          >
            <div
              style={{
                flex: 1,
                padding: '10px 20px',
                borderRadius: 999,
                backgroundColor: 'rgba(30,41,59,0.75)',
                border: '1.5px solid rgba(255,255,255,0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: CORES.marcaBrilho,
                }}
              >
                Follow-up em andamento
              </span>
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  backgroundColor: CORES.marca,
                  boxShadow: `0 0 12px ${CORES.marca}`,
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — DONO / O RESULTADO (19.71s a 27.89s -> 246 frames)
// Composição (h) + (g): Punch-in 1.15x no dono + checklist sincronizado com micro-bump
// ============================================================================
const Cena3DonoResultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.round((27.89 - 19.71) * fps); // 245
  const tAbs = 19.71 + frame / fps;

  const entrada = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const saida = interpolate(tAbs, [27.54, 27.86], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Punch-in digital de 1.18x a 1.24x para diferenciar do plano médio da Cena 1,
  // rebaixado em panY (+145px a +128px) e deslocado levemente à esquerda para tirar o tablet apagado e garantir amplo headroom
  const zoomVideo = interpolate(frame, [0, duracaoFrames], [1.18, 1.24], {
    extrapolateRight: 'clamp',
  });
  const panYVideo = interpolate(frame, [0, duracaoFrames], [145, 128], {
    extrapolateRight: 'clamp',
  });
  const panXVideo3 = interpolate(frame, [0, duracaoFrames], [-38, -28], {
    extrapolateRight: 'clamp',
  });

  // 3 itens sincronizados rigorosamente com a locução (21.5s, 23.0s, 24.2s)
  const tarefas = [
    {nome: 'Follow-up', tAtiva: 21.5, tFimFala: 22.65},
    {nome: 'Agendamento', tAtiva: 23.0, tFimFala: 23.85},
    {nome: 'Pesquisa', tAtiva: 24.2, tFimFala: 25.1},
  ];

  // Frase final da cena ("para não deixar nenhum cliente sem retorno" -> 24.98s)
  const sRetorno = spring({
    frame: Math.round((tAbs - 24.85) * fps),
    fps,
    config: {damping: 13, stiffness: 140},
  });

  return (
    <AbsoluteFill style={{opacity: entrada * saida, backgroundColor: CORES.fundoEscuro}}>
      <AbsoluteFill
        style={{
          overflow: 'hidden',
          transform: `translateX(${panXVideo3}px) translateY(${panYVideo}px) scale(${zoomVideo})`,
          transformOrigin: '50% 48%',
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
      </AbsoluteFill>
      <VinhetaBaseMesa modoAtivo={true} tAbs={tAbs} />

      {/* TOPO EXCLUSIVO (y=156 a 355) — Cabelo e cabeça do dono 100% livres abaixo de y=485 */}
      <div
        style={{
          position: 'absolute',
          top: 156,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {/* Cabeçalho de rótulo */}
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <div
            style={{
              padding: '6px 22px',
              borderRadius: 999,
              backgroundColor: CORES.marca,
              boxShadow: '0 8px 20px rgba(0,0,0,0.45)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#052E16',
                textTransform: 'uppercase',
              }}
            >
              O resultado
            </span>
          </div>

          {tAbs >= 24.85 && (
            <div
              style={{
                padding: '6px 20px',
                borderRadius: 999,
                backgroundColor: CORES.cardSolido,
                border: `2px solid ${CORES.marca}`,
                transform: `scale(${sRetorno})`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: CORES.marcaBrilho,
                }}
              >
                Nenhum cliente sem retorno
              </span>
            </div>
          )}
        </div>

        {/* Régua de 3 tarefas delegadas que acendem uma a uma sincronizadas com a locução */}
        <div
          style={{
            display: 'flex',
            gap: 14,
            width: '100%',
          }}
        >
          {tarefas.map((item, idx) => {
            const ativo = tAbs >= item.tAtiva;
            const falandoAgora = tAbs >= item.tAtiva && tAbs <= item.tFimFala;
            // Pop de escala (1.12x -> 1.0x) sincronizado quando cada item é ativado pela voz
            const bump = ativo
              ? interpolate(
                  tAbs,
                  [item.tAtiva, item.tAtiva + 0.16, item.tAtiva + 0.45],
                  [0.95, 1.12, 1.0],
                  {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
                )
              : 0.96;

            return (
              <div
                key={idx}
                style={{
                  flex: 1,
                  padding: '12px 14px',
                  borderRadius: 20,
                  backgroundColor: ativo ? '#065F46' : 'rgba(15, 23, 42, 0.95)',
                  border: `3px solid ${ativo ? (falandoAgora ? CORES.marcaBrilho : CORES.marca) : 'rgba(203, 213, 225, 0.42)'}`,
                  boxShadow: ativo
                    ? '0 14px 30px rgba(16,185,129,0.45)'
                    : '0 10px 24px rgba(0,0,0,0.65)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 6,
                  opacity: 1,
                  transform: `scale(${bump})`,
                }}
              >
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: '50%',
                    backgroundColor: ativo ? CORES.marca : 'rgba(226, 232, 240, 0.18)',
                    border: ativo ? 'none' : '2.5px dashed #E2E8F0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {ativo ? (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M20 6L9 17L4 12"
                        stroke="#052E16"
                        strokeWidth="3.4"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : (
                    <div
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        backgroundColor: '#E2E8F0',
                      }}
                    />
                  )}
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: ativo ? CORES.texto : '#E2E8F0',
                    textAlign: 'center',
                  }}
                >
                  {item.nome}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL / CTA (27.54s a 31.48s -> 119 frames)
// Fundo desfocado + slow zoom-in + marca grande + 1 frase + botão pulsando + @agentesdeia.ia acima de y=1400
// ============================================================================
const Cena4CartaoFinal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.ceil((31.48 - 27.54) * fps); // 119

  // Todos os elementos entram desde o primeiro frame com 100% de opacidade garantida no badge @agentesdeia.ia
  const sLogo = spring({frame: frame + 4, fps, config: {damping: 11, stiffness: 150}});
  const sTexto = spring({frame: frame + 2, fps, config: {damping: 12, stiffness: 150}});
  const sBotao = spring({frame: frame + 4, fps, config: {damping: 11, stiffness: 150}});

  // Slow push-in contínuo na composição inteira (1.0 -> 1.05)
  const zoomCena = interpolate(frame, [0, duracaoFrames], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Pulso contínuo de escala (heartbeat) no botão e no badge
  const pulsoBotao = 1.03 + Math.sin(frame / 5.5) * 0.04;
  const pulsoArroba = 1.0 + Math.cos(frame / 7.0) * 0.022;

  // Efeito de brilho passando (shimmer sweep) contínuo no botão 'CHAME NO DIRECT'
  const brilhoX = interpolate(frame % 42, [0, 42], [-180, 820]);

  // Leve flutuação e rotação sutil no logo da marca
  const floatLogo = Math.sin(frame / 9.5) * 8;
  const rotLogo = Math.sin(frame / 13.0) * 2.5;

  // Pulso no brilho/sombra do botão
  const glowBotao = 0.55 + Math.sin(frame / 7.3) * 0.25;

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <FundoFotoVivo foto="img_4.jpg" duracaoFrames={duracaoFrames} blur={16} escurecer={0.72} />

      <AbsoluteFill
        style={{
          transform: `scale(${zoomCena})`,
          transformOrigin: '50% 45%',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 200,
            bottom: 540,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Bloco da Marca — entra caindo do topo com overshoot elástico */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 18,
              transform: `translateY(${(1 - sLogo) * -65 + floatLogo}px) rotate(${rotLogo}deg)`,
              opacity: interpolate(sLogo, [0, 0.3], [0, 1], {extrapolateRight: 'clamp'}),
            }}
          >
            <div
              style={{
                width: 120,
                height: 120,
                borderRadius: 34,
                backgroundColor: CORES.marca,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 20px 45px rgba(16,185,129,0.48)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 56,
                  fontWeight: 900,
                  color: '#052E16',
                }}
              >
                IA
              </span>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 68,
                fontWeight: 900,
                color: CORES.texto,
                textAlign: 'center',
                letterSpacing: -0.5,
                lineHeight: 1.08,
              }}
            >
              Agentes de IA
            </div>

            <div
              style={{
                padding: '10px 28px',
                borderRadius: 999,
                backgroundColor: 'rgba(16,185,129,0.18)',
                border: `2px solid ${CORES.marca}`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: CORES.marcaBrilho,
                }}
              >
                Agente Pessoal IA
              </span>
            </div>
          </div>

          {/* Frase única do que o produto faz — fade-in slide em cascata */}
          <div
            style={{
              fontFamily,
              fontSize: 46,
              fontWeight: 800,
              color: CORES.textoClaro,
              textAlign: 'center',
              lineHeight: 1.24,
              maxWidth: 920,
              transform: `translateY(${(1 - sTexto) * 45}px) scale(${0.92 + 0.08 * sTexto})`,
              opacity: interpolate(sTexto, [0, 0.3], [0, 1], {extrapolateRight: 'clamp'}),
            }}
          >
            {'Delegue tarefas reais a um agente IA: pesquisa, agendamento e follow-up.'}
          </div>

          {/* CTA Principal + @arroba bem acima da zona segura (base em y <= 1380) */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 24,
              width: '100%',
            }}
          >
            <div
              style={{
                position: 'relative',
                overflow: 'hidden',
                padding: '30px 64px',
                borderRadius: 999,
                backgroundColor: CORES.marca,
                boxShadow: `0 22px 50px rgba(16,185,129,${glowBotao})`,
                transform: `translateY(${(1 - sBotao) * 70}px) scale(${sBotao * pulsoBotao})`,
                opacity: interpolate(sBotao, [0, 0.35], [0, 1], {extrapolateRight: 'clamp'}),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 18,
              }}
            >
              {/* Brilho diagonal passando no botão continuamente */}
              <div
                style={{
                  position: 'absolute',
                  top: -50,
                  bottom: -50,
                  left: brilhoX,
                  width: 140,
                  background:
                    'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 50%, rgba(255,255,255,0) 100%)',
                  transform: 'rotate(24deg)',
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#052E16',
                  letterSpacing: 1,
                }}
              >
                CHAME NO DIRECT
              </span>
            </div>

            <div
              style={{
                padding: '14px 36px',
                borderRadius: 999,
                backgroundColor: CORES.cardSolido,
                border: `2.5px solid ${CORES.marca}`,
                boxShadow: '0 10px 25px rgba(0,0,0,0.6)',
                transform: `scale(${pulsoArroba})`,
                opacity: 1,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 800,
                  color: CORES.texto,
                }}
              >
                @agentesdeia.ia
              </span>
            </div>
          </div>
        </div>
      </AbsoluteFill>
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

  // Volume da trilha: ~0.10 com fala, fade in no início e fade out no fim
  const volTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 25, durationInFrames],
    [0, 0.1, 0.1, 0.02],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, fontFamily}}>
      {/* Áudios */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {/* CENA 0: 0.00s -> 4.76s */}
      <Sequence from={0} durationInFrames={Math.ceil(4.76 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 4.41s -> 12.60s */}
      <Sequence
        from={Math.floor(4.41 * fps)}
        durationInFrames={Math.ceil((12.6 - 4.41) * fps)}
      >
        <Cena1DonoProblema />
      </Sequence>

      {/* CENA 2: 12.25s -> 20.06s */}
      <Sequence
        from={Math.floor(12.25 * fps)}
        durationInFrames={Math.ceil((20.06 - 12.25) * fps)}
      >
        <Cena2Conversa />
      </Sequence>

      {/* CENA 3: 19.71s -> 27.89s */}
      <Sequence
        from={Math.floor(19.71 * fps)}
        durationInFrames={Math.ceil((27.89 - 19.71) * fps)}
      >
        <Cena3DonoResultado />
      </Sequence>

      {/* CENA 4: 27.54s -> 31.48s */}
      <Sequence
        from={Math.floor(27.54 * fps)}
        durationInFrames={TOTAL_FRAMES - Math.floor(27.54 * fps)}
      >
        <Cena4CartaoFinal />
      </Sequence>

      {/* Barra de progresso fina no topo dentro da Safe Zone (y=152) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 999,
          backgroundColor: 'rgba(255,255,255,0.18)',
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: CORES.marca,
            borderRadius: 999,
          }}
        />
      </div>

      {/* Karaokê oficial (desligado no cartão final: t < 27.54s) — base=480 mantém limite inferior em y=1440 (bem acima de y=1540 e dentro de 1420-1500) */}
      {t < 27.54 && (
        <Karaoke
          palavras={PALAVRAS_K}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#052E16"
          tamanho={40}
          base={480}
          maxLetras={34}
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
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
