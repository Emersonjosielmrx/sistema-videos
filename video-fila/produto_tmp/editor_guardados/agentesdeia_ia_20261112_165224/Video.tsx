import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';

const {fontFamily} = loadFont();

const COR = {
  marca: '#10B981',
  marcaBrilho: '#34D399',
  marcaEscura: '#059669',
  apoio: '#111827',
  cardEscuro: 'rgba(17, 24, 39, 0.92)',
  cardBorda: 'rgba(16, 185, 129, 0.45)',
  texto: '#FFFFFF',
  textoSec: '#E2E8F0',
  alerta: '#F43F5E',
};

const PALAVRAS: PalavraK[] = [
  {p: 'Cansado', ini: 0.318, fim: 0.835},
  {p: 'de', ini: 0.847, fim: 0.919},
  {p: 'IA', ini: 0.931, fim: 2.181},
  {p: 'que', ini: 2.193, fim: 2.301},
  {p: 'só', ini: 2.313, fim: 2.506},
  {p: 'conversa', ini: 2.518, fim: 3.119},
  {p: 'e', ini: 3.131, fim: 3.179, quebraAntes: true},
  {p: 'não', ini: 3.191, fim: 3.347},
  {p: 'faz', ini: 3.359, fim: 3.539},
  {p: 'o', ini: 3.551, fim: 3.659},
  {p: 'trabalho?', ini: 3.671, fim: 4.212, quebraApos: true},

  {p: 'Eu', ini: 5.817, fim: 5.937, quebraAntes: true},
  {p: 'achava', ini: 5.949, fim: 6.334},
  {p: 'que', ini: 6.346, fim: 6.43},
  {p: 'IA', ini: 6.442, fim: 7.68},
  {p: 'só', ini: 7.692, fim: 7.908},
  {p: 'escrevia', ini: 7.92, fim: 8.401},
  {p: 'texto,', ini: 8.413, fim: 8.822, quebraApos: true},
  {p: 'até', ini: 9.038, fim: 9.267, quebraAntes: true},
  {p: 'colocar', ini: 9.279, fim: 9.723},
  {p: 'meu', ini: 9.735, fim: 9.892},
  {p: 'agente', ini: 9.904, fim: 10.276},
  {p: 'pessoal', ini: 10.288, fim: 10.721},
  {p: 'para', ini: 10.733, fim: 10.913},
  {p: 'trabalhar.', ini: 10.925, fim: 11.454, quebraApos: true},

  {p: 'Em', ini: 12.893, fim: 13.049, quebraAntes: true},
  {p: 'vez', ini: 13.061, fim: 13.29},
  {p: 'de', ini: 13.302, fim: 13.398},
  {p: 'só', ini: 13.41, fim: 13.59},
  {p: 'bater', ini: 13.602, fim: 13.879},
  {p: 'papo,', ini: 13.915, fim: 14.335, quebraApos: true},
  {p: 'eu', ini: 14.383, fim: 14.48, quebraAntes: true},
  {p: 'peço', ini: 14.492, fim: 14.768},
  {p: 'um', ini: 14.78, fim: 14.852},
  {p: 'follow-up', ini: 14.864, fim: 15.537},
  {p: 'de', ini: 15.549, fim: 15.645},
  {p: 'cliente', ini: 15.657, fim: 16.162, quebraApos: true},
  {p: 'e', ini: 16.186, fim: 16.27, quebraAntes: true},
  {p: 'ele', ini: 16.282, fim: 16.427},
  {p: 'mesmo', ini: 16.439, fim: 16.787},
  {p: 'realiza.', ini: 16.799, fim: 17.34, quebraApos: true},

  {p: 'No', ini: 18.193, fim: 18.301, quebraAntes: true},
  {p: 'Agente', ini: 18.313, fim: 18.686},
  {p: 'Pessoal', ini: 18.698, fim: 19.119},
  {p: 'IA,', ini: 19.131, fim: 20.441, quebraApos: true},
  {p: 'eu', ini: 20.681, fim: 20.789, quebraAntes: true},
  {p: 'entrego', ini: 20.801, fim: 21.198},
  {p: 'qualquer', ini: 21.21, fim: 21.582},
  {p: 'coisa', ini: 21.607, fim: 21.895},
  {p: 'da', ini: 21.907, fim: 22.003},
  {p: 'rotina', ini: 22.015, fim: 22.52, quebraApos: true},
  {p: 'e', ini: 22.544, fim: 22.58, quebraAntes: true},
  {p: 'recebo', ini: 22.592, fim: 23.025},
  {p: 'a', ini: 23.037, fim: 23.073},
  {p: 'tarefa', ini: 23.085, fim: 23.445},
  {p: 'pronta.', ini: 23.457, fim: 23.902, quebraApos: true},
];

