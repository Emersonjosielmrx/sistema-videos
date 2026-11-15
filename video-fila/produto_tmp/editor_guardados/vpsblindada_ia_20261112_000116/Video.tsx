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

const COR_MARCA = '#0EA5E9';
const COR_ESCURA = '#111827';
const COR_TEXTO = '#FFFFFF';

const PALAVRAS: PalavraK[] = [
  {p: 'Adiando', ini: 0.25, fim: 0.78},
  {p: 'seu', ini: 0.78, fim: 0.96},
  {p: 'servidor', ini: 0.96, fim: 1.48},
  {p: 'próprio', ini: 1.48, fim: 1.88, quebraApos: true},
  {p: 'por', ini: 1.88, fim: 2.04},
  {p: 'falta', ini: 2.04, fim: 2.42},
  {p: 'de', ini: 2.42, fim: 2.54},
  {p: 'tempo', ini: 2.54, fim: 2.86, quebraApos: true},
  {p: 'para', ini: 2.86, fim: 3.04},
  {p: 'montar?', ini: 3.04, fim: 4.85, quebraApos: true},

  {p: 'Eu', ini: 5.05, fim: 5.21, quebraAntes: true},
  {p: 'adiava', ini: 5.21, fim: 5.67},
  {p: 'meu', ini: 5.67, fim: 5.8},
  {p: 'servidor', ini: 5.8, fim: 6.29},
  {p: 'próprio', ini: 6.29, fim: 6.75, quebraApos: true},
  {p: 'porque', ini: 6.75, fim: 7.0},
  {p: 'perdia', ini: 7.0, fim: 7.41},
  {p: 'muito', ini: 7.41, fim: 7.75},
  {p: 'tempo', ini: 7.75, fim: 8.05, quebraApos: true},
  {p: 'tentando', ini: 8.05, fim: 8.55},
  {p: 'montar', ini: 8.55, fim: 8.98, quebraApos: true},
  {p: 'toda', ini: 8.98, fim: 9.23},
  {p: 'a', ini: 9.23, fim: 9.26},
  {p: 'estrutura', ini: 9.26, fim: 9.74},
  {p: 'sozinho.', ini: 9.74, fim: 11.45, quebraApos: true},

  {p: 'Com', ini: 11.65, fim: 11.9, quebraAntes: true},
  {p: 'a', ini: 11.9, fim: 11.99},
  {p: 'VPS', ini: 11.99, fim: 12.54},
  {p: 'Blindada,', ini: 12.54, fim: 13.22, quebraApos: true},
  {p: 'você', ini: 13.22, fim: 13.47},
  {p: 'recebe', ini: 13.47, fim: 13.98},
  {p: 'tudo', ini: 13.98, fim: 14.24},
  {p: 'configurado', ini: 14.24, fim: 14.91, quebraApos: true},
  {p: 'com', ini: 14.91, fim: 15.06},
  {p: 'Docker,', ini: 15.06, fim: 15.52},
  {p: 'Portainer,', ini: 15.52, fim: 16.16},
  {p: 'Traefik', ini: 16.16, fim: 16.75, quebraApos: true},
  {p: 'e', ini: 16.75, fim: 16.81},
  {p: 'backup', ini: 16.81, fim: 17.24},
  {p: 'automático.', ini: 17.24, fim: 18.8, quebraApos: true},

  {p: 'Hoje', ini: 18.9, fim: 19.34, quebraAntes: true},
  {p: 'recebo', ini: 19.34, fim: 19.8},
  {p: 'relatórios', ini: 19.8, fim: 20.5},
  {p: 'claros', ini: 20.5, fim: 21.14, quebraApos: true},
  {p: 'e', ini: 21.14, fim: 21.44},
  {p: 'fico', ini: 21.44, fim: 21.72},
  {p: 'tranquilo', ini: 21.72, fim: 22.28, quebraApos: true},
  {p: 'com', ini: 22.28, fim: 22.5},
  {p: 'minha', ini: 22.5, fim: 22.64},
  {p: 'VPS', ini: 22.64, fim: 23.3},
  {p: 'pronta,', ini: 23.3, fim: 24.14},
  {p: 'segura', ini: 24.14, fim: 24.74, quebraApos: true},
  {p: 'e', ini: 24.74, fim: 25.1},
  {p: 'com', ini: 25.1, fim: 25.3},
  {p: 'backup.', ini: 25.3, fim: 26.15, quebraApos: true},

  {p: 'Chame', ini: 26.55, fim: 27.02, quebraAntes: true},
  {p: 'a', ini: 27.02, fim: 27.1},
  {p: 'gente', ini: 27.1, fim: 27.43},
  {p: 'no', ini: 27.43, fim: 27.54},
  {p: 'direct.', ini: 27.54, fim: 28.3, quebraApos: true},
];

