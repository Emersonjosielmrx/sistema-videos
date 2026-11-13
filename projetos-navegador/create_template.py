import re

html_to_append = '''<div class="panel" id="panel-config">
  <div class="sec">
    <h2>Configurações do Robô <span id="cfg-status">Carregando...</span></h2>
    <div class="cfg-grid">
      <div class="cfg-row"><label>Workers:</label><input type="range" id="c_workers" min="1" max="25" oninput="document.getElementById('wv').innerText=this.value"><span id="wv">5</span></div>
      <div class="cfg-row"><label>Modo:</label><select id="c_mode"><option value="both">Likes + Comentários</option><option value="likes">Apenas Likes</option><option value="comments">Apenas Comentários</option></select></div>
      <div class="cfg-row"><label>Sleep Min (s):</label><input type="number" id="c_sleep_min" step="0.5"></div>
      <div class="cfg-row"><label>Sleep Max (s):</label><input type="number" id="c_sleep_max" step="0.5"></div>
      <div class="cfg-row"><label>Lote p/ Conta:</label><input type="number" id="c_batch"></div>
      <div class="cfg-row"><label>Máx Ações/Dia:</label><input type="number" id="c_max_dia"></div>
      <div class="cfg-row"><label>Hora Início:</label><input type="number" id="c_hr_st" min="0" max="23"></div>
      <div class="cfg-row"><label>Hora Fim:</label><input type="number" id="c_hr_en" min="0" max="23"></div>
      <div class="cfg-row" style="grid-column:1/-1"><label>Prioridade:</label><input type="text" id="c_priority" placeholder="Ex: @seucanal ou palavra chave" style="width:100%"></div>
      <div class="cfg-row" style="grid-column:1/-1"><label>Comentários Extras (1/linha):</label><textarea id="c_com_extra"></textarea></div>
      <div class="cfg-row" style="grid-column:1/-1"><label>Blacklist Canais (vírgula):</label><textarea id="c_bl_chan"></textarea></div>
      <div class="cfg-row" style="grid-column:1/-1"><label>Blacklist Vídeos IDs (vírgula):</label><textarea id="c_bl_vid"></textarea></div>
      <div class="cfg-row" style="grid-column:1/-1"><label>Proxies Adicionais:</label><textarea id="c_proxies"></textarea></div>
      <div class="cfg-row" style="grid-column:1/-1"><label><input type="checkbox" id="c_rand"> <span>Randomizar Ordem dos Vídeos (anti-padrão)</span></label></div>
    </div>
    <div class="cfg-actions">
      <button class="btn active" onclick="saveConfig()">Salvar e Aplicar (Hot-Reload)</button>
      <button class="btn" onclick="postCmd('/pause')" id="btnPause">Pausar Robô</button>
      <button class="btn" onclick="postCmd('/restart')">Reiniciar (Soft)</button>
      <button class="btn red" onclick="postCmd('/stop')">Parada de Emergência</button>
      <button class="btn yellow" onclick="if(confirm('Zerar contador e logs da tela?')) postCmd('/clear-progress')">Limpar Tela</button>
    </div>
  </div>
</div>

<script>
const TABS = ["canais","videos","contas","log","erros","config"];
let RAW_DATA = null;
let FILTER_HOURS = 9999;
let IS_PAUSED = false;

function switchTab(t){
  document.querySelectorAll(".tab").forEach((e,i)=>e.classList.toggle("active",TABS[i]===t));
  document.querySelectorAll(".panel").forEach(e=>e.classList.remove("active"));
  document.getElementById("panel-"+t).classList.add("active");
  if(t==="config") loadConfig();
}

function postCmd(path) {
  fetch(path, {method:"POST"}).then(r=>r.json()).then(d=>{
    if(path==="/pause") {
      IS_PAUSED = d.paused;
      document.getElementById("btnPause").innerText = IS_PAUSED ? "Retomar Robô" : "Pausar Robô";
      document.getElementById("btnPause").className = IS_PAUSED ? "btn yellow" : "btn";
    } else {
      document.getElementById("cfg-status").innerText = d.msg; setTimeout(()=>document.getElementById("cfg-status").innerText="", 3000);
    }
  }).catch(e=>alert("Erro de conexão"));
}

function loadConfig() {
  document.getElementById("cfg-status").innerText = "Carregando...";
  fetch("/config").then(r=>r.json()).then(d=>{
    document.getElementById("c_workers").value = d.workers||5;
    document.getElementById("wv").innerText = d.workers||5;
    document.getElementById("c_sleep_min").value = d.sleep_min||2;
    document.getElementById("c_sleep_max").value = d.sleep_max||8;
    document.getElementById("c_batch").value = d.batch||500;
    document.getElementById("c_max_dia").value = d.max_per_account_day||200;
    if(d.active_hours) { document.getElementById("c_hr_st").value = d.active_hours[0]; document.getElementById("c_hr_en").value = d.active_hours[1]; }
    document.getElementById("c_mode").value = d.mode||"both";
    document.getElementById("c_priority").value = d.priority||"";
    document.getElementById("c_bl_chan").value = (d.blacklist_channels||[]).join(", ");
    document.getElementById("c_bl_vid").value = (d.blacklist_videos||[]).join(", ");
    document.getElementById("c_proxies").value = (d.proxies||[]).join("\\n");
    document.getElementById("c_com_extra").value = (d.comments_extra||[]).join("\\n");
    document.getElementById("c_rand").checked = d.randomize_order !== false;
    IS_PAUSED = d.paused || false;
    document.getElementById("btnPause").innerText = IS_PAUSED ? "Retomar Robô" : "Pausar Robô";
    document.getElementById("btnPause").className = IS_PAUSED ? "btn yellow" : "btn";
    document.getElementById("cfg-status").innerText = "";
  });
}

function saveConfig() {
  const d = {
    workers: parseInt(document.getElementById("c_workers").value),
    sleep_min: parseFloat(document.getElementById("c_sleep_min").value),
    sleep_max: parseFloat(document.getElementById("c_sleep_max").value),
    batch: parseInt(document.getElementById("c_batch").value),
    max_per_account_day: parseInt(document.getElementById("c_max_dia").value),
    active_hours: [parseInt(document.getElementById("c_hr_st").value), parseInt(document.getElementById("c_hr_en").value)],
    mode: document.getElementById("c_mode").value,
    priority: document.getElementById("c_priority").value,
    blacklist_channels: document.getElementById("c_bl_chan").value.split(",").map(x=>x.trim()).filter(x=>x),
    blacklist_videos: document.getElementById("c_bl_vid").value.split(",").map(x=>x.trim()).filter(x=>x),
    proxies: document.getElementById("c_proxies").value.split("\\n").map(x=>x.trim()).filter(x=>x),
    comments_extra: document.getElementById("c_com_extra").value.split("\\n").map(x=>x.trim()).filter(x=>x),
    randomize_order: document.getElementById("c_rand").checked,
    paused: IS_PAUSED
  };
  document.getElementById("cfg-status").innerText = "Salvando...";
  fetch("/save-config", {method:"POST", body: JSON.stringify(d)}).then(r=>r.json()).then(res=>{
    document.getElementById("cfg-status").innerText = "Salvo com sucesso!";
    setTimeout(()=>document.getElementById("cfg-status").innerText="", 3000);
  });
}

function filterTable(inp, tid){
  const q = inp.value.toLowerCase();
  const rows = document.getElementById(tid).querySelectorAll("tr:not(:first-child)");
  rows.forEach(r => {
    r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
  });
}
function sortCol(tid, idx){
  const tb = document.getElementById(tid);
  const rows = Array.from(tb.querySelectorAll("tr:not(:first-child)"));
  const isNum = !isNaN(rows[0].children[idx].innerText.split("/")[0]);
  rows.sort((a,b) => {
    let v1 = a.children[idx].innerText; let v2 = b.children[idx].innerText;
    if(isNum){ v1 = parseFloat(v1.split("/")[0])||0; v2 = parseFloat(v2.split("/")[0])||0; return v2 - v1; }
    return v1.localeCompare(v2);
  });
  rows.forEach(r => tb.appendChild(r));
}
function filterLang(sel, tid){
  const v = sel.value;
  const rows = document.getElementById(tid).querySelectorAll("tr:not(:first-child)");
  rows.forEach(r => {
    const langCell = r.querySelector(".lb");
    r.style.display = (!v || (langCell && langCell.innerText === v)) ? "" : "none";
  });
}
function filterType(sel, tid){
  const v = sel.value;
  const rows = document.getElementById(tid).querySelectorAll("tr:not(:first-child)");
  rows.forEach(r => {
    const tagCell = r.querySelector(".tag");
    r.style.display = (!v || (tagCell && tagCell.innerText === v)) ? "" : "none";
  });
}
function filterStatus(sel, tid){
  const v = sel.value;
  const rows = document.getElementById(tid).querySelectorAll("tr:not(:first-child)");
  rows.forEach(r => {
    const st = r.children[6].innerText;
    if(!v) r.style.display = "";
    else if(v==="DONE") r.style.display = (st.split("/")[0] === st.split("/")[1]) ? "" : "none";
    else r.style.display = (st.split("/")[0] !== st.split("/")[1]) ? "" : "none";
  });
}

function exportCSV(tid, name) {
  const table = document.getElementById(tid);
  let csv = [];
  let rows = table.querySelectorAll("tr");
  for (let i = 0; i < rows.length; i++) {
    if (rows[i].style.display !== "none") {
      let row = [], cols = rows[i].querySelectorAll("td, th");
      for (let j = 0; j < cols.length; j++) row.push("'" + cols[j].innerText.replace(/'/g, "''") + "'");
      csv.push(row.join(","));
    }
  }
  const blob = new Blob([csv.join("\\n")], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.setAttribute("download", `${name}_${new Date().getTime()}.csv`);
  document.body.appendChild(link); link.click(); document.body.removeChild(link);
}

// Autorefresh stats via ajax if bot active
function refreshStats() {
  fetch("/data").then(r=>r.json()).then(d=>{
    if(d.stats && d.stats.bot_pid) {
      document.getElementById("bot-indicator").innerHTML = `<span class="status-dot on"></span> BOT ATIVO - PID: ${d.stats.bot_pid} (Up: ${parseFloat(d.stats.uptime_hrs).toFixed(1)}h)`;
      // Update basic numbers without full reload if we wanted, but python static build is safer for now.
    } else {
      document.getElementById("bot-indicator").innerHTML = `<span class="status-dot off"></span> BOT PARADO`;
    }
  }).catch(e=>{});
}
setInterval(refreshStats, 10000);
refreshStats();
</script>
</body></html>'''

with open("D:/projetos-navegador/painel_template.html", "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r'<div class="panel"[^>]*id="panel-(config|erros)".*', "", content, flags=re.DOTALL)
content = re.sub(r'<script>.*?</script>', "", content, flags=re.DOTALL)
content = re.sub(r'</body>\s*</html>', "", content, flags=re.DOTALL)

with open("D:/projetos-navegador/painel_template.html", "w", encoding="utf-8") as f:
    f.write(content + "\n" + html_to_append)

print("Done template generation")
