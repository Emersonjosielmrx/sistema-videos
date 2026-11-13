import { useCallback, useEffect, useRef, useState } from 'react';
import ReactFlow, { 
  Background, 
  useNodesState,
  useEdgesState,
  addEdge, 
  Handle, 
  Position, 
  NodeProps,
  EdgeProps,
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath
} from 'reactflow';
import 'reactflow/dist/style.css';
import { BrainCircuit, Bot, Zap, Plus, Settings2, Trash2, X, GitBranch, TerminalSquare, ArrowRightLeft, Play, MessageSquare, Globe, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';
import dagre from 'dagre';
import { apiGet, apiPost } from '@/lib/api';
import { logError } from '@/lib/log';

// --- CUSTOM NODES ---

const BaseNodeContainer = ({ children, selected, borderColor }: any) => (
  <div className={`w-64 bg-[#111] border ${selected ? 'border-primary shadow-[0_0_15px_rgba(99,102,241,0.5)]' : (borderColor || 'border-indigo-500/40')} rounded-xl shadow-lg transition-transform hover:scale-[1.02] relative group`}>
    {children}
  </div>
);

// Agent Node (Existing)
const CustomNode = ({ data, selected }: NodeProps) => {
  return (
    <BaseNodeContainer selected={selected} borderColor={data.borderColor}>
      <Handle type="target" position={Position.Top} isConnectable={true} className="!w-6 !h-6 !bg-indigo-500 !border-4 !border-[#111] hover:!bg-indigo-400 z-50 cursor-crosshair" />
      
      {!data.isRoot && (
        <button 
          onClick={(e) => { e.stopPropagation(); data.onRemove(data.id); }}
          className="absolute -top-3 -right-3 bg-destructive text-destructive-foreground rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity shadow-md z-50"
          title="Remover"
        >
          <X className="w-4 h-4" />
        </button>
      )}

      <div className={`${data.headerBg || 'bg-indigo-500/10'} p-3 border-b ${data.borderColor ? data.borderColor.replace('/40','/20') : 'border-indigo-500/20'} flex items-center justify-between rounded-t-xl`}>
        <span className={`text-sm font-bold ${data.textColor || 'text-indigo-400'} flex items-center gap-2 truncate`}>
          {data.icon === 'brain' ? <BrainCircuit className="w-5 h-5"/> : <Bot className="w-5 h-5"/>} 
          {data.label}
        </span>
        {data.isRoot && <div className="w-3 h-3 rounded-full bg-indigo-500 animate-pulse"></div>}
      </div>
      
      <div className="p-4 space-y-4">
        {data.isRoot ? (
          <p className="text-sm text-muted-foreground text-center pb-2">
            Recebe e analisa a intenção do cliente antes de acionar um agente.
          </p>
        ) : (
          <div className="bg-black/50 p-3 rounded-lg border border-border/50 text-white shadow-inner nodrag cursor-text space-y-3">
            <div className="bg-black/30 p-2 rounded-md border border-border/20">
              <span className={`${data.textColor} font-bold block mb-1 opacity-80 text-[10px] uppercase`}>
                Lógica Exata
              </span>
              <div className="flex gap-1 flex-col mt-2">
                <select 
                  value={data.logicType || "contains"}
                  onChange={(e) => data.onTriggerChange(data.id, 'logicType', e.target.value)}
                  className="w-full bg-[#111] border border-border/50 rounded-md text-[10px] p-1.5 text-white outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="none">Nenhuma Regra</option>
                  <option value="tag">Possui a Tag...</option>
                  <option value="stage">Está na Etapa...</option>
                  <option value="time">Dentro do Horário...</option>
                  <option value="exact">Mensagem Exata...</option>
                  <option value="contains">Contém a palavra...</option>
                  <option value="similar">Palavra parecida com...</option>
                </select>
                
                {data.logicType === 'tag' && (
                  <select 
                    value={data.trigger || ""}
                    onChange={(e) => data.onTriggerChange(data.id, 'trigger', e.target.value)}
                    className="w-full bg-[#111] border border-border/50 rounded-md text-[10px] p-1.5 text-white outline-none focus:ring-1 focus:ring-primary mt-1"
                  >
                    <option value="">Selecione a Tag</option>
                    <option value="vip">⭐ Cliente VIP</option>
                    <option value="devedor">⚠️ Inadimplente</option>
                    <option value="novo">👋 Lead Novo</option>
                  </select>
                )}

                {data.logicType === 'stage' && (
                  <select 
                    value={data.trigger || ""}
                    onChange={(e) => data.onTriggerChange(data.id, 'trigger', e.target.value)}
                    className="w-full bg-[#111] border border-border/50 rounded-md text-[10px] p-1.5 text-white outline-none focus:ring-1 focus:ring-primary mt-1"
                  >
                    <option value="">Selecione a Etapa</option>
                    <option value="1">1. Qualificação</option>
                    <option value="2">2. Apresentação</option>
                    <option value="3">3. Fechamento</option>
                  </select>
                )}
                
                {data.logicType === 'time' && (
                  <div className="flex gap-1 mt-1">
                    <Input type="time" value={(data.trigger || "").split('-')[0] || "08:00"} onChange={(e) => data.onTriggerChange(data.id, 'trigger', `${e.target.value}-${(data.trigger || "").split('-')[1] || "18:00"}`)} className="h-6 text-[10px] bg-transparent border-border/50 px-1" />
                    <span className="text-muted-foreground self-center text-[10px]">até</span>
                    <Input type="time" value={(data.trigger || "").split('-')[1] || "18:00"} onChange={(e) => data.onTriggerChange(data.id, 'trigger', `${(data.trigger || "").split('-')[0] || "08:00"}-${e.target.value}`)} className="h-6 text-[10px] bg-transparent border-border/50 px-1" />
                  </div>
                )}

                {['exact', 'contains', 'similar'].includes(data.logicType || 'contains') && data.logicType !== 'none' && (
                  <Input 
                    value={data.trigger} 
                    onChange={(e) => data.onTriggerChange(data.id, 'trigger', e.target.value)}
                    placeholder="Digite o texto..."
                    className="h-6 text-[10px] bg-transparent border-border/50 mt-1 focus-visible:ring-1 focus-visible:ring-primary/50"
                  />
                )}
              </div>
            </div>
            
            <div className="bg-black/30 p-2 rounded-md border border-border/20">
              <span className={`${data.textColor} font-bold block mb-1 opacity-80 text-[10px] uppercase`}>
                Condição Inteligente (IA)
              </span>
              <Input 
                value={data.aiTrigger || ""} 
                onChange={(e) => data.onTriggerChange(data.id, 'aiTrigger', e.target.value)}
                placeholder="Ex: Cliente quer saber o preço"
                className="h-7 text-[10px] bg-transparent border-border/50 focus-visible:ring-1 focus-visible:ring-primary/50"
              />
            </div>
            <div>
              <span className={`${data.textColor} font-bold block mb-1 opacity-80 text-[10px] uppercase mt-2`}>
                Prioridade (Resolução)
              </span>
              <select 
                value={data.priority || "ai_first"}
                onChange={(e) => data.onTriggerChange(data.id, 'priority', e.target.value)}
                className="w-full bg-[#111] border border-border/50 rounded-md text-[10px] p-1.5 text-white outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="rule_first">Forçar Lógica Exata primeiro</option>
                <option value="ai_first">Deixar IA avaliar intenção primeiro</option>
              </select>
            </div>
          </div>
        )}
        
        {!data.isRoot && (
          <div className="flex gap-2 justify-between border-t border-border/50 pt-2 mt-2 text-[10px] uppercase font-bold items-center">
             <div className="flex flex-col gap-0.5">
               <span className="opacity-70 font-mono truncate max-w-[100px]">{data.model}</span>
               <span className="opacity-70 text-emerald-400">{data.status === 'production' ? 'Ativo' : data.status === 'draft' ? 'Treinando' : 'Pausado'}</span>
             </div>
             <button onClick={(e) => { e.stopPropagation(); data.onTestChat?.(data.id); }} className="bg-primary/20 hover:bg-primary/40 text-primary p-1.5 rounded-lg flex items-center gap-1 transition-colors">
               <MessageSquare className="w-3 h-3" /> <span className="sr-only">Testar</span>
             </button>
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} isConnectable={true} className="!w-6 !h-6 !bg-indigo-500 !border-4 !border-[#111] hover:!bg-indigo-400 z-50 cursor-crosshair" />
    </BaseNodeContainer>
  );
};

// We removed ConditionAINode and ConditionLogicNode, logic is now embedded in the Agent node

// Handoff Node
const HandoffNode = ({ data, selected }: NodeProps) => (
  <BaseNodeContainer selected={selected} borderColor="border-orange-500/40">
    <Handle type="target" position={Position.Top} isConnectable={true} className="!w-6 !h-6 !bg-orange-500 !border-4 !border-[#111] hover:!bg-orange-400 z-50 cursor-crosshair" />
    <button onClick={(e) => { e.stopPropagation(); data.onRemove(data.id); }} className="absolute -top-3 -right-3 bg-destructive text-destructive-foreground rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity shadow-md z-50"><X className="w-4 h-4" /></button>
    
    <div className="bg-orange-500/10 p-3 border-b border-orange-500/20 flex items-center justify-between rounded-t-xl">
      <span className="text-sm font-bold text-orange-400 flex items-center gap-2 truncate"><ArrowRightLeft className="w-5 h-5"/> Regra de Handoff</span>
    </div>
    <div className="p-4 space-y-3">
       <p className="text-xs text-muted-foreground text-center">Configura a transferência de agentes.</p>
       <div className="bg-black/50 p-2 rounded-lg border border-border/50 nodrag cursor-text">
         <select className="w-full bg-transparent border-none text-xs outline-none text-white focus:ring-0">
            <option className="bg-[#111]" value="silent">Transferência Silenciosa</option>
            <option className="bg-[#111]" value="spoken">Aviso de Transferência</option>
         </select>
       </div>
    </div>
    <Handle type="source" position={Position.Bottom} isConnectable={true} className="!w-6 !h-6 !bg-orange-500 !border-4 !border-[#111] hover:!bg-orange-400 z-50 cursor-crosshair" />
  </BaseNodeContainer>
);

// HTTP AI Request Node
const AIHttpRequestNode = ({ data, selected }: NodeProps) => (
  <BaseNodeContainer selected={selected} borderColor="border-blue-500/40">
    <Handle type="target" position={Position.Top} isConnectable={true} className="!w-6 !h-6 !bg-blue-500 !border-4 !border-[#111] hover:!bg-blue-400 z-50 cursor-crosshair" />
    <button onClick={(e) => { e.stopPropagation(); data.onRemove(data.id); }} className="absolute -top-3 -right-3 bg-destructive text-destructive-foreground rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity shadow-md z-50"><X className="w-4 h-4" /></button>
    
    <div className="bg-blue-500/10 p-3 border-b border-blue-500/20 flex items-center justify-between rounded-t-xl">
      <span className="text-sm font-bold text-blue-400 flex items-center gap-2 truncate"><Globe className="w-5 h-5"/> HTTP Automático (IA)</span>
    </div>
    <div className="p-4 space-y-3">
       <p className="text-xs text-muted-foreground text-center">A IA gera o payload automaticamente.</p>
       <div className="bg-black/50 p-2 rounded-lg border border-border/50 nodrag cursor-text">
         <span className="text-blue-400 font-bold block mb-1 opacity-80 text-[10px] uppercase">Instrução para a IA</span>
         <Input defaultValue={data.prompt || "Buscar saldo do cliente usando o telefone dele"} className="h-7 text-[10px] bg-transparent border-border/50 mb-2" />
         
         {/* Antes havia "Executar" e "Pin Data" que só mostravam um aviso (nada rodava). */}
         <p className="mt-2 text-[10px] text-amber-500">Executar e testar este passo: em breve.</p>
       </div>
    </div>
    <Handle type="source" position={Position.Bottom} isConnectable={true} className="!w-6 !h-6 !bg-blue-500 !border-4 !border-[#111] hover:!bg-blue-400 z-50 cursor-crosshair" />
  </BaseNodeContainer>
);

const nodeTypes = {
  custom: CustomNode,
  handoff: HandoffNode,
  ai_http: AIHttpRequestNode,
};

// --- CUSTOM EDGE ---
const CustomEdge = ({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style = {}, markerEnd, data }: EdgeProps) => {
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={style} />
      <EdgeLabelRenderer>
        <div style={{ position: 'absolute', transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`, pointerEvents: 'all' }} className="nodrag nopan group">
          <button className="bg-background text-muted-foreground p-1.5 rounded-full shadow-lg border border-border/50 hover:bg-destructive hover:text-white hover:border-destructive hover:scale-110 transition-all opacity-0 group-hover:opacity-100 flex items-center justify-center" onClick={(event) => { event.stopPropagation(); if (data && data.onDelete) data.onDelete(id); }} title="Remover Ligação">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  );
};
const edgeTypes = { customEdge: CustomEdge };

// --- AUTO LAYOUT LOGIC ---
const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  const nodeWidth = 280;
  const nodeHeight = 200;
  
  dagreGraph.setGraph({ rankdir: direction, ranksep: 100, nodesep: 50 });
  
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });
  
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });
  
  dagre.layout(dagreGraph);
  
  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });
  
  return { nodes: newNodes, edges };
};

// Remove funções do objeto data de um nó (não serializáveis). Mantém só campos de dados.
const sanitizeData = (data: any) => {
  if (!data || typeof data !== "object") return data;
  const out: any = {};
  for (const k of Object.keys(data)) {
    if (typeof data[k] !== "function") out[k] = data[k];
  }
  return out;
};

// --- MAIN COMPONENT ---
export function AgentOrchestratorFlow({ agents, onUpdateAgent }: { agents: any[], onUpdateAgent: (id: string, updates: any) => void }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  // Chaves fixas onde o desenho é gravado (o carregamento sempre usou estas). Antes havia
  // seletores com opções fictícias ("WhatsApp +55 11 9999-9999", "Instagram DM").
  const activeEnvironment = "campanha_vendas_1";
  const activeChannel = "whatsapp_551199999999";

  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState<{role: 'user'|'system', content: string, trace?: string[]}[]>([]);
  const [simQuery, setSimQuery] = useState("");
  
  const initialized = useRef(false);

  const removeNode = useCallback((nodeId: string) => {
    setNodes(nds => nds.filter(n => n.id !== nodeId));
    setEdges(eds => eds.filter(e => e.source !== nodeId && e.target !== nodeId));
  }, [setNodes, setEdges]);

  const removeEdge = useCallback((edgeId: string) => {
    setEdges(eds => eds.filter(e => e.id !== edgeId));
  }, [setEdges]);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const rootNode = {
      id: 'root', type: 'custom', position: { x: 350, y: 50 },
      data: { id: 'root', label: 'Triagem Central (Mestre)', isRoot: true, icon: 'brain' },
    };

    const initialNodes: any[] = [rootNode];
    const initialEdges: any[] = [];

    agents.forEach((agent, idx) => {
      const borderColor = agent.kind === 'call' ? 'border-sky-500/40' : agent.kind === 'message' ? 'border-emerald-500/40' : 'border-amber-500/40';
      const headerBg = agent.kind === 'call' ? 'bg-sky-500/10' : agent.kind === 'message' ? 'bg-emerald-500/10' : 'bg-amber-500/10';
      const textColor = agent.kind === 'call' ? 'text-sky-400' : agent.kind === 'message' ? 'text-emerald-400' : 'text-amber-400';
      const xPos = 50 + (idx * 300);

      initialNodes.push({
        id: agent.id, type: 'custom', position: { x: xPos, y: 300 },
        data: {
          id: agent.id, label: agent.name, trigger: agent.trigger || '', model: agent.llm_model, status: agent.status,
          borderColor, headerBg, textColor, onRemove: removeNode,
          onTestChat: () => setChatOpen(true),
          onTriggerChange: (id: string, field: string, val: string) => {
            onUpdateAgent(id, { [field === 'trigger' ? 'trigger' : field]: val });
            setNodes(nds => nds.map(n => n.id === id ? { ...n, data: { ...n.data, [field]: val } } : n));
          }
        }
      });
      initialEdges.push({ id: `e-root-${agent.id}`, source: 'root', target: agent.id, type: 'customEdge', animated: true, style: { stroke: 'rgba(99, 102, 241, 0.6)', strokeWidth: 2 }, data: { onDelete: removeEdge } });
    });

    setNodes(initialNodes);
    setEdges(initialEdges as any);

    // Restaura o fluxo salvo (posições + arestas desenhadas) por cima do build default,
    // preservando os callbacks (onRemove/onTriggerChange) que não são serializáveis.
    apiGet<{ flow: { nodes: any[]; edges: any[] } | null }>(
      `/api/orchestration?environment=${encodeURIComponent('campanha_vendas_1')}&channel=${encodeURIComponent('whatsapp_551199999999')}`
    ).then((r) => {
      const flow = r.flow;
      if (!flow || !Array.isArray(flow.nodes) || flow.nodes.length === 0) return;
      const savedPos = new Map<string, any>(flow.nodes.map((n: any) => [n.id, n.position]));
      const savedData = new Map<string, any>(flow.nodes.map((n: any) => [n.id, n.data]));
      setNodes((cur) => cur.map((n) => savedPos.has(n.id)
        ? { ...n, position: savedPos.get(n.id) || n.position, data: { ...n.data, ...(savedData.get(n.id) || {}) } }
        : n));
      if (Array.isArray(flow.edges) && flow.edges.length > 0) {
        setEdges(flow.edges.map((e: any) => ({ ...e, type: 'customEdge', data: { onDelete: removeEdge } })) as any);
      }
    }).catch(logError("AgentOrchestratorFlow"));
  }, [agents, onUpdateAgent, removeNode, removeEdge, setNodes, setEdges]);

  const onConnect = useCallback((params: any) => {
    setEdges((eds) => {
      const exists = eds.find(e => e.source === params.source && e.target === params.target);
      if (exists) return eds;
      return addEdge({ ...params, type: 'customEdge', animated: true, style: { stroke: 'rgba(99, 102, 241, 0.8)', strokeWidth: 3 }, data: { onDelete: removeEdge } }, eds);
    });
  }, [setEdges, removeEdge]);

  const handleAddAgentToFlow = (agent: any) => {
    if (nodes.find(n => n.id === agent.id)) return;
    const borderColor = agent.kind === 'call' ? 'border-sky-500/40' : agent.kind === 'message' ? 'border-emerald-500/40' : 'border-amber-500/40';
    const headerBg = agent.kind === 'call' ? 'bg-sky-500/10' : agent.kind === 'message' ? 'bg-emerald-500/10' : 'bg-amber-500/10';
    const textColor = agent.kind === 'call' ? 'text-sky-400' : agent.kind === 'message' ? 'text-emerald-400' : 'text-amber-400';

    const newNode = {
      id: agent.id, type: 'custom', position: { x: 100, y: 100 },
      data: {
        id: agent.id, label: agent.name, trigger: agent.trigger || '', model: agent.llm_model, status: agent.status,
        borderColor, headerBg, textColor, onRemove: removeNode,
        onTestChat: () => setChatOpen(true),
        onTriggerChange: (id: string, field: string, val: string) => {
          onUpdateAgent(id, { [field === 'trigger' ? 'trigger' : field]: val });
          setNodes(nds => nds.map(n => n.id === id ? { ...n, data: { ...n.data, [field]: val } } : n));
        }
      }
    };
    setNodes(nds => [...nds, newNode]);
  };

  const handleAddToolNode = (type: string) => {
    const id = `${type}_${Date.now()}`;
    const newNode = {
      id,
      type,
      position: { x: 150, y: 150 },
      data: { id, onRemove: removeNode }
    };
    setNodes(nds => [...nds, newNode]);
  };

  const handleAutoLayout = () => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(nodes, edges);
    setNodes([...layoutedNodes]);
    setEdges([...layoutedEdges]);
    toast.success("Fluxo organizado automaticamente!");
  };

  // Remove callbacks (onRemove/onTriggerChange/onDelete...) do data antes de salvar —
  // funções não são serializáveis e não devem ir pro banco. Mantém só o que descreve o nó.
  const serializableNodes = (ns: any[]) => ns.map(n => ({
    id: n.id, type: n.type, position: n.position,
    data: sanitizeData(n.data),
  }));
  const serializableEdges = (es: any[]) => es.map(e => ({
    id: e.id, source: e.source, target: e.target, type: e.type, animated: e.animated, style: e.style,
  }));

  const handleSave = async () => {
    try {
      await apiPost("/api/orchestration", {
        environment: activeEnvironment,
        channel: activeChannel,
        nodes: serializableNodes(nodes),
        edges: serializableEdges(edges),
      });
      toast.success("Fluxograma salvo! O desenho será recarregado assim na próxima vez.");
    } catch (e) {
      toast.error("Erro ao salvar", { description: (e as Error).message });
    }
  };

  // SIMULAÇÃO (não afeta as ligações reais): mostra qual agente do desenho tem uma regra de
  // palavra que bate com a mensagem. Sem sorteio — antes escolhia um agente ALEATÓRIO e
  // inventava uma resposta dele. Regras de tag, etapa, horário e "condição por IA" não
  // entram aqui (dependem do contato real).
  const simulateRoute = (text: string) => {
    const norm = (v: string) => v.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    const msg = norm(text);
    const matches: { id: string; name: string; rule: string }[] = [];
    for (const n of nodes) {
      if (n.type !== 'custom' || n.data?.isRoot) continue;
      const logic = n.data?.logicType || 'contains';
      const words = String(n.data?.trigger || '').split(',').map(norm).filter(Boolean);
      if (words.length === 0) continue;
      let hit = '';
      if (logic === 'exact') hit = words.find((w) => msg === w) || '';
      else if (logic === 'contains' || logic === 'similar') hit = words.find((w) => msg.includes(w)) || '';
      if (hit) matches.push({ id: n.id, name: n.data?.label || n.id, rule: `${logic === 'exact' ? 'mensagem exata' : 'contém'} "${hit}"` });
    }
    return matches;
  };

  const agentsNotInFlow = agents.filter(a => !nodes.find(n => n.id === a.id));

  return (
    <div className="flex flex-col gap-4 w-full h-full">
      {/* Barra de Ferramentas / Ambientes */}
      <div className="flex flex-wrap items-center justify-between bg-[#111] border border-border/50 rounded-xl p-3 shadow-sm gap-3">
        <p className="flex items-start gap-2 text-xs text-amber-500 w-full lg:w-auto lg:max-w-md">
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          Rascunho visual: o desenho é salvo, mas ainda não muda qual agente atende as ligações e mensagens reais.
        </p>

        <div className="flex flex-wrap gap-2 w-full lg:w-auto justify-end mt-2 lg:mt-0">
           <Button variant="outline" size="sm" onClick={handleAutoLayout} className="gap-2 border-border/50">
             <Settings2 className="w-4 h-4"/> Arrumar Mapa (Auto-Layout)
           </Button>

           <Button variant="secondary" size="sm" onClick={() => setChatOpen(!chatOpen)} className={chatOpen ? "bg-primary text-white" : ""}>
             <Play className="w-4 h-4 mr-2"/> {chatOpen ? "Fechar Simulador" : "Simular Roteamento"}
           </Button>

           <DropdownMenu>
             <DropdownMenuTrigger asChild>
               <Button variant="secondary" size="sm" className="gap-2 border border-border/50">
                 <Plus className="w-4 h-4"/> Adicionar Nó
               </Button>
             </DropdownMenuTrigger>
             <DropdownMenuContent align="end" className="w-56 bg-background border-border/50">
                <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase">Agentes Existentes</div>
                {agentsNotInFlow.map(a => (
                  <DropdownMenuItem key={a.id} onClick={() => handleAddAgentToFlow(a)} className="cursor-pointer">
                    <Bot className="w-4 h-4 mr-2 text-muted-foreground"/> {a.name}
                  </DropdownMenuItem>
                ))}
                
                <div className="px-2 py-1 mt-2 text-xs font-semibold text-muted-foreground uppercase border-t border-border/50 pt-2">Lógica & Integrações</div>
                <DropdownMenuItem onClick={() => handleAddToolNode('handoff')} className="cursor-pointer">
                  <ArrowRightLeft className="w-4 h-4 mr-2 text-orange-500"/> Regra de Handoff
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleAddToolNode('ai_http')} className="cursor-pointer">
                  <Globe className="w-4 h-4 mr-2 text-blue-500"/> Webhook Automático (IA)
                </DropdownMenuItem>
             </DropdownMenuContent>
           </DropdownMenu>

           <Button size="sm" onClick={handleSave} className="gap-2 shadow-glow">
             <Zap className="w-4 h-4"/> Salvar Fluxograma
           </Button>
        </div>
      </div>

      {/* Canvas React Flow */}
      <div className="relative w-full h-[600px] bg-[#0a0a0a] border border-border/50 rounded-2xl overflow-hidden shadow-inner flex-1">
        {/* Help tooltip */}
        <div className="absolute top-4 left-4 z-10 bg-black/60 backdrop-blur-sm border border-border/50 text-[10px] text-muted-foreground px-3 py-2 rounded-lg pointer-events-none">
          • Clique e arraste nas <span className="inline-block w-2 h-2 bg-indigo-500 rounded-full mx-1"></span> bolinhas para ligar nós<br/>
          • Use "Adicionar Nó" para Handoffs ou If/Else<br/>
          • O Auto-Layout organiza tudo para você
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          deleteKeyCode={['Backspace', 'Delete']}
          className="react-flow-dark"
        >
          <Background color="#ffffff22" gap={24} />
        </ReactFlow>

        {/* Chat Simulator Overlay (Side Panel) */}
        {chatOpen && (
          <div className="absolute top-0 right-0 h-full w-80 bg-[#111]/95 backdrop-blur-md border-l border-border/50 z-50 flex flex-col shadow-2xl animate-in slide-in-from-right-8">
            <div className="p-3 border-b border-border/50 flex items-center justify-between bg-black/40">
              <span className="font-bold text-sm flex items-center gap-2"><TerminalSquare className="w-4 h-4 text-emerald-400"/> Simulação de roteamento</span>
              <div className="flex gap-2 items-center">
                <button onClick={() => setMessages([])} className="text-muted-foreground hover:text-red-400 transition-colors" title="Limpar">
                  <Trash2 className="w-4 h-4"/>
                </button>
                <button onClick={() => setChatOpen(false)} className="text-muted-foreground hover:text-white"><X className="w-4 h-4"/></button>
              </div>
            </div>
            
            <div className="px-3 py-2 text-[10px] text-amber-500 bg-amber-500/10 border-b border-amber-500/20">
              Simulação — não afeta as ligações reais. Só confere as regras de palavra (mensagem exata / contém) dos agentes no desenho.
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
               {messages.length === 0 && (
                 <div className="text-center text-xs text-muted-foreground mt-10">
                   Digite uma mensagem para ver qual agente teria a regra de palavra.
                 </div>
               )}
               {messages.map((m, i) => (
                 <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                   {m.role === 'system' && m.trace && (
                     <div className="flex items-center gap-1 text-[9px] text-indigo-400 mb-1 ml-1">
                       <GitBranch className="w-3 h-3"/> Rota: {m.trace.join(' → ')}
                     </div>
                   )}
                   <div className={`text-xs p-2.5 rounded-xl max-w-[90%] ${m.role === 'user' ? 'bg-primary text-primary-foreground rounded-tr-none' : 'bg-muted/50 border border-border/50 rounded-tl-none'}`}>
                     {m.content}
                   </div>
                 </div>
               ))}
            </div>

            <div className="p-3 border-t border-border/50 bg-black/40">
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  if(!simQuery) return;
                  setMessages(prev => [...prev, { role: 'user', content: simQuery }]);
                  
                  const matches = simulateRoute(simQuery);
                  const chosen = matches[0];
                  setMessages(prev => [...prev, {
                    role: 'system',
                    content: chosen
                      ? `Iria para: ${chosen.name} (regra: ${chosen.rule}).` + (matches.length > 1 ? ` Também bateria: ${matches.slice(1).map(m => m.name).join(', ')}.` : '')
                      : 'Nenhuma regra de palavra bateu com essa mensagem.',
                    trace: chosen ? ['Triagem Central', chosen.name] : ['Triagem Central'],
                  }]);
                  if (chosen) {
                    setEdges(eds => eds.map(edge =>
                      (edge.source === 'root' && edge.target === chosen.id)
                        ? { ...edge, style: { stroke: '#10b981', strokeWidth: 4 } }
                        : edge
                    ));
                    setTimeout(() => {
                      setEdges(eds => eds.map(edge => ({ ...edge, style: { stroke: 'rgba(99, 102, 241, 0.8)', strokeWidth: 3 } })));
                    }, 2000);
                  }

                  setSimQuery("");
                }} 
                className="flex items-center gap-2"
              >
                <Input 
                  value={simQuery}
                  onChange={e => setSimQuery(e.target.value)}
                  placeholder="Mensagem de teste..."
                  className="flex-1 bg-[#1a1a1a] border-border/50 text-xs h-8 focus-visible:ring-1 focus-visible:ring-primary/50"
                />
                <Button type="submit" size="icon" className="h-8 w-8 rounded-full shadow-glow">
                  <Play className="w-3 h-3 ml-0.5" />
                </Button>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
