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
  weights: ['500', '600', '700', '800', '900'],
  subsets: ['latin'],
});

const COR = {
  marca: '#1F93FF',
  marcaClara: '#60B5FF',
  marcaEscura: '#0B4F94',
  apoio: '#111827',
  fundo: '#0B1120',
  card: 'rgba(17, 24, 39, 0.92)',
  cardSolido: '#111827',
  texto: '#FFFFFF',
  textoSec: '#E2E8F0',
  alerta: '#EF4444',
  alertaBg: 'rgba(239, 68, 68, 0.22)',
  sucesso: '#10B981',
};

export const PALAVRAS_K: PalavraK[] = [
  // Cena 0 (0.0 - 5.0)
  {p: 'Perdendo', ini: 0.318, fim: 0.739, quebraAntes: true},
  {p: 'controle', ini: 0.751, fim: 1.232, quebraApos: true},
  {p: 'dos', ini: 1.244, fim: 1.34, quebraAntes: true},
  {p: 'atendimentos', ini: 1.352, fim: 2.085, quebraApos: true},
  {p: 'com', ini: 2.097, fim: 2.241, quebraAntes: true},
  {p: 'ferramentas', ini: 2.253, fim: 2.83},
  {p: 'básicas?', ini: 2.842, fim: 3.539, quebraApos: true},

  // Cena 1 (4.65 - 11.83)
  {p: 'Uma', ini: 5.632, fim: 6.232, quebraAntes: true},
  {p: 'ferramenta', ini: 6.232, fim: 6.732},
  {p: 'padrão', ini: 6.732, fim: 7.132, quebraApos: true},
  {p: 'de', ini: 7.132, fim: 7.392, quebraAntes: true},
  {p: 'mensagens', ini: 7.392, fim: 8.052},
  {p: 'não', ini: 8.052, fim: 8.612},
  {p: 'entende', ini: 8.612, fim: 9.112, quebraApos: true},
  {p: 'a', ini: 9.112, fim: 9.352, quebraAntes: true},
  {p: 'rotina', ini: 9.352, fim: 9.672},
  {p: 'específica', ini: 9.672, fim: 10.352, quebraApos: true},
  {p: 'da', ini: 10.352, fim: 10.492, quebraAntes: true},
  {p: 'sua', ini: 10.492, fim: 10.672},
  {p: 'empresa.', ini: 10.672, fim: 11.032, quebraApos: true},

  // Cena 2 (11.48 - 18.39)
  {p: 'Nós', ini: 12.232, fim: 12.952, quebraAntes: true},
  {p: 'adaptamos', ini: 12.952, fim: 13.512},
  {p: 'o', ini: 13.512, fim: 13.692},
  {p: 'sistema', ini: 13.692, fim: 14.092, quebraApos: true},
  {p: 'com', ini: 14.092, fim: 14.432, quebraAntes: true},
  {p: 'inteligência', ini: 14.432, fim: 15.052},
  {p: 'artificial', ini: 15.052, fim: 15.672, quebraApos: true},
  {p: 'para', ini: 15.672, fim: 16.232, quebraAntes: true},
  {p: 'o', ini: 16.232, fim: 16.492},
  {p: 'fluxo', ini: 16.492, fim: 16.832, quebraApos: true},
  {p: 'do', ini: 16.832, fim: 16.972, quebraAntes: true},
  {p: 'seu', ini: 16.972, fim: 17.132},
  {p: 'negócio.', ini: 17.132, fim: 17.592, quebraApos: true},

  // Cena 3 (18.04 - 25.52)
  {p: 'Sua', ini: 19.022, fim: 19.682, quebraAntes: true},
  {p: 'equipe', ini: 19.682, fim: 20.082},
  {p: 'trabalha', ini: 20.082, fim: 20.422, quebraApos: true},
  {p: 'com', ini: 20.422, fim: 20.682, quebraAntes: true},
  {p: 'muito', ini: 20.682, fim: 20.982},
  {p: 'mais', ini: 20.982, fim: 21.302},
  {p: 'clareza', ini: 21.302, fim: 22.682, quebraApos: true},
  {p: 'tendo', ini: 23.082, fim: 23.262, quebraAntes: true},
  {p: 'tudo', ini: 23.262, fim: 23.482},
  {p: 'reunido', ini: 23.482, fim: 24.022, quebraApos: true},
  {p: 'no', ini: 24.022, fim: 24.242, quebraAntes: true},
  {p: 'dia', ini: 24.242, fim: 24.522},
  {p: 'a', ini: 24.522, fim: 24.562},
  {p: 'dia.', ini: 24.562, fim: 24.722, quebraApos: true},
];

