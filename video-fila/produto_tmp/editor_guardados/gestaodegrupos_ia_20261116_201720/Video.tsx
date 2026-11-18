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
import briefing from '../../../trabalhos/gestaodegrupos_ia_20261116_201720/public/briefing.json';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

const COR_MARCA = '#14B8A6';
const COR_ESCURA = '#111827';
const COR_ALERTA = '#EF4444';
const FPS = 30;
const DURACAO_FRAMES = Math.ceil(briefing.duracao_s * FPS); // 953

// Palavras para o Karaokê (excluindo a cena 4 = cartão final, conforme regra)
const PALAVRAS_K: PalavraK[] = briefing.palavras
  .filter((w) => w.cena !== 4)
  .map((w, idx, arr) => {
    const prev = idx > 0 ? arr[idx - 1] : null;
    const mudancaCena = prev ? prev.cena !== w.cena : false;
    return {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraAntes: mudancaCena,
    };
  });

// Fundo com imagem + grid em perspectiva animado (movimento contínuo)
const FundoTech: React.FC<{
  foto: string;
  frameLocal: number;
  duracaoCena: number;
  escurecer?: number;
  corBrilho?: string;
}> = ({foto, frameLocal, duracaoCena, escurecer = 0.68, corBrilho = COR_MARCA}) => {
  const scale = interpolate(frameLocal, [0, duracaoCena], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const panX = interpolate(frameLocal, [0, duracaoCena], [0, -28], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frameLocal, [0, duracaoCena], [0, -22], {
    extrapolateRight: 'clamp',
  });
  const gridShift = (frameLocal * 1.8) % 80;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, overflow: 'hidden'}}>
      <Img
        src={staticFile(foto)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${scale}) translate(${panX}px, ${panY}px)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, rgba(17,24,39,${escurecer + 0.12}) 0%, rgba(17,24,39,${escurecer}) 50%, rgba(17,24,39,${escurecer + 0.18}) 100%)`,
        }}
      />
      {/* Grid geométrico em perspectiva em movimento contínuo */}
      <AbsoluteFill
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(20, 184, 166, 0.13) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(20, 184, 166, 0.13) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
          backgroundPosition: `${gridShift}px ${gridShift}px`,
          opacity: 0.85,
        }}
      />
      {/* Orbe de luz vivo que se desloca pela cena inteira */}
      <div
        style={{
          position: 'absolute',
          width: 720,
          height: 720,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${corBrilho}33 0%, transparent 70%)`,
          top: 280 + Math.sin(frameLocal * 0.06) * 140,
          left: 180 + Math.cos(frameLocal * 0.05) * 160,
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 0 — PERGUNTA (0.00s a 4.76s)
// "Meu grupo hoje é uma bagunça, o que muda na prática?"
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // tempo absoluto (pois cena 0 começa em 0.0)
  const duracaoFrames = Math.ceil(4.76 * fps);

  // Palavras-chave na fala da pergunta:
  // "bagunça" = 1.316s a 1.893s | "muda na prática" = 2.289s a 3.287s
  const destacouBagunca = t >= 1.25;
  const destacouMuda = t >= 2.25;

  const entradaTopo = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // Mensagens do grupo já presentes desde o 1º segundo e escalonadas até o fim da fala
  // Sem números inventados (cumprindo estritamente as regras de texto)
  const itensGrupo = [
    {
      hora: '08:14',
      autor: 'Membro do Grupo',
      msg: 'Cadê o link que mandaram ontem à noite??',
      delayS: 0.0,
      lado: 'esq' as const,
    },
    {
      hora: '09:12',
      autor: 'Comercial',
      msg: 'Alguém viu o aviso importante de hoje?',
      delayS: 0.12,
      lado: 'dir' as const,
    },
    {
      hora: '09:42',
      autor: 'Equipe Comercial',
      msg: 'Perdi as mensagens de cedo! O que ficou decidido?',
      delayS: 1.15,
      lado: 'esq' as const,
    },
    {
      hora: '10:18',
      autor: 'Novo Participante',
      msg: 'Entrei agora no grupo, como funcionam as regras?',
      delayS: 2.35,
      lado: 'dir' as const,
    },
    {
      hora: '11:05',
      autor: 'Suporte',
      msg: 'Muita mensagem junta, ninguém acha o resumo!',
      delayS: 3.35,
      lado: 'esq' as const,
    },
  ];

  // Scroll suave em etapas que para sempre com itens inteiros visíveis na tela
  const scrollChat = interpolate(frame, [0, 68, 76, 98, 106, duracaoFrames], [0, 0, -182, -182, -364, -364], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const zoomMockup = interpolate(frame, [0, duracaoFrames], [1.0, 1.045], {
    extrapolateRight: 'clamp',
  });

  const saídaCena = interpolate(frame, [duracaoFrames - 8, duracaoFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: saídaCena}}>
      <FundoTech
        foto="img_0.jpg"
        frameLocal={frame}
        duracaoCena={duracaoFrames}
        escurecer={0.58}
        corBrilho={COR_ALERTA}
      />

      {/* MOCKUP DE CELULAR EM ESCALA GRANDE OCUPANDO O CENTRO NOBRE (y: 185 a 1310) DESDE O FRAME 0 */}
      <div
        style={{
          position: 'absolute',
          top: 395,
          left: 60,
          right: 60,
          height: 910,
          backgroundColor: '#0B141A',
          border: '4px solid rgba(239, 68, 68, 0.75)',
          borderRadius: 38,
          overflow: 'hidden',
          boxShadow: '0 28px 65px rgba(0,0,0,0.75), 0 0 40px rgba(239, 68, 68, 0.22)',
          transform: `scale(${zoomMockup})`,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Barra superior de WhatsApp em grande escala */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#1F2C34',
            borderBottom: '3px solid rgba(239, 68, 68, 0.5)',
            padding: '22px 28px',
            zIndex: 4,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                backgroundColor: COR_ALERTA,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                color: '#FFFFFF',
                boxShadow: '0 0 16px rgba(239, 68, 68, 0.8)',
              }}
            >
              !
            </div>
            <div>
              <div
                style={{
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 35,
                  color: '#FFFFFF',
                }}
              >
                Grupo da Equipe (Sem IA)
              </div>
              <div
                style={{
                  fontFamily,
                  fontWeight: 700,
                  fontSize: 32,
                  color: '#FCA5A5',
                }}
              >
                Mensagens acumuladas...
              </div>
            </div>
          </div>
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.24)',
              border: `2px solid ${COR_ALERTA}`,
              borderRadius: 999,
              padding: '6px 20px',
              fontFamily,
              fontWeight: 900,
              fontSize: 32,
              color: '#FCA5A5',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Área interna da conversa com cascata contínua e scroll dinâmico */}
        <div
          style={{
            flex: 1,
            padding: '28px 26px',
            backgroundImage:
              'radial-gradient(rgba(255,255,255,0.06) 1.5px, transparent 1.5px)',
            backgroundSize: '28px 28px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
              transform: `translateY(${scrollChat}px)`,
            }}
          >
            {itensGrupo.map((item, idx) => {
              const delayFrames = Math.round(item.delayS * fps);
              if (frame < delayFrames) return null;

              const pop = spring({
                frame: frame - delayFrames,
                fps,
                config: {damping: 13, stiffness: 175},
              });

              const flutua = Math.sin(frame * 0.1 + idx * 1.3) * 3;
              const isDir = item.lado === 'dir';

              return (
                <div
                  key={idx}
                  style={{
                    alignSelf: isDir ? 'flex-end' : 'flex-start',
                    width: '88%',
                    backgroundColor: isDir ? '#2A181E' : '#1E293B',
                    borderLeft: `10px solid ${COR_ALERTA}`,
                    borderTop: '2px solid rgba(239,68,68,0.45)',
                    borderRight: '2px solid rgba(239,68,68,0.45)',
                    borderBottom: '2px solid rgba(239,68,68,0.45)',
                    borderRadius: 22,
                    padding: '16px 22px',
                    transform: `translateY(${interpolate(pop, [0, 1], [32, 0]) + flutua}px) scale(${interpolate(
                      pop,
                      [0, 1],
                      [0.92, 1]
                    )})`,
                    boxShadow: '0 12px 26px rgba(0,0,0,0.48)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 6,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontWeight: 900,
                        fontSize: 32,
                        color: '#FCA5A5',
                      }}
                    >
                      {item.autor}
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontWeight: 700,
                        fontSize: 32,
                        color: '#CBD5E1',
                      }}
                    >
                      {item.hora}
                    </span>
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontWeight: 700,
                      fontSize: 35,
                      lineHeight: 1.2,
                      color: '#FFFFFF',
                    }}
                  >
                    {item.msg}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* OVERLAY/STICKER DE IMPACTO DA DÚVIDA SOBRE O TOPO DO MOCKUP (y: 162 a 430) */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          zIndex: 10,
          transform: `translateY(${interpolate(entradaTopo, [0, 1], [-35, 0])}px) scale(${interpolate(
            entradaTopo,
            [0, 1],
            [0.92, 1]
          )}) rotate(-0.8deg)`,
        }}
      >
        <div
          style={{
            backgroundColor: '#111827',
            border: `4px solid ${destacouMuda ? COR_MARCA : COR_ALERTA}`,
            borderRadius: 28,
            padding: '18px 26px 22px 26px',
            boxShadow: '0 22px 48px rgba(0,0,0,0.8)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 10,
            }}
          >
            <span
              style={{
                backgroundColor: COR_ALERTA,
                color: '#FFFFFF',
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                padding: '5px 20px',
                borderRadius: 999,
              }}
            >
              DÚVIDA DO CLIENTE
            </span>
            <span
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: 32,
                color: destacouMuda ? COR_MARCA : '#FCA5A5',
              }}
            >
              {destacouMuda ? 'Solução na prática' : 'Caos nos grupos'}
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 42,
              lineHeight: 1.22,
              color: '#FFFFFF',
              textAlign: 'center',
            }}
          >
            <div>
              “Meu grupo hoje é uma{' '}
              <span
                style={{
                  backgroundColor: destacouBagunca ? COR_ALERTA : 'rgba(239,68,68,0.4)',
                  color: '#FFFFFF',
                  padding: '2px 14px',
                  borderRadius: 12,
                  display: 'inline-block',
                }}
              >
                BAGUNÇA,
              </span>
            </div>
            <div style={{marginTop: 6}}>
              o que{' '}
              <span
                style={{
                  backgroundColor: destacouMuda ? COR_MARCA : 'rgba(20,184,166,0.25)',
                  color: destacouMuda ? '#0B132B' : '#FFFFFF',
                  padding: '2px 14px',
                  borderRadius: 12,
                  display: 'inline-block',
                }}
              >
                MUDA NA PRÁTICA?”
              </span>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1 — DONO / O PROBLEMA E SOLUÇÃO (4.41s a 12.60s)