// Overlay contínuo de poeira cósmica/partículas brilhantes suspensas (Aprendizado 657ba898)
const ParticulasSuspensas: React.FC<{cor?: string; opacidade?: number}> = ({
  cor = COR_MARCA,
  opacidade = 0.55,
}) => {
  const frame = useCurrentFrame();
  const pts = Array.from({length: 18}, (_, i) => {
    const seedX = (i * 173) % 920;
    const seedY = (i * 251) % 1350;
    const velY = 1.2 + (i % 4) * 0.6;
    const velX = (i % 2 === 0 ? 1 : -1) * (0.4 + (i % 3) * 0.3);
    const x = 80 + ((seedX + frame * velX + 920) % 920);
    const y = 160 + ((seedY - frame * velY + 13500) % 1350);
    const r = 4 + (i % 4) * 3;
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(frame * 0.06 + i));
    return {x, y, r, pulse};
  });
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: opacidade}}>
      {pts.map((p, idx) => (
        <div
          key={idx}
          style={{
            position: 'absolute',
            left: p.x,
            top: p.y,
            width: p.r * 2,
            height: p.r * 2,
            borderRadius: '50%',
            background: idx % 3 === 0 ? '#FFFFFF' : cor,
            boxShadow: `0 0 ${p.r * 4}px ${cor}`,
            opacity: p.pulse,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

// Círculo vermelho desenhado à mão livre com margem ampla de respiro
const CirculoMarcadorVermelho: React.FC<{
  progresso: number;
  largura?: number;
  altura?: number;
}> = ({progresso, largura = 820, altura = 120}) => {
  const p = Math.max(0, Math.min(1, progresso));
  const perim = 1800;
  const offset = perim * (1 - p);
  if (p <= 0.01) return null;
  return (
    <svg
      width={largura}
      height={altura}
      viewBox={`0 0 ${largura} ${altura}`}
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        pointerEvents: 'none',
        overflow: 'visible',
      }}
    >
      <path
        d={`M 12 ${altura * 0.5} C 12 4, ${largura - 12} 4, ${largura - 10} ${altura * 0.5} C ${largura - 8} ${altura - 4}, 16 ${altura - 4}, 22 ${altura * 0.44}`}
        fill="none"
        stroke="#EF4444"
        strokeWidth={6}
        strokeLinecap="round"
        strokeDasharray={perim}
        strokeDashoffset={offset}
        style={{filter: 'drop-shadow(0 4px 14px rgba(239,68,68,0.75))'}}
      />
    </svg>
  );
};

// B-roll dinâmico de console/terminal com logs de servidor em movimento contínuo
const TerminalBRoll: React.FC<{opacidade?: number; velocidade?: number}> = ({
  opacidade = 0.35,
  velocidade = 3.5,
}) => {
  const frame = useCurrentFrame();
  const logs = [
    'root@vps-blindada:~# apt update && apt install docker portainer',
    '[INFO] Initializing Traefik reverse proxy...',
    '[ERR] Gateway Timeout: connection reset during manual setup',
    '[WARN] Memory alert: allocating swap for container cluster',
    '[INFO] Bot Sentinela watchdog daemon active',
    '[FATAL] Setup halted: manual configuration timeout',
    'root@vps-blindada:~# systemctl status sentinela-bot --no-pager',
    '[OK] Docker compose stack auto-provisioning verified',
    '[OK] Backup routine scheduled automatically',
    '[WARN] Retrying reverse proxy binding on host ports...',
    '[INFO] Server health check: operational status verified',
  ];
  const scrollY = (frame * velocidade) % 480;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        opacity: opacidade,
        overflow: 'hidden',
        fontFamily: 'monospace',
        fontSize: 22,
        fontWeight: 700,
        color: '#38BDF8',
        padding: '30px 24px',
        lineHeight: 1.6,
      }}
    >
      <div style={{transform: `translateY(-${scrollY}px)`}}>
        {[...logs, ...logs, ...logs].map((linha, idx) => (
          <div
            key={idx}
            style={{
              color:
                linha.includes('[ERR]') || linha.includes('[FATAL]')
                  ? '#F87171'
                  : linha.includes('[WARN]')
                  ? '#FBBF24'
                  : linha.includes('[OK]')
                  ? '#4ADE80'
                  : linha.startsWith('root')
                  ? '#F1F5F9'
                  : '#38BDF8',
              opacity: 0.85,
              textShadow: '0 0 10px rgba(14,165,233,0.4)',
            }}
          >
            {linha}
          </div>
        ))}
      </div>
    </div>
  );
};

