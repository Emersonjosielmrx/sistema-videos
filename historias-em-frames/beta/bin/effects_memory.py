# COMUM — fonte única: D:\hipercool-materiais\comum\effects_memory.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir effects_memory.py --de <projeto>
"""effects_memory.py — continuidade visual entre painéis (T4, porte do MemorySystem do n8n).

Hoje cada painel sorteia filtro/movimento isolado → vídeo "pula" de grading quente p/ frio.
Esta memória guarda as últimas N escolhas por categoria e PUXA a próxima pra perto da tendência
recente (continuidade), SEM engessar (continuidade é PESO, não trava: evita repetir idêntico).

Categorias: color_grading, movement_direction, atmosphere, pacing.
Uso: EffectsMemory() por VÍDEO (resetar em cada run_pipeline). record(cat,val) + suggest(cat,options).
Flag de uso no caller: EFFECTS_MEMORY=1. smoothingWindow=3 (config n8n).
"""
import os
import random

SMOOTHING_WINDOW = int(os.environ.get("EFFECTS_MEMORY_WINDOW", "3"))
# probabilidade de honrar a continuidade quando há tendência (resto = variação livre).
# continuidade é PESO, não trava (cuidado do doc: não engessar).
CONTINUITY_PROB = float(os.environ.get("EFFECTS_MEMORY_PROB", "0.7"))


class EffectsMemory:
    def __init__(self, window=None):
        self.window = window or SMOOTHING_WINDOW
        self.history = {}

    def reset(self):
        self.history = {}

    def record(self, category, value):
        h = self.history.setdefault(category, [])
        h.append(value)
        if len(h) > self.window:
            h.pop(0)

    def trend(self, category):
        """Valor mais recente da categoria (None se vazio)."""
        h = self.history.get(category)
        return h[-1] if h else None

    def _key(self, opt):
        """Chave de comparação de uma opção (dict usa 'name'/'speed'; senão o próprio valor)."""
        if isinstance(opt, dict):
            return opt.get("name") or opt.get("speed") or str(sorted(opt.items()))
        return opt

    def suggest(self, category, options):
        """Escolhe uma opção de `options` preferindo continuidade com a tendência recente,
        mas SEM repetir idêntico ao último e mantendo variação. Retorna a opção escolhida.
        Sempre faz record() do resultado."""
        if not options:
            return None
        tr = self.trend(category)
        choice = None
        # com tendência e dado o peso, tenta puxar pra perto — mas não idêntico ao último
        if tr is not None and random.random() < CONTINUITY_PROB:
            tr_key = self._key(tr)
            # similares = mesma "família" (mesmo speed, ou mesmo prefixo de nome) mas não idênticos
            similares = []
            for o in options:
                ok = self._key(o)
                if ok == tr_key:
                    continue  # evita repetir idêntico
                if isinstance(o, dict) and isinstance(tr, dict):
                    if o.get("speed") and o.get("speed") == tr.get("speed"):
                        similares.append(o)
                elif isinstance(ok, str) and isinstance(tr_key, str) and ok[:6] == tr_key[:6]:
                    similares.append(o)
            if similares:
                choice = random.choice(similares)
        if choice is None:
            # variação livre: qualquer opção != último
            pool = [o for o in options if self._key(o) != self._key(tr)] or list(options)
            choice = random.choice(pool)
        self.record(category, choice)
        return choice
