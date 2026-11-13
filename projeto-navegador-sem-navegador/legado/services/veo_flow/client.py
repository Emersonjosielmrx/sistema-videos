# -*- coding: utf-8 -*-
"""
services/veo_flow/client.py — Cliente HTTP puro do Google Flow (Veo 3.1 & Nano Banana 2.1).
Permite submeter prompts de vídeo e imagem diretamente para a API do AI Sandbox (Google Labs)
sem abrir a interface pesada do Next.js/React no Chrome.
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from config import UA_DESKTOP, URLS
from core.auth import headers_google
from core.session import PersistentSession

log = logging.getLogger("flow_http")

ORIGIN_SANDBOX = URLS["flow_ai"]
ORIGIN_LABS = "https://labs.google"


class GoogleFlowClient:
    """
    Cliente HTTP para o Google Flow (AI Sandbox).
    Comunica-se diretamente com os endpoints REST internos do FlowCreationAgent
    usando cookies e autorização SAPISIDHASH.
    """

    def __init__(self, conta: str):
        self.conta = conta
        self.session = PersistentSession("veo_flow", self.conta, timeout=120)
        self.session_id = None
        self._inicializar_agente()

    def _inicializar_agente(self) -> None:
        """Verifica a presença de cookies Google com SAPISID."""
        cookies = self.session.session.cookies.get_dict()
        sapisid = cookies.get("SAPISID") or cookies.get("__Secure-3PAPISID")
        if not sapisid:
            log.warning(f"Sem cookies Google SAPISID para conta {self.conta}. Sincronize com cofre primeiro.")

    def _headers(self) -> Dict[str, str]:
        cookies = self.session.session.cookies.get_dict()
        # Origem alinhada com o host da API para o proxy XD3 do Google
        hd = headers_google(ORIGIN_SANDBOX, cookies)
        hd.update({
            "Referer": "https://labs.google/fx/pt/tools/flow",
            "Content-Type": "application/json",
            "X-Same-Domain": "1",
        })
        return hd

    def criar_sessao_projeto(self, nome_projeto: str = "Projeto Auto") -> Optional[str]:
        """
        Cria uma nova sessão de projeto no FlowCreationAgent via HTTP.
        """
        url = f"{ORIGIN_SANDBOX}/v1/flowCreationAgent/sessions"
        payload = {
            "sessionMetadata": {
                "title": nome_projeto,
                "locale": "pt-BR"
            }
        }
        try:
            r = self.session.post(url, json=payload, headers=self._headers())
            if r.status_code in (200, 201):
                dados = r.json()
                self.session_id = dados.get("name") or dados.get("sessionId")
                log.info(f"Sessão do Flow criada: {self.session_id}")
                return self.session_id
            else:
                log.warning(f"Resposta ao criar sessão Flow: status {r.status_code} - {r.text[:200]}")
        except Exception as e:
            log.error(f"Erro ao criar sessão no Flow via HTTP: {e}")
        return None

    def enviar_prompt_video(self, prompt: str, duracao_segundos: int = 8, formato: str = "9:16") -> Dict[str, Any]:
        """
        Envia prompt formatado com as diretrizes do Veo 3.1 (áudio embutido, proporção e duração).
        """
        prompt_enriquecido = (
            f"{prompt} (make it a {duracao_segundos}-second video; "
            f"{formato} vertical portrait aspect ratio; use the Veo 3.1 model; include audio)"
        )
        if not self.session_id:
            self.criar_sessao_projeto()

        if not self.session_id:
            return {"erro": "Não foi possível inicializar sessão no Flow (autenticação necessária)", "prompt": prompt}

        url = f"{ORIGIN_SANDBOX}/v1/{self.session_id}:submitPrompt"
        payload = {
            "userMessage": {
                "userPrompt": {
                    "parts": [{"text": prompt_enriquecido}]
                }
            }
        }
        try:
            r = self.session.post(url, json=payload, headers=self._headers())
            if r.status_code == 200:
                return r.json()
            return {"status": r.status_code, "resposta": r.text[:300]}
        except Exception as e:
            return {"erro": str(e)}

    def gerar_video_lateral(self, prompt: str, duracao_segundos: int = 8, modelo: str = "Veo 3.1") -> Dict[str, Any]:
        """
        Gera vídeo horizontal / widescreen 16:9 para YouTube longo ou desktop.
        """
        return self.enviar_prompt_video(prompt, duracao_segundos=duracao_segundos, formato="16:9")

    def gerar_video_de_imagem(self, prompt: str, imagem_url_ou_id: Optional[str] = None, formato: str = "9:16", duracao_segundos: int = 8) -> Dict[str, Any]:
        """
        Geração Image-to-Video (I2V): anima uma imagem ou foto de objeto real
        (como placas solares, produtos da MS Energy, ou rostos consistentes).
        """
        ref_text = f"Use the provided image reference [{imagem_url_ou_id}] as the starting frame" if imagem_url_ou_id else "Use the uploaded image as starting frame"
        prompt_i2v = f"{ref_text} (image-to-video mode). Animate it smoothly with natural motion: {prompt}"
        return self.enviar_prompt_video(prompt_i2v, duracao_segundos=duracao_segundos, formato=formato)

    def estender_video(self, prompt_extensao: str, duracao_adicional: int = 5) -> Dict[str, Any]:
        """
        Extensão temporal de vídeo existente (Veo 3.1 extend).
        Continua a narrativa e o movimento da cena anterior.
        """
        prompt_ext = (
            f"Extend the previous video clip seamlessly. Continue the motion for {duracao_adicional} more seconds: {prompt_extensao}. "
            f"Maintain full stylistic and character consistency with audio continuity."
        )
        return self.enviar_prompt_video(prompt_ext, duracao_segundos=duracao_adicional)

    def inpaint_correcao_video(self, prompt_correcao: str) -> Dict[str, Any]:
        """
        Inpainting e correção de defeitos em vídeos gerados (mãos, artefatos visuais ou texto).
        """
        prompt_inp = (
            f"Fix and correct visual defects in the current video: {prompt_correcao}. "
            f"Preserve existing subjects and background while fixing deformities."
        )
        return self.enviar_prompt_video(prompt_inp)

    def extrair_urls_videos(self, resposta_json: Dict[str, Any]) -> List[str]:
        """
        Analisa a resposta da API do Flow e extrai todas as URLs de vídeo (.mp4 ou fife / videoUri).
        """
        texto = json.dumps(resposta_json)
        urls_mp4 = re.findall(r'https?://[^\s"\']+\.mp4[^\s"\']*', texto, re.I)
        uris = re.findall(r'"videoUri"\s*:\s*"(https?://[^"]+)"', texto, re.I)
        return list(set(urls_mp4 + uris))
