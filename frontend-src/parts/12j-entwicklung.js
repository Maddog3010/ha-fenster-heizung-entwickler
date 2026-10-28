  /* ================= Nur Entwickler-Version =================
     Sperrbildschirm, Schlüssel und „Ins Hauptprojekt veröffentlichen“. Diese Datei gehört nicht zum Hauptprojekt,
     tools/release_build.py entfernt sie beim Veröffentlichen. */
  _dvCss() {
    return `<style>
.dvlock{min-height:100vh;display:grid;place-items:center;padding:16px;background:radial-gradient(90% 70% at 50% 0%,#2a1f55 0%,transparent 70%)}
.dvlock .card{max-width:440px;width:100%;text-align:center;padding:26px 22px}
.dvlock .mlogo{position:static;transform:none;margin:0 auto 14px;width:84px;height:84px;border-radius:22px}
.dvlock small.k{color:#c4b5fd;font-weight:800;letter-spacing:.11em;font-size:.68rem}
.dvlock h1{margin:6px 0 4px;font-size:1.5rem}.dvlock p{color:var(--mut);margin:0 0 14px}
.dvin{width:100%;background:var(--primary-background-color);color:var(--primary-text-color);border:1px solid var(--line);border-radius:12px;padding:12px;font:inherit;font-family:ui-monospace,Menlo,monospace;font-size:.85rem}
.dvtok{-webkit-text-security:disc}
.dvta{min-height:84px;resize:vertical;display:block}
.dverr{color:#f87171;font-size:.8rem;margin-top:8px;text-align:left}
.dvstp .st{display:grid;grid-template-columns:34px 1fr auto;gap:12px;padding:12px 0;border-bottom:1px solid var(--line);align-items:center}.dvstp .st:last-child{border:0}
.dvdot{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-weight:800;font-size:.85rem;border:2px solid var(--line);color:var(--mut)}
.dvdot.ok{background:var(--green);border-color:var(--green);color:#042f2e}.dvdot.run{border-color:var(--teal);color:var(--teal)}.dvdot.bad{background:#f87171;border-color:#f87171;color:#fff}
.dvstp b{display:block}.dvstp small{color:var(--mut)}
.dvtag{font-size:.7rem;font-weight:800;border-radius:99px;padding:3px 10px;border:1px solid var(--line)}
.dvtag.g{color:var(--green);border-color:#34d39955}.dvtag.t{color:var(--teal);border-color:#2dd4bf55}.dvtag.r{color:#f87171;border-color:#f8717155}
.dvg2{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:820px){.dvg2{grid-template-columns:1fr}}
.dvkv{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:6px}.dvkv>div{background:var(--primary-background-color);border:1px solid var(--line);border-radius:12px;padding:9px 11px}.dvkv span{font-size:.7rem;color:var(--mut)}.dvkv b{display:block;font-size:1.02rem}
.dvfld{display:grid;gap:4px;margin:8px 0}.dvfld label{font-size:.72rem;color:var(--mut)}
.dvrow{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}.dvrow .btn2{min-width:140px}
.a-dv{--a1:#a78bfa;--a2:#1e1b4b}
</style>`;
  }
  _dvLockRender() {
    const sr = this.shadowRoot, d = this._dv, adm = this._admin();
    let msg = "Diese Version ist nur für den Entwickler. Ohne Schlüssel sind alle Funktionen gesperrt.";
    if (!d) msg = "Status wird geprüft …";
    else if (d.state === "expired") msg = "Der Schlüssel ist abgelaufen. Bitte einen neuen Schlüssel eingeben.";
    const key = (this._dvF && this._dvF.dvkey) || "";
    sr.getElementById("main").innerHTML = this._dvCss() + `<div class="dvlock"><div class="card">
      <div class="mlogo" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="44" height="44">${ICONS.lock}</svg></div>
      <small class="k">STROM &amp; WÄRME · ENTWICKLER-VERSION</small><h1>Gesperrt</h1><p>${esc(msg)}</p>
      ${this._dvBusy ? `<p>Wird entsperrt …</p>` : adm ? `<input class="dvin" type="text" data-f="dvkey" value="${esc(key)}" placeholder="FHDEV1-…" spellcheck="false" autocomplete="off" aria-label="Entwickler-Schlüssel">
      <div class="dverr" role="alert">${esc(this._dvErr || "")}</div>
      <button class="btn2 pri" style="width:100%;margin-top:12px" data-act="dvxkey">Entsperren</button>` : `<p>Nur ein Administrator kann entsperren.</p>`}
      <div class="mut sm" style="margin-top:14px;text-align:left;border:1px dashed var(--teal);border-radius:14px;padding:10px 12px">Solange gesperrt: keine Module, keine Steuerung, keine Schalter oder Sensoren, keine Dienste. Der Schlüssel wird nur lokal geprüft.</div>
      <div class="mut sm" style="margin-top:12px">Strom &amp; Wärme Entwickler</div></div></div>`;
  }
  _dvLoadInfo(force) {
    if (!this._hass || this._dvBusyI) return;
    const fast = this._dvI && this._dvI.run && this._dvI.run.status !== "completed";
    if (!force && this._dvI && Date.now() - this._dvTs < (fast ? 4000 : 30000)) return;
    this._dvBusyI = true;
    this._hass.callWS({ type: "fenster_heizung_dev/dev_info" }).then((r) => { this._dvI = r; this._dvTs = Date.now(); if (this._mdActive() === "dv") this._render(); }).catch(() => {}).finally(() => { this._dvBusyI = false; });
  }
  _dvSteps() {
    const I = this._dvI || {}, run = I.run, st = I.steps || [];
    const pick = (n) => st.find((s) => String(s.name).startsWith(n));
    const cls = (s, idle) => !s ? idle : s.status === "in_progress" ? "run" : s.status === "completed" ? (s.conclusion === "success" ? "ok" : s.conclusion === "skipped" ? "" : "bad") : "";
    const queued = run && run.status !== "completed" && !st.length;
    const defs = [["1", "Prüfen", "Version, Schlüssel im Code, Aufbau"], ["2", "Bauen", "Ohne Entwickler-Teile, panel.js neu gebaut"], ["3", "Hochladen", "Ein Commit auf main im Hauptprojekt, kein Tag"]];
    const out = defs.map(([n, k, h]) => { const s = pick(n + " "); let c = cls(s, ""); if (queued && n === "1") c = "run"; return { n, t: k === "Hochladen" ? "In ha-fenster-heizung hochladen" : k === "Bauen" ? "Bauen ohne Entwickler-Teile" : "Prüfen", h, c }; });
    const done = run && run.status === "completed" && run.conclusion === "success";
    out.push({ n: "4", t: "Release anlegen", h: "Du legst den Release auf GitHub an (Tag vorausgefüllt)", c: done ? "run" : "" });
    return out;
  }
  _dvPage() {
    const I = this._dvI || {}, F = this._dvF || (this._dvF = {}), main = I.main_version || "", run = I.run;
    const sug = (() => { const p = (main || String(this._ver || "").replace(/-dev$/, "")).split("."); if (p.length > 1) { p[p.length - 1] = String((+p[p.length - 1] || 0) + 1); } return p.join("."); })();
    if (F.dvver == null || F.dvverAuto !== false) { F.dvver = sug; F.dvverAuto = true; }
    const steps = this._dvSteps(), working = run && run.status !== "completed";
    const when = run && run.created ? new Date(run.created).toLocaleString("de-DE", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "–";
    const tag = (c, n) => n === "4" ? (c ? `<span class="dvtag t">BEREIT</span>` : "") : c === "ok" ? `<span class="dvtag g">OK</span>` : c === "run" ? `<span class="dvtag t">${working || c === "run" ? "LÄUFT" : ""}</span>` : c === "bad" ? `<span class="dvtag r">FEHLER</span>` : "";
    const ready = I.token_set && !working;
    const doneOk = run && run.status === "completed" && run.conclusion === "success";
    return this._dvCss() + `
      <div class="card hero mh a-dv">${this._modLogo("dv")}<div class="lbl">${ic("tools", 16)}Entwicklung</div><div class="big bs">${esc(this._ver || "–")}</div><div class="sub">${main ? `Hauptprojekt: ${esc(main)}` : "Hauptprojekt: –"}</div><div class="chips"><span class="chip">${working ? "Veröffentlichen läuft" : doneOk ? "Zuletzt erfolgreich" : "Bereit"}</span><span class="chip">Entwickler-Modus aktiv</span></div></div>
      <div class="dvg2"><div class="card"><h2>${ic("upload", 18)}Ins Hauptprojekt veröffentlichen</h2>
        ${I.token_set ? "" : `<div class="banner" style="margin-bottom:10px">${ic("alert", 18)}<div>Zuerst unten das GitHub-Token eintragen. Es darf nur den Workflow starten.</div></div>`}
        <div class="dvfld"><label>Neue Version</label><input class="dvin" type="text" data-f="dvver" value="${esc(F.dvver)}" spellcheck="false" autocomplete="off"></div>
        <div class="dvfld"><label>Änderungen (kommen in den CHANGELOG)</label><textarea class="dvin dvta" data-f="dvlog" spellcheck="false" placeholder="### Neu&#10;- …">${esc(F.dvlog || "")}</textarea></div>
        <div class="dvstp">${steps.map((s) => `<div class="st"><span class="dvdot ${s.c}">${s.c === "ok" ? "✓" : s.n}</span><div><b>${esc(s.t)}</b><small>${esc(s.h)}</small></div>${tag(s.c, s.n)}</div>`).join("")}</div>
        <div class="dverr" role="alert">${esc(this._dvMsg || "")}</div>
        <div class="dvrow"><button class="btn2 pri" data-act="dvxpub" ${ready ? "" : "disabled"}>${this._dvConfirm ? "Wirklich veröffentlichen?" : "In Hauptprojekt veröffentlichen"}</button>
        <button class="btn2" data-act="dvxrel" ${doneOk ? "" : "disabled"}>Release auf GitHub anlegen</button></div></div>
      <div style="display:grid;gap:14px;align-content:start"><div class="card"><h2>${ic("info", 18)}Stand</h2>
        <div class="dvkv"><div><span>Entwicklung</span><b>${esc(String(this._ver || "–").replace(/-dev$/, ""))}</b></div><div><span>Hauptprojekt</span><b>${esc(main || "–")}</b></div><div><span>Letzter Lauf</span><b>${esc(when)}</b></div></div>
        <div class="mut sm">Entwickler-Repo: ${esc(I.dev_repo || "")}<br>Hauptprojekt: ${esc(I.main_repo || "")}</div>
        <div class="dvrow"><button class="btn2" data-act="dvxrefresh">Aktualisieren</button></div></div>
      <div class="card"><h2>${ic("lock", 18)}Zugang</h2>
        <div class="mut sm" style="margin-bottom:8px">Entwickler-Schlüssel gültig bis ${esc(I.bis || "–")}${I.name ? ` · ${esc(I.name)}` : ""}.</div>
        <div class="dvfld"><label>GitHub-Token (${I.token_set ? "hinterlegt" : "fehlt"}), darf nur Workflows im Entwickler-Repo starten</label><input class="dvin dvtok" type="text" data-f="dvtok" value="" placeholder="${I.token_set ? "Neues Token (leer lassen zum Behalten)" : "github_pat_…"}" spellcheck="false" autocomplete="off"></div>
        <div class="dvrow"><button class="btn2" data-act="dvxtok">Token speichern</button><button class="btn2" data-act="dvxlock">Sperren</button></div></div></div></div>`;
  }
  _dvRead() { const F = this._dvF || (this._dvF = {}); this.shadowRoot.querySelectorAll("[data-f^='dv']").forEach((el) => { F[el.dataset.f] = el.value; }); return F; }
  async _dvAct(a, b) {
    const F = this._dvRead();
    const ws = (o) => this._hass.callWS({ type: "fenster_heizung_dev/" + o.type, ...o.p });
    try {
      if (a === "dvxkey") {
        const key = String(F.dvkey || "").trim(); if (!key) { this._dvErr = "Bitte den Schlüssel eingeben."; this._render(); return; }
        const r = await ws({ type: "dev_unlock", p: { key } });
        if (r.unlocked) { this._dv = r; this._dvErr = ""; F.dvkey = ""; this._dvBusy = true; this._render(); setTimeout(async () => { this._dvBusy = false; this._dvI = null; await this._load(); }, 2500); }
        else { this._dv = r; this._dvErr = r.state === "expired" ? "Schlüssel abgelaufen." : "Schlüssel ungültig."; this._render(); }
      } else if (a === "dvxlock") {
        const r = await ws({ type: "dev_lock", p: {} }); this._dv = r; this._dvI = null; this._cfgReady = true; this._render();
      } else if (a === "dvxtok") {
        const t = String(F.dvtok || "").trim(); if (!t) { this._toast("Bitte ein Token eingeben"); return; }
        const r = await ws({ type: "dev_token", p: { token: t } }); F.dvtok = "";
        if (r.error) this._toast(r.error); else { this._toast("Token gespeichert"); this._dvLoadInfo(true); }
        this._render();
      } else if (a === "dvxrefresh") { this._dvLoadInfo(true); }
      else if (a === "dvxpub") {
        if (!this._dvConfirm) { this._dvConfirm = true; this._dvMsg = ""; this._render(); clearTimeout(this._dvCt); this._dvCt = setTimeout(() => { this._dvConfirm = false; this._render(); }, 6000); return; }
        this._dvConfirm = false; clearTimeout(this._dvCt);
        const r = await ws({ type: "dev_publish", p: { version: String(F.dvver || "").trim(), changelog: String(F.dvlog || "").trim() } });
        this._dvMsg = r.ok ? "" : (r.error || "Fehlgeschlagen"); if (r.ok) { this._toast("Veröffentlichen gestartet"); setTimeout(() => this._dvLoadInfo(true), 3000); }
        this._render();
      } else if (a === "dvxrel") {
        const v = encodeURIComponent((this._dvI && this._dvI.main_version) || F.dvver || "");
        window.open(`https://github.com/Maddog3010/ha-fenster-heizung/releases/new?tag=${v}&title=${v}`, "_blank", "noopener");
      }
    } catch (e) { this._toast((e && e.message) || "Fehler"); }
  }
