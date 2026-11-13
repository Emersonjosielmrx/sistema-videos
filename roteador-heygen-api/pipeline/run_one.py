# -*- coding: utf-8 -*-
"""run_one.py - executa o fluxo COMPLETO de geracao de UM video:
  1. garante avatar = emerson (se nao, troca via galeria Choose Avatar)
  2. garante Motion Engine = Avatar III (se nao, troca)
  3. limpa campo, cola texto via SendKeys Ctrl+V
  4. clica Render Scene e VERIFICA que rendering=true; se nao, re-clica
  5. espera "Scene rendered"
  6. pega URL do video e baixa MP4

Uso:
  python run_one.py 5000
  python run_one.py 30000
"""
import asyncio, json, os, sys, time, uuid, subprocess, tempfile
os.environ["PYTHONUTF8"] = "1"
import urllib.request
import websockets
from pathlib import Path

CDP_PORT = int(os.environ.get("HEYGEN_CDP_PORT", "9225"))
OUT = Path("D:/roteador-heygen-api/videos/api_jobs")


def flush(m):
    try:
        print("[" + time.strftime("%H:%M:%S") + "] " + str(m), flush=True)
    except UnicodeEncodeError:
        print("[" + time.strftime("%H:%M:%S") + "] " + str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def set_clipboard(text):
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tf.write(text); tf.close()
    ps = "Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 '{}')".format(tf.name.replace("\\", "\\\\"))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=30)
    os.unlink(tf.name)
    return r.returncode == 0


def sendkeys_paste():
    ps = r'''
Add-Type -AssemblyName System.Windows.Forms
$p = Get-Process chrome | Where-Object { $_.MainWindowTitle -ne "" } | Select-Object -First 1
if ($p) {
  Add-Type @"
using System;using System.Runtime.InteropServices;
public class Win{[DllImport("user32.dll")]public static extern bool SetForegroundWindow(IntPtr h);}
"@
  [Win]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
  Start-Sleep -Milliseconds 700
  [System.Windows.Forms.SendKeys]::SendWait("^v")
  "OK"
} else { "NO_WINDOW" }
'''
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=30, text=True)
    return (r.stdout or "").strip()


BASE = """Fala, galera! Hoje, eu vou mostrar para vocês algo que está revolucionando a forma como programadores trabalham. O Cláudi Cód é uma ferramenta de inteligência artificial, que funciona direto no seu editor de có-di-go, como o Visiual Studio Code. Diferente de um simples autocompletar, ele entende o contexto inteiro do seu projeto. Você pode pedir para ele criar funções complexas, refatorar có-di-go le-ga-do, escrever testes automatizados, e até de-bug-ar problemas que você levaria horas para encontrar. O mais impressionante é que ele lembra do que você já fez na conversa, e mantém pad-rão de consistência. Por exemplo, se você definiu um pad-rão de arquitetura no início, ele vai seguir esse pad-rão em todo có-di-go que gerar depois. Ele tam-bém consegue executar comandos no terminal, ler arquivos, fazer buscas no projeto, e até criar com-mits no Git Húb. Isso significa que você pode dar uma tarefa complexa, tipo implemen-tar autenticação O-Auth, e ele vai fazer tudo do zero até os testes passarem. A produtividade aumenta absurdo, porque você foca nas decisões de design, enquanto a I A cuida da implementação. Programadores que adotaram essa ferra-men-ta relatam economia de três a cinco horas por dia em tarefas repetitivas. E o melhor, quanto mais você usa, mais ele aprende suas preferências e estilo de có-di-go. O fu-turo da programação já chegou, e quem não se adaptar, vai ficar para trás. """


def build_text(target_chars):
    from tts_fixes import apply_fixes
    out = []
    cur = 0
    i = 0
    while cur < target_chars:
        # adiciona apenas quebra de paragrafo, SEM o marcador '[Bloco N]'
        chunk = BASE + "\n\n"
        out.append(chunk); cur += len(chunk); i += 1
    raw = "".join(out)[:target_chars]
    return apply_fixes(raw)