// ---------------------------------------------------------------------------
// CENA 0: PERGUNTA (0.00s - 5.00s)
// Gancho vivo nativo de Reels: Apresentador na base + Notificações de chat animadas + Pergunta
// ---------------------------------------------------------------------------
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const bgScale = interpolate(frame, [0, 150], [1.06, 1.16], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(t, [4.65, 5.0], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const exitScale = interpolate(t, [4.65, 5.0], [1, 1.05], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const pop1 = spring({frame: Math.max(0, frame - 2), fps, config: {damping: 13, stiffness: 160}});
  const pop2 = spring({frame: Math.max(0, frame - Math.round(1.24 * fps)), fps, config: {damping: 13, stiffness: 160}});
  const pop3 = spring({frame: Math.max(0, frame - Math.round(2.1 * fps)), fps, config: {damping: 13, stiffness: 160}});

  const phoneEnter = spring({frame: Math.max(0, frame - 6), fps, config: {damping: 14, stiffness: 130}});
  const cardScale = interpolate(frame, [0, 150], [0.98, 1.04], {extrapolateRight: 'clamp'});
  const tiltY = interpolate(frame, [0, 150], [-10, 4], {extrapolateRight: 'clamp'});
  const tiltX = interpolate(frame, [0, 150], [6, -2], {extrapolateRight: 'clamp'});
  const floatY = Math.sin(frame / 9) * 10;
  const alertPulse = 1 + 0.06 * Math.sin(frame / 5);

  const tickets = [
    {tIni: 0.35, cliente: 'Atendimento #104', msg: 'Qual status do meu chamado?', tag: 'Sem histórico'},
    {tIni: 1.55, cliente: 'Suporte Comercial', msg: 'Cliente aguardando retorno', tag: 'Sem ticket'},
    {tIni: 2.85, cliente: 'Fila de Mensagens', msg: 'Conversa perdida no chat básico', tag: 'Desconectado'},
  ];

  return (
    <AbsoluteFill style={{backgroundColor: COR.fundo, opacity: exitOp, transform: `scale(${exitScale})`}}>
      {/* Fundo vivo com simulação dinâmica de mensagens + orbes luminosos (sem cobrir rosto de apresentador) */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translateX(${Math.sin(frame / 18) * 20}px)`,
            filter: 'brightness(0.55) contrast(1.18)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at ${50 + Math.sin(frame / 12) * 18}% ${32 + Math.cos(frame / 15) * 10}%, rgba(239,68,68,0.28) 0%, rgba(31,147,255,0.22) 45%, rgba(11,17,32,0.94) 100%)`,
          }}
        />
      </AbsoluteFill>

      {/* TOPO: Pílula fixa + Pergunta Cinética (y=168 a 485) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
        }}
      >
        {/* Selo gancho_tela FIXO do início ao fim da Cena 0 (sem troca brusca) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 26px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.94)',
            border: `2px solid ${COR.marca}`,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            transform: `scale(${0.88 + 0.12 * pop1})`,
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: 99,
              background: COR.marca,
              boxShadow: `0 0 12px ${COR.marca}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.texto,
              letterSpacing: 0.3,
            }}
          >
            Chatwoot comum ou com IA?
          </span>
        </div>

        {/* Frase da pergunta sincronizada com a fala */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid rgba(255,255,255,0.18)',
            borderRadius: 28,
            padding: '20px 28px',
            width: '100%',
            boxShadow: '0 18px 40px rgba(0,0,0,0.6)',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 50,
              fontWeight: 900,
              lineHeight: 1.16,
              color: COR.texto,
              textWrap: 'balance',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                transform: `scale(${0.85 + 0.15 * pop1})`,
                color: '#FFFFFF',
                background: COR.alerta,
                padding: '2px 14px',
                borderRadius: 12,
                marginRight: 10,
              }}
            >
              Perdendo controle
            </span>
            <span
              style={{
                display: 'inline-block',
                color: t >= 1.2 ? '#FFFFFF' : '#E2E8F0',
                transform: `translateY(${(1 - pop2) * 12}px) scale(${t >= 1.2 ? 0.94 + 0.06 * pop2 : 0.95})`,
              }}
            >
              dos atendimentos
            </span>{' '}
            <span
              style={{
                display: 'inline-block',
                transform: `translateY(${(1 - pop3) * 12}px) scale(${t >= 2.05 ? 0.94 + 0.06 * pop3 : 0.95})`,
                color: t >= 2.05 ? COR.marcaClara : '#CBD5E1',
              }}
            >
              com ferramentas básicas?
            </span>
          </div>
        </div>
      </div>

      {/* CENTRO: Simulação viva com zoom contínuo e itens escalonados até o final (y=505 a 1080) */}
      <div
        style={{
          position: 'absolute',
          top: 505,
          left: 60,
          right: 60,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: 940,
            borderRadius: 30,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '3px solid rgba(239, 68, 68, 0.65)',
            boxShadow: '0 26px 65px rgba(0,0,0,0.75)',
            padding: '22px 26px',
            transform: `translateY(${(1 - phoneEnter) * 60 + floatY}px) scale(${cardScale}) rotateY(${tiltY}deg) rotateX(${tiltX}deg)`,
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          {/* Cabeçalho da janela com selo Simulação */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingBottom: 12,
              borderBottom: '2px solid rgba(255,255,255,0.12)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 99,
                  background: COR.alerta,
                  transform: `scale(${alertPulse})`,
                  boxShadow: `0 0 12px ${COR.alerta}`,
                }}
              />
              <span style={{fontFamily, fontSize: 36, fontWeight: 800, color: COR.texto}}>
                Chat Básico Padrão
              </span>
            </div>
            <div
              style={{
                padding: '6px 18px',
                borderRadius: 99,
                background: 'rgba(255,255,255,0.14)',
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: COR.texto,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Notificações entrando escalonadas (0.35s, 1.55s, 2.85s) + pulso contínuo nos alertas */}
          <div style={{display: 'flex', flexDirection: 'column', gap: 12}}>
            {tickets.map((item, idx) => {
              if (t < item.tIni) return null;
              const itemSpring = spring({
                frame: Math.max(0, frame - Math.round(item.tIni * fps)),
                fps,
                config: {damping: 13, stiffness: 150},
              });
              const rowFloat = Math.sin((frame + idx * 12) / 8) * 3;
              return (
                <div
                  key={idx}
                  style={{
                    opacity: itemSpring,
                    transform: `translateX(${(1 - itemSpring) * 55 + rowFloat}px) scale(${0.94 + 0.06 * itemSpring})`,
                    background: 'rgba(30, 41, 59, 0.96)',
                    borderLeft: `8px solid ${COR.alerta}`,
                    borderRadius: 18,
                    padding: '14px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                    <span style={{fontFamily, fontSize: 35, fontWeight: 800, color: COR.texto}}>
                      {item.cliente}
                    </span>
                    <span style={{fontFamily, fontSize: 34, fontWeight: 600, color: COR.textoSec}}>
                      {item.msg}
                    </span>
                  </div>
                  <div
                    style={{
                      background: COR.alertaBg,
                      border: `2px solid ${COR.alerta}`,
                      padding: '8px 16px',
                      borderRadius: 14,
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FECACA',
                      whiteSpace: 'nowrap',
                      transform: `scale(${1 + 0.03 * Math.sin((frame + idx * 10) / 6)})`,
                    }}
                  >
                    {item.tag}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// CENA 1: DONO 1 - O PROBLEMA (4.65s - 11.83s)
// Plano médio do dono (1.0 -> 1.06) + Comparador Limpo de 2 Blocos com Alto Contraste
// ---------------------------------------------------------------------------
const Cena1Problema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((11.83 - 4.65) * fps);
  const tAbs = 4.65 + frame / fps;

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [durFrames - 10, durFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const hudSlideY = interpolate(frame, [durFrames - 10, durFrames], [0, -35], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const vidScale = interpolate(frame, [0, durFrames], [1.0, 1.06], {extrapolateRight: 'clamp'});

  const sRotulo = spring({frame: Math.max(0, frame - 4), fps, config: {damping: 14, stiffness: 150}});
  const sPadrao = spring({
    frame: Math.max(0, Math.round((tAbs - 5.63) * fps)),
    fps,
    config: {damping: 13, stiffness: 150},
  });
  const sNaoEntende = spring({
    frame: Math.max(0, Math.round((tAbs - 8.05) * fps)),
    fps,
    config: {damping: 12, stiffness: 170},
  });
  const sRotina = spring({
    frame: Math.max(0, Math.round((tAbs - 9.35) * fps)),
    fps,
    config: {damping: 13, stiffness: 150},
  });

  const onRotina = tAbs >= 9.35;
  const onNaoEntende = tAbs >= 8.05;

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, backgroundColor: COR.fundo}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${vidScale})`,
          }}
        />
      </AbsoluteFill>

      {/* HUD no topo (y=158 a 385) — respiro amplo acima da cabeça do dono */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          transform: `translateY(${(1 - sRotulo) * -20 + hudSlideY}px)`,
          opacity: sRotulo,
        }}
      >
        {/* Linha superior: Tópico numerado SEMPRE à esquerda + Gancho à direita */}
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10}}>
          <div
            style={{
              background: COR.alerta,
              padding: '8px 20px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: '#FFFFFF',
              boxShadow: '0 8px 20px rgba(0,0,0,0.45)',
              whiteSpace: 'nowrap',
            }}
          >
            • 01 • O PROBLEMA
          </div>
          <div
            style={{
              background: COR.card,
              border: `2px solid ${COR.marca}`,
              padding: '8px 20px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.texto,
              whiteSpace: 'nowrap',
            }}
          >
            ATENÇÃO NO ATENDIMENTO
          </div>
        </div>

        {/* Card Comparativo Limpo (2 blocos bem delimitados + conector sem sobreposição) */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.94)',
            borderRadius: 24,
            padding: '16px 20px',
            border: '2px solid rgba(255,255,255,0.22)',
            boxShadow: '0 16px 36px rgba(0,0,0,0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 14,
          }}
        >
          {/* Bloco Esquerdo: Ferramenta padrão */}
          <div
            style={{
              flex: 1,
              background: 'rgba(30, 41, 59, 0.96)',
              borderRadius: 18,
              padding: '12px 16px',
              border: `2px solid ${onNaoEntende ? COR.alerta : 'rgba(255,255,255,0.28)'}`,
              transform: `scale(${0.95 + 0.05 * sPadrao})`,
            }}
          >
            <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#CBD5E1', lineHeight: 1.15}}>
              Chat padrão
            </div>
            <div style={{fontFamily, fontSize: 36, fontWeight: 900, color: '#FFFFFF', marginTop: 4, lineHeight: 1.15}}>
              {onNaoEntende ? '✕ Não entende' : 'Só mensagens'}
            </div>
          </div>

          {/* Conector compacto central sem sobrepor caixas */}
          <div
            style={{
              width: 58,
              height: 58,
              borderRadius: 999,
              background: onNaoEntende ? COR.alerta : 'rgba(255,255,255,0.16)',
              border: '2px solid rgba(255,255,255,0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transform: `scale(${onNaoEntende ? 0.92 + 0.12 * sNaoEntende : 0.95})`,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: '#FFFFFF',
            }}
          >
            {onNaoEntende ? '✕' : '≠'}
          </div>

          {/* Bloco Direito: Sua empresa (Alto contraste legível desde o 1º frame, acende em azul aos 9.35s) */}
          <div
            style={{
              flex: 1,
              background: onRotina ? 'rgba(31, 147, 255, 0.28)' : 'rgba(30, 41, 59, 0.92)',
              borderRadius: 18,
              padding: '12px 16px',
              border: `2px solid ${onRotina ? COR.marca : 'rgba(255,255,255,0.38)'}`,
              boxShadow: onRotina ? '0 0 22px rgba(31,147,255,0.45)' : 'none',
              transform: `scale(${onRotina ? 0.95 + 0.07 * sRotina : 0.96})`,
              opacity: onRotina ? 1 : 0.85,
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: onRotina ? COR.marcaClara : 'rgba(255,255,255,0.85)',
                lineHeight: 1.15,
              }}
            >
              Sua empresa
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: onRotina ? '#FFFFFF' : 'rgba(255,255,255,0.92)',
                marginTop: 4,
                lineHeight: 1.15,
              }}
            >
              Rotina específica
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// CENA 2: DONO 2 - COMO FUNCIONA (11.48s - 18.39s)
// Punch-in de câmera (1.14 -> 1.21) + Card Único de Destaque com Ícone (sem 3 caixas)
// ---------------------------------------------------------------------------
const Cena2ComoFunciona: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((18.39 - 11.48) * fps);
  const tAbs = 11.48 + frame / fps;

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [durFrames - 10, durFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const hudEnterY = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  const hudExitX = interpolate(frame, [durFrames - 10, durFrames], [0, -60], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Punch-in de câmera para quebrar o plano médio estático da Cena 1
  const vidScale = interpolate(frame, [0, durFrames], [1.14, 1.21], {extrapolateRight: 'clamp'});

  const stage = tAbs >= 16.49 ? 2 : tAbs >= 14.43 ? 1 : 0;
  const stageStart = stage === 2 ? 16.49 : stage === 1 ? 14.43 : 12.0;
  const stagePop = spring({
    frame: Math.max(0, Math.round((tAbs - stageStart) * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  const stageInfo = [
    {
      ico: '⚙️',
      etapa: 'ETAPA 1 DE 3 · BASE',
      titulo: 'CRM a partir do Chatwoot',
      sub: 'Sistema adaptado para sua empresa',
    },
    {
      ico: '🤖',
      etapa: 'ETAPA 2 DE 3 · INTELIGÊNCIA',
      titulo: 'Personalizado com IA',
      sub: 'Inteligência artificial integrada',
    },
    {
      ico: '🔄',
      etapa: 'ETAPA 3 DE 3 · SOB MEDIDA',
      titulo: 'Feito para o seu fluxo',
      sub: 'Adaptado à rotina do seu negócio',
    },
  ][stage];

  const progressPct = interpolate(tAbs, [12.0, 17.5], [33, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, backgroundColor: COR.fundo}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${vidScale}) translateY(18px)`,
          }}
        />
      </AbsoluteFill>

      {/* Topo (y=158 a 385): Card Único de Destaque — zero microtextos e zero 3 caixas */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          transform: `translateY(${(1 - hudEnterY) * -28}px) translateX(${hudExitX}px)`,
        }}
      >
        {/* Cabeçalho padronizado: Tópico numerado à esquerda + Tag à direita */}
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div
            style={{
              background: `linear-gradient(135deg, ${COR.marca} 0%, #0284C7 100%)`,
              padding: '8px 24px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: '#FFFFFF',
              boxShadow: '0 8px 20px rgba(31,147,255,0.4)',
            }}
          >
            • 02 • COMO FUNCIONA
          </div>
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.94)',
              padding: '8px 22px',
              borderRadius: 999,
              border: `2px solid ${COR.marca}`,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.marcaClara,
            }}
          >
            SISTEMA ADAPTADO
          </div>
        </div>

        {/* Card Único de Destaque com Ícone Grande e Tipografia Limpa */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.95)',
            borderRadius: 24,
            padding: '16px 24px',
            border: `2px solid ${COR.marca}`,
            boxShadow: '0 18px 40px rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            transform: `scale(${0.95 + 0.05 * stagePop})`,
          }}
        >
          <div
            style={{
              width: 78,
              height: 78,
              borderRadius: 22,
              background: `linear-gradient(135deg, ${COR.marca} 0%, #0B4F94 100%)`,
              border: '2px solid #93C5FD',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 42,
              flexShrink: 0,
              boxShadow: '0 8px 22px rgba(31,147,255,0.45)',
            }}
          >
            {stageInfo.ico}
          </div>

          <div style={{display: 'flex', flexDirection: 'column', flex: 1, gap: 4}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <span style={{fontFamily, fontSize: 34, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.15}}>
                {stageInfo.titulo}
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: COR.marcaClara,
                  background: 'rgba(31,147,255,0.18)',
                  padding: '2px 14px',
                  borderRadius: 99,
                }}
              >
                {stage + 1}/3
              </span>
            </div>
            <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#E2E8F0', lineHeight: 1.15}}>
              {stageInfo.sub}
            </div>
            {/* Barra contínua de progresso da adaptação */}
            <div
              style={{
                marginTop: 6,
                height: 8,
                borderRadius: 99,
                background: 'rgba(255,255,255,0.16)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${progressPct}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, ${COR.marca} 0%, ${COR.marcaClara} 100%)`,
                  borderRadius: 99,
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// CENA 3: DONO 3 - O RESULTADO (18.04s - 25.52s)
// Mudança de escala no corte + Paleta Azul/Ciano da Marca + Pílula 03 à esquerda + Respiro acima do cabelo
// ---------------------------------------------------------------------------
const Cena3Resultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((25.52 - 18.04) * fps);
  const tAbs = 18.04 + frame / fps;

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [durFrames - 12, durFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const exitScale = interpolate(frame, [durFrames - 12, durFrames], [1, 0.92], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const exitBlur = interpolate(frame, [durFrames - 12, durFrames], [0, 10], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const hudEnter = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  // Retorno para enquadramento mais aberto (1.0 -> 1.07) contrastando com o close 1.21x da Cena 2
  const vidScale = interpolate(frame, [0, durFrames], [1.0, 1.07], {extrapolateRight: 'clamp'});

  const p1 = spring({frame: Math.max(0, Math.round((tAbs - 19.02) * fps)), fps, config: {damping: 13, stiffness: 150}});
  const p2 = spring({frame: Math.max(0, Math.round((tAbs - 21.3) * fps)), fps, config: {damping: 13, stiffness: 150}});
  const p3 = spring({frame: Math.max(0, Math.round((tAbs - 23.08) * fps)), fps, config: {damping: 13, stiffness: 150}});

  const pilares = [
    {t: 19.02, sp: p1, tit: '✓ Atendimento', desc: 'Em um só lugar'},
    {t: 21.3, sp: p2, tit: '✓ Tickets', desc: 'Helpdesk integrado'},
    {t: 23.08, sp: p3, tit: '✓ Histórico', desc: 'de cada cliente'},
  ];

  return (
    <AbsoluteFill
      style={{
        opacity: enterOp * exitOp,
        backgroundColor: COR.fundo,
        transform: `scale(${exitScale})`,
        filter: exitBlur > 0.2 ? `blur(${exitBlur}px)` : 'none',
      }}
    >
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${vidScale})`,
          }}
        />
      </AbsoluteFill>

      {/* HUD compacto no topo (y=154 a 375) — folga generosa acima do cabelo do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          transform: `translateX(${(1 - hudEnter) * 50}px)`,
          opacity: hudEnter,
        }}
      >
        {/* Pílula numerada SEMPRE à esquerda + Tema à direita, na paleta azul/ciano da marca */}
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div
            style={{
              background: `linear-gradient(135deg, ${COR.marca} 0%, #0284C7 100%)`,
              padding: '8px 24px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: '#FFFFFF',
              boxShadow: '0 8px 20px rgba(31,147,255,0.4)',
            }}
          >
            • 03 • O RESULTADO
          </div>
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.94)',
              padding: '8px 22px',
              borderRadius: 999,
              border: `2px solid ${COR.marcaClara}`,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.marcaClara,
            }}
          >
            CLAREZA NA OPERAÇÃO
          </div>
        </div>

        {/* Painel compacto em Azul/Ciano com 2 linhas legíveis por pilar e alto contraste */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.95)',
            borderRadius: 24,
            padding: '14px 18px',
            border: `2px solid ${COR.marca}`,
            boxShadow: '0 18px 40px rgba(0,0,0,0.6)',
            display: 'flex',
            justifyContent: 'space-between',
            gap: 12,
          }}
        >
          {pilares.map((item, idx) => {
            const on = tAbs >= item.t;
            return (
              <div
                key={idx}
                style={{
                  flex: 1,
                  background: on ? 'rgba(31, 147, 255, 0.28)' : 'rgba(30, 41, 59, 0.92)',
                  border: `2px solid ${on ? COR.marcaClara : 'rgba(255,255,255,0.35)'}`,
                  borderRadius: 18,
                  padding: '10px 10px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transform: `scale(${on ? 0.96 + 0.04 * item.sp : 0.96})`,
                  opacity: on ? 1 : 0.85,
                  textAlign: 'center',
                  boxShadow: on ? '0 0 18px rgba(31,147,255,0.35)' : 'none',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: on ? '#FFFFFF' : 'rgba(255,255,255,0.92)',
                    lineHeight: 1.15,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {item.tit}
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: on ? COR.marcaClara : 'rgba(226,232,240,0.88)',
                    marginTop: 4,
                    lineHeight: 1.15,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {item.desc}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// CENA 4: CARTÃO FINAL (25.17s - 29.12s)
// Transição fluida + Copy enxuto sem redundâncias + Todos os 3 cartões legíveis desde o frame 0
// ---------------------------------------------------------------------------
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.ceil((29.12 - 25.17) * fps);

  const enterSpring = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const enterOp = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const enterScale = interpolate(enterSpring, [0, 1], [1.06, 1.0]);

  const bgScale = interpolate(frame, [0, durFrames], [1.0, 1.2], {extrapolateRight: 'clamp'});
  const bgPanX = interpolate(frame, [0, durFrames], [-30, 30], {extrapolateRight: 'clamp'});
  const bgPanY = interpolate(frame, [0, durFrames], [15, -30], {extrapolateRight: 'clamp'});
  const glowX = interpolate(frame, [0, durFrames], [25, 75], {extrapolateRight: 'clamp'});
  const glowY = interpolate(frame, [0, durFrames], [30, 60], {extrapolateRight: 'clamp'});

  const cardSpring = spring({frame: Math.max(0, frame - 2), fps, config: {damping: 13, stiffness: 140}});
  const ctaSpring = spring({frame: Math.max(0, frame - 8), fps, config: {damping: 12, stiffness: 150}});

  // Pulso e flutuação contínuos até o último frame
  const pulse = 1 + 0.05 * Math.sin((frame / fps) * Math.PI * 2.8);
  const floatCard = interpolate(frame, [0, durFrames], [12, -14], {extrapolateRight: 'clamp'});
  const shineX = interpolate(frame % 40, [0, 40], [-260, 1060]);

  const features = [
    {
      tIni: 4,
      ico: '💬',
      tit: 'Atendimento e Histórico',
      desc: 'Contexto de cada cliente em um só lugar',
    },
    {
      tIni: 18,
      ico: '🎫',
      tit: 'Integração CRM & Helpdesk',
      desc: 'Tickets organizados por etapas',
    },
    {
      tIni: 32,
      ico: '🤖',
      tit: 'Personalizado com IA',
      desc: 'Adaptado a partir do Chatwoot',
    },
  ];

  return (
    <AbsoluteFill style={{opacity: enterOp, transform: `scale(${enterScale})`, backgroundColor: COR.fundo}}>
      {/* Fundo foto desfocada + véu escuro da marca com luz viva em movimento */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translate(${bgPanX}px, ${bgPanY}px)`,
            filter: 'blur(16px) brightness(0.55)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at ${glowX}% ${glowY}%, rgba(31,147,255,0.45) 0%, rgba(17,24,39,0.85) 60%, rgba(11,17,32,0.96) 100%)`,
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo perfeitamente distribuído na Safe Zone (y=240 a 1420, x=60 a 1020) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 24,
          transform: `translateY(${floatCard}px)`,
        }}
      >
        {/* Bloco Superior da Marca + Proposta (sem redundâncias) */}
        <div
          style={{
            width: '100%',
            background: 'rgba(17, 24, 39, 0.94)',
            border: `3px solid ${COR.marca}`,
            borderRadius: 34,
            padding: '30px 34px',
            boxShadow: '0 24px 60px rgba(0,0,0,0.65)',
            transform: `scale(${0.92 + 0.08 * cardSpring})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 14,
          }}
        >
          <div
            style={{
              background: 'rgba(31, 147, 255, 0.22)',
              border: `2px solid ${COR.marca}`,
              padding: '8px 28px',
              borderRadius: 999,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.marcaClara,
            }}
          >
            SOB MEDIDA
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.08,
              letterSpacing: -0.5,
            }}
          >
            CRM Chatwoot <span style={{color: COR.marca}}>IA</span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 600,
              color: '#E2E8F0',
              lineHeight: 1.28,
              textWrap: 'balance',
            }}
          >
            Atendimento, tickets e IA integrados ao seu fluxo.
          </div>
        </div>

        {/* 3 Cards de Benefícios — Texto branco legível desde o frame 0 + ativação escalonada em azul */}
        <div style={{display: 'flex', flexDirection: 'column', gap: 16, width: '100%'}}>
          {features.map((f, i) => {
            const fSp = spring({frame: Math.max(0, frame - f.tIni), fps, config: {damping: 13, stiffness: 150}});
            const activeHighlight = frame >= f.tIni;
            return (
              <div
                key={i}
                style={{
                  background: activeHighlight ? 'rgba(31, 147, 255, 0.24)' : 'rgba(30, 41, 59, 0.92)',
                  border: `2px solid ${activeHighlight ? COR.marca : 'rgba(255,255,255,0.34)'}`,
                  borderRadius: 24,
                  padding: '20px 26px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 20,
                  boxShadow: activeHighlight ? '0 14px 35px rgba(31,147,255,0.28)' : '0 10px 24px rgba(0,0,0,0.4)',
                  transform: `translateX(${(1 - fSp) * 28}px) scale(${0.96 + 0.04 * fSp})`,
                  opacity: activeHighlight ? 1 : 0.88,
                }}
              >
                <div
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: 18,
                    background: `linear-gradient(135deg, ${COR.marca} 0%, #0B4F94 100%)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily,
                    fontSize: 36,
                    flexShrink: 0,
                    boxShadow: '0 8px 18px rgba(31,147,255,0.45)',
                  }}
                >
                  {f.ico}
                </div>
                <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                  <div style={{fontFamily, fontSize: 36, fontWeight: 900, color: '#FFFFFF'}}>
                    {f.tit}
                  </div>
                  <div style={{fontFamily, fontSize: 34, fontWeight: 600, color: '#E2E8F0'}}>
                    {f.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bloco de Conversão: Botão CTA Pulsante + @arroba */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
            marginTop: 8,
            transform: `scale(${0.92 + 0.08 * ctaSpring})`,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              width: '100%',
              background: `linear-gradient(135deg, ${COR.marca} 0%, #0A66C2 100%)`,
              borderRadius: 28,
              padding: '26px 32px',
              boxShadow: '0 22px 55px rgba(31, 147, 255, 0.55)',
              border: '3px solid #93C5FD',
              transform: `scale(${pulse})`,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 16,
            }}
          >
            {/* Brilho passando */}
            <div
              style={{
                position: 'absolute',
                top: -40,
                bottom: -40,
                left: shineX,
                width: 160,
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)',
                transform: 'rotate(20deg)',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 0.8,
                textTransform: 'uppercase',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          <div
            style={{
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(255,255,255,0.22)',
              padding: '14px 38px',
              borderRadius: 999,
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              boxShadow: '0 10px 28px rgba(0,0,0,0.45)',
            }}
          >
            @crmchatwoot.ia
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// COMPONENTE PRINCIPAL
// ---------------------------------------------------------------------------
export const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  const volTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0.02, 0.1, 0.1, 0.0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  return (
    <AbsoluteFill style={{backgroundColor: COR.fundo, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {/* CENA 0: 0.00s - 5.00s */}
      <Sequence from={0} durationInFrames={150}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 4.65s - 11.83s */}
      <Sequence from={Math.round(4.65 * fps)} durationInFrames={Math.round((11.83 - 4.65) * fps)}>
        <Cena1Problema />
      </Sequence>

      {/* CENA 2: 11.48s - 18.39s */}
      <Sequence from={Math.round(11.48 * fps)} durationInFrames={Math.round((18.39 - 11.48) * fps)}>
        <Cena2ComoFunciona />
      </Sequence>

      {/* CENA 3: 18.04s - 25.52s */}
      <Sequence from={Math.round(18.04 * fps)} durationInFrames={Math.round((25.52 - 18.04) * fps)}>
        <Cena3Resultado />
      </Sequence>

      {/* CENA 4: 25.17s - 29.12s */}
      <Sequence from={Math.round(25.17 * fps)} durationInFrames={durationInFrames - Math.round(25.17 * fps)}>
        <Cena4Cartao />
      </Sequence>

      {/* Barra de progresso fina na Safe Zone (y=150, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 99,
          background: 'rgba(255,255,255,0.2)',
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            background: COR.marca,
            borderRadius: 99,
          }}
        />
      </div>

      {/* Legenda Karaokê oficial (desligada no cartão final t >= 25.17s) */}
      {t < 25.17 && (
        <Karaoke
          palavras={PALAVRAS_K}
          fontFamily={fontFamily}
          destaque={COR.marca}
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={360}
          maxLetras={32}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <>
      <Composition
        id="Main"
        component={VideoPrincipal}
        fps={30}
        width={1080}
        height={1920}
        durationInFrames={Math.ceil(29.12 * 30)}
      />
    </>
  );
};