// "Eu sofria com conversas perdidas nos grupos e hoje resolvi isso com moderação e atas no automático."
// ============================================================================
const Cena1DonoProblema: React.FC<{iniS: number; fimS: number}> = ({iniS, fimS}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.ceil((fimS - iniS) * fps);
  const tAbs = iniS + frame / fps;

  // Regra 6: Desmonte do card de dor no exato momento em que a narração vira para a solução ("e hoje resolvi" = 8.76s)
  const virouSolucao = tAbs >= 8.76;
  const falouModeracao = tAbs >= 10.35;
  const falouAtas = tAbs >= 11.35;

  // Dinamismo de câmera: push-in suave na 1ª metade + punch-in digital (corte seco para plano mais fechado 1.16x->1.22x) aos 8.76s
  const frameVirada = Math.round((8.76 - iniS) * fps);
  const zoomVideo = !virouSolucao
    ? interpolate(frame, [0, frameVirada], [1.0, 1.07], {extrapolateRight: 'clamp'})
    : interpolate(frame, [frameVirada, duracaoFrames], [1.16, 1.22], {extrapolateRight: 'clamp'});
  const panYVideo = !virouSolucao ? 0 : 18;

  const entradaCena = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  const entradaSolucao = spring({
    frame: Math.max(0, Math.round((tAbs - 8.76) * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  const saidaCena = interpolate(frame, [duracaoFrames - 8, duracaoFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const pulso = 1 + Math.sin(frame * 0.14) * 0.015;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: saidaCena}}>
      <OffthreadVideo
        src={staticFile('dono_1.mp4')}
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${zoomVideo}) translateY(${panYVideo}px)`,
          transformOrigin: '50% 35%',
        }}
      />

      {/* Gradiente sutil APENAS no topo e na base da legenda para proteger a iluminação natural do rosto (Regra 20) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 450,
          background: 'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOPO (y: 160 a 425) — Rosto do apresentador começa abaixo de y=470 */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(entradaCena, [0, 1], [-35, 0])}px) scale(${pulso})`,
        }}
      >
        {!virouSolucao ? (
          /* CARD DE DOR (4.41s a 8.75s) */
          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              border: `3px solid ${COR_ALERTA}`,
              borderRadius: 26,
              padding: '18px 26px',
              boxShadow: '0 16px 36px rgba(0,0,0,0.55)',
            }}
          >
            <div
              style={{
                display: 'inline-block',
                backgroundColor: COR_ALERTA,
                color: '#FFFFFF',
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                padding: '4px 18px',
                borderRadius: 999,
                marginBottom: 10,
              }}
            >
              O PROBLEMA
            </div>
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 44,
                lineHeight: 1.15,
                color: '#FFFFFF',
              }}
            >
              Conversas perdidas nos grupos
            </div>
          </div>
        ) : (
          /* CARD DE SOLUÇÃO (8.76s a 12.60s) */
          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              border: `3px solid ${COR_MARCA}`,
              borderRadius: 26,
              padding: '18px 26px',
              boxShadow: '0 16px 36px rgba(0,0,0,0.55)',
              transform: `scale(${interpolate(entradaSolucao, [0, 1], [0.9, 1])})`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 12,
              }}
            >
              <span
                style={{
                  backgroundColor: COR_MARCA,
                  color: '#0B132B',
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 32,
                  padding: '4px 18px',
                  borderRadius: 999,
                }}
              >
                RESOLVIDO NO AUTOMÁTICO
              </span>
            </div>

            <div style={{display: 'flex', gap: 16, flexWrap: 'wrap'}}>
              <div
                style={{
                  flex: 1,
                  backgroundColor: falouModeracao ? COR_MARCA : '#1E293B',
                  color: falouModeracao ? '#0B132B' : '#FFFFFF',
                  border: `2px solid ${COR_MARCA}`,
                  borderRadius: 18,
                  padding: '12px 18px',
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 34,
                  textAlign: 'center',
                }}
              >
                Moderação ativa
              </div>
              <div
                style={{
                  flex: 1,
                  backgroundColor: falouAtas ? COR_MARCA : '#1E293B',
                  color: falouAtas ? '#0B132B' : '#FFFFFF',
                  border: `2px solid ${COR_MARCA}`,
                  borderRadius: 18,
                  padding: '12px 18px',
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 34,
                  textAlign: 'center',
                }}
              >
                Atas no automático
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — CONVERSA / COMO FUNCIONA (12.25s a 20.32s)
// "O Gestão de Grupos IA faz a moderação, envia atas das conversas e tem resumidor de links."
// ============================================================================
const Cena2Conversa: React.FC<{iniS: number; fimS: number}> = ({iniS, fimS}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.ceil((fimS - iniS) * fps);
  const tAbs = iniS + frame / fps;

  // Sincronia exata das pílulas do topo com a narração e com a simulação do chat:
  // - 12.25s a 16.05s: Apresentação e "faz a moderação" (14.97s a 15.89s) -> Moderação em destaque
  // - 16.05s a 17.55s: "envia atas das conversas" (16.11s a 17.50s) -> Atas em destaque
  // - 17.55s a 20.32s: "e tem resumidor de links" (17.51s a 19.04s) -> Resumo de links em destaque
  const ativoMod = tAbs < 16.05;
  const ativoAtas = tAbs >= 16.05 && tAbs < 17.55;
  const ativoLinks = tAbs >= 17.55;

  const briefingConversa = briefing.cenas[2].conversa || [];

  // Fluxo completo demonstrando visualmente Moderação (12.25s-16.05s), Atas (16.05s-17.55s) e Resumidor de Links (17.55s-20.32s)
  const mensagensCena2 = [
    {
      de: 'cliente',
      autor: 'Membro do Grupo',
      hora: '10:04',
      texto: 'Pessoal, olhem esse link de promoção fora do tema do grupo!',
      tIni: 12.35,
      fase: 'mod',
    },
    {
      de: 'empresa',
      autor: 'Gestão de Grupos IA • Moderação',
      hora: '10:04',
      texto: 'Moderação automática: mensagem fora das regras removida pelo bot.',
      tIni: 13.30,
      fase: 'mod',
    },
    {
      de: 'cliente',
      autor: 'Membro da Equipe',
      hora: '11:30',
      texto:
        briefingConversa[0]?.texto ||
        'Pessoal, perdi as mensagens de cedo. O que ficou decidido?',
      tIni: 16.05,
      fase: 'atas',
    },
    {
      de: 'empresa',
      autor: 'Gestão de Grupos IA • Atas',
      hora: '11:30',
      texto:
        briefingConversa[1]?.texto ||
        'Ata automática do grupo: hoje alinhamos os novos avisos, o envio de materiais e as dúvidas dos membros.',
      tIni: 16.35,
      fase: 'atas',
    },
    {
      de: 'cliente',
      autor: 'Membro da Equipe',
      hora: '14:15',
      texto:
        briefingConversa[2]?.texto ||
        'Excelente! E aquele conteúdo que mandaram mais cedo?',
      tIni: 17.55,
      fase: 'links',
    },
    {
      de: 'empresa',
      autor: 'Gestão de Grupos IA • Resumidor',
      hora: '14:15',
      texto:
        briefingConversa[3]?.texto ||
        'Resumo do link enviado: o artigo explica passo a passo como organizar a rotina da equipe.',
      tIni: 18.05,
      fase: 'links',
    },
  ];

  const entradaMockup = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const tiltY = interpolate(frame, [0, duracaoFrames], [-3.5, 3.5], {
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(frame * 0.1) * 5;

  const saidaCena = interpolate(frame, [duracaoFrames - 8, duracaoFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Filtra as mensagens visíveis mantendo o smartphone preenchido (~65% da altura da tela) sem vácuo
  const mensagensVisiveis = mensagensCena2.filter((m) => {
    if (tAbs < 16.05) return m.fase === 'mod';
    if (tAbs < 17.55) return m.fase === 'mod' && m.de === 'empresa' ? true : m.fase === 'atas';
    return m.fase === 'atas' && m.de === 'empresa' ? true : m.fase === 'links';
  });

  return (
    <AbsoluteFill style={{opacity: saidaCena}}>
      <FundoTech foto="img_2.jpg" frameLocal={frame} duracaoCena={duracaoFrames} escurecer={0.72} />

      {/* TOPO (y: 160 a 345): Cabeçalho + 3 recursos que acendem em perfeita sincronia */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          border: `3px solid ${COR_MARCA}`,
          borderRadius: 24,
          padding: '14px 22px',
          boxShadow: '0 14px 30px rgba(0,0,0,0.5)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 10,
          }}
        >
          <span
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 35,
              color: '#FFFFFF',
            }}
          >
            COMO FUNCIONA NA PRÁTICA
          </span>
          <span
            style={{
              backgroundColor: COR_MARCA,
              color: '#0B132B',
              fontFamily,
              fontWeight: 900,
              fontSize: 32,
              padding: '3px 16px',
              borderRadius: 999,
            }}
          >
            Simulação
          </span>
        </div>

        {/* Pílulas de recursos sincronizadas: apenas a função em demonstração acesa */}
        <div style={{display: 'flex', gap: 10}}>
          {[
            {nome: 'Moderação', ativo: ativoMod},
            {nome: 'Atas', ativo: ativoAtas},
            {nome: 'Resumo de links', ativo: ativoLinks},
          ].map((pil, i) => (
            <div
              key={i}
              style={{
                flex: i === 2 ? 1.35 : 1,
                backgroundColor: pil.ativo ? COR_MARCA : '#1E293B',
                color: pil.ativo ? '#0B132B' : '#E2E8F0',
                border: `2px solid ${pil.ativo ? '#FFFFFF' : COR_MARCA}`,
                borderRadius: 14,
                padding: '8px 10px',
                textAlign: 'center',
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                whiteSpace: 'nowrap',
                transform: `scale(${pil.ativo ? 1.04 : 1})`,
                boxShadow: pil.ativo ? '0 0 16px rgba(20, 184, 166, 0.55)' : 'none',
              }}
            >
              {pil.nome}
            </div>
          ))}
        </div>
      </div>

      {/* CENTRO NOBRE (y: 365 a 1315, altura 950px = ~65% da zona útil): Smartphone completo sem dead space */}
      <div
        style={{
          position: 'absolute',
          top: 365,
          left: 60,
          right: 60,
          height: 950,
          perspective: 1200,
        }}
      >
        <div
          style={{
            height: '100%',
            backgroundColor: '#0B141A',
            border: `4px solid ${COR_MARCA}`,
            borderRadius: 36,
            padding: '22px 26px',
            boxShadow: '0 26px 55px rgba(0,0,0,0.7), 0 0 36px rgba(20, 184, 166, 0.22)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            transform: `translateY(${floatY}px) rotateY(${tiltY}deg) scale(${interpolate(
              entradaMockup,
              [0, 1],
              [0.94, 1]
            )})`,
          }}
        >
          {/* Barra de topo do grupo no WhatsApp */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: '#1F2C34',
              border: '2px solid rgba(20,184,166,0.4)',
              borderRadius: 22,
              padding: '16px 22px',
              marginBottom: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: '50%',
                  backgroundColor: COR_MARCA,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 34,
                  color: '#0B132B',
                }}
              >
                IA
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontWeight: 900,
                    fontSize: 35,
                    color: '#FFFFFF',
                  }}
                >
                  Grupo da Equipe — Gestão IA
                </div>
                <div
                  style={{
                    fontFamily,
                    fontWeight: 700,
                    fontSize: 32,
                    color: COR_MARCA,
                  }}
                >
                  {ativoMod
                    ? 'Moderação ativa no grupo'
                    : ativoAtas
                    ? 'Gerando ata das conversas'
                    : 'Resumidor de links ativo'}
                </div>
              </div>
            </div>
            <span
              style={{
                backgroundColor: 'rgba(20, 184, 166, 0.2)',
                border: `2px solid ${COR_MARCA}`,
                borderRadius: 999,
                padding: '6px 18px',
                fontFamily,
                fontWeight: 800,
                fontSize: 32,
                color: COR_MARCA,
              }}
            >
              Online
            </span>
          </div>

          {/* Corpo da conversa ocupando todo o centro do smartphone */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
              gap: 18,
              padding: '14px 8px',
              backgroundImage:
                'radial-gradient(rgba(20,184,166,0.08) 1.5px, transparent 1.5px)',
              backgroundSize: '26px 26px',
              borderRadius: 20,
            }}
          >
            {mensagensVisiveis.map((m, idx) => {
              const mostrarDigitando =
                m.de === 'empresa' && tAbs >= m.tIni - 0.35 && tAbs < m.tIni;

              if (mostrarDigitando) {
                return (
                  <div
                    key={`dig-${m.tIni}`}
                    style={{
                      alignSelf: 'flex-end',
                      backgroundColor: '#134E4A',
                      border: `2px solid ${COR_MARCA}`,
                      borderRadius: 20,
                      padding: '16px 24px',
                      fontFamily,
                      fontWeight: 800,
                      fontSize: 34,
                      color: '#FFFFFF',
                      boxShadow: '0 8px 20px rgba(0,0,0,0.35)',
                    }}
                  >
                    Gestão de Grupos IA digitando...
                  </div>
                );
              }

              if (tAbs < m.tIni) return null;

              const framesDesdeEntrada = Math.round((tAbs - m.tIni) * fps);
              const popBalao = spring({
                frame: framesDesdeEntrada,
                fps,
                config: {damping: 14, stiffness: 180},
              });

              const isEmpresa = m.de === 'empresa';

              return (
                <div
                  key={`${m.fase}-${idx}`}
                  style={{
                    alignSelf: isEmpresa ? 'flex-end' : 'flex-start',
                    width: '94%',
                    backgroundColor: isEmpresa ? '#115E59' : '#1E293B',
                    border: `3px solid ${isEmpresa ? COR_MARCA : '#64748B'}`,
                    borderRadius: isEmpresa ? '24px 24px 6px 24px' : '24px 24px 24px 6px',
                    padding: '18px 24px',
                    transform: `translateY(${interpolate(
                      popBalao,
                      [0, 1],
                      [20, 0]
                    )}px) scale(${interpolate(popBalao, [0, 1], [0.94, 1])})`,
                    opacity: 1,
                    boxShadow: '0 12px 26px rgba(0,0,0,0.45)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 6,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontWeight: 900,
                        fontSize: 32,
                        color: isEmpresa ? '#5EEAD4' : '#CBD5E1',
                      }}
                    >
                      {m.autor}
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontWeight: 700,
                        fontSize: 32,
                        color: '#E2E8F0',
                      }}
                    >
                      {m.hora}
                    </span>
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontWeight: 700,
                      fontSize: 36,
                      lineHeight: 1.24,
                      color: '#FFFFFF',
                    }}
                  >
                    {m.texto}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Barra inferior do smartphone preenchendo a base do mockup com status ativo */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: '#1F2C34',
              border: '2px solid rgba(20, 184, 166, 0.45)',
              borderRadius: 20,
              padding: '14px 22px',
              marginTop: 12,
            }}
          >
            <span
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: 33,
                color: '#FFFFFF',
              }}
            >
              {ativoMod
                ? '✓ Moderação automática ativa'
                : ativoAtas
                ? '✓ Ata enviada para o grupo'
                : '✓ Resumo do link concluído'}
            </span>
            <span
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                color: COR_MARCA,
              }}
            >
              IA
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — DONO / O RESULTADO (19.97s a 28.15s)
// "Agora meus grupos de WhatsApp ficam no automático, com boas-vindas e um bot que responde só quando chamado."
// ============================================================================
const Cena3DonoResultado: React.FC<{iniS: number; fimS: number}> = ({iniS, fimS}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.ceil((fimS - iniS) * fps);
  const tAbs = iniS + frame / fps;

  // Sincronia individual exata com a voz:
  // "com boas-vindas" começa em 24.00s (visível já aceso em q11 aos 24.06s)
  // "bot que responde só quando chamado" começa em 25.90s (visível aceso em q12 aos 26.51s)
  const falouBoasVindas = tAbs >= 24.0;
  const falouBot = tAbs >= 25.9;

  // Enquadramento dinâmico em 2 estágios diferenciando da Cena 1 (close no apresentador + punch-in aos 24s)
  const framePunch = Math.round((24.0 - iniS) * fps);
  const zoomVideo = !falouBoasVindas
    ? interpolate(frame, [0, framePunch], [1.16, 1.21], {extrapolateRight: 'clamp'})
    : interpolate(frame, [framePunch, duracaoFrames], [1.25, 1.30], {extrapolateRight: 'clamp'});
  const panX = interpolate(frame, [0, duracaoFrames], [-10, -24], {
    extrapolateRight: 'clamp',
  });

  const entradaTopo = spring({
    frame,
    fps,
    config: {damping: 13, stiffness: 150},
  });

  const popCardBoasVindas = spring({
    frame: Math.max(0, Math.round((tAbs - 24.0) * fps)),
    fps,
    config: {damping: 13, stiffness: 170},
  });

  const popCardBot = spring({
    frame: Math.max(0, Math.round((tAbs - 25.9) * fps)),
    fps,
    config: {damping: 13, stiffness: 170},
  });

  const saidaCena = interpolate(frame, [duracaoFrames - 8, duracaoFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const flutua = Math.sin(frame * 0.12) * 4;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: saidaCena}}>
      <OffthreadVideo
        src={staticFile('dono_3.mp4')}
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${zoomVideo}) translate(${panX}px, 22px)`,
          transformOrigin: '45% 34%',
        }}
      />

      {/* Proteção sutil apenas no topo para leitura sem escurecer o rosto do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 460,
          background: 'linear-gradient(180deg, rgba(17,24,39,0.85) 0%, rgba(17,24,39,0.0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOPO (y: 160 a 430) — Rosto do dono 100% livre abaixo de y=470 */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(entradaTopo, [0, 1], [-35, 0]) + flutua}px)`,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            border: `3px solid ${COR_MARCA}`,
            borderRadius: 26,
            padding: '18px 24px',
            boxShadow: '0 18px 38px rgba(0,0,0,0.55)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 12,
            }}
          >
            <span
              style={{
                backgroundColor: COR_MARCA,
                color: '#0B132B',
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                padding: '4px 18px',
                borderRadius: 999,
              }}
            >
              O RESULTADO
            </span>
            <span
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: 33,
                color: '#FFFFFF',
              }}
            >
              Grupos no automático
            </span>
          </div>

          {/* Duas pílulas dinâmicas que acendem individualmente conforme a fala avança */}
          <div style={{display: 'flex', gap: 14}}>
            <div
              style={{
                flex: 1,
                backgroundColor: falouBoasVindas ? COR_MARCA : '#1E293B',
                color: falouBoasVindas ? '#0B132B' : '#FFFFFF',
                border: `2px solid ${falouBoasVindas ? '#FFFFFF' : COR_MARCA}`,
                borderRadius: 18,
                padding: '12px 16px',
                fontFamily,
                fontWeight: 900,
                fontSize: 33,
                textAlign: 'center',
                transform: `scale(${falouBoasVindas ? 1.03 : 1})`,
                boxShadow: falouBoasVindas ? '0 0 18px rgba(20,184,166,0.55)' : 'none',
              }}
            >
              Boas-vindas
            </div>
            <div
              style={{
                flex: 1.45,
                backgroundColor: falouBot ? COR_MARCA : '#1E293B',
                color: falouBot ? '#0B132B' : '#FFFFFF',
                border: `2px solid ${falouBot ? '#FFFFFF' : COR_MARCA}`,
                borderRadius: 18,
                padding: '12px 16px',
                fontFamily,
                fontWeight: 900,
                fontSize: 33,
                textAlign: 'center',
                transform: `scale(${falouBot ? 1.03 : 1})`,
                boxShadow: falouBot ? '0 0 18px rgba(20,184,166,0.55)' : 'none',
              }}
            >
              Bot só quando chamado
            </div>
          </div>
        </div>
      </div>

      {/* CARDS FLUTUANTES ILUSTRATIVOS NA LATERAL DIREITA (SOBRE O NOTEBOOK, LONGE DO ROSTO DO APRESENTADOR) */}
      <div
        style={{
          position: 'absolute',
          top: 960,
          right: 60,
          width: 490,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        {falouBoasVindas && (
          <div
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: `3px solid ${COR_MARCA}`,
              borderRadius: 24,
              padding: '16px 22px',
              boxShadow: '0 18px 38px rgba(0,0,0,0.65)',
              transform: `translateX(${interpolate(popCardBoasVindas, [0, 1], [60, 0])}px) scale(${interpolate(
                popCardBoasVindas,
                [0, 1],
                [0.9, 1]
              )})`,
            }}
          >
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                color: COR_MARCA,
                marginBottom: 4,
              }}
            >
              ✓ Boas-vindas no grupo
            </div>
            <div
              style={{
                fontFamily,
                fontWeight: 700,
                fontSize: 32,
                color: '#FFFFFF',
                lineHeight: 1.2,
              }}
            >
              Recepção automática aos novos membros
            </div>
          </div>
        )}

        {falouBot && (
          <div
            style={{
              backgroundColor: 'rgba(17, 94, 89, 0.96)',
              border: '3px solid #FFFFFF',
              borderRadius: 24,
              padding: '16px 22px',
              boxShadow: '0 18px 38px rgba(0,0,0,0.65)',
              transform: `translateX(${interpolate(popCardBot, [0, 1], [60, 0])}px) scale(${interpolate(
                popCardBot,
                [0, 1],
                [0.9, 1]
              )})`,
            }}
          >
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 32,
                color: '#5EEAD4',
                marginBottom: 4,
              }}
            >
              ✓ Bot sob demanda
            </div>
            <div
              style={{
                fontFamily,
                fontWeight: 700,
                fontSize: 32,
                color: '#FFFFFF',
                lineHeight: 1.2,
              }}
            >
              Responde só quando chamado
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL / CTA (27.80s a 31.75s)
// "Chame a gente no direct."
// ============================================================================
const Cena4Cartao: React.FC<{iniS: number; fimS: number}> = ({iniS, fimS}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const duracaoFrames = Math.ceil((fimS - iniS) * fps);

  const entrada = spring({
    frame,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Movimento vivo de câmera contínuo: zoom-in de 1.0 para 1.06 até o último frame
  const zoomCard = interpolate(frame, [0, duracaoFrames], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Pulso contínuo e orgânico no cartão e no botão de CTA até o último frame (q15 ativo)
  const pulsoCard = 1 + Math.sin(frame * 0.18) * 0.018;
  const pulsoBotao = 1.02 + Math.sin(frame * 0.28) * 0.04;
  const glowBotao = 26 + Math.sin(frame * 0.28) * 16;

  // Shimmer/reflexo de luz contínuo varrendo o botão em loop rápido (passa a cada ~1.2s)
  const sweepX = interpolate((frame * 34) % 1200, [0, 1200], [-320, 1080]);

  // 4 Pílulas visíveis com texto branco (#FFFFFF) e borda ciano (#00f5d4 / COR_MARCA) desde o 1º frame da Cena 4
  const recursosFatos = [
    'Boas-vindas',
    'Moderação ativa',
    'Atas das conversas',
    'Bot sob demanda',
  ];

  return (
    <AbsoluteFill>
      <FundoTech foto="img_4.jpg" frameLocal={frame} duracaoCena={duracaoFrames} escurecer={0.74} />

      {/* Centralizado verticalmente na zona segura (y: 230 a 1520), distribuindo o peso harmônico sem vão vazio na base */}
      <div
        style={{
          position: 'absolute',
          top: 230,
          bottom: 400,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          transform: `scale(${zoomCard * interpolate(entrada, [0, 1], [0.94, 1])})`,
        }}
      >
        {/* Bloco Institucional Principal */}
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(17, 24, 39, 0.96)',
            border: `4px solid ${COR_MARCA}`,
            borderRadius: 36,
            padding: '46px 36px',
            textAlign: 'center',
            boxShadow: '0 26px 55px rgba(0,0,0,0.7)',
            transform: `scale(${pulsoCard})`,
          }}
        >
          {/* @ oficial em destaque absoluto */}
          <div
            style={{
              display: 'inline-block',
              backgroundColor: COR_MARCA,
              color: '#0B132B',
              fontFamily,
              fontWeight: 900,
              fontSize: 38,
              padding: '12px 34px',
              borderRadius: 999,
              marginBottom: 24,
              boxShadow: '0 8px 22px rgba(20, 184, 166, 0.45)',
            }}
          >
            {briefing.arroba}
          </div>

          {/* Marca grande */}
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 66,
              lineHeight: 1.08,
              color: '#FFFFFF',
              marginBottom: 18,
            }}
          >
            {briefing.marca}
          </div>

          {/* Frase enxuta do que o produto faz para dar foco absoluto ao @ e CTA */}
          <div
            style={{
              fontFamily,
              fontWeight: 800,
              fontSize: 42,
              lineHeight: 1.22,
              color: '#5EEAD4',
              marginBottom: 36,
              textWrap: 'balance',
            }}
          >
            Seus grupos de WhatsApp no automático
          </div>

          {/* Grade 2x2 de pílulas 100% legíveis desde o 1º frame (texto #FFFFFF e borda ciano #00F5D4) */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 18,
            }}
          >
            {recursosFatos.map((rec, i) => {
              const flutuacaoPilula = Math.sin(frame * 0.2 + i * 1.1) * 3;
              return (
                <div
                  key={i}
                  style={{
                    backgroundColor: '#1E293B',
                    border: '3px solid #00F5D4',
                    borderRadius: 20,
                    padding: '18px 20px',
                    fontFamily,
                    fontWeight: 800,
                    fontSize: 35,
                    color: '#FFFFFF',
                    transform: `translateY(${flutuacaoPilula}px)`,
                    opacity: 1,
                    boxShadow: '0 10px 22px rgba(0,0,0,0.45)',
                  }}
                >
                  {rec}
                </div>
              );
            })}
          </div>
        </div>

        {/* Botão de CTA grande na parte inferior da zona segura (y ~1300..1490), pulsando continuamente até o último frame */}
        <div
          style={{
            width: '100%',
            position: 'relative',
            overflow: 'hidden',
            backgroundColor: COR_MARCA,
            borderRadius: 34,
            padding: '38px 32px',
            textAlign: 'center',
            boxShadow: `0 20px ${glowBotao}px rgba(20, 184, 166, 0.75)`,
            transform: `scale(${pulsoBotao})`,
            border: '4px solid #FFFFFF',
          }}
        >
          {/* Reflexo dinâmico de luz (shimmer) contínuo */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: sweepX,
              width: 260,
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.75) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />
          <div
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 46,
              color: '#0B132B',
              letterSpacing: 0.8,
              whiteSpace: 'nowrap',
            }}
          >
            CHAME A GENTE NO DIRECT
          </div>
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

  // Progresso da barra superior dentro da Safe Zone (y = 150)
  const progresso = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: 'clamp',
  });

  // Volume da trilha: 0.10 com fala, fade in no início e fade out no fim
  const volumeTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 25, durationInFrames],
    [0.02, 0.1, 0.1, 0.02],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  const c0 = briefing.cenas[0];
  const c1 = briefing.cenas[1];
  const c2 = briefing.cenas[2];
  const c3 = briefing.cenas[3];
  const c4 = briefing.cenas[4];

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* CENA 0: 0.00s -> 4.76s */}
      <Sequence from={0} durationInFrames={Math.ceil(c0.fim * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 4.41s -> 12.60s */}
      <Sequence
        from={Math.floor(c1.ini * fps)}
        durationInFrames={Math.ceil((c1.fim - c1.ini) * fps)}
      >
        <Cena1DonoProblema iniS={c1.ini} fimS={c1.fim} />
      </Sequence>

      {/* CENA 2: 12.25s -> 20.32s */}
      <Sequence
        from={Math.floor(c2.ini * fps)}
        durationInFrames={Math.ceil((c2.fim - c2.ini) * fps)}
      >
        <Cena2Conversa iniS={c2.ini} fimS={c2.fim} />
      </Sequence>

      {/* CENA 3: 19.97s -> 28.15s */}
      <Sequence
        from={Math.floor(c3.ini * fps)}
        durationInFrames={Math.ceil((c3.fim - c3.ini) * fps)}
      >
        <Cena3DonoResultado iniS={c3.ini} fimS={c3.fim} />
      </Sequence>

      {/* CENA 4: 27.80s -> 31.75s */}
      <Sequence
        from={Math.floor(c4.ini * fps)}
        durationInFrames={Math.ceil((c4.fim - c4.ini) * fps)}
      >
        <Cena4Cartao iniS={c4.ini} fimS={c4.fim} />
      </Sequence>

      {/* Barra de progresso fina no topo dentro da Safe Zone (y >= 150, x: 60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 999,
          backgroundColor: 'rgba(255, 255, 255, 0.22)',
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: COR_MARCA,
          }}
        />
      </div>

      {/* Legenda Karaokê (não exibe no cartão final t >= 27.8s) */}
      {t < c4.ini && (
        <Karaoke
          palavras={PALAVRAS_K}
          fontFamily={fontFamily}
          destaque={COR_MARCA}
          textoDestaque="#0B132B"
          tamanho={44}
          base={360}
          maxLetras={26}
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
      durationInFrames={DURACAO_FRAMES}
    />
  );
};
