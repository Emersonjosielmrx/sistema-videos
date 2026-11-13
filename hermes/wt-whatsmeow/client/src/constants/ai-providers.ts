export const LLM_PROVIDERS = [
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Google Gemini" },
  { value: "groq", label: "Groq" },
  { value: "custom", label: "Custom / Proxy (compatível OpenAI)" },
] as const;

export const STT_PROVIDERS = [
  { value: "local", label: "Whisper (grátis e lento) — padrão, sem chave" },
  { value: "groq", label: "Groq (rápido, precisa de chave)" },
  { value: "openai", label: "OpenAI Whisper API" },
  { value: "custom", label: "Custom / Servidor próprio (ex: faster-whisper-server)" },
] as const;

export const TTS_PROVIDERS = [
  { value: "piper", label: "Piper (local na VPS, rápido) — recomendado p/ ligação" },
  { value: "edge-tts", label: "Edge TTS (grátis, sem chave)" },
  { value: "elevenlabs", label: "ElevenLabs (vozes realistas)" },
  { value: "cartesia", label: "Cartesia (baixíssima latência)" },
  { value: "gemini", label: "Google Gemini TTS" },
  { value: "openai", label: "OpenAI TTS" },
] as const;

export const FALLBACK_MODELS: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
  groq: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
  gemini: ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
  anthropic: [
    "claude-opus-4-1-20250805",
    "claude-sonnet-4-5-20250929",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
  ],
};

export const PROVIDER_INFO: Record<string, { name: string; link: string; tut: string }> = {
  groq: { name: "Groq", link: "https://console.groq.com/keys", tut: "Crie a conta, vá no menu lateral esquerdo em 'API Keys' e clique em 'Create API Key'." },
  gemini: { name: "Google Gemini", link: "https://aistudio.google.com/apikey", tut: "Acesse o AI Studio, clique em 'Get API key' no botão azul à esquerda e gere." },
  openai: { name: "OpenAI", link: "https://platform.openai.com/api-keys", tut: "Você precisa ter saldo na conta. Vá em 'API Keys' e crie uma nova secret key." },
  anthropic: { name: "Anthropic", link: "https://console.anthropic.com/settings/keys", tut: "Adicione créditos na conta e crie uma chave no console." },
  elevenlabs: { name: "ElevenLabs", link: "https://elevenlabs.io/app/settings/api-keys", tut: "Crie conta, clique no seu perfil no canto inferior esquerdo > Profile + API Key." },
  cartesia: { name: "Cartesia", link: "https://play.cartesia.ai/keys", tut: "Acesse a aba Keys no painel deles e gere uma chave de produção." },
  piper: { name: "Piper (Local)", link: "#", tut: "Piper roda localmente no servidor. Não precisa de chave de API externa." },
  "edge-tts": { name: "Edge TTS (Grátis)", link: "#", tut: "Edge TTS da Microsoft é gratuito e não requer chave de API." },
  local: { name: "Local (Grátis)", link: "#", tut: "Modelo local rodando no servidor. Não precisa de chave de API externa." },
  custom: { name: "Custom / Proxy", link: "#", tut: "Configure um servidor customizado ou proxy compatível com OpenAI." },
};
