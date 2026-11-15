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
  marca: '#0284C7',
  marcaClara: '#38BDF8',
  apoio: '#0F172A',
  fundoEscuro: '#0F172A',
  destaque: '#0284C7',
  textoClaro: '#FFFFFF',
  alerta: '#EF4444',
  sucesso: '#10B981',
};

const DURACAO_S = 31.94;
const FPS = 30;
const TOTAL_FRAMES = Math.ceil(DURACAO_S * FPS);

const PALAVRAS: PalavraK[] = [
  // Cena 0 (0.00 - 5.43)
  {p: 'Sua', ini: 0.318, fim: 0.558},
  {p: 'equipe', ini: 0.57, fim: 0.883},
  {p: 'ainda', ini: 0.895, fim: 1.183, quebraAntes: true},
  {p: 'divide', ini: 1.196, fim: 1.604},
  {p: 'o', ini: 1.616, fim: 1.652, quebraAntes: true},
  {p: 'mesmo', ini: 1.664, fim: 2.013},
  {p: 'aparelho', ini: 2.025, fim: 2.506},
  {p: 'e', ini: 2.518, fim: 2.59, quebraAntes: true},
  {p: 'atropela', ini: 2.602, fim: 3.107},
  {p: 'as', ini: 3.119, fim: 3.203, quebraAntes: true},
  {p: 'conversas?', ini: 3.215, fim: 3.96},

  // Cena 1 (5.08 - 13.27)
  {p: 'Meus', ini: 5.744, fim: 6.384, quebraAntes: true},
  {p: 'vendedores', ini: 6.384, fim: 6.944},
  {p: 'dividiam', ini: 6.944, fim: 7.504, quebraAntes: true},
  {p: 'o', ini: 7.504, fim: 7.644, quebraAntes: true},
  {p: 'mesmo', ini: 7.644, fim: 7.844},
  {p: 'celular', ini: 7.844, fim: 8.304},
  {p: 'sem', ini: 8.304, fim: 8.584, quebraAntes: true},
  {p: 'controle,', ini: 8.584, fim: 9.124},
  {p: 'até', ini: 9.824, fim: 9.944, quebraAntes: true},
  {p: 'eu', ini: 9.944, fim: 10.144},
  {p: 'adotar', ini: 10.144, fim: 10.464},
  {p: 'um', ini: 10.464, fim: 10.704, quebraAntes: true},
  {p: 'CRM', ini: 10.704, fim: 11.284},
  {p: 'feito', ini: 11.284, fim: 11.624},
  {p: 'para', ini: 11.624, fim: 11.804, quebraAntes: true},
  {p: 'o', ini: 11.804, fim: 11.904},
  {p: 'meu', ini: 11.904, fim: 12.064},
  {p: 'negócio.', ini: 12.064, fim: 12.504},

  // Cena 2 (12.92 - 20.51)
  {p: 'A', ini: 13.411, fim: 13.519, quebraAntes: true},
  {p: 'plataforma', ini: 13.531, fim: 14.228},
  {p: 'une', ini: 14.24, fim: 14.444},
  {p: 'o', ini: 14.456, fim: 14.492, quebraAntes: true},
  {p: 'Chatwoot', ini: 14.504, fim: 15.129},
  {p: 'ao', ini: 15.165, fim: 15.322, quebraAntes: true},
  {p: 'helpdesk', ini: 15.334, fim: 15.778},
  {p: 'para', ini: 15.79, fim: 15.983, quebraAntes: true},
  {p: 'separar', ini: 15.995, fim: 16.439},
  {p: 'as', ini: 16.451, fim: 16.56, quebraAntes: true},
  {p: 'conversas', ini: 16.572, fim: 17.173},
  {p: 'por', ini: 17.185, fim: 17.329, quebraAntes: true},
  {p: 'setor', ini: 17.341, fim: 17.737},
  {p: 'sem', ini: 17.75, fim: 17.966, quebraAntes: true},
  {p: 'misturar', ini: 17.978, fim: 18.435},
  {p: 'o', ini: 18.447, fim: 18.507, quebraAntes: true},
  {p: 'atendimento.', ini: 18.519, fim: 19.216},

  // Cena 3 (20.16 - 28.34)
  {p: 'Hoje', ini: 21.101, fim: 21.841, quebraAntes: true},
  {p: 'cada', ini: 22.181, fim: 22.221},
  {p: 'vendedor', ini: 22.221, fim: 22.761},
  {p: 'sabe', ini: 22.761, fim: 23.081, quebraAntes: true},
  {p: 'exatamente', ini: 23.081, fim: 23.941},
  {p: 'quem', ini: 23.941, fim: 24.341, quebraAntes: true},
  {p: 'está', ini: 24.341, fim: 24.581},
  {p: 'atendendo', ini: 24.581, fim: 25.321},
  {p: 'e', ini: 25.741, fim: 25.961, quebraAntes: true},
  {p: 'ninguém', ini: 25.961, fim: 26.261},
  {p: 'mais', ini: 26.261, fim: 26.661},
  {p: 'responde', ini: 26.661, fim: 27.201, quebraAntes: true},
  {p: 'por', ini: 27.201, fim: 27.501},
  {p: 'cima', ini: 27.501, fim: 27.701},
  {p: 'do', ini: 27.701, fim: 27.901, quebraAntes: true},
  {p: 'colega.', ini: 27.901, fim: 28.121},
];