class CDP:
    def __init__(self, ws):
        self.ws = ws; self.cid = 0; self.pending = {}; self._stop = False

    async def _pump(self):
        while not self._stop:
            try:
                raw = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except Exception:
                return
            d = json.loads(raw)
            if "id" in d and d["id"] in self.pending:
                f = self.pending.pop(d["id"])
                if not f.done(): f.set_result(d)

    async def cmd(self, m, p=None, t=20):
        self.cid += 1; cid = self.cid
        fut = asyncio.get_event_loop().create_future()
        self.pending[cid] = fut
        await self.ws.send(json.dumps({"id": cid, "method": m, "params": p or {}}))
        try:
            return await asyncio.wait_for(fut, timeout=t)
        except asyncio.TimeoutError:
            self.pending.pop(cid, None); return None

    async def js(self, e, t=20):
        r = await self.cmd("Runtime.evaluate", {"expression": e, "returnByValue": True}, t)
        if r and "result" in r and "result" in r["result"]:
            return r["result"]["result"].get("value")
        return None

    async def click(self, x, y):
        # CDP clique direito: move, press, pause, release. Sem pausa o dropdowns
        # pode abrir entre press e release e o release cai na opcao abaixo.
        await self.cmd("Input.dispatchMouseEvent", {"type":"mouseMoved","x":x,"y":y})
        await asyncio.sleep(0.05)
        await self.cmd("Input.dispatchMouseEvent", {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
        await asyncio.sleep(0.08)
        await self.cmd("Input.dispatchMouseEvent", {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})

    async def wait_editor(self, secs=40):
        for i in range(secs):
            r = await self.js('(function(){var b=document.querySelectorAll("button");for(var i=0;i<b.length;i++){if((b[i].textContent||"").indexOf("Render Scene")>=0)return "ok";}return "no";})()')
            if r == "ok":
                return True
            await asyncio.sleep(2)
        return False

    async def state_str(self):
        return await self.js('(function(){var els=document.querySelectorAll("*");var r=false,d=false,pct="",scn="";for(var i=0;i<els.length;i++){var e=els[i];if(e.children.length>0)continue;var t=(els[i].textContent||"").trim();if(t==="Scene rendered")d=true;if(t==="Rendering"||t==="Rendering...")r=true;if(/^\\d{1,3}%$/.test(t))pct=t;if(/^\\d+:\\d+$/.test(t))scn=t;}return JSON.stringify({r:r,d:d,pct:pct,scn:scn});})()')

    async def current_avatar(self):
        # checa o ATIVO no card 'Avatar & Voice' do painel direito (y 140-220,
        # x 1470-1830). Antes pegava x>1200 y<300 w 30-80 que enganava caindo
        # nas miniaturas da library lateral (Annie em Tan Jacket etc).
        cur = await self.js(
            '(function(){var imgs=document.querySelectorAll("img[alt]");'
            'for(var i=0;i<imgs.length;i++){var a=(imgs[i].getAttribute("alt")||"").trim();'
            'if(!a||imgs[i].offsetParent===null)continue;'
            'var r=imgs[i].getBoundingClientRect();'
            'if(r.x>1470&&r.x<1830&&r.y>130&&r.y<220&&r.width>=30&&r.width<=60)return a.toLowerCase();}'
            'return "";})()')
        if cur: return cur
        # fallback: texto do card Avatar & Voice (captura 'emerson' / 'emerson2' etc)
        return await self.js(
            '(function(){var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null);'
            'var n;while(n=w.nextNode()){var t=(n.textContent||"").trim().toLowerCase();'
            'if(!t)continue;var p=n.parentElement;if(!p||p.offsetParent===null)continue;'
            'var r=p.getBoundingClientRect();'
            'if(r.x>1470&&r.x<1830&&r.y>130&&r.y<220&&r.width<250)return t;}return "";})()') or ""

    async def ensure_avatar_emerson(self, max_tries=3):
        """Garante que o avatar ativo e emerson. Abre o modal 'Choose Avatar'
        clicando na miniatura (thumbnail) do avatar no painel esquerdo
        'Avatar & Voice' (o React do HeyGen precisa de hover ANTES do clique pra
        registrar), busca 'emerson' no input Search e clica no card.
        NAO usar o icone 'Avatar' da toolbar direita: ele so alterna o painel."""
        TARGET = "emerson"
        for attempt in range(1, max_tries + 1):
            cur = await self.current_avatar()
            flush("[avatar] tentativa " + str(attempt) + " atual='" + cur + "'")
            if cur == TARGET:
                flush("[avatar] ja e emerson")
                return True
            await self.cmd("Page.bringToFront")
            # 1) acha a miniatura (img[alt]) do avatar no painel esquerdo. Mesma
            #    regiao que current_avatar() usa (x>1200, y<300, w 30-80) pra nao
            #    divergir. Retorna centro da imagem p/ clique e centro do card
            #    (imagem + 150px a direita) p/ hover que prime o React.
            thumb = await self.js(
                '(function(){var els=document.querySelectorAll("img[alt]");'
                'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
                'var r=e.getBoundingClientRect();'
                'if(r.x>1200&&r.y<300&&r.width>=30&&r.width<=80){'
                'return JSON.stringify({ix:Math.round(r.x+r.width/2),iy:Math.round(r.y+r.height/2),'
                'cx:Math.round(r.x+r.width/2+150),cy:Math.round(r.y+r.height/2)});}}return null;})()')
            if not thumb:
                flush("[avatar] miniatura do avatar no painel esquerdo nao encontrada")
                await asyncio.sleep(1); continue
            tp = json.loads(thumb)
            # 2) HOVER no card (prime o React) e depois clica na miniatura
            await self.cmd("Input.dispatchMouseEvent", {"type":"mouseMoved","x":tp["cx"],"y":tp["cy"]})
            await asyncio.sleep(1.2)
            await self.click(tp["ix"], tp["iy"])
            await asyncio.sleep(2.5)
            # 3) confirma que modal "Choose Avatar" abriu
            modal_ok = await self.js(
                '(function(){var el=document.querySelectorAll("h1,h2,h3,div,span");'
                'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
                'if(t==="Choose Avatar"&&el[i].offsetParent!==null)return true;}return false;})()')
            if not modal_ok:
                flush("[avatar] modal Choose Avatar nao abriu")
                await asyncio.sleep(1); continue
            # 4) garante aba "My Avatars" ativa (mouse real). Abas: Recently Used
            #    (547,214), My Avatars (674,214), Public Avatars (782,214).
            tab_pos = await self.js(
                '(function(){var el=document.querySelectorAll("button,div,span");'
                'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
                'var r=el[i].getBoundingClientRect();'
                'if(t==="My Avatars"&&r.x>600&&r.x<800&&r.y>200&&r.y<230&&el[i].offsetParent!==null){'
                'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}}return null;})()')
            if tab_pos:
                tp2 = json.loads(tab_pos)
                await self.click(tp2["x"], tp2["y"])
                await asyncio.sleep(1.5)
            # 5) acha o search input (placeholder "Search") dentro do modal
            #    (confirmado em @(547,259) w=827, dentro do modal y 200-300).
            search = await self.js(
                '(function(){var ins=document.querySelectorAll("input");'
                'for(var i=0;i<ins.length;i++){var r=ins[i].getBoundingClientRect();'
                'if((ins[i].placeholder||"").toLowerCase()==="search"&&r.width>200'
                '&&r.y>230&&r.y<300&&ins[i].offsetParent!==null){'
                'return JSON.stringify({x:Math.round(r.x+20),y:Math.round(r.y+r.height/2)});}}return null;})()')
            if not search:
                flush("[avatar] input search nao encontrado")
                await asyncio.sleep(1); continue
            p = json.loads(search)
            await self.click(p["x"], p["y"])
            await asyncio.sleep(0.3)
            # 5) digita via native setter (React controlled input)
            ok = await self.js(
                '(function(){var ins=document.querySelectorAll("input");'
                'var target=null;for(var i=0;i<ins.length;i++){'
                'if((ins[i].placeholder||"").toLowerCase()==="search"&&ins[i].offsetParent!==null)target=ins[i];}'
                'if(!target)return "no";'
                'var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;'
                'ns.call(target,"' + TARGET + '");'
                'target.dispatchEvent(new Event("input",{bubbles:true}));'
                'target.dispatchEvent(new Event("change",{bubbles:true}));'
                'return "ok";})()')
            if ok != "ok":
                flush("[avatar] nao consegui digitar no search")
                await asyncio.sleep(1); continue
            await asyncio.sleep(2)
            # 6) espera o card TARGET aparecer no resultado. Clica na MINIATURA
            #    (img[alt~emerson], ~76x76 em y>300) que e o elemento clicavel.
            #    Confirmado: img alt='emerson' centro ~(596,366).
            card = await self.js(
                '(function(){var e=document.querySelectorAll("img[alt]");'
                'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
                'var a=(e[i].getAttribute("alt")||"").toLowerCase();'
                'if(a.indexOf("' + TARGET + '")<0)continue;var r=e[i].getBoundingClientRect();'
                'if(r.x>400&&r.y>300&&r.y<700&&r.width>=40)'
                'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}return null;})()')
            if not card:
                flush("[avatar] card " + TARGET + " nao apareceu no resultado")
                # limpa search pra proxima tentativa
                await self.js(
                    '(function(){var ins=document.querySelectorAll("input");'
                    'for(var i=0;i<ins.length;i++){'
                    'if((ins[i].placeholder||"").toLowerCase()==="search"&&ins[i].offsetParent!==null){'
                    'var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;'
                    'ns.call(ins[i],"");ins[i].dispatchEvent(new Event("input",{bubbles:true}));}}}return 1;})()')
                await asyncio.sleep(1); continue
            p = json.loads(card)
            await self.click(int(p["x"]), int(p["y"]))
            await asyncio.sleep(3)
            # 7) fecha modal com Escape (botao X nao tem aria-label confiavel)
            await self.cmd("Input.dispatchKeyEvent", {"type":"keyDown","key":"Escape","windowsVirtualKeyCode":27})
            await self.cmd("Input.dispatchKeyEvent", {"type":"keyUp","key":"Escape","windowsVirtualKeyCode":27})
            await asyncio.sleep(1.5)
            # 8) re-verifica
            cur = await self.current_avatar()
            flush("[avatar] pos-troca tentativa " + str(attempt) + " = " + cur)
            if cur == TARGET:
                flush("[avatar] emerson garantido")
                return True
            await asyncio.sleep(1)
        return False

    async def dismiss_plan_modal(self, max_tries=2):
        """Fecha o modal 'Plans that fit your scale' (upsell) que aparece as
        vezes quando tenta renderizar com plano Free. Procura botao X ou
        link 'Looking for API plans?' X. Clica e checa se fechou."""
        for attempt in range(1, max_tries + 1):
            # heuristica: o modal tem o texto 'Plans that fit your scale' E
            # um dos precos ('/mo')
            detected = await self.js(
                '(function(){var t=document.body.innerText||"";'
                'if(t.indexOf("Plans that fit your scale")>=0||t.indexOf("Most Popular")>=0)return "plans";'
                'if(t.indexOf("Upgrade to")>=0||t.indexOf("upgrade to")>=0)return "upgrade";'
                'return "";})()')
            if not detected:
                return True
            flush("[plan-modal] tentativa " + str(attempt) + ": " + detected)
            # 1) tenta X classico no canto superior direito do modal
            # confirmado: rc-dialog-close aria-label='Close' @(1367,66) 40x40
            x = await self.js(
                '(function(){var b=document.querySelectorAll("button,svg,[role=button]");'
                'for(var i=0;i<b.length;i++){if(b[i].offsetParent===null)continue;'
                'var al=(b[i].getAttribute("aria-label")||"").toLowerCase();'
                'var cls=(b[i].className||"").toString().toLowerCase();'
                'var r=b[i].getBoundingClientRect();'
                'if((al.indexOf("close")>=0||cls.indexOf("dialog-close")>=0||cls.indexOf("modal-close")>=0)'
                '&&r.width<=50&&r.height<=50&&r.x>1300&&r.x<1450&&r.y>30&&r.y<200)'
                'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}return null;})()')
            if not x:
                # 2) tenta botao 'Looking for API plans?' X (geralmente ao lado)
                x = await self.js(
                    '(function(){var b=document.querySelectorAll("button,svg");'
                    'for(var i=0;i<b.length;i++){if(b[i].offsetParent===null)continue;'
                    'var al=(b[i].getAttribute("aria-label")||"").toLowerCase();'
                    'var r=b[i].getBoundingClientRect();'
                    'if((al.indexOf("close")>=0||al.indexOf("fechar")>=0)&&r.width<40&&r.height<40)'
                    'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}return null;})()')
            if not x:
                # 3) Escape
                await self.cmd("Input.dispatchKeyEvent", {"type":"keyDown","key":"Escape","windowsVirtualKeyCode":27})
                await self.cmd("Input.dispatchKeyEvent", {"type":"keyUp","key":"Escape","windowsVirtualKeyCode":27})
            else:
                p = json.loads(x)
                await self.click(p["x"], p["y"])
            await asyncio.sleep(1.5)
        detected = await self.js(
            '(function(){var t=document.body.innerText||"";'
            'if(t.indexOf("Plans that fit your scale")>=0||t.indexOf("Most Popular")>=0)return "plans";return "";})()')
        if detected:
            flush("[plan-modal] nao foi possivel fechar")
            return False
        flush("[plan-modal] fechado")
        return True


    async def ensure_av3(self):
        s = await self.js('(function(){var b=document.querySelectorAll("button");for(var i=0;i<b.length;i++){var t=(b[i].textContent||"").trim();if(t==="Avatar III")return "iii";if(t==="Avatar IV")return "iv";if(t==="Avatar V")return "v";}return "none";})()')
        if s == "iii":
            flush("[me] ja e Avatar III")
            return True
        flush("[me] precisa trocar pra Avatar III (atual: " + s + ")")
        # clica no CARET/SVG da direita do seletor (botao SVG na extremidade
        # direita). React dropdowns costumam exigir clique no icone de seta,
        # nao no texto. Localizado em x~1817 y~370 (SVG w 20-30).
        btn = await self.js(
            '(function(){var els=document.querySelectorAll("svg,button,div");'
            'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
            'var r=e.getBoundingClientRect();'
            'if(r.x>1800&&r.x<1830&&r.y>360&&r.y<390&&r.width<=30&&r.height<=30){'
            'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}}'
            'return null;})()')
        if not btn:
            # fallback: clica no centro do botao Avatar IV/V (texto)
            btn = await self.js(
                '(function(){var els=document.querySelectorAll("button");'
                'for(var i=0;i<els.length;i++){var t=(els[i].textContent||"").trim();'
                'if((t==="Avatar IV"||t==="Avatar V")&&els[i].offsetWidth>100){'
                'var r=els[i].getBoundingClientRect();'
                'return JSON.stringify({x:Math.round(r.x+r.width-30),y:Math.round(r.y+r.height/2)});}}return null;})()')
        if not btn: return False
        p = json.loads(btn); await self.cmd("Page.bringToFront"); await asyncio.sleep(0.3)
        await self.click(p["x"], p["y"]); await asyncio.sleep(1.5)
        # opcao Avatar III no dropdown aberto (span/div). O dropdown abre logo
        # abaixo do seletor (y 370 confirmado), entao y 380-550.
        op = await self.js(
            '(function(){var els=document.querySelectorAll("span,div,button");'
            'for(var i=0;i<els.length;i++){var t=(els[i].textContent||"").trim();'
            'if(t==="Avatar III"&&els[i].offsetParent!==null&&els[i].offsetWidth>50){'
            'var r=els[i].getBoundingClientRect();'
            'if(r.y>380&&r.y<600)return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}}return null;})()')
        if not op:
            flush("[me] opcao Avatar III no dropdown nao encontrada")
            return False
        p = json.loads(op); await self.click(p["x"], p["y"]); await asyncio.sleep(1.5)
        flush("[me] trocado pra Avatar III")
        return True

    async def paste_text(self, text):
        flush("[paste] " + str(len(text)) + " chars")
        # foca o contenteditable
        await self.cmd("Page.bringToFront")
        await asyncio.sleep(0.5)
        await self.js('(function(){var pm=document.querySelector("[contenteditable=true]");if(pm){pm.focus();pm.click();}return "ok";})()')
        await asyncio.sleep(0.3)
        # limpa com Ctrl+A + Delete
        await self.cmd("Input.dispatchKeyEvent", {"type":"keyDown","key":"a","code":"KeyA","modifiers":2})
        await self.cmd("Input.dispatchKeyEvent", {"type":"keyUp","key":"a","code":"KeyA","modifiers":2})
        await self.cmd("Input.dispatchKeyEvent", {"type":"keyDown","key":"Delete","code":"Delete"})
        await self.cmd("Input.dispatchKeyEvent", {"type":"keyUp","key":"Delete","code":"Delete"})
        await asyncio.sleep(0.4)
        # injeccao via synthetic ClipboardEvent (TipTap/ProseMirror reage a paste event)
        # text precisa ser JSON-escaped
        ok = await self.js(
            '(function(){var pm=document.querySelector("[contenteditable=true]");if(!pm)return "no";'
            'pm.focus();'
            'var dt=new DataTransfer();'
            'dt.setData("text/plain", ' + json.dumps(text) + ');'
            'var ev=new ClipboardEvent("paste",{clipboardData:dt,bubbles:true,cancelable:true});'
            'pm.dispatchEvent(ev);'
            'return "ok";})()')
        flush("[paste] event: " + str(ok))
        await asyncio.sleep(2)
        got = await self.js('(function(){var pm=document.querySelector("[contenteditable=true]");return pm?(pm.textContent||"").length:0;})()')
        got = got or 0
        flush("[paste] campo " + str(got) + "/" + str(len(text)) + " (" + str(round(got / len(text) * 100)) + "%)")
        return got

    async def click_render_with_verify(self, max_attempts=5):
        """Clica Render Scene e VERIFICA que rendering=true. Re-clica se nao mudar.
        Retorna True se iniciou o render. Antes de cada tentativa, fecha
        modal 'Plans that fit your scale' (upsell do plano Free) se aparecer."""
        for attempt in range(1, max_attempts + 1):
            await self.dismiss_plan_modal()
            pos = await self.js(
                '(function(){var b=document.querySelectorAll("button");'
                'for(var i=0;i<b.length;i++){var t=(b[i].textContent||"").trim();'
                'if(t.indexOf("Render Scene")>=0){'
                'var r=b[i].getBoundingClientRect();'
                'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),disabled:b[i].disabled});}}'
                'return null;})()')
            if not pos:
                flush("[render] (tentativa " + str(attempt) + ") Render Scene nao encontrado")
                await asyncio.sleep(1)
                continue
            p = json.loads(pos)
            flush("[render] (tentativa " + str(attempt) + ") Render Scene disabled=" + str(p.get("disabled")))
            await self.click(p["x"], p["y"])
            await asyncio.sleep(2)
            s = json.loads(await self.state_str() or "{}")
            if s.get("r"):
                flush("[render] clicado e VERIFICADO rendering=true (tentativa " + str(attempt) + ")")
                return True
            flush("[render] (tentativa " + str(attempt) + ") clicou mas rendering ainda false")
        return False

    async def wait_render(self, max_wait=3000):
        flush("[render] esperando Scene rendered (max " + str(max_wait // 60) + " min)")
        for i in range(max_wait // 10):
            s = json.loads(await self.state_str() or "{}")
            if s.get("d"):
                return True
            if i > 0 and i % 6 == 0:
                flush("[render] " + str(i * 10) + "s...")
            await asyncio.sleep(10)
        return False

    async def get_video_url(self):
        return await self.js(
            '(function(){var videos=document.querySelectorAll("video");'
            'for(var i=0;i<videos.length;i++){var s=videos[i].src;'
            'if(s&&s.indexOf("blob:")!==0)return s;}'
            'var links=document.querySelectorAll("a[href*=mp4],a[href*=amazonaws]");'
            'for(var i=0;i<links.length;i++){return links[i].href;}'
            'return "";})()')


EDITOR_URL = "https://app.heygen.com/create-v4"


async def run(target_chars, force_av3=True):
    tag = "emerson_" + str(target_chars // 1000) + "k"
    flush("=== TARGET " + str(target_chars) + " chars -> " + tag + " ===")

    # 0. garante sessao logada (reloga sozinho se expirou)
    try:
        from auto_login import ensure_login
        if not await ensure_login():
            flush("[ERRO] nao consegui garantir login"); return False
    except Exception as e:
        flush("[login] aviso: auto_login falhou (" + str(e)[:60] + ") - seguindo assim mesmo")

    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    tab = next((t for t in tabs if 'app.heygen.com' in t.get('url','') and t.get('type') == 'page'), tabs[0])
    async with websockets.connect(tab['webSocketDebuggerUrl'], max_size=200*1024*1024, ping_interval=None, ping_timeout=None) as ws:
        c = CDP(ws)
        pump = asyncio.create_task(c._pump())
        await c.cmd("Page.enable")
        await c.cmd("Runtime.enable")
        # 1. garante que estamos no editor (navega se preciso)
        cur = await c.js("location.href") or ""
        if "create-v4" not in cur or "panel=scene" not in cur:
            flush("[nav] indo pro editor")
            await c.cmd("Page.navigate", {"url": EDITOR_URL + "?panel=scene"})
            await asyncio.sleep(5)
        if not await c.wait_editor(60):
            flush("[ERRO] editor nao carregou"); c._stop = True; await pump; return False
        # editor React handlers precisam de ~30s a mais para hidratar pos-load
        # wait_editor soh confirma que Render Scene existe no DOM, mas os handlers
        # dos botoes ainda nao estao prontos nessa hora (HeyGen carrega em etapas)
        await asyncio.sleep(30)
        # avatar (aceita emerson/emerson2/emerson3 etc)
        atual = await c.current_avatar()
        flush("[avatar] atual=" + str(atual))
        if not atual.startswith("emerson"):
            flush("[avatar] precisa trocar pra emerson (atual: " + str(atual) + ") - trocando sozinho")
            if not await c.ensure_avatar_emerson():
                flush("[ERRO] nao foi possivel garantir avatar emerson")
                c._stop = True; await pump; return False
            # re-verifica
            atual = await c.current_avatar()
            flush("[avatar] pos-troca=" + str(atual))
            if not atual.startswith("emerson"):
                flush("[ERRO] avatar ainda nao e emerson apos tentativa")
                c._stop = True; await pump; return False
        # motion: soh troca se force_av3 (default True). Em cota-test o Avatar IV
        # default ja basta, e forcar III no Free abre paywall.
        if force_av3:
            if not await c.ensure_av3():
                flush("[ERRO] nao foi possivel garantir Avatar III")
                c._stop = True; await pump; return False
        else:
            flush("[me] pulando troca pra Avatar III (force_av3=False)")
        # paste
        text = build_text(target_chars)
        got = await c.paste_text(text)
        if got < target_chars * 0.95:
            flush("[ERRO] paste incompleto (" + str(got) + "/" + str(target_chars) + ")")
            c._stop = True; await pump; return False
        # clique com verificacao
        if not await c.click_render_with_verify():
            flush("[ERRO] Render Scene nao iniciou apos 5 tentativas")
            c._stop = True; await pump; return False
        # espera
        if not await c.wait_render(max_wait=3000):
            flush("[ERRO] timeout esperando Scene rendered")
            c._stop = True; await pump; return False
        flush("[render] DONE")
        # url
        url = await c.get_video_url()
        if not url:
            flush("[ERRO] url do video nao encontrada")
            c._stop = True; await pump; return False
        flush("[dl] " + str(url)[:80])
        # baixa via urllib (com User-Agent do chrome)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=1200) as r:
                body = r.read()
            mb = len(body) / (1024 * 1024)
            out = OUT / (tag + "_" + uuid.uuid4().hex[:5] + ".mp4")
            out.write_bytes(body)
            flush("[OK] " + out.name + " (" + str(round(mb, 1)) + "MB)")
            c._stop = True; await pump
            return True
        except Exception as e:
            flush("[dl ERRO] " + str(e))
            c._stop = True; await pump
            return False


if __name__ == "__main__":
    import sys as _s
    target = int(_s.argv[1]) if len(_s.argv) > 1 else 5000
    force = "--no-av3" not in _s.argv
    asyncio.run(run(target, force_av3=force))