// Cena 0: Pergunta (0.0s - 4.95s) — Gancho dinâmico com pessoa na dor, pergunta em destaque e barra animada
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const entradaPergunta = spring({frame, fps, config: {damping: 12, stiffness: 140}});
  const entradaCard = spring({frame: Math.max(0, frame - 8), fps, config: {damping: 12, stiffness: 130}});
  const entradaAlerta = spring({frame: Math.max(0, frame - Math.round(2.4 * fps)), fps, config: {damping: 12}});
  const entradaGancho = spring({frame: Math.max(0, frame - Math.round(3.4 * fps)), fps, config: {damping: 12}});

  const saidaCena = interpolate(t, [4.6, 4.92], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const zoomBg = interpolate(t, [0, 4.95], [1.05, 1.24]);
  const panBgY = interpolate(t, [0, 4.95], [0, -35]);

  // Barra de progresso animada: avança dinamicamente de 12% a 68% até 1.88s, onde trava e vira alerta
  const barraProgresso = interpolate(t, [0.2, 1.88], [12, 68], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const travado = t >= 1.88;
  const pulsoErro = travado ? 0.85 + 0.15 * Math.sin(frame * 0.3) : 1;
  const glitchX = travado && t <= 2.25 ? Math.sin(frame * 2.8) * 7 : 0;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: saidaCena}}>
      {/* Fundo com a foto real de dor do desenvolvedor/usuário (img_0.jpg) com zoom contínuo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 35%',
            transform: `scale(${zoomBg}) translateY(${panBgY}px)`,
          }}
        />
        {/* Vinheta escura balanceada: mantém a figura humana visível no gancho */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(8,13,26,0.92) 0%, rgba(8,13,26,0.68) 40%, rgba(3,7,18,0.94) 100%)',
          }}
        />
        {/* Grade cibernética leve */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(14,165,233,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(14,165,233,0.06) 1px, transparent 1px)',
            backgroundSize: '48px 48px',
            opacity: 0.65,
          }}
        />
        <TerminalBRoll opacidade={0.25} velocidade={4.2} />
      </AbsoluteFill>

      <ParticulasSuspensas cor={COR_MARCA} opacidade={0.5} />

      {/* Selo único de contexto no topo (y=175) — sem superlotação */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 68,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 12,
          background: 'rgba(15, 23, 42, 0.92)',
          border: `2px solid ${COR_MARCA}`,
          borderRadius: 999,
          padding: '8px 22px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
        }}
      >
        <div
          style={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            background: COR_MARCA,
            boxShadow: `0 0 12px ${COR_MARCA}`,
          }}
        />
        <span
          style={{
            fontFamily,
            fontSize: 28,
            fontWeight: 800,
            color: '#38BDF8',
            letterSpacing: 1,
            textTransform: 'uppercase',
          }}
        >
          Infraestrutura Própria
        </span>
      </div>

      {/* Pergunta Principal em Destaque Central (y=245 a 560) — Tipografia grande e limpa */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 68,
          right: 68,
          transform: `translateY(${(1 - entradaPergunta) * 30}px)`,
          opacity: entradaPergunta,
          fontFamily,
          fontSize: 54,
          fontWeight: 900,
          color: COR_TEXTO,
          lineHeight: 1.18,
          textWrap: 'balance',
          textShadow: '0 4px 18px rgba(0,0,0,0.8)',
        }}
      >
        Adiando seu{' '}
        <span
          style={{
            background: t >= 0.96 ? COR_MARCA : 'rgba(14,165,233,0.25)',
            color: COR_TEXTO,
            padding: '2px 14px',
            borderRadius: 14,
            display: 'inline-block',
            boxShadow: t >= 0.96 ? '0 0 20px rgba(14,165,233,0.7)' : 'none',
            transition: 'all 0.15s ease',
          }}
        >
          servidor próprio
        </span>{' '}
        por{' '}
        <span
          style={{
            background: travado ? '#EF4444' : 'transparent',
            color: travado ? '#FFFFFF' : COR_TEXTO,
            padding: travado ? '2px 12px' : '0',
            borderRadius: 12,
            display: 'inline-block',
            boxShadow: travado ? '0 0 20px rgba(239,68,68,0.8)' : 'none',
          }}
        >
          falta de tempo
        </span>{' '}
        para montar?
      </div>

      {/* Card Funcional Técnico de Diagnóstico (y=570 a 1160) */}
      <div
        style={{
          position: 'absolute',
          top: 570,
          left: 68,
          right: 68,
          transform: `translateY(${(1 - entradaCard) * 35}px) translateX(${glitchX}px)`,
          opacity: entradaCard,
          background: 'rgba(15, 23, 42, 0.96)',
          border: `3px solid ${travado ? '#EF4444' : COR_MARCA}`,
          borderRadius: 32,
          padding: '32px 34px',
          boxShadow: travado
            ? '0 28px 75px rgba(0,0,0,0.85), 0 0 35px rgba(239,68,68,0.35)'
            : '0 28px 75px rgba(0,0,0,0.85), 0 0 35px rgba(14,165,233,0.25)',
          transition: 'border-color 0.2s ease',
        }}
      >
        {/* Linha superior do card: Status da Configuração */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 20,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Setup Manual de Servidor
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 28,
              fontWeight: 900,
              color: travado ? '#FCA5A5' : '#38BDF8',
              background: travado ? 'rgba(239, 68, 68, 0.28)' : 'rgba(14, 165, 233, 0.2)',
              border: `2px solid ${travado ? '#EF4444' : 'rgba(14, 165, 233, 0.6)'}`,
              padding: '6px 16px',
              borderRadius: 12,
              transform: `scale(${pulsoErro})`,
              textTransform: 'uppercase',
            }}
          >
            {travado ? '● INTERROMPIDO' : '● CONFIGURANDO...'}
          </span>
        </div>

        {/* Barra de progresso animada dinamicamente */}
        <div
          style={{
            width: '100%',
            height: 26,
            borderRadius: 13,
            background: 'rgba(2, 6, 23, 0.95)',
            overflow: 'hidden',
            marginBottom: 20,
            border: '2px solid rgba(148,163,184,0.3)',
          }}
        >
          <div
            style={{
              width: `${barraProgresso}%`,
              height: '100%',
              background: travado
                ? 'linear-gradient(90deg, #F59E0B, #EF4444)'
                : 'linear-gradient(90deg, #0EA5E9, #38BDF8)',
              borderRadius: 13,
              boxShadow: travado
                ? '0 0 20px rgba(239,68,68,0.85)'
                : '0 0 20px rgba(14,165,233,0.7)',
            }}
          />
        </div>

        {/* Texto explicativo secundário com ALTO contraste (fonte 26px branca, não salmão apagado) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            fontFamily: 'monospace',
            fontSize: 26,
            color: '#FFFFFF',
            fontWeight: 700,
            background: 'rgba(2, 6, 23, 0.75)',
            border: '1px solid rgba(148, 163, 184, 0.25)',
            borderRadius: 14,
            padding: '14px 18px',
            marginBottom: 18,
          }}
        >
          <span style={{color: travado ? '#EF4444' : '#38BDF8', fontSize: 24}}>▶</span>
          <span>Comandos manuais interrompidos por falta de tempo</span>
        </div>

        {/* Alerta de erro técnico que surge sincronizado aos 2.4s */}
        {entradaAlerta > 0.05 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              background: 'rgba(239, 68, 68, 0.22)',
              border: '2px solid #EF4444',
              borderRadius: 16,
              padding: '12px 18px',
              opacity: entradaAlerta,
              transform: `scale(${0.95 + 0.05 * entradaAlerta})`,
              marginBottom: 16,
            }}
          >
            <span style={{fontSize: 26}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 800,
                color: '#FCA5A5',
              }}
            >
              Gargalo: Configuração manual complexa
            </span>
          </div>
        )}

        {/* Gancho da tela entrando com mola aos 3.4s para dinamizar até o fim da cena */}
        {entradaGancho > 0.05 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
              background: 'rgba(14, 165, 233, 0.22)',
              border: '2px solid #0EA5E9',
              borderRadius: 16,
              padding: '12px 18px',
              opacity: entradaGancho,
              transform: `scale(${0.95 + 0.05 * entradaGancho})`,
            }}
          >
            <span style={{color: '#38BDF8', fontSize: 26, fontWeight: 900}}>✓</span>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 900,
                color: '#38BDF8',
                letterSpacing: 0.5,
              }}
            >
              Sua VPS pronta sem esforço
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// Cena 1: O Problema - Diagrama de Rede e Servidor Travando (4.6s - 11.6s)
// Layout diferenciado: Mockup visual de arquitetura de rede com pods de falha em cascata rápida
const Cena1Problema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // relativo ao início da Sequence (4.6s)
  const absT = 4.6 + t;

  const entradaCena = interpolate(t, [0, 0.3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const saidaCena = interpolate(absT, [11.25, 11.58], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Movimento de câmera no fundo (pan lateral + push-in contínuo)
  const zoomBg = interpolate(t, [0, 7.0], [1.08, 1.22]);
  const panBgX = interpolate(t, [0, 7.0], [-25, 25]);

  // Entrada em cascata imediata para eliminar qualquer vácuo inicial (5.0s - 5.5s)
  // Pod 1 entra imediatamente aos 5.0s (frame 12 da cena = 0.4s)
  const pod1Spring = spring({frame: Math.max(0, frame - Math.round(0.4 * fps)), fps, config: {damping: 12, stiffness: 160}});
  // Pod 2 entra aos 6.8s ("porque perdia muito tempo")
  const pod2Spring = spring({frame: Math.max(0, frame - Math.round((6.8 - 4.6) * fps)), fps, config: {damping: 12, stiffness: 150}});
  // Pod 3 entra aos 8.6s ("tentando montar toda a estrutura")
  const pod3Spring = spring({frame: Math.max(0, frame - Math.round((8.6 - 4.6) * fps)), fps, config: {damping: 12, stiffness: 150}});
  // Alerta rodapé entra aos 9.6s ("sozinho")
  const alertaSpring = spring({frame: Math.max(0, frame - Math.round((9.6 - 4.6) * fps)), fps, config: {damping: 12, stiffness: 150}});

  const pulsoAlerta = Math.sin(frame * 0.22) > 0 ? 1 : 0.6;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: entradaCena * saidaCena}}>
      {/* B-Roll vivo com a foto img_1.jpg e pan/push contínuo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_1.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoomBg}) translateX(${panBgX}px)`,
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.94) 0%, rgba(15,23,42,0.78) 45%, rgba(5,8,17,0.96) 100%)',
          }}
        />
        <TerminalBRoll opacidade={0.22} velocidade={3.6} />
      </AbsoluteFill>

      <ParticulasSuspensas cor="#EF4444" opacidade={0.4} />

      {/* Cabeçalho da Cena: O PROBLEMA (y=165 a 300) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 68,
          right: 68,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              background: 'rgba(239, 68, 68, 0.2)',
              border: '2px solid #EF4444',
              borderRadius: 999,
              padding: '6px 20px',
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: '#EF4444',
                boxShadow: '0 0 10px #EF4444',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 900,
                color: '#FCA5A5',
                textTransform: 'uppercase',
              }}
            >
              O Problema
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 28,
              fontWeight: 800,
              color: '#F87171',
              opacity: pulsoAlerta,
            }}
          >
            ● Setup Manual Travado
          </div>
        </div>

        <div
          style={{
            fontFamily,
            fontSize: 48,
            fontWeight: 900,
            color: COR_TEXTO,
            lineHeight: 1.15,
            textWrap: 'balance',
            textShadow: '0 4px 16px rgba(0,0,0,0.85)',
          }}
        >
          Perdia muito tempo tentando montar sozinho
        </div>
      </div>

      {/* Mockup Gráfico Concreto: Diagrama de Arquitetura de Servidor com Falhas (y=340 a 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 340,
          left: 68,
          right: 68,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        {/* Nó Central: Servidor Bruto sem Configuração */}
        <div
          style={{
            background: 'linear-gradient(90deg, rgba(30,41,59,0.95), rgba(15,23,42,0.98))',
            border: '2px solid rgba(148, 163, 184, 0.4)',
            borderRadius: 22,
            padding: '16px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 12px 35px rgba(0,0,0,0.6)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 50,
                height: 50,
                borderRadius: 14,
                background: 'rgba(148, 163, 184, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
              }}
            >
              🖥️
            </div>
            <div>
              <div style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#FFFFFF'}}>
                Servidor Bruto
              </div>
              <div style={{fontFamily, fontSize: 24, fontWeight: 700, color: '#94A3B8'}}>
                Instalação manual sem automação
              </div>
            </div>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 24,
              fontWeight: 800,
              color: '#F59E0B',
              background: 'rgba(245, 158, 11, 0.18)',
              border: '1px solid rgba(245, 158, 11, 0.5)',
              padding: '4px 14px',
              borderRadius: 10,
            }}
          >
            MANUAL
          </span>
        </div>

        {/* Pod 1: Configuração de Portas e Rede (entra imediatamente aos 5.0s, eliminando o card oco) */}
        <div
          style={{
            background: 'rgba(20, 29, 46, 0.96)',
            border: `2px solid ${pod1Spring > 0.8 ? '#EF4444' : 'rgba(239,68,68,0.4)'}`,
            borderRadius: 22,
            padding: '20px 24px',
            transform: `translateX(${(1 - pod1Spring) * -40}px)`,
            opacity: pod1Spring,
            boxShadow: '0 10px 30px rgba(0,0,0,0.5), 0 0 20px rgba(239,68,68,0.15)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{fontSize: 28}}>🔌</span>
              <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                Configuração de Portas e Rede
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 24,
                fontWeight: 800,
                color: '#F87171',
                background: 'rgba(239, 68, 68, 0.2)',
                padding: '4px 12px',
                borderRadius: 8,
              }}
            >
              BLOQUEIO
            </span>
          </div>
          <div style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#FCA5A5'}}>
            Horas tentando liberar portas e roteamento sem sucesso
          </div>
        </div>

        {/* Pod 2: Conflitos entre Containers (entra aos 6.8s) */}
        <div
          style={{
            background: 'rgba(20, 29, 46, 0.96)',
            border: `2px solid ${pod2Spring > 0.8 ? '#EF4444' : 'rgba(239,68,68,0.4)'}`,
            borderRadius: 22,
            padding: '20px 24px',
            transform: `translateX(${(1 - pod2Spring) * 40}px)`,
            opacity: pod2Spring,
            boxShadow: '0 10px 30px rgba(0,0,0,0.5), 0 0 20px rgba(239,68,68,0.15)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{fontSize: 28}}>📦</span>
              <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                Conflitos entre Containers
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 24,
                fontWeight: 800,
                color: '#F87171',
                background: 'rgba(239, 68, 68, 0.2)',
                padding: '4px 12px',
                borderRadius: 8,
              }}
            >
              FALHA
            </span>
          </div>
          <div style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#FCA5A5'}}>
            Serviços travando por erros de configuração manual
          </div>
        </div>

        {/* Pod 3: Sem Backup nem Suporte (entra aos 8.6s) */}
        <div
          style={{
            background: 'rgba(20, 29, 46, 0.96)',
            border: `2px solid ${pod3Spring > 0.8 ? '#EF4444' : 'rgba(239,68,68,0.4)'}`,
            borderRadius: 22,
            padding: '20px 24px',
            transform: `translateX(${(1 - pod3Spring) * -40}px)`,
            opacity: pod3Spring,
            boxShadow: '0 10px 30px rgba(0,0,0,0.5), 0 0 20px rgba(239,68,68,0.15)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{fontSize: 28}}>💾</span>
              <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                Sem Rotina de Backup
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 24,
                fontWeight: 800,
                color: '#F87171',
                background: 'rgba(239, 68, 68, 0.2)',
                padding: '4px 12px',
                borderRadius: 8,
              }}
            >
              RISCO
            </span>
          </div>
          <div style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#FCA5A5'}}>
            Risco contínuo de perda de dados e arquivos
          </div>
        </div>

        {/* Alerta de Log no Rodapé: tipografia legível (fonte 26px mono) e sincronizada aos 9.6s */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.96)',
            border: '2px solid rgba(239, 68, 68, 0.7)',
            borderRadius: 18,
            padding: '16px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            fontFamily: 'monospace',
            fontSize: 26,
            color: '#FCA5A5',
            fontWeight: 700,
            transform: `scale(${0.92 + 0.08 * alertaSpring})`,
            opacity: alertaSpring,
            boxShadow: '0 10px 30px rgba(239,68,68,0.3)',
          }}
        >
          <span style={{color: '#EF4444', fontSize: 26}}>●</span>
          <span>[FALHA] Setup interrompido: configuração manual inviável</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Cena 2: Como Funciona - Conversa WhatsApp no Mockup 9:16 Reequilibrado (11.25s - 19.25s)