// ============================================================================
// CENA 0 — PERGUNTA (0.00s a 5.67s | 170 frames)
// Composição (a): Apresentador real em primeiro plano desde 0.0s + Pergunta em alto contraste
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo sobre o profissional em primeiro plano (sem mesa vazia nem banana)
  const scaleBg = interpolate(frame, [0, 170], [1.06, 1.18], {extrapolateRight: 'clamp'});
  const panX = interpolate(frame, [0, 170], [10, -15], {extrapolateRight: 'clamp'});
  const panY = interpolate(frame, [0, 170], [5, -5], {extrapolateRight: 'clamp'});

  const spPilula = spring({frame: frame - 2, fps, config: {damping: 14, stiffness: 150}});
  const spBloco1 = spring({frame: Math.max(0, frame - Math.round(0.28 * fps)), fps, config: {damping: 13, stiffness: 160}});
  const spBloco2 = spring({frame: Math.max(0, frame - Math.round(2.25 * fps)), fps, config: {damping: 13, stiffness: 160}});
  const spBloco3 = spring({frame: Math.max(0, frame - Math.round(3.15 * fps)), fps, config: {damping: 12, stiffness: 170}});

  const saidaOp = interpolate(frame, [158, 170], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: COR.apoio, opacity: saidaOp}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 45%',
            transform: `scale(${scaleBg}) translate(${panX}px, ${panY}px)`,
            filter: 'brightness(0.92) contrast(1.06)',
          }}
        />
      </AbsoluteFill>

      {/* Vinheta suave: topo escurecido para a pergunta cinestésica, centro-baixo livre para o apresentador */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.3) 26%, rgba(15,23,42,0.02) 45%, rgba(15,23,42,0.82) 100%)',
        }}
      />

      {/* Pílula Superior (y=168) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transform: `translateY(${interpolate(spPilula, [0, 1], [-25, 0])}px)`,
          opacity: spPilula,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            backgroundColor: '#0F172A',
            border: `2px solid ${COR.marca}`,
            borderRadius: 999,
            padding: '12px 28px',
            boxShadow: '0 10px 28px rgba(0,0,0,0.45)',
          }}
        >
          <div
            style={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              backgroundColor: COR.marca,
              boxShadow: `0 0 14px ${COR.marca}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.texto,
              letterSpacing: 1,
            }}
          >
            AGENTES DE IA
          </span>
        </div>
      </div>

      {/* Bloco Principal — Pergunta Sincronizada na faixa superior (y=250..530), deixando o apresentador 100% livre */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        {/* Parte 1: 0.31s "Cansado de IA" */}
        <div
          style={{
            backgroundColor: '#0F172A',
            borderLeft: `10px solid ${COR.alerta}`,
            borderRadius: 20,
            padding: '16px 26px',
            boxShadow: '0 16px 36px rgba(0,0,0,0.6)',
            transform: `translateX(${interpolate(spBloco1, [0, 1], [-70, 0])}px) scale(${interpolate(spBloco1, [0, 1], [0.94, 1])})`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 50,
              fontWeight: 900,
              color: COR.texto,
              lineHeight: 1.1,
              textTransform: 'uppercase',
            }}
          >
            CANSADO DE IA
          </div>
        </div>

        {/* Parte 2: 2.31s "que só conversa" */}
        {frame >= Math.round(2.2 * fps) && (
          <div
            style={{
              backgroundColor: '#0F172A',
              borderLeft: `10px solid #F59E0B`,
              borderRadius: 20,
              padding: '16px 26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 16px 36px rgba(0,0,0,0.6)',
              transform: `translateX(${interpolate(spBloco2, [0, 1], [70, 0])}px) scale(${interpolate(spBloco2, [0, 1], [0.94, 1])})`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FDE68A',
                lineHeight: 1.1,
                textTransform: 'uppercase',
              }}
            >
              QUE SÓ CONVERSA
            </span>
            <div
              style={{
                backgroundColor: '#78350F',
                border: '2px solid #F59E0B',
                borderRadius: 12,
                padding: '6px 16px',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              SÓ TEXTO
            </div>
          </div>
        )}

        {/* Parte 3: 3.19s "e não faz o trabalho?" — Mantém padrão de fundo escuro com texto em alto contraste, sem pílula antecipada */}
        {frame >= Math.round(3.1 * fps) && (
          <div
            style={{
              backgroundColor: '#0F172A',
              borderLeft: `10px solid ${COR.marca}`,
              border: `2px solid ${COR.marca}`,
              borderRadius: 20,
              padding: '18px 26px',
              boxShadow: '0 18px 42px rgba(0, 0, 0, 0.65)',
              transform: `translateY(${interpolate(spBloco3, [0, 1], [35, 0])}px) scale(${interpolate(spBloco3, [0, 1], [0.94, 1])})`,
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: COR.texto,
                lineHeight: 1.1,
                textTransform: 'uppercase',
              }}
            >
              E NÃO FAZ O <span style={{color: COR.marcaBrilho}}>TRABALHO?</span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1 — A SITUAÇÃO: ANTES X DEPOIS (5.32s a 12.75s | 223 frames)
// Composição (c): Troca direta no mesmo espaço físico (Antes -> Agora sem empilhar nem opacidade fantasma)
// Usa img_2.jpg com enquadramento dinâmico Ken Burns, deixando tronco e mãos operando o laptop visíveis
// ============================================================================
const Cena1Situacao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // tempo relativo à cena (início = 5.32s)
  const absT = 5.32 + t;

  const entradaOp = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  const saidaOp = interpolate(frame, [212, 223], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Ken Burns dinâmico de 1.0x a 1.10x com leve pan expressivo
  const scaleBg = interpolate(frame, [0, 223], [1.0, 1.1], {extrapolateRight: 'clamp'});
  const panX = interpolate(frame, [0, 223], [-15, 25], {extrapolateRight: 'clamp'});
  const panY = interpolate(frame, [0, 223], [10, -14], {extrapolateRight: 'clamp'});

  // Sincronia exata com a voz:
  // 5.81s: "Eu achava que IA só escrevia texto"
  // 9.03s: "até colocar meu agente pessoal para trabalhar"
  const spTopo = spring({frame: frame - 3, fps, config: {damping: 14, stiffness: 150}});
  const spAntes = spring({frame: Math.max(0, Math.round((absT - 5.65) * fps)), fps, config: {damping: 13, stiffness: 180}});
  const spDepois = spring({frame: Math.max(0, Math.round((absT - 9.03) * fps)), fps, config: {damping: 12, stiffness: 200}});
  const spTrabalhar = spring({frame: Math.max(0, Math.round((absT - 10.65) * fps)), fps, config: {damping: 12, stiffness: 180}});

  const mostrarDepois = absT >= 9.03;

  return (
    <AbsoluteFill style={{backgroundColor: COR.apoio, opacity: entradaOp * saidaOp}}>
      {/* Fotografia real do profissional operando o laptop (img_2.jpg) com Ken Burns contínuo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 28%',
            transform: `scale(${scaleBg}) translate(${panX}px, ${panY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Gradiente leve apenas no topo e na base, deixando rosto, tronco e mãos no notebook 100% livres */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.05) 22%, rgba(17,24,39,0.08) 65%, rgba(17,24,39,0.92) 100%)',
        }}
      />

      {/* Topo informativo padronizado (y=165) — mantém 'A SITUAÇÃO' e 'ANTES VS DEPOIS' fixos durante toda a cena 1 */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transform: `translateY(${interpolate(spTopo, [0, 1], [-25, 0])}px)`,
          opacity: spTopo,
        }}
      >
        <div
          style={{
            backgroundColor: '#0F172A',
            border: `2px solid ${COR.marca}`,
            borderRadius: 999,
            padding: '12px 28px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: COR.marcaBrilho,
              textTransform: 'uppercase',
            }}
          >
            A SITUAÇÃO
          </span>
        </div>

        <div
          style={{
            backgroundColor: '#0F172A',
            borderRadius: 999,
            padding: '12px 28px',
            border: `2px solid ${COR.marca}`,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: COR.texto,
            }}
          >
            ANTES VS DEPOIS
          </span>
        </div>
      </div>

      {/* Troca direta no mesmo espaço físico no terço inferior (y=1010..1250), deixando o homem e o laptop visíveis */}
      <div
        style={{
          position: 'absolute',
          top: 1015,
          left: 60,
          right: 60,
        }}
      >
        {!mostrarDepois ? (
          /* Card ANTES — Opacidade 100% sólida, sem transparência fantasma */
          <div
            style={{
              backgroundColor: '#0F172A',
              borderRadius: 26,
              padding: '26px 32px',
              border: '3px solid #F59E0B',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              transform: `translateY(${interpolate(spAntes, [0, 1], [55, 0])}px) scale(${interpolate(spAntes, [0, 1], [0.94, 1])})`,
              boxShadow: '0 20px 45px rgba(0,0,0,0.65)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FBBF24',
                  textTransform: 'uppercase',
                }}
              >
                ANTES • IA COMUM
              </span>
              <div
                style={{
                  backgroundColor: '#78350F',
                  border: '2px solid #F59E0B',
                  borderRadius: 999,
                  padding: '8px 22px',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                SÓ CONVERSA
              </div>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              Só escrevia texto
            </div>
          </div>
        ) : (
          /* Card AGORA — Entra em 9.03s ("até colocar...") com fundo sólido 100% opaco e slide-up ágil */
          <div
            style={{
              backgroundColor: '#064E3B',
              borderRadius: 26,
              padding: '26px 32px',
              border: `3px solid ${COR.marcaBrilho}`,
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              transform: `translateY(${interpolate(spDepois, [0, 1], [65, 0])}px) scale(${interpolate(spDepois, [0, 1], [0.94, 1])})`,
              boxShadow: '0 22px 48px rgba(0,0,0,0.75)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                }}
              >
                AGORA • AGENTE PESSOAL IA
              </span>
              <div
                style={{
                  backgroundColor: '#022C22',
                  border: `2px solid ${COR.marcaBrilho}`,
                  borderRadius: 999,
                  padding: '8px 22px',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  transform: `scale(${interpolate(spTrabalhar, [0, 1], [0.9, 1.04])})`,
                }}
              >
                FAZ POR VOCÊ
              </div>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              Executa as tarefas do seu dia
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — NA PRÁTICA: CONVERSA SIMULADA (12.40s a 18.05s | 170 frames)
// Composição (b): Simulação de chat integrada a painel de automação CRM em tempo real.
// Elimina o vácuo ocioso em q07/q08 e mantém follow-up/agendamento até o fim da cena.
// ============================================================================
const Cena2Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const absT = 12.4 + t;

  const entradaOp = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  const saidaOp = interpolate(frame, [158, 170], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const phoneSp = spring({frame, fps, config: {damping: 14, stiffness: 130}});
  const tiltY = interpolate(frame, [0, 170], [-4, 3], {extrapolateRight: 'clamp'});
  const gridPan = interpolate(frame, [0, 170], [0, -50], {extrapolateRight: 'clamp'});

  // Sincronia fiel à locução:
  // 12.89s..14.33s: "Em vez de só bater papo"
  // 14.38s..16.16s: "eu peço um follow-up de cliente"
  // 16.18s..17.34s: "e ele mesmo realiza."
  const spMsg1 = spring({frame: Math.max(0, Math.round((absT - 12.65) * fps)), fps, config: {damping: 14, stiffness: 150}});
  const mostrarDigitando = absT >= 14.35 && absT < 15.15;
  const mostrarMsg2 = absT >= 15.15;
  const spMsg2 = spring({frame: Math.max(0, Math.round((absT - 15.15) * fps)), fps, config: {damping: 13, stiffness: 150}});
  const realizado = absT >= 16.18;
  const spRealizado = spring({frame: Math.max(0, Math.round((absT - 16.18) * fps)), fps, config: {damping: 12, stiffness: 160}});

  // Pulso dos 3 pontinhos digitando
  const dot1 = 0.5 + Math.sin(t * 12) * 0.5;
  const dot2 = 0.5 + Math.sin(t * 12 + 1) * 0.5;
  const dot3 = 0.5 + Math.sin(t * 12 + 2) * 0.5;

  return (
    <AbsoluteFill style={{backgroundColor: '#080E1B', opacity: entradaOp * saidaOp}}>
      {/* Background tecnológico com dashboard CRM sutil */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 25% 20%, rgba(16,185,129,0.22) 0%, rgba(8,14,27,0.96) 55%), radial-gradient(circle at 80% 80%, rgba(5,150,105,0.18) 0%, rgba(8,14,27,1) 65%)',
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(16, 185, 129, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(16, 185, 129, 0.08) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          transform: `translateY(${gridPan}px)`,
        }}
      />

      {/* Marca d'água / Interface de CRM em desfoque no fundo para reforçar automação corporativa real */}
      <div
        style={{
          position: 'absolute',
          top: 230,
          left: 45,
          right: 45,
          opacity: 0.16,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
          pointerEvents: 'none',
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: 12}}>
          <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>CRM HUB • CONTATOS & PIPELINE</span>
          <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: COR.marcaBrilho}}>AUTOMAÇÃO ATIVA</span>
        </div>
        <div style={{display: 'flex', gap: 16}}>
          <div style={{flex: 1, backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: 16, padding: '16px 20px'}}>
            <div style={{fontSize: 32, color: '#94A3B8'}}>Follow-ups Pendentes</div>
            <div style={{fontSize: 44, fontWeight: 900, color: '#FFFFFF'}}>12</div>
          </div>
          <div style={{flex: 1, backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: 16, padding: '16px 20px'}}>
            <div style={{fontSize: 32, color: '#94A3B8'}}>Reuniões Agendadas</div>
            <div style={{fontSize: 44, fontWeight: 900, color: '#FFFFFF'}}>06</div>
          </div>
        </div>
      </div>

      {/* Topo: Rótulo "Na prática" + Selo "Simulação" (y=165) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        <div
          style={{
            backgroundColor: COR.marca,
            borderRadius: 999,
            padding: '12px 28px',
            boxShadow: '0 8px 24px rgba(16,185,129,0.3)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: '#042F2E',
              textTransform: 'uppercase',
            }}
          >
            NA PRÁTICA
          </span>
        </div>

        <div
          style={{
            backgroundColor: '#0F172A',
            border: '2px solid rgba(255,255,255,0.4)',
            borderRadius: 999,
            padding: '10px 24px',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#FFFFFF',
            }}
          >
            Simulação
          </span>
        </div>
      </div>

      {/* Bloco Central: Chat + Painel de Execução em tempo real (y=265..1360) */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
          transform: `scale(${interpolate(phoneSp, [0, 1], [0.94, 1])}) rotateY(${tiltY}deg)`,
        }}
      >
        {/* Chat Card */}
        <div
          style={{
            width: '100%',
            backgroundColor: '#0F172A',
            borderRadius: 32,
            border: `3px solid ${COR.marca}`,
            boxShadow: '0 24px 60px rgba(0,0,0,0.75)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Cabeçalho do Chat */}
          <div
            style={{
              backgroundColor: '#064E3B',
              padding: '18px 26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: `2px solid ${COR.marca}`,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: '50%',
                  backgroundColor: COR.marca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#042F2E',
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
                  Agente Pessoal IA
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: COR.marcaBrilho,
                  }}
                >
                  ● Executando tarefas
                </span>
              </div>
            </div>
          </div>

          {/* Área de Mensagens */}
          <div
            style={{
              padding: '24px 24px 28px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
            }}
          >
            {/* Mensagem 1: Usuário pedindo follow-up e reuniões */}
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '92%',
                backgroundColor: '#1E293B',
                border: '2px solid #475569',
                borderRadius: '24px 24px 6px 24px',
                padding: '18px 24px',
                transform: `translateY(${interpolate(spMsg1, [0, 1], [25, 0])}px) scale(${interpolate(spMsg1, [0, 1], [0.94, 1])})`,
                boxShadow: '0 10px 24px rgba(0,0,0,0.35)',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#94A3B8',
                  marginBottom: 4,
                }}
              >
                Você
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Preciso fazer o follow-up dos clientes pendentes e agendar as reuniões.
              </div>
            </div>

            {/* Digitando... */}
            {mostrarDigitando && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  backgroundColor: '#064E3B',
                  border: `2px solid ${COR.marca}`,
                  borderRadius: 20,
                  padding: '14px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                  Agente digitando
                </span>
                <div style={{display: 'flex', gap: 6, alignItems: 'center'}}>
                  <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#34D399', opacity: dot1}} />
                  <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#34D399', opacity: dot2}} />
                  <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#34D399', opacity: dot3}} />
                </div>
              </div>
            )}

            {/* Mensagem 2: Resposta do Agente */}
            {mostrarMsg2 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '92%',
                  backgroundColor: '#065F46',
                  border: `2.5px solid ${COR.marcaBrilho}`,
                  borderRadius: '24px 24px 24px 6px',
                  padding: '18px 24px',
                  transform: `translateY(${interpolate(spMsg2, [0, 1], [25, 0])}px) scale(${interpolate(spMsg2, [0, 1], [0.94, 1])})`,
                  boxShadow: '0 12px 28px rgba(0,0,0,0.45)',
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#A7F3D0',
                    marginBottom: 4,
                  }}
                >
                  Agente Pessoal IA
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Pode deixar. Vou realizar o follow-up e fazer o agendamento por você.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Painel de Execução de Tarefas em Tempo Real (preenche a metade inferior eliminando o vácuo) */}
        <div
          style={{
            width: '100%',
            backgroundColor: '#0F172A',
            border: `2.5px solid ${realizado ? COR.marcaBrilho : '#334155'}`,
            borderRadius: 28,
            padding: '24px 28px',
            boxShadow: '0 16px 40px rgba(0,0,0,0.6)',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            transform: realizado ? `scale(${interpolate(spRealizado, [0, 0.6, 1], [0.96, 1.02, 1])})` : 'scale(1)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#94A3B8',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Automação em Execução
            </span>
            <div
              style={{
                backgroundColor: realizado ? '#064E3B' : '#1E293B',
                border: `2px solid ${realizado ? COR.marcaBrilho : '#475569'}`,
                borderRadius: 999,
                padding: '6px 18px',
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: realizado ? '#FFFFFF' : '#CBD5E1',
              }}
            >
              {realizado ? 'REALIZADO' : 'EM ANDAMENTO'}
            </div>
          </div>

          {/* Tarefa 1: Follow-up */}
          <div
            style={{
              backgroundColor: realizado ? '#064E3B' : '#1E293B',
              border: `2px solid ${realizado ? COR.marcaBrilho : 'transparent'}`,
              borderRadius: 18,
              padding: '14px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: realizado ? COR.marca : '#334155',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M5 13L9.5 17.5L19 7.5"
                    stroke={realizado ? '#042F2E' : '#94A3B8'}
                    strokeWidth="3.2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                Follow-up de clientes
              </span>
            </div>
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: realizado ? '#A7F3D0' : '#94A3B8'}}>
              {realizado ? 'Enviado' : 'Processando'}
            </span>
          </div>

          {/* Tarefa 2: Agendamento */}
          <div
            style={{
              backgroundColor: realizado ? '#064E3B' : '#1E293B',
              border: `2px solid ${realizado ? COR.marcaBrilho : 'transparent'}`,
              borderRadius: 18,
              padding: '14px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: realizado ? COR.marca : '#334155',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M5 13L9.5 17.5L19 7.5"
                    stroke={realizado ? '#042F2E' : '#94A3B8'}
                    strokeWidth="3.2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                Agendamento de reuniões
              </span>
            </div>
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: realizado ? '#A7F3D0' : '#94A3B8'}}>
              {realizado ? 'Confirmado' : 'Processando'}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — O RESULTADO (17.70s a 25.20s | 225 frames)
// Composição (g): Micro-cards executivos (HUD) compactos no terço inferior (y=960..1300)
// Enquadramento superior de img_3.jpg com slow push-in contínuo (elimina a mesa com banana
// e deixa o apresentador e os participantes da reunião 100% visíveis e livres no centro-alto)
// ============================================================================
const TAREFAS_ENTREGUES = [
  {titulo: 'Pesquisa completa', prontoAbs: 22.59},
  {titulo: 'Agendamento de reuniões', prontoAbs: 23.08},
  {titulo: 'Follow-up de clientes', prontoAbs: 23.45},
];

const Cena3Resultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absT = 17.7 + frame / fps;

  const entradaOp = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  const saidaOp = interpolate(frame, [212, 225], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Enquadramento superior da sala de reunião com câmera elevada (elimina a banana da mesa)
  const scaleBg = interpolate(frame, [0, 225], [1.38, 1.50], {extrapolateRight: 'clamp'});
  const panX = interpolate(frame, [0, 225], [-12, 18], {extrapolateRight: 'clamp'});
  const panY = interpolate(frame, [0, 225], [-160, -200], {extrapolateRight: 'clamp'});
  const spHeader = spring({frame: frame - 3, fps, config: {damping: 14, stiffness: 150}});

  return (
    <AbsoluteFill style={{backgroundColor: COR.apoio, opacity: entradaOp * saidaOp}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 42%',
            transform: `scale(${scaleBg}) translate(${panX}px, ${panY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Véu suave no topo e no terço inferior (y >= 920), deixando a equipe inteira livre em y=240..920 */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.04) 18%, rgba(15,23,42,0.08) 50%, rgba(15,23,42,0.96) 70%, rgba(11,17,32,0.99) 100%)',
        }}
      />

      {/* Cabeçalho compacto no topo (y=165) com alto contraste em ambas as pílulas */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transform: `translateY(${interpolate(spHeader, [0, 1], [-25, 0])}px)`,
          opacity: spHeader,
        }}
      >
        <div
          style={{
            backgroundColor: '#0F172A',
            border: `2px solid ${COR.marca}`,
            borderRadius: 999,
            padding: '12px 28px',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: COR.marcaBrilho,
              textTransform: 'uppercase',
            }}
          >
            O RESULTADO
          </span>
        </div>

        <div
          style={{
            backgroundColor: '#0F172A',
            border: `2px solid ${COR.marcaBrilho}`,
            borderRadius: 999,
            padding: '12px 28px',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: '#FFFFFF',
            }}
          >
            AGENTE PESSOAL IA
          </span>
        </div>
      </div>

      {/* Micro-cards HUD compactos no terço inferior (y=960..1300), sincronizados com "e recebo a tarefa pronta" (22.59s+) */}
      <div
        style={{
          position: 'absolute',
          top: 960,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        {TAREFAS_ENTREGUES.map((item, idx) => {
          const spEntrada = spring({
            frame: Math.max(0, frame - (6 + idx * 8)),
            fps,
            config: {damping: 14, stiffness: 150},
          });
          const ativo = absT >= item.prontoAbs;
          const spVirada = spring({
            frame: Math.max(0, Math.round((absT - item.prontoAbs) * fps)),
            fps,
            config: {damping: 11, stiffness: 180},
          });
          const popScale = ativo ? interpolate(spVirada, [0, 0.5, 1], [1, 1.05, 1]) : 1;

          return (
            <div
              key={idx}
              style={{
                backgroundColor: ativo ? '#064E3B' : '#0F172A',
                border: `2.5px solid ${ativo ? COR.marcaBrilho : 'rgba(148,163,184,0.45)'}`,
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transform: `translateX(${interpolate(spEntrada, [0, 1], [-45, 0])}px) scale(${popScale})`,
                boxShadow: '0 12px 26px rgba(0,0,0,0.55)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: '50%',
                    backgroundColor: ativo ? COR.marca : '#334155',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transform: `scale(${ativo ? interpolate(spVirada, [0, 1], [0.6, 1]) : 1})`,
                  }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M5 13L9.5 17.5L19 7.5"
                      stroke={ativo ? '#042F2E' : '#CBD5E1'}
                      strokeWidth="3.2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  {item.titulo}
                </span>
              </div>

              <div
                style={{
                  backgroundColor: ativo ? '#022C22' : '#1E293B',
                  border: `2px solid ${ativo ? COR.marcaBrilho : '#475569'}`,
                  borderRadius: 12,
                  padding: '6px 18px',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  transform: `scale(${ativo ? interpolate(spVirada, [0, 0.6, 1], [0.85, 1.08, 1]) : 1})`,
                }}
              >
                {ativo ? 'Tarefa pronta' : 'Rotina'}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL / CTA (24.85s a 28.79s | 119 frames)
// Entrada sequencial escalonada (card principal -> botão CTA com spring -> @arroba),
// pulso contínuo + shimmer no botão e slow push-in sobre fundo tecnológico exclusivo,
// perfeitamente equilibrado e centralizado no quadro vertical.
// ============================================================================
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const entradaOp = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});

  // Slow push-in contínuo na textura de fundo
  const bgScale = interpolate(frame, [0, 119], [1.05, 1.25], {extrapolateRight: 'clamp'});
  const panX = interpolate(frame, [0, 119], [0, -35], {extrapolateRight: 'clamp'});
  const panY = interpolate(frame, [0, 119], [0, -25], {extrapolateRight: 'clamp'});

  // Entrada sequencial dos elementos:
  // 1) Card principal (frame 2)
  // 2) Botão CTA (frame 16 ~ 25.38s)
  // 3) @arroba (frame 32 ~ 25.92s)
  const spCard = spring({frame: Math.max(0, frame - 2), fps, config: {damping: 13, stiffness: 140}});
  const spBtn = spring({frame: Math.max(0, frame - 16), fps, config: {damping: 10, stiffness: 160}});
  const spArroba = spring({frame: Math.max(0, frame - 32), fps, config: {damping: 12, stiffness: 150}});

  const floatCardY = Math.sin(t * 3.5) * 6;
  const pulseBtn = 1 + Math.sin(t * 6.5) * 0.038;
  const shineX = interpolate(frame % 40, [0, 40], [-50, 135]);

  return (
    <AbsoluteFill style={{backgroundColor: '#070D19', opacity: entradaOp}}>
      {/* Ambientação tecnológica animada em slow push-in */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${bgScale}) translate(${panX}px, ${panY}px)`,
            background:
              'radial-gradient(circle at 50% 40%, rgba(16,185,129,0.32) 0%, rgba(6,78,59,0.2) 40%, rgba(7,13,25,0.98) 80%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: -120,
            backgroundImage:
              'radial-gradient(rgba(52, 211, 153, 0.22) 2px, transparent 2px), linear-gradient(rgba(16, 185, 129, 0.07) 1.5px, transparent 1.5px)',
            backgroundSize: '56px 56px',
            transform: `scale(${bgScale}) translate(${panX * 1.3}px, ${panY * 1.3}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Container Central Unificado perfeitamente equilibrado no centro vertical (y=430..1360) */}
      <div
        style={{
          position: 'absolute',
          top: 430,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 32,
        }}
      >
        {/* 1. Card de Identidade da Marca */}
        <div
          style={{
            width: '100%',
            backgroundColor: '#0F172A',
            border: `3px solid ${COR.marca}`,
            borderRadius: 36,
            padding: '40px 38px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 18,
            transform: `translateY(${interpolate(spCard, [0, 1], [60, 0]) + floatCardY}px) scale(${interpolate(spCard, [0, 1], [0.92, 1])})`,
            boxShadow: '0 24px 60px rgba(0,0,0,0.75)',
          }}
        >
          <div
            style={{
              backgroundColor: '#064E3B',
              border: `2px solid ${COR.marcaBrilho}`,
              borderRadius: 999,
              padding: '10px 28px',
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              textTransform: 'uppercase',
            }}
          >
            Agentes de IA
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 64,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.08,
            }}
          >
            Agente Pessoal IA
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: COR.textoSec,
              lineHeight: 1.3,
              maxWidth: 820,
            }}
          >
            Delegue tarefas reais a um agente IA: pesquisa, agendamento e follow-up.
          </div>

          <div style={{display: 'flex', gap: 14, marginTop: 4}}>
            {['Pesquisa', 'Agendamento', 'Follow-up'].map((tag, i) => (
              <div
                key={i}
                style={{
                  backgroundColor: '#064E3B',
                  border: '1.5px solid #34D399',
                  borderRadius: 999,
                  padding: '6px 18px',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                {tag}
              </div>
            ))}
          </div>
        </div>

        {/* 2. Botão CTA Pulsante Fiel à Voz: "Chame a gente no direct" (entrada sequencial frame 16) */}
        {frame >= 14 && (
          <div
            style={{
              width: '100%',
              backgroundColor: COR.marca,
              borderRadius: 999,
              padding: '30px 40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 20,
              position: 'relative',
              overflow: 'hidden',
              transform: `translateY(${interpolate(spBtn, [0, 1], [45, 0])}px) scale(${interpolate(spBtn, [0, 1], [0.85, 1]) * pulseBtn})`,
              boxShadow: '0 20px 55px rgba(16, 185, 129, 0.55)',
            }}
          >
            {/* Brilho dinâmico (shimmer) contínuo */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${shineX}%`,
                width: '35%',
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.38) 50%, rgba(255,255,255,0) 100%)',
                transform: 'skewX(-20deg)',
                pointerEvents: 'none',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#042F2E',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              CHAME A GENTE NO DIRECT
            </span>
          </div>
        )}

        {/* 3. @arroba com entrada sequencial (frame 32) e microanimação (y <= 1420) */}
        {frame >= 30 && (
          <div
            style={{
              backgroundColor: '#0F172A',
              border: `2.5px solid ${COR.marcaBrilho}`,
              borderRadius: 999,
              padding: '16px 40px',
              transform: `translateY(${interpolate(spArroba, [0, 1], [35, 0]) - floatCardY * 0.5}px) scale(${interpolate(spArroba, [0, 1], [0.88, 1])})`,
              boxShadow: '0 14px 32px rgba(0,0,0,0.6)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              @agentesdeia.ia
            </span>
          </div>
        )}
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

  const volTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 25, durationInFrames],
    [0, 0.1, 0.1, 0.02],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: COR.apoio, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {/* CENA 0: 0.00s a 5.67s (0 a 170) */}
      <Sequence from={0} durationInFrames={170}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 5.32s a 12.75s (160 a 382 -> 223 frames) */}
      <Sequence from={160} durationInFrames={223}>
        <Cena1Situacao />
      </Sequence>

      {/* CENA 2: 12.40s a 18.05s (372 a 542 -> 170 frames) */}
      <Sequence from={372} durationInFrames={170}>
        <Cena2Conversa />
      </Sequence>

      {/* CENA 3: 17.70s a 25.20s (531 a 756 -> 225 frames) */}
      <Sequence from={531} durationInFrames={225}>
        <Cena3Resultado />
      </Sequence>

      {/* CENA 4: 24.85s a 28.79s (745 a 864 -> 119 frames) */}
      <Sequence from={745} durationInFrames={119}>
        <Cena4Cartao />
      </Sequence>

      {/* Barra de Progresso na Zona Segura (y=152, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255,255,255,0.2)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: COR.marca,
          }}
        />
      </div>

      {/* Legenda Karaokê (oculta no cartão final t >= 24.85s) */}
      {t < 24.8 && (
        <Karaoke
          palavras={PALAVRAS}
          fontFamily={fontFamily}
          destaque={COR.marca}
          textoDestaque="#062E22"
          tamanho={44}
          base={350}
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
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(28.79 * 30)}
    />
  );
};
