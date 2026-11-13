import { GlobalRagManager } from "./GlobalRagManager";

// "Biblioteca de Treinamento (RAG)". Antes era uma prévia 100% visual com documentos e
// um site "treinados" inventados (Manual_De_Vendas_2026.pdf, www.hipercool.com.br, um CNPJ
// fictício no texto). Agora mostra a Central de Conhecimento REAL (base global + bases por
// agente, ligadas a /api/rag/documents).
export const KnowledgeManagerTab = () => <GlobalRagManager />;