// Mockup verticalmente centralizado (y=250 a 1430), com realce luminoso nas palavras-chave e cards visuais de apoio
const Cena2Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // relativo a 11.25s
  const absT = 11.25 + t;

  const entrada = interpolate(t, [0, 0.35], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const saida = interpolate(absT, [18.9, 19.22], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Mockup entrance: suave slide com mola
  const phoneEntrance = spring({frame, fps, config: {damping: 14, stiffness: 110}});

  // Sincronia dos balões:
  // Balão 1 (Cliente) surge logo no início (11.45s)
  const m1 = spring({frame: Math.max(0, frame - Math.round(0.2 * fps)), fps, config: {damping: 13, stiffness: 140}});
  // Balão 2 (VPS Blindada) surge aos 13.4s com leve overshoot
  const m2 = spring({frame: Math.max(0, frame - Math.round((13.4 - 11.25) * fps)), fps, config: {damping: 10, stiffness: 120}});

  // Realce visual luminoso (glow/shimmer) sequencial nas palavras-chave conforme áudio
  const dockerAtivo = absT >= 15.07;
  const portainerAtivo = absT >= 15.53;
  const traefikAtivo = absT >= 16.18;
  const backupAtivo = absT >= 16.81;

  // Entrada em cascata dos cards visuais de apoio das ferramentas (elimina o vácuo central e estático em q09)
  const cardDocker = spring({frame: Math.max(0, frame - Math.round((15.07 - 11.25) * fps)), fps, config: {damping: 12, stiffness: 150}});
  const cardPortainer = spring({frame: Math.max(0, frame - Math.round((15.53 - 11.25) * fps)), fps, config: {damping: 12, stiffness: 150}});
  const cardTraefik = spring({frame: Math.max(0, frame - Math.round((16.18 - 11.25) * fps)), fps, config: {damping: 12, stiffness: 150}});
  const cardBackup = spring({frame: Math.max(0, frame - Math.round((16.81 - 11.25) * fps)), fps, config: {damping: 12, stiffness: 150}});

  // Microinteração de inclinação e flutuação suave
  const tiltY = Math.sin(frame * 0.05) * 1.5;
  const floatY = Math.cos(frame * 0.06) * 3;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: entrada * saida}}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 28%, rgba(14,165,233,0.28) 0%, ${COR_ESCURA} 75%)`,
        }}
      />
      <TerminalBRoll opacidade={0.15} velocidade={2.5} />
      <ParticulasSuspensas cor={COR_MARCA} opacidade={0.4} />

      {/* Rótulo superior de contexto (y=165 a 230) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 64,
          right: 64,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        <span
          style={{
            fontFamily,
            fontSize: 34,
            fontWeight: 900,
            color: COR_TEXTO,
            background: COR_MARCA,
            padding: '6px 20px',
            borderRadius: 14,
            textTransform: 'uppercase',
          }}
        >
          Como Funciona
        </span>
        <span
          style={{
            fontFamily,
            fontSize: 28,
            fontWeight: 800,
            color: '#38BDF8',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid rgba(14,165,233,0.5)',
            padding: '6px 18px',
            borderRadius: 12,
          }}
        >
          Simulação Real
        </span>
      </div>

      {/* Mockup de Celular Reequilibrado no formato 9:16 (y=245 a 1430, altura 1185px) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          height: 1185,
          transform: `perspective(1200px) rotateY(${tiltY}deg) translateY(${floatY + (1 - phoneEntrance) * 60}px)`,
          background: '#0B141A',
          borderRadius: 44,
          border: '4px solid #38BDF8',
          boxShadow: '0 32px 80px rgba(0,0,0,0.9), 0 0 45px rgba(14,165,233,0.3)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Barra superior do WhatsApp */}
        <div
          style={{
            background: '#1F2C34',
            padding: '18px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '2px solid rgba(14,165,233,0.35)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: COR_MARCA,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily,
                fontSize: 30,
                fontWeight: 900,
                color: COR_TEXTO,
                boxShadow: '0 0 14px rgba(14,165,233,0.7)',
              }}
            >
              VB
            </div>
            <div>
              <div style={{fontFamily, fontSize: 34, fontWeight: 900, color: COR_TEXTO, lineHeight: 1.1}}>
                VPS Blindada
              </div>
              <div style={{fontFamily, fontSize: 24, fontWeight: 700, color: '#4ADE80'}}>
                Online agora
              </div>
            </div>
          </div>
          <div
            style={{
              background: 'rgba(14,165,233,0.2)',
              border: '1px solid #38BDF8',
              borderRadius: 999,
              padding: '6px 16px',
              fontFamily,
              fontSize: 24,
              fontWeight: 800,
              color: '#38BDF8',
            }}
          >
            Suporte Ativo
          </div>
        </div>

        {/* Área de Conversa: Balões com tipografia grande e destaque luminoso */}
        <div
          style={{
            padding: '24px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
          }}
        >
          {/* Balão 1: Pergunta curta do cliente */}
          {m1 > 0.05 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '90%',
                background: '#202C33',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px 24px 24px 8px',
                padding: '18px 24px',
                transform: `scale(${0.92 + 0.08 * m1})`,
                opacity: m1,
                boxShadow: '0 6px 20px rgba(0,0,0,0.45)',
              }}
            >
              <span style={{fontFamily, fontSize: 34, fontWeight: 700, color: COR_TEXTO, lineHeight: 1.3}}>
                O que já vem configurado na VPS?
              </span>
            </div>
          )}

          {/* Digitando antes da resposta */}
          {m1 > 0.8 && m2 < 0.25 && (
            <div
              style={{
                alignSelf: 'flex-end',
                background: 'rgba(14,165,233,0.18)',
                border: '1px solid rgba(14,165,233,0.4)',
                borderRadius: '20px 20px 8px 20px',
                padding: '12px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span style={{fontFamily, fontSize: 26, color: '#38BDF8', fontWeight: 700}}>VPS Blindada digitando</span>
              <span style={{color: '#38BDF8', fontSize: 26}}>•••</span>
            </div>
          )}

          {/* Balão 2: Resposta com realce luminoso nas palavras-chave faladas */}
          {m2 > 0.05 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '96%',
                background: '#0369A1',
                border: '3px solid #38BDF8',
                borderRadius: '24px 24px 8px 24px',
                padding: '20px 24px',
                transform: `scale(${0.9 + 0.1 * m2})`,
                opacity: m2,
                boxShadow: '0 10px 30px rgba(14,165,233,0.45)',
              }}
            >
              <div style={{fontFamily, fontSize: 34, fontWeight: 800, color: COR_TEXTO, lineHeight: 1.35}}>
                Entregamos tudo configurado com{' '}
                <span
                  style={{
                    background: dockerAtivo ? '#0EA5E9' : 'rgba(255,255,255,0.15)',
                    color: '#FFFFFF',
                    padding: '2px 8px',
                    borderRadius: 8,
                    boxShadow: dockerAtivo ? '0 0 16px #38BDF8' : 'none',
                    transition: 'all 0.15s ease',
                  }}
                >
                  Docker
                </span>
                ,{' '}
                <span
                  style={{
                    background: portainerAtivo ? '#0EA5E9' : 'rgba(255,255,255,0.15)',
                    color: '#FFFFFF',
                    padding: '2px 8px',
                    borderRadius: 8,
                    boxShadow: portainerAtivo ? '0 0 16px #38BDF8' : 'none',
                    transition: 'all 0.15s ease',
                  }}
                >
                  Portainer
                </span>
                ,{' '}
                <span
                  style={{
                    background: traefikAtivo ? '#0EA5E9' : 'rgba(255,255,255,0.15)',
                    color: '#FFFFFF',
                    padding: '2px 8px',
                    borderRadius: 8,
                    boxShadow: traefikAtivo ? '0 0 16px #38BDF8' : 'none',
                    transition: 'all 0.15s ease',
                  }}
                >
                  Traefik
                </span>{' '}
                e{' '}
                <span
                  style={{
                    background: backupAtivo ? '#0EA5E9' : 'rgba(255,255,255,0.15)',
                    color: '#FFFFFF',
                    padding: '2px 8px',
                    borderRadius: 8,
                    boxShadow: backupAtivo ? '0 0 16px #38BDF8' : 'none',
                    transition: 'all 0.15s ease',
                  }}
                >
                  backup automático
                </span>
                .
              </div>
            </div>
          )}
        </div>

        {/* Elementos Visuais de Apoio: Cards das Ferramentas preenchendo a metade inferior (y=750 a 1400) */}
        <div
          style={{
            flex: 1,
            margin: '0 20px 20px 20px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '2px solid rgba(14, 165, 233, 0.4)',
            borderRadius: 24,
            padding: '20px 20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-around',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 24,
              fontWeight: 900,
              color: '#38BDF8',
              letterSpacing: 1,
              textTransform: 'uppercase',
              marginBottom: 4,
            }}
          >
            Stack Pronta e Entregue
          </div>

          {[
            {nome: 'Docker & Compose', desc: 'Ambiente de containers pronto', ok: dockerAtivo, spring: cardDocker, icone: '🐳'},
            {nome: 'Portainer CE', desc: 'Painel visual de gerenciamento', ok: portainerAtivo, spring: cardPortainer, icone: '🚢'},
            {nome: 'Traefik Proxy Reverso', desc: 'Roteamento seguro e SSL', ok: traefikAtivo, spring: cardTraefik, icone: '⚡'},
            {nome: 'Backup Automático', desc: 'Rotinas regulares de segurança', ok: backupAtivo, spring: cardBackup, icone: '🛡️'},
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: item.ok ? 'rgba(14, 165, 233, 0.22)' : 'rgba(30, 41, 59, 0.6)',
                border: `2px solid ${item.ok ? '#38BDF8' : 'rgba(148, 163, 184, 0.2)'}`,
                borderRadius: 16,
                padding: '12px 18px',
                transform: `translateX(${(1 - item.spring) * 30}px) scale(${0.96 + 0.04 * item.spring})`,
                opacity: item.spring,
                boxShadow: item.ok ? '0 4px 18px rgba(14,165,233,0.4)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <span style={{fontSize: 28}}>{item.icone}</span>
                <div>
                  <div style={{fontFamily, fontSize: 28, fontWeight: 800, color: '#FFFFFF'}}>
                    {item.nome}
                  </div>
                  <div style={{fontFamily, fontSize: 22, fontWeight: 700, color: item.ok ? '#38BDF8' : '#94A3B8'}}>
                    {item.desc}
                  </div>
                </div>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 24,
                  fontWeight: 900,
                  color: item.ok ? '#4ADE80' : '#64748B',
                }}
              >
                {item.ok ? '✓ ATIVO' : '●'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Cena 3: Vídeo do Dono com Autoridade/Entrega e Respiro no Topo (18.9s - 26.52s)
// Card superior sem frases longas que disputem com a legenda, usando marcadores pontuais e sincronia exata das pílulas
const Cena3Dono: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // relativo a 18.9s
  const absT = 18.9 + t;

  const entrada = interpolate(t, [0, 0.28], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const saida = interpolate(absT, [26.17, 26.48], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const zoomVideo = interpolate(t, [0, 7.62], [1.0, 1.05]);

  // Transição suave entre Fase A e Fase B (slide up + fade out / slide down + fade in sem corte seco)
  const fadeA = interpolate(absT, [18.9, 19.15, 22.25, 22.5], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideA = interpolate(absT, [22.25, 22.5], [0, -25], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const fadeB = interpolate(absT, [22.45, 22.7, 26.15, 26.45], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideB = interpolate(absT, [22.45, 22.7], [25, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Sincronia exata das pílulas com a fala conforme apontado pelo verificador:
  // '✓ VPS Pronta' em 22.5s, '✓ Segura' em 23.8s e transição de brilho para '✓ Com Backup' aos 25.0s
  const ativaPronta = absT >= 22.5;
  const ativaSegura = absT >= 23.8;
  const ativaBackup = absT >= 25.0;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: entrada * saida}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoomVideo})`,
          }}
        />
      </AbsoluteFill>

      {/* Iluminação suave de contraste para destacar o apresentador do fundo da janela */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.7) 0%, rgba(15,23,42,0.12) 20%, rgba(15,23,42,0.0) 50%, rgba(15,23,42,0.65) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Card Superior Fase A (18.9s a 22.4s): Marcadores curtos e pontuais, deixando a fala para a legenda */}
      {fadeA > 0.01 && (
        <div
          style={{
            position: 'absolute',
            top: 155,
            left: 68,
            right: 68,
            opacity: fadeA,
            transform: `translateY(${slideA}px)`,
            background: 'rgba(15, 23, 42, 0.95)',
            border: `3px solid ${COR_MARCA}`,
            borderRadius: 22,
            padding: '16px 24px',
            boxShadow: '0 16px 40px rgba(0,0,0,0.85)',
          }}
        >
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12}}>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 900,
                color: '#38BDF8',
                textTransform: 'uppercase',
              }}
            >
              O Resultado
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 800,
                color: '#4ADE80',
              }}
            >
              ● Bot Sentinela Ativo
            </span>
          </div>

          <div style={{display: 'flex', gap: 14, justifyContent: 'space-between'}}>
            <div
              style={{
                flex: 1,
                background: 'rgba(14, 165, 233, 0.2)',
                border: '2px solid rgba(14, 165, 233, 0.6)',
                borderRadius: 14,
                padding: '10px 14px',
                textAlign: 'center',
                fontFamily,
                fontSize: 28,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              📊 Relatórios Claros
            </div>
            <div
              style={{
                flex: 1,
                background: 'rgba(14, 165, 233, 0.2)',
                border: '2px solid rgba(14, 165, 233, 0.6)',
                borderRadius: 14,
                padding: '10px 14px',
                textAlign: 'center',
                fontFamily,
                fontSize: 28,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              🛡️ Servidor Monitorado
            </div>
          </div>
        </div>
      )}

      {/* Card Superior Fase B (22.5s a 26.5s): 3 pílulas sincronizadas milimetricamente com a locução */}
      {fadeB > 0.01 && (
        <div
          style={{
            position: 'absolute',
            top: 155,
            left: 68,
            right: 68,
            opacity: fadeB,
            transform: `translateY(${slideB}px)`,
            background: 'rgba(15, 23, 42, 0.95)',
            border: `3px solid ${COR_MARCA}`,
            borderRadius: 22,
            padding: '14px 22px',
            boxShadow: '0 16px 40px rgba(0,0,0,0.85)',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 30,
              fontWeight: 900,
              color: COR_TEXTO,
              marginBottom: 10,
              textAlign: 'center',
            }}
          >
            Sua VPS pronta, segura e com backup
          </div>
          <div style={{display: 'flex', gap: 10, justifyContent: 'space-between'}}>
            {[
              {txt: 'VPS Pronta', ativo: ativaPronta, destaque: absT < 23.8},
              {txt: 'Segura', ativo: ativaSegura, destaque: absT >= 23.8 && absT < 25.0},
              {txt: 'Com Backup', ativo: ativaBackup, destaque: absT >= 25.0},
            ].map((it, idx) => {
              const bg = it.destaque ? COR_MARCA : it.ativo ? 'rgba(14,165,233,0.45)' : 'rgba(30,41,59,0.9)';
              const border = it.destaque ? '#FFFFFF' : it.ativo ? '#38BDF8' : 'rgba(148,163,184,0.3)';
              const shadow = it.destaque ? '0 0 20px rgba(14,165,233,0.95)' : 'none';
              const scale = it.destaque ? 'scale(1.04)' : 'scale(1)';

              return (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '10px 6px',
                    borderRadius: 14,
                    background: bg,
                    border: `2px solid ${border}`,
                    fontFamily,
                    fontSize: 28,
                    fontWeight: 900,
                    color: COR_TEXTO,
                    boxShadow: shadow,
                    transform: scale,
                    transition: 'all 0.15s ease',
                  }}
                >
                  ✓ {it.txt}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// Cena 4: Cartão Final / CTA (26.17s - 30.11s) — Layout verticalmente equilibrado, badges estáveis e microinteração contínua
const Cena4CartaoFinal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  // Transição fluida de entrada com zoom suave
  const entrada = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const zoomBg = interpolate(t, [0, 3.94], [1.02, 1.18]);

  // Pulso contínuo não-harmônico no botão CTA para garantir que quadros nunca sejam idênticos
  const pulsoBotao = 1.0 + 0.04 * Math.sin(frame * 0.14);

  // Varredura linear contínua do feixe de luz sobre o botão (evita aliasing cíclico)
  const shimmerTranslateX = ((frame * 12) % 750) - 200;

  // Microinteração de flutuação vertical leve no painel
  const floatPanelY = Math.sin(frame * 0.07) * 4;

  // Badges da stack técnica com escala fixa de 100% e alta legibilidade (>= 32px)
  const TECNOLOGIAS = [
    {nome: 'Docker', icone: '📦'},
    {nome: 'Portainer', icone: '🚢'},
    {nome: 'Traefik', icone: '⚡'},
    {nome: 'n8n próprio', icone: '⚙️'},
    {nome: 'Bot Sentinela', icone: '🛡️'},
  ];

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: entrada}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: '20% 50%',
            transform: `scale(${zoomBg})`,
            filter: 'blur(22px) brightness(0.22)',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(circle at 50% 30%, rgba(14,165,233,0.35) 0%, rgba(17,24,39,0.96) 65%)',
          }}
        />
      </AbsoluteFill>

      <TerminalBRoll opacidade={0.12} velocidade={2.0} />
      <ParticulasSuspensas cor={COR_MARCA} opacidade={0.65} />

      {/* Container Principal Verticalmente Equilibrado (ocupa y=180 a 1480 sem vácuo inferior) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(${floatPanelY}px)`,
        }}
      >
        {/* Card Principal da Oferta (y=180 a 760) */}
        <div
          style={{
            position: 'absolute',
            top: 180,
            left: 64,
            right: 64,
            background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(17, 24, 39, 0.95) 100%)',
            border: `3px solid ${COR_MARCA}`,
            borderRadius: 36,
            padding: '34px 34px',
            textAlign: 'center',
            boxShadow: '0 25px 70px rgba(0,0,0,0.85), 0 0 40px rgba(14,165,233,0.25)',
          }}
        >
          {/* Badge de Marca */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '8px 26px',
              borderRadius: 999,
              background: `linear-gradient(90deg, ${COR_MARCA}, #0284C7)`,
              boxShadow: '0 8px 24px rgba(14,165,233,0.5)',
              marginBottom: 16,
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                background: '#FFFFFF',
                boxShadow: '0 0 10px #FFFFFF',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: COR_TEXTO,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              VPS BLINDADA
            </span>
          </div>

          {/* Título Principal */}
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: COR_TEXTO,
              lineHeight: 1.16,
              marginBottom: 24,
              textWrap: 'balance',
            }}
          >
            Sua VPS pronta, segura e com backup automático
          </div>

          {/* Grade de Tecnologias Estáveis (escala 100% fixa, fonte 32px garantindo leitura no celular) */}
          <div style={{display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center'}}>
            {/* Linha 1: Docker, Portainer, Traefik */}
            <div style={{display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap'}}>
              {TECNOLOGIAS.slice(0, 3).map((tech, idx) => (
                <div
                  key={idx}
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#E0F2FE',
                    background: 'rgba(14, 165, 233, 0.22)',
                    border: '2px solid rgba(14, 165, 233, 0.65)',
                    padding: '10px 22px',
                    borderRadius: 16,
                    boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
                  }}
                >
                  ✓ {tech.nome}
                </div>
              ))}
            </div>

            {/* Linha 2: n8n próprio, Bot Sentinela (escala 100% estável, nunca encolhe) */}
            <div style={{display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap'}}>
              {TECNOLOGIAS.slice(3, 5).map((tech, idx) => (
                <div
                  key={idx + 3}
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#E0F2FE',
                    background: 'rgba(14, 165, 233, 0.22)',
                    border: '2px solid rgba(14, 165, 233, 0.65)',
                    padding: '10px 24px',
                    borderRadius: 16,
                    boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
                  }}
                >
                  ✓ {tech.nome}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Card Intermediário Integrado: Garantia Técnica de Entrega (y=780 a 980) */}
        <div
          style={{
            position: 'absolute',
            top: 780,
            left: 64,
            right: 64,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid rgba(56, 189, 248, 0.45)',
            borderRadius: 26,
            padding: '20px 28px',
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            boxShadow: '0 16px 45px rgba(0,0,0,0.6)',
          }}
        >
          <div
            style={{
              width: 58,
              height: 58,
              borderRadius: 18,
              background: 'rgba(14, 165, 233, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 32,
            }}
          >
            🛡️
          </div>
          <div>
            <div style={{fontFamily, fontSize: 30, fontWeight: 900, color: '#FFFFFF'}}>
              Robô Vigia e Relatórios Claros
            </div>
            <div style={{fontFamily, fontSize: 24, fontWeight: 700, color: '#38BDF8'}}>
              Bot Sentinela vigiando os erros por você
            </div>
          </div>
        </div>

        {/* Bloco de Ação: Botão CTA e @ Arroba (y=1010 a 1380, preenchendo a metade inferior) */}
        <div
          style={{
            position: 'absolute',
            top: 1010,
            left: 64,
            right: 64,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
          }}
        >
          {/* Botão CTA com Varredura Contínua e Pulso Dinâmico */}
          <div
            style={{
              position: 'relative',
              width: '100%',
              padding: '26px 36px',
              borderRadius: 999,
              background: `linear-gradient(90deg, ${COR_MARCA}, #0284C7)`,
              border: '4px solid #E0F2FE',
              boxShadow: '0 20px 55px rgba(14, 165, 233, 0.7), 0 0 35px rgba(14,165,233,0.4)',
              transform: `scale(${pulsoBotao})`,
              overflow: 'hidden',
              textAlign: 'center',
            }}
          >
            {/* Shimmer contínuo com deslocamento linear que não se repete no mesmo ponto */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: 0,
                width: '60%',
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.7), transparent)',
                transform: `translateX(${shimmerTranslateX}%) skewX(-25deg)`,
                pointerEvents: 'none',
              }}
            />
            <span
              style={{
                position: 'relative',
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: COR_TEXTO,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.5)',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          {/* Arroba obrigatório posicionado na faixa y=1240 a 1340 */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.95)',
              border: '2px solid rgba(56, 189, 248, 0.7)',
              borderRadius: 999,
              padding: '12px 38px',
              boxShadow: '0 8px 25px rgba(0,0,0,0.5)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#38BDF8',
              }}
            >
              @vpsblindada.ia
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const progressoTotal = interpolate(frame, [0, durationInFrames - 1], [0, 100]);

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const seg = f / 30;
          if (seg < 0.5) return interpolate(seg, [0, 0.5], [0, 0.1]);
          if (seg > 28.5) return interpolate(seg, [28.5, 30.11], [0.16, 0.04], {extrapolateRight: 'clamp'});
          return 0.1;
        }}
      />

      {/* Cena 0: 0.0s a 4.95s */}
      <Sequence from={0} durationInFrames={Math.ceil(4.95 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* Cena 1: 4.6s a 11.6s */}
      <Sequence from={Math.floor(4.6 * fps)} durationInFrames={Math.ceil((11.6 - 4.6) * fps)}>
        <Cena1Problema />
      </Sequence>

      {/* Cena 2: 11.25s a 19.25s */}
      <Sequence from={Math.floor(11.25 * fps)} durationInFrames={Math.ceil((19.25 - 11.25) * fps)}>
        <Cena2Conversa />
      </Sequence>

      {/* Cena 3: 18.9s a 26.52s */}
      <Sequence from={Math.floor(18.9 * fps)} durationInFrames={Math.ceil((26.52 - 18.9) * fps)}>
        <Cena3Dono />
      </Sequence>

      {/* Cena 4: 26.17s a 30.11s */}
      <Sequence from={Math.floor(26.17 * fps)} durationInFrames={Math.ceil((30.11 - 26.17) * fps)}>
        <Cena4CartaoFinal />
      </Sequence>

      {/* Barra de progresso no topo dentro da Safe Zone (y=152) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 68,
          right: 68,
          height: 6,
          borderRadius: 999,
          background: 'rgba(255,255,255,0.18)',
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progressoTotal}%`,
            height: '100%',
            background: COR_MARCA,
          }}
        />
      </div>

      {/* Legenda Karaokê ativa durante as falas incluindo a fala final do CTA até 28.3s */}
      {frame < Math.floor(28.35 * fps) && (
        <Karaoke
          palavras={PALAVRAS}
          fontFamily={fontFamily}
          destaque={COR_MARCA}
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={355}
          maxLetras={32}
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
      durationInFrames={Math.ceil(30.11 * 30)}
    />
  );
};