// CENA 0: Pergunta (0.00s - 5.43s)
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const bgScale = interpolate(frame, [0, 163], [1.02, 1.15], {extrapolateRight: 'clamp'});
  const exitOpacity = interpolate(t, [5.05, 5.4], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const enterTitle = spring({frame, fps, config: {damping: 15, stiffness: 240}});
  const divideActive = t >= 1.18;
  const atropelaActive = t >= 2.55;

  // Slow zoom contínuo no cartão de simulação (100% -> 104%) + flutuação para manter tensão visual até o corte
  const cardScale = interpolate(frame, [0, 163], [1.0, 1.04], {extrapolateRight: 'clamp'});
  const phonePop = spring({frame, fps, config: {damping: 15, stiffness: 230}});
  const floatY = Math.sin(frame / 8) * 6;

  // Shake forte no instante do atropelo (2.55s) seguido de micro-vibração contínua
  const framesSinceAtropela = Math.max(0, frame - Math.round(2.55 * fps));
  const impactDecay = atropelaActive ? Math.exp(-framesSinceAtropela / 18) : 0;
  const shakeX = atropelaActive
    ? Math.sin(frame * 1.35) * (9 * impactDecay + 2.5)
    : 0;

  // Balão 1 (Cliente) presente desde o início com pop ágil
  const b1 = spring({frame, fps, config: {damping: 16, stiffness: 260}});

  // Balão 2 (Vendedor A) entra logo aos 0.45s para preencher o gancho nos primeiros 2s
  const f2 = Math.round(0.45 * fps);
  const b2Show = frame >= f2;
  const b2 = b2Show
    ? spring({frame: frame - f2, fps, config: {damping: 14, stiffness: 250}})
    : 0;

  // Balão 3 (Vendedor B atropelando a conversa) entra aos 2.50s com overshoot spring
  const f3 = Math.round(2.5 * fps);
  const b3Show = frame >= f3;
  const b3 = b3Show
    ? spring({frame: frame - f3, fps, config: {damping: 10, stiffness: 240}})
    : 0;

  // Evolução pós-2.7s: indicador de conflito/digitação simultânea que mantém movimento vivo de 2.7s a 5.4s
  const conflictWave = Math.sin(frame / 3.5);
  const b3Scale = atropelaActive
    ? interpolate(b3, [0, 1], [0.88, 1]) + Math.sin(frame / 4) * 0.016
    : 1;
  const b2OverlapY = atropelaActive
    ? interpolate(b3, [0, 1], [0, -6]) + Math.cos(frame / 5) * 2
    : 0;

  return (
    <AbsoluteFill style={{opacity: exitOpacity, fontFamily}}>
      {/* Fundo dinâmico com zoom contínuo + iluminação radial viva (sem cobrir rosto de apresentador) */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale})`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 30%, rgba(56,189,248,0.35) 0%, rgba(15,23,42,0.92) 72%)',
          }}
        />
      </AbsoluteFill>

      {/* TOPO: Gancho e pergunta principal (y: 165..485) */}
      <div
        style={{
          position: 'absolute',
          top: 166,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(enterTitle, [0, 1], [-22, 0])}px)`,
          opacity: enterTitle,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            background: CORES.marca,
            border: '2px solid #BAE6FD',
            padding: '8px 24px',
            borderRadius: 999,
            marginBottom: 14,
            boxShadow: '0 10px 24px rgba(0,0,0,0.45)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: 99,
              background: '#FFFFFF',
              transform: `scale(${1 + Math.sin(frame / 4) * 0.25})`,
            }}
          />
          <span style={{color: '#FFFFFF', fontSize: 33, fontWeight: 800}}>
            Vários atendentes no mesmo celular?
          </span>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid rgba(56, 189, 248, 0.55)',
            borderRadius: 28,
            padding: '20px 28px',
            boxShadow: '0 18px 40px rgba(0,0,0,0.55)',
          }}
        >
          <div
            style={{
              color: '#FFFFFF',
              fontSize: 45,
              fontWeight: 900,
              lineHeight: 1.18,
              letterSpacing: -0.5,
            }}
          >
            Sua equipe ainda{' '}
            <span
              style={{
                color: divideActive ? '#38BDF8' : '#FFFFFF',
                textDecoration: divideActive ? 'underline' : 'none',
                textDecorationColor: '#38BDF8',
                textUnderlineOffset: 6,
              }}
            >
              divide o mesmo aparelho
            </span>{' '}
            e{' '}
            <span
              style={{
                color: atropelaActive ? '#FCA5A5' : '#FFFFFF',
                textDecoration: atropelaActive ? 'underline' : 'none',
                textDecorationColor: '#EF4444',
                textUnderlineOffset: 6,
              }}
            >
              atropela as conversas?
            </span>
          </div>
        </div>
      </div>

      {/* CENTRO: Simulação SaaS corporativa com slow zoom contínuo e sobreposição orgânica de mensagens */}
      <div
        style={{
          position: 'absolute',
          top: 525,
          left: 60,
          right: 60,
          height: 755,
          transform: `translate(${shakeX}px, ${interpolate(phonePop, [0, 1], [24, 0]) + floatY}px) scale(${cardScale})`,
          opacity: phonePop,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          background: 'rgba(15, 23, 42, 0.96)',
          borderRadius: 34,
          border: `3px solid ${atropelaActive ? '#F87171' : '#38BDF8'}`,
          padding: '22px 28px',
          boxShadow: '0 24px 60px rgba(0,0,0,0.7)',
        }}
      >
        {/* Cabeçalho do aparelho compartilhado */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '2px solid rgba(255,255,255,0.12)',
            paddingBottom: 14,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 20,
                height: 20,
                borderRadius: 99,
                background: atropelaActive ? '#EF4444' : '#F59E0B',
                boxShadow: atropelaActive ? '0 0 12px #EF4444' : 'none',
              }}
            />
            <span style={{color: '#FFFFFF', fontSize: 35, fontWeight: 800}}>
              1 Aparelho Compartilhado
            </span>
          </div>
          <div
            style={{
              background: 'rgba(255,255,255,0.14)',
              padding: '6px 18px',
              borderRadius: 999,
              color: '#FFFFFF',
              fontSize: 32,
              fontWeight: 700,
            }}
          >
            Simulação
          </div>
        </div>

        {/* Área de conversa com avatares e sobreposição orgânica de atendentes */}
        <div style={{display: 'flex', flexDirection: 'column', gap: 14, marginTop: 6, flex: 1}}>
          {/* Mensagem do Cliente */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              background: '#1E293B',
              border: '2px solid #475569',
              borderRadius: '22px 22px 22px 6px',
              padding: '14px 20px',
              transform: `translateY(${interpolate(b1, [0, 1], [16, 0])}px)`,
              opacity: b1,
            }}
          >
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 99,
                background: '#334155',
                border: '2px solid #94A3B8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                flexShrink: 0,
              }}
            >
              CL
            </div>
            <div style={{flex: 1}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <span style={{color: '#BAE6FD', fontSize: 32, fontWeight: 800}}>Cliente</span>
                <span style={{color: '#94A3B8', fontSize: 32, fontWeight: 700}}>Novo pedido</span>
              </div>
              <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 700}}>
                Olá, alguém pode atender meu pedido?
              </div>
            </div>
          </div>

          {/* Mensagem Vendedor A */}
          {b2Show && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                background: '#0369A1',
                border: '2px solid #7DD3FC',
                borderRadius: '22px 22px 6px 22px',
                padding: '14px 20px',
                transform: `translateY(${interpolate(b2, [0, 1], [18, 0]) + b2OverlapY}px)`,
                opacity: b2,
              }}
            >
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 99,
                  background: '#0284C7',
                  border: '2px solid #BAE6FD',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 900,
                  flexShrink: 0,
                }}
              >
                VA
              </div>
              <div style={{flex: 1}}>
                <div style={{color: '#E0F2FE', fontSize: 32, fontWeight: 800}}>
                  Vendedor A • Mesmo celular
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 700}}>
                  Oi! Vou te passar o orçamento agora.
                </div>
              </div>
            </div>
          )}

          {/* Mensagem Vendedor B atropelando a conversa com badge de Atendimento Duplicado (sem colisão de borda) */}
          {b3Show && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                background: 'rgba(127, 29, 29, 0.96)',
                border: '2px solid #FCA5A5',
                borderRadius: '22px 22px 6px 22px',
                padding: '14px 20px',
                transform: `translateY(${interpolate(b3, [0, 1], [24, 0])}px) scale(${b3Scale})`,
                opacity: b3,
                boxShadow: '0 14px 32px rgba(239, 68, 68, 0.4)',
              }}
            >
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 99,
                  background: '#B91C1C',
                  border: '2px solid #FECACA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 900,
                  flexShrink: 0,
                }}
              >
                VB
              </div>
              <div style={{flex: 1}}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <span style={{color: '#FECACA', fontSize: 32, fontWeight: 900}}>
                    Vendedor B
                  </span>
                  <span
                    style={{
                      background: 'rgba(239, 68, 68, 0.35)',
                      border: '1px solid #FCA5A5',
                      color: '#FFFFFF',
                      fontSize: 32,
                      fontWeight: 800,
                      padding: '2px 14px',
                      borderRadius: 999,
                    }}
                  >
                    Atendimento Duplicado
                  </span>
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 700}}>
                  Olá! Qual é o seu nome para cadastro?
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Barra de status inferior limpa e profissional em linha única (sem quebra e sem tarja vermelha) */}
        <div
          style={{
            background: '#1E293B',
            border: `2px solid ${atropelaActive ? 'rgba(248, 113, 113, 0.65)' : '#475569'}`,
            borderRadius: 20,
            padding: '12px 22px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: 99,
                background: atropelaActive ? '#F87171' : '#38BDF8',
                transform: `scale(${1 + conflictWave * 0.25})`,
              }}
            />
            <span style={{color: '#E2E8F0', fontSize: 32, fontWeight: 800}}>
              {atropelaActive
                ? 'Conflito: 2 respostas simultâneas'
                : '2 vendedores digitando juntos...'}
            </span>
          </div>
          <span
            style={{
              color: atropelaActive ? '#FCA5A5' : '#BAE6FD',
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            {atropelaActive ? 'Sem controle' : '1 aparelho'}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 1: Dono Antes -> Adotar CRM (5.08s - 13.27s)
const Cena1DonoAntes: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absT = 5.08 + frame / fps;

  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOpacity = interpolate(absT, [12.92, 13.25], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const virouSolucao = absT >= 9.8;

  // Zoom progressivo e punch-in suave na virada para SOLUÇÃO ADOTADA aos 9.8s
  const baseZoom = interpolate(frame, [0, 245], [1.0, 1.05], {extrapolateRight: 'clamp'});
  const turnProgress = spring({
    frame: Math.max(0, Math.round((absT - 9.8) * fps)),
    fps,
    config: {damping: 14, stiffness: 180},
  });
  const punchZoom = baseZoom + turnProgress * 0.07;

  const cardEnter = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const pulse = 1 + Math.sin(frame / 7) * 0.014;
  const dotPulse = 1 + Math.sin(frame / 4) * 0.3;

  // Interpolação suave (flip vertical + slide) durante a substituição dos badges aos 9.8s
  const badgeSlideY = virouSolucao
    ? interpolate(turnProgress, [0, 1], [16, 0])
    : Math.sin(frame / 6) * 2;
  const badgeOpacity = virouSolucao
    ? interpolate(turnProgress, [0, 0.3, 1], [0.3, 0.85, 1])
    : 1;

  return (
    <AbsoluteFill style={{opacity: enterOpacity * exitOpacity, fontFamily}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${punchZoom})`,
            transformOrigin: '50% 42%',
          }}
        />
      </AbsoluteFill>

      {/* Card único no topo (y: 168..425) com transição animada e sem redundância de texto */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(cardEnter, [0, 1], [-26, 0])}px) scale(${pulse})`,
          opacity: cardEnter,
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.94)',
            border: `3px solid ${virouSolucao ? '#38BDF8' : '#EF4444'}`,
            borderRadius: 28,
            padding: '18px 28px',
            boxShadow: '0 16px 36px rgba(0,0,0,0.55)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 10,
              transform: `translateY(${badgeSlideY}px)`,
              opacity: badgeOpacity,
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                background: virouSolucao ? CORES.marca : '#EF4444',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 900,
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 99,
                  background: '#FFFFFF',
                  transform: `scale(${dotPulse})`,
                }}
              />
              <span>{virouSolucao ? 'SOLUÇÃO ADOTADA' : 'ANTES'}</span>
            </div>
            <span
              style={{
                background: virouSolucao
                  ? 'rgba(2, 132, 199, 0.28)'
                  : 'rgba(239, 68, 68, 0.28)',
                border: `2px solid ${
                  virouSolucao ? '#38BDF8' : '#FCA5A5'
                }`,
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              {virouSolucao ? '✓ Chatwoot + IA' : 'Antes do CRM'}
            </span>
          </div>

          <div
            style={{
              color: '#FFFFFF',
              fontSize: 40,
              fontWeight: 900,
              lineHeight: 1.18,
              transform: `translateY(${badgeSlideY}px)`,
              opacity: badgeOpacity,
            }}
          >
            {virouSolucao
              ? 'CRM feito para o meu negócio'
              : 'Mesmo celular sem controle'}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 2: Conversa / Como Funciona (12.92s - 20.51s)
const Cena2Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absT = 12.92 + frame / fps;

  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOpacity = interpolate(absT, [20.16, 20.48], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, 228], [1.02, 1.14], {extrapolateRight: 'clamp'});
  const bgPanY = interpolate(frame, [0, 228], [0, -24], {extrapolateRight: 'clamp'});
  const floatY = Math.sin(frame / 10) * 6;
  const rotY = interpolate(frame, [0, 228], [-5, 4], {extrapolateRight: 'clamp'});
  const rotX = interpolate(frame, [0, 228], [3, -2], {extrapolateRight: 'clamp'});

  // Acendimento sincronizado com a fala:
  // "Chatwoot" (14.50s), "helpdesk" (15.33s), "por setor" (17.34s)
  const chatwootAtivo = absT >= 14.48;
  const helpdeskAtivo = absT >= 15.3;
  const setorAtivo = absT >= 17.18;

  const m1 = spring({frame, fps, config: {damping: 18, stiffness: 260}});

  const fM2 = Math.round((14.2 - 12.92) * fps);
  const showM2 = frame >= fM2;
  const m2 = showM2
    ? spring({frame: frame - fM2, fps, config: {damping: 16, stiffness: 250}})
    : 0;

  const fM3 = Math.round((15.9 - 12.92) * fps);
  const showM3 = frame >= fM3;
  const m3 = showM3
    ? spring({frame: frame - fM3, fps, config: {damping: 15, stiffness: 240}})
    : 0;

  const fM4 = Math.round((17.75 - 12.92) * fps);
  const showM4 = frame >= fM4;
  const m4 = showM4
    ? spring({frame: frame - fM4, fps, config: {damping: 16, stiffness: 250}})
    : 0;

  const aiPulse = 1 + Math.sin(frame / 5) * 0.03;

  return (
    <AbsoluteFill
      style={{
        opacity: enterOpacity * exitOpacity,
        fontFamily,
        perspective: 1400,
      }}
    >
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.84) 0%, rgba(2,132,199,0.25) 50%, rgba(15,23,42,0.92) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* TOPO ENXUTO: Rótulo Como Funciona + Etapa descritiva (sem repetir 'Chatwoot + Helpdesk' do rodapé) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          background: 'rgba(15, 23, 42, 0.94)',
          borderRadius: 26,
          border: '2px solid rgba(56, 189, 248, 0.5)',
          padding: '18px 26px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 16px 36px rgba(0,0,0,0.5)',
        }}
      >
        <span
          style={{
            background: CORES.marca,
            color: '#FFFFFF',
            fontSize: 33,
            fontWeight: 900,
            padding: '8px 22px',
            borderRadius: 999,
          }}
        >
          COMO FUNCIONA
        </span>
        <span
          style={{
            color: setorAtivo ? '#34D399' : '#BAE6FD',
            fontSize: 34,
            fontWeight: 800,
          }}
        >
          {setorAtivo
            ? '✓ Separado por Setor'
            : helpdeskAtivo
            ? 'Integração de Canais'
            : chatwootAtivo
            ? 'Triagem Automática'
            : 'Fluxo Inteligente'}
        </span>
      </div>

      {/* CENTRO EQUILIBRADO NO TERÇO MÉDIO (top: 345, height: 915 -> y: 345..1260, respiro amplo acima e abaixo) */}
      <div
        style={{
          position: 'absolute',
          top: 345,
          left: 65,
          right: 65,
          height: 915,
          transform: `translateY(${floatY}px) rotateY(${rotY}deg) rotateX(${rotX}deg)`,
          transformStyle: 'preserve-3d',
          background: 'rgba(15, 23, 42, 0.97)',
          borderRadius: 40,
          border: '3px solid #38BDF8',
          boxShadow: '-16px 26px 60px rgba(0,0,0,0.75), 0 0 0 6px rgba(15,23,42,0.9)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header SaaS Premium com tag 'Simulação' permanente e badge de Setor */}
        <div
          style={{
            background: 'linear-gradient(90deg, #0284C7 0%, #0369A1 100%)',
            padding: '18px 26px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '2px solid rgba(255,255,255,0.18)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <div
              style={{
                width: 18,
                height: 18,
                borderRadius: 99,
                background: '#34D399',
                boxShadow: '0 0 10px #34D399',
              }}
            />
            <span style={{color: '#FFFFFF', fontSize: 34, fontWeight: 900}}>
              Inovare CRM
            </span>
            <span
              style={{
                background: setorAtivo ? '#065F46' : 'rgba(15, 23, 42, 0.55)',
                border: `2px solid ${setorAtivo ? '#34D399' : '#BAE6FD'}`,
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                padding: '4px 14px',
                borderRadius: 999,
              }}
            >
              {setorAtivo ? 'Setor: Suporte' : 'Triagem IA'}
            </span>
          </div>
          <span
            style={{
              background: 'rgba(15, 23, 42, 0.88)',
              color: '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              padding: '6px 18px',
              borderRadius: 999,
              border: '1px solid rgba(255,255,255,0.25)',
            }}
          >
            Simulação
          </span>
        </div>

        {/* Área de mensagens SaaS com avatares, badges de ação e respiro tipográfico */}
        <div
          style={{
            flex: 1,
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
            {/* Msg 1: Cliente com Avatar */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                width: '100%',
                background: '#1E293B',
                border: '2px solid #475569',
                borderRadius: '22px 22px 22px 6px',
                padding: '14px 20px',
                transform: `translateY(${interpolate(m1, [0, 1], [18, 0])}px)`,
                opacity: interpolate(m1, [0, 1], [0.85, 1]),
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 99,
                  background: '#334155',
                  border: '2px solid #93C5FD',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                  flexShrink: 0,
                }}
              >
                CL
              </div>
              <div style={{flex: 1}}>
                <div style={{color: '#93C5FD', fontSize: 32, fontWeight: 800, marginBottom: 2}}>
                  Cliente
                </div>
                <div style={{color: '#FFFFFF', fontSize: 33, fontWeight: 700, lineHeight: 1.2}}>
                  Olá, preciso falar com o suporte sobre meu pedido.
                </div>
              </div>
            </div>

            {/* Msg 2: IA com Avatar e realce sutil */}
            {showM2 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  width: '100%',
                  background: 'linear-gradient(90deg, #0284C7 0%, #0369A1 100%)',
                  border: '2px solid #7DD3FC',
                  borderRadius: '22px 22px 6px 22px',
                  padding: '14px 20px',
                  transform: `translateY(${interpolate(m2, [0, 1], [20, 0])}px)`,
                  opacity: m2,
                  boxShadow: '0 10px 25px rgba(2,132,199,0.35)',
                }}
              >
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 99,
                    background: '#0F172A',
                    border: '2px solid #38BDF8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#38BDF8',
                    fontSize: 32,
                    fontWeight: 900,
                    flexShrink: 0,
                    transform: `scale(${aiPulse})`,
                  }}
                >
                  IA
                </div>
                <div style={{flex: 1}}>
                  <div style={{color: '#E0F2FE', fontSize: 32, fontWeight: 800, marginBottom: 2}}>
                    Inovare CRM • IA
                  </div>
                  <div style={{color: '#FFFFFF', fontSize: 33, fontWeight: 700, lineHeight: 1.2}}>
                    Olá! Sou a IA de atendimento. Já localizei seu cadastro aqui no sistema.
                  </div>
                </div>
              </div>
            )}

            {/* Msg 3: Abertura de Ticket + roteamento para Setor com destaque visual */}
            {showM3 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  width: '100%',
                  background: '#0F172A',
                  border: '2px solid #38BDF8',
                  borderRadius: '22px 22px 6px 22px',
                  padding: '14px 20px',
                  transform: `translateY(${interpolate(m3, [0, 1], [20, 0])}px)`,
                  opacity: m3,
                  boxShadow: '0 0 24px rgba(56, 189, 248, 0.35)',
                }}
              >
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 16,
                    background: '#0284C7',
                    border: '2px solid #BAE6FD',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 32,
                    fontWeight: 900,
                    flexShrink: 0,
                  }}
                >
                  ✓
                </div>
                <div style={{flex: 1}}>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2}}>
                    <span style={{color: '#38BDF8', fontSize: 32, fontWeight: 900}}>
                      Helpdesk • Ticket Aberto
                    </span>
                    <span
                      style={{
                        background: 'rgba(16, 185, 129, 0.25)',
                        border: '1px solid #34D399',
                        color: '#A7F3D0',
                        fontSize: 32,
                        fontWeight: 800,
                        padding: '2px 12px',
                        borderRadius: 999,
                      }}
                    >
                      Suporte
                    </span>
                  </div>
                  <div style={{color: '#FFFFFF', fontSize: 33, fontWeight: 700, lineHeight: 1.2}}>
                    Abri seu ticket de suporte e transferi sua conversa para o setor responsável.
                  </div>
                </div>
              </div>
            )}

            {/* Msg 4: Cliente atendido no setor correto */}
            {showM4 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  width: '100%',
                  background: '#065F46',
                  border: '2px solid #34D399',
                  borderRadius: '22px 22px 22px 6px',
                  padding: '14px 20px',
                  transform: `translateY(${interpolate(m4, [0, 1], [20, 0])}px)`,
                  opacity: m4,
                }}
              >
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 99,
                    background: '#047857',
                    border: '2px solid #A7F3D0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 32,
                    fontWeight: 800,
                    flexShrink: 0,
                  }}
                >
                  CL
                </div>
                <div style={{flex: 1}}>
                  <div style={{color: '#A7F3D0', fontSize: 32, fontWeight: 800, marginBottom: 2}}>
                    Cliente • Atendimento separado
                  </div>
                  <div style={{color: '#FFFFFF', fontSize: 33, fontWeight: 700, lineHeight: 1.2}}>
                    Perfeito, fico no aguardo.
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Barra de status inferior do Helpdesk */}
          <div
            style={{
              background: '#1E293B',
              border: '2px solid rgba(56, 189, 248, 0.38)',
              borderRadius: 20,
              padding: '12px 22px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{color: '#BAE6FD', fontSize: 32, fontWeight: 800}}>
              Histórico unificado
            </span>
            <span style={{color: '#34D399', fontSize: 32, fontWeight: 900}}>
              {setorAtivo ? 'Sem misturar conversas' : 'Chatwoot + Helpdesk'}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 3: Dono Depois (20.16s - 28.34s)
const Cena3DonoDepois: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absT = 20.16 + frame / fps;

  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOpacity = interpolate(absT, [27.95, 28.06], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const segundaParte = absT >= 25.7;
  // Punch-in digital de 18% a 26% na Cena 3 (enquadramento fechado do peito para cima, bem distinto do plano médio da Cena 1)
  const baseZoom = interpolate(frame, [0, 166], [1.18, 1.23], {extrapolateRight: 'clamp'});
  const punchDrift = interpolate(frame, [166, 245], [1.26, 1.3], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const videoScale = segundaParte ? punchDrift : baseZoom;

  const cardEnter = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const shiftPop = spring({
    frame: Math.max(0, Math.round((absT - 25.7) * fps)),
    fps,
    config: {damping: 15, stiffness: 200},
  });
  const pulse = 1 + Math.sin(frame / 9) * 0.012;

  return (
    <AbsoluteFill style={{opacity: enterOpacity * exitOpacity, fontFamily}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${videoScale})`,
            transformOrigin: '50% 38%',
          }}
        />
      </AbsoluteFill>

      {/* Card superior compacto (y: 168..410), preservando 100% o rosto do dono */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(cardEnter, [0, 1], [-26, 0])}px) scale(${pulse})`,
          opacity: cardEnter,
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.94)',
            border: `3px solid ${segundaParte ? '#10B981' : '#38BDF8'}`,
            borderRadius: 28,
            padding: '18px 28px',
            boxShadow: '0 16px 36px rgba(0,0,0,0.55)',
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
                background: segundaParte ? '#10B981' : CORES.marca,
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 900,
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              DEPOIS • ORGANIZADO
            </span>
            <span
              style={{
                background: segundaParte
                  ? 'rgba(16, 185, 129, 0.25)'
                  : 'rgba(2, 132, 199, 0.25)',
                border: `2px solid ${segundaParte ? '#34D399' : '#38BDF8'}`,
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              {segundaParte ? '✓ Sem atropelo' : 'CRM Chatwoot IA'}
            </span>
          </div>

          <div
            style={{
              color: '#FFFFFF',
              fontSize: 40,
              fontWeight: 900,
              lineHeight: 1.18,
              transform: segundaParte
                ? `translateY(${interpolate(shiftPop, [0, 1], [12, 0])}px)`
                : 'none',
            }}
          >
            {segundaParte
              ? 'Ninguém responde por cima do colega'
              : 'Cada vendedor sabe quem está atendendo'}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 4: Cartão Final / CTA (27.99s - 31.94s)
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Entrada escalonada rápida (stagger nos primeiros 14 frames) + movimento contínuo forte até o frame 120 (q13 a q15)
  const sLogo = spring({frame, fps, config: {damping: 15, stiffness: 260}});
  const sMockup = spring({
    frame: Math.max(0, frame - 2),
    fps,
    config: {damping: 15, stiffness: 250},
  });
  const sBloco1 = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 13, stiffness: 230},
  });
  const sBloco2 = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 13, stiffness: 230},
  });
  const sBloco3 = spring({
    frame: Math.max(0, frame - 13),
    fps,
    config: {damping: 13, stiffness: 230},
  });
  const sCta = spring({
    frame: Math.max(0, frame - 1),
    fps,
    config: {damping: 14, stiffness: 260},
  });

  const bgScale = interpolate(frame, [0, 120], [1.0, 1.2], {extrapolateRight: 'clamp'});
  // Pulso contínuo de escala no botão CTA + varredura luminosa (shimmer) + inclinação 3D contínua nos cards
  const btnPulse = interpolate(Math.sin(frame / 2.8), [-1, 1], [1.0, 1.05]);
  const bloco1Scale = 1 + Math.sin(frame / 4.0) * 0.03;
  const bloco2Scale = 1 + Math.cos(frame / 4.0) * 0.03;
  const bloco3Scale = 1 + Math.sin((frame + 6) / 4.0) * 0.022;
  const mockupFloat = Math.sin(frame / 5.0) * 10;
  const mockupTiltY = interpolate(frame, [0, 120], [-7, 7], {extrapolateRight: 'clamp'});
  const shineX = interpolate((frame * 28) % 1050, [0, 1050], [-250, 950]);

  return (
    <AbsoluteFill style={{fontFamily}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale})`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 38%, rgba(2,132,199,0.45) 0%, rgba(15,23,42,0.95) 75%)',
          }}
        />
      </AbsoluteFill>

      {/* Composição coesa e integrada (y: 235..1485), sem vazios excessivos entre título, card e CTA */}
      <div
        style={{
          position: 'absolute',
          top: 235,
          bottom: 435,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 38,
        }}
      >
        {/* 1. Marca + Produto */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 10,
            transform: `translateY(${interpolate(sLogo, [0, 1], [-20, 0])}px)`,
            opacity: sLogo,
          }}
        >
          <div
            style={{
              background: CORES.marca,
              color: '#FFFFFF',
              fontSize: 34,
              fontWeight: 900,
              padding: '8px 28px',
              borderRadius: 999,
              letterSpacing: 1,
              boxShadow: '0 10px 26px rgba(2,132,199,0.5)',
            }}
          >
            CRM CHATWOOT IA
          </div>

          <div
            style={{
              color: '#FFFFFF',
              fontSize: 68,
              fontWeight: 900,
              letterSpacing: -1.5,
              textAlign: 'center',
              textShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            Inovare CRM
          </div>
        </div>

        {/* 2. Card Central de Benefícios com Stagger e Movimento Contínuo */}
        <div
          style={{
            width: '100%',
            background: 'rgba(15, 23, 42, 0.96)',
            border: '3px solid #38BDF8',
            borderRadius: 32,
            overflow: 'hidden',
            boxShadow: '0 22px 50px rgba(0,0,0,0.7)',
            transform: `perspective(1200px) translateY(${interpolate(sMockup, [0, 1], [24, 0]) + mockupFloat}px) rotateY(${mockupTiltY}deg)`,
            opacity: sMockup,
          }}
        >
          <div
            style={{
              background: 'linear-gradient(90deg, #0284C7 0%, #0369A1 100%)',
              padding: '16px 26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div style={{width: 16, height: 16, borderRadius: 99, background: '#34D399'}} />
              <span style={{color: '#FFFFFF', fontSize: 34, fontWeight: 900}}>
                Painel Inovare CRM
              </span>
            </div>
            <span
              style={{
                background: 'rgba(15,23,42,0.88)',
                color: '#BAE6FD',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              Chatwoot + IA
            </span>
          </div>

          <div style={{padding: '22px 24px', display: 'flex', gap: 16}}>
            <div
              style={{
                flex: 1,
                background: '#1E293B',
                border: '2px solid #38BDF8',
                borderRadius: 22,
                padding: '18px 16px',
                textAlign: 'center',
                transform: `translateY(${interpolate(sBloco1, [0, 1], [22, 0])}px) scale(${interpolate(sBloco1, [0, 1], [0.88, 1]) * bloco1Scale})`,
                opacity: interpolate(sBloco1, [0, 1], [0, 1]),
              }}
            >
              <div style={{color: '#BAE6FD', fontSize: 33, fontWeight: 800}}>✓ Atendimento</div>
              <div style={{color: '#FFFFFF', fontSize: 36, fontWeight: 900}}>Por Setor</div>
            </div>
            <div
              style={{
                flex: 1,
                background: '#1E293B',
                border: '2px solid #34D399',
                borderRadius: 22,
                padding: '18px 16px',
                textAlign: 'center',
                transform: `translateY(${interpolate(sBloco2, [0, 1], [22, 0])}px) scale(${interpolate(sBloco2, [0, 1], [0.88, 1]) * bloco2Scale})`,
                opacity: interpolate(sBloco2, [0, 1], [0, 1]),
              }}
            >
              <div style={{color: '#A7F3D0', fontSize: 33, fontWeight: 800}}>✓ Helpdesk</div>
              <div style={{color: '#FFFFFF', fontSize: 36, fontWeight: 900}}>Tickets + IA</div>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(2, 132, 199, 0.22)',
              borderTop: '2px solid rgba(56, 189, 248, 0.35)',
              padding: '18px 26px',
              textAlign: 'center',
              transform: `translateY(${interpolate(sBloco3, [0, 1], [18, 0])}px) scale(${bloco3Scale})`,
              opacity: interpolate(sBloco3, [0, 1], [0, 1]),
            }}
          >
            <div
              style={{
                color: '#FFFFFF',
                fontSize: 36,
                fontWeight: 800,
                lineHeight: 1.24,
              }}
            >
              Atendimento, tickets e histórico de cada cliente em um só lugar.
            </div>
          </div>
        </div>

        {/* 3. Botão CTA Principal com Shimmer + @inovarecrm ampliado e 100% aceso desde o início */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
            width: '100%',
            transform: `translateY(${interpolate(sCta, [0, 1], [14, 0])}px)`,
            opacity: 1,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              background: 'linear-gradient(90deg, #0284C7 0%, #0369A1 50%, #0284C7 100%)',
              border: '4px solid #BAE6FD',
              borderRadius: 999,
              padding: '24px 48px',
              width: '94%',
              textAlign: 'center',
              transform: `scale(${btnPulse})`,
              boxShadow: '0 20px 50px rgba(2, 132, 199, 0.75)',
            }}
          >
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shineX,
                width: 220,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)',
                transform: 'skewX(-20deg)',
              }}
            />
            <span
              style={{
                position: 'relative',
                color: '#FFFFFF',
                fontSize: 48,
                fontWeight: 900,
                letterSpacing: 1,
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          <div
            style={{
              background: 'rgba(15, 23, 42, 0.96)',
              border: '3px solid #38BDF8',
              padding: '14px 42px',
              borderRadius: 999,
              color: '#FFFFFF',
              fontSize: 48,
              fontWeight: 900,
              boxShadow: '0 12px 30px rgba(0,0,0,0.6)',
              letterSpacing: 0.5,
            }}
          >
            @inovarecrm
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const progresso = interpolate(frame, [0, TOTAL_FRAMES - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  // Volume da trilha: fade in/out e 0.10 durante a fala
  const volTrilha = interpolate(
    t,
    [0, 0.8, DURACAO_S - 1.2, DURACAO_S],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {/* CENA 0: 0.00s - 5.43s */}
      <Sequence from={0} durationInFrames={Math.ceil(5.43 * FPS)}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 5.08s - 13.27s */}
      <Sequence
        from={Math.floor(5.08 * FPS)}
        durationInFrames={Math.ceil((13.27 - 5.08) * FPS)}
      >
        <Cena1DonoAntes />
      </Sequence>

      {/* CENA 2: 12.92s - 20.51s */}
      <Sequence
        from={Math.floor(12.92 * FPS)}
        durationInFrames={Math.ceil((20.51 - 12.92) * FPS)}
      >
        <Cena2Conversa />
      </Sequence>

      {/* CENA 3: 20.16s - 28.34s */}
      <Sequence
        from={Math.floor(20.16 * FPS)}
        durationInFrames={Math.ceil((28.08 - 20.16) * FPS)}
      >
        <Cena3DonoDepois />
      </Sequence>

      {/* CENA 4: 27.99s - 31.94s */}
      <Sequence
        from={Math.floor(27.99 * FPS)}
        durationInFrames={TOTAL_FRAMES - Math.floor(27.99 * FPS)}
      >
        <Cena4Cartao />
      </Sequence>

      {/* Barra de progresso fina na Safe Zone (y=152) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 8,
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 99,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            background: CORES.marcaClara,
            borderRadius: 99,
          }}
        />
      </div>

      {/* Legenda Karaokê (apenas nas cenas 0 a 3, oculta no cartão final) */}
      {t < 28.15 && (
        <Karaoke
          palavras={PALAVRAS}
          fontFamily={fontFamily}
          destaque={CORES.marca}
          textoDestaque="#FFFFFF"
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
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
