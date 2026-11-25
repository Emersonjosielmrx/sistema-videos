r"""Liga permissões no caso de uso "Gerenciar tudo na sua Página" do app da conta (25/11/2026), pelo Chrome da conta.

    python fb_app_permissao.py <conta> pages_manage_posts pages_read_engagement read_insights

Abre developers.facebook.com/apps/<app_id>/use_cases/, pega o HREF do "Personalizar" (o clique não abre pela automação),
e clica "+ Adicionar" na LINHA de cada permissão. Linha com "Ações" = já adicionada. Print: logs\fb_app_<conta>_perm.png.
"""
import json
import sys
import time

sys.path.insert(0, r"D:\postador-de-videos\bin")
import fb_token_auto as t  # noqa: E402  (com_chrome: trava da conta + Chrome na saída fixa)

JS = """(perm) => {
  const tits = [...document.querySelectorAll('*')].filter(e => e.childElementCount===0 && e.textContent.trim()===perm);
  for (const ti of tits) {
    let n = ti;
    for (let k=0; k<8 && n; k++, n=n.parentElement) {
      const bts = [...n.querySelectorAll('[role=button],button')].filter(b => /Adicionar|Ações|Add|Actions/.test(b.textContent));
      if (bts.length === 1) return {estado: bts[0].textContent.trim(), idx: [...document.querySelectorAll('[role=button],button')].indexOf(bts[0])};
      if (bts.length > 1) break;
    }
  }
  return null;
}"""


def ligar(conta, perms):
    aid = json.loads((t.SEC / f"fb_app_{conta}.json").read_text(encoding="utf-8"))["app_id"]

    def fazer(ctx):
        pg = ctx.new_page()
        pg.set_viewport_size({"width": 1366, "height": 1000})
        pg.goto(f"https://developers.facebook.com/apps/{aid}/use_cases/", wait_until="domcontentloaded", timeout=120000)
        time.sleep(12)
        href = next((a.get_attribute("href") or "" for a in pg.locator("a").all()
                     if "use_case_enum=PAGES_API" in (a.get_attribute("href") or "")), None)
        if not href:
            print("não achei o caso de uso 'Gerenciar tudo na sua Página' neste app")
            pg.screenshot(path=str(t.LOGS / f"fb_app_{conta}_perm.png")); return
        pg.goto(href if href.startswith("http") else "https://developers.facebook.com" + href,
                wait_until="domcontentloaded", timeout=120000)
        time.sleep(15)
        c = pg.get_by_role("button", name="Concluir")
        if c.count():
            c.first.click(); time.sleep(2)
        for perm in perms:
            r = pg.evaluate(JS, perm)
            if not r:
                print(f"{perm}: não aparece na lista deste caso de uso"); continue
            if "Adicionar" in r["estado"] or "Add" in r["estado"]:
                bt = pg.locator("[role=button],button").nth(r["idx"])
                bt.scroll_into_view_if_needed(); time.sleep(1); bt.click(); time.sleep(6)
                d = pg.get_by_role("dialog")
                if d.count():
                    for nb in ("Adicionar", "Confirmar", "Continuar", "Salvar"):
                        b = d.last.get_by_role("button", name=nb)
                        if b.count():
                            b.last.click(); time.sleep(5); break
                r = pg.evaluate(JS, perm)
            print(f"{perm}: {'ligada' if r and ('Ações' in r['estado'] or 'Actions' in r['estado']) else 'NÃO ligou'}")
        pg.screenshot(path=str(t.LOGS / f"fb_app_{conta}_perm.png"))
        pg.close()

    t.com_chrome(conta, fazer)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ligar(sys.argv[1], sys.argv[2:])
