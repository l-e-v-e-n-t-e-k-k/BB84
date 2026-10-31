"use strict";

// A böngésző megjelenít és kéréseket küld. A protokoll számításai Pythonban maradnak.
const phases = [
  {id:"elokeszites", name:"Előkészítés", description:"Alice bitenként egy bázist választ az állapot előkészítéséhez."},
  {id:"eve_merese", name:"Eve mérése", description:"Eve megméri, majd a saját eredménye alapján újraküldi a qubitet."},
  {id:"bob_merese", name:"Bob mérése", description:"Bob a saját bázisában méri a kapott qubitet."},
  {id:"szures", name:"Bázisegyeztetés", description:"Az egyező Alice–Bob bázisú pozíciókat megtartjuk."},
  {id:"mintavetel", name:"Ellenőrző minta", description:"A kijelölt biteket felfedjük, ezért kimaradnak a kulcsjelöltből."},
  {id:"eredmenyek", name:"Eredmények", description:"A QBER a mintából, a kulcsjelöltek a fel nem fedett pozíciókból készülnek."},
];
const $ = id => document.getElementById(id);
let responseState = {allapot:null, elozmenyek:[]};
let viewPhase = null;
let selectedIndex = null;
let busy = false;

function symbol(basis, bit, inactive=false) {
  if (inactive) return '<svg viewBox="0 0 100 100" aria-hidden="true"><path d="M25 75L75 25" stroke="currentColor" stroke-width="2"/><circle cx="50" cy="50" r="34" fill="none" stroke="currentColor" stroke-width="1"/></svg>';
  let angle = bit === null ? null : (basis === "Z" ? (bit ? 90 : 0) : (bit ? 45 : -45));
  return `<svg viewBox="0 0 100 100" role="img" aria-label="${angle === null ? "Mérésre vár" : `${basis} bázis, ${bit} bit`}"><circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" opacity=".22"/><path d="M50 7V93M7 50H93" stroke="currentColor" opacity=".15"/>${angle === null ? '<circle cx="50" cy="50" r="5" fill="none" stroke="currentColor" stroke-width="2"/>' : `<g transform="rotate(${angle} 50 50)"><path d="M19 50H81" stroke="currentColor" stroke-width="4"/><path d="M19 50L26 45M19 50L26 55M81 50L74 45M81 50L74 55" stroke="currentColor" stroke-width="2" fill="none"/></g>`}</svg>`;
}

function shownState() {
  return (viewPhase && responseState.elozmenyek.find(s => s.fazis === viewPhase)) || responseState.allapot;
}

function phaseParticipant(state) {
  if (!state) return null;
  if (state.fazis === "eve_merese" || (state.fazis === "elokeszites" && state.eve_aktiv)) return "eve";
  if (state.fazis === "bob_merese" || state.fazis === "elokeszites") return "bob";
  return null;
}

function drawNav(state) {
  const live = responseState.allapot;
  const existing = new Map(responseState.elozmenyek.map(s => [s.fazis, s]));
  $("phaseNav").innerHTML = phases.map((phase, index) => {
    const snapshot = existing.get(phase.id);
    const skipped = live && !live.eve_aktiv && phase.id === "eve_merese";
    let status = skipped ? "Kihagyva" : "";
    if (snapshot) {
      if (["eve_merese","bob_merese"].includes(phase.id)) {
        const who = phase.id === "eve_merese" ? "eve" : "bob";
        const count = snapshot.poziciok.filter(p => p[who]?.[1] !== null).length;
        status = `${count} / ${snapshot.poziciok.length} mérés`;
      } else status = phase.id === live?.fazis ? "Aktuális" : "Kész";
    }
    const selected = state?.fazis === phase.id || (!state && index === 0);
    return `<button type="button" class="phase-button ${selected ? "selected" : ""}" data-phase="${phase.id}" ${snapshot && !busy ? "" : "disabled"} aria-pressed="${selected}"><span class="phase-index">${String(index+1).padStart(2,"0")}</span><span><span class="phase-name">${phase.name}</span><span class="phase-status">${status}</span></span></button>`;
  }).join("");
}

function drawActors(state, index) {
  const position = state?.poziciok[index];
  const participant = phaseParticipant(state);
  for (const who of ["alice", "eve", "bob"]) {
    const actor = document.querySelector(`.actor.${who}`);
    const inactive = who === "eve" && state && !state.eve_aktiv;
    const pair = position?.[who];
    actor.classList.toggle("inactive", Boolean(inactive));
    actor.classList.toggle("focused", state?.fazis === "elokeszites" ? who === "alice" : who === participant);
    $(`${who}Symbol`).innerHTML = symbol(pair?.[0] ?? "Z", pair?.[1] ?? null, inactive);
    if (!state) $(`${who}State`).textContent = {alice:"A küldő",eve:"A lehallgató",bob:"A fogadó"}[who];
    else if (inactive) $(`${who}State`).textContent = "Kihagyva";
    else if (pair[1] === null) $(`${who}State`).innerHTML = `<b>${pair[0]}</b> bázis · mérésre vár`;
    else $(`${who}State`).innerHTML = `<b>${pair[0]}</b> bázis · <b>${pair[1]}</b> bit`;
  }
}

function drawTable(state, focusIndex) {
  if (!state) {
    $("positionRows").innerHTML = '<tr><td colspan="10" class="empty-table">Nincs adat.</td></tr>';
    $("keptCount").textContent = "—"; $("sampleCount").textContent = "—"; return;
  }
  $("keptCount").textContent = state.poziciok.filter(p => p.megtartva === true).length;
  $("sampleCount").textContent = state.poziciok.filter(p => p.ellenorzo_minta).length;
  $("positionRows").innerHTML = state.poziciok.map((p,index) => {
    const mismatch = p.bob[1] !== null && p.alice[0] === p.bob[0] && p.alice[1] !== p.bob[1];
    const actorCells = ["alice","eve","bob"].map(who => `<td><span class="basis-tag">${p[who]?.[0] ?? "—"}</span></td><td><span class="${p[who]?.[1] == null ? "muted" : "bit-value"}">${p[who]?.[1] ?? "—"}</span></td>`).join("");
    const kept = p.megtartva === null ? '—' : p.megtartva ? '<span class="status-keep">✓ Megtartva</span>' : '<span class="muted">Elvetve</span>';
    return `<tr data-qubit="${index}" class="${p.ellenorzo_minta ? "sample-row" : ""} ${index === focusIndex ? "selected-row" : ""}"><td><button type="button" class="qubit-select" aria-label="${index+1}. qubit megtekintése" aria-pressed="${index===focusIndex}">${String(index+1).padStart(2,"0")}</button></td>${actorCells}<td>${kept}</td><td>${p.ellenorzo_minta ? '<span class="status-sample">◇ Felfedve</span>' : '—'}</td><td>${mismatch ? '<span class="status-error">≠ Eltérés</span>' : '—'}</td></tr>`;
  }).join("");
}

function drawControls() {
  const live = responseState.allapot;
  const historical = viewPhase && viewPhase !== live?.fazis;
  const finished = live?.fazis === "eredmenyek";
  $("nextButton").disabled = busy || !live || historical || finished;
  $("allButton").disabled = busy || !live || historical || !phaseParticipant(live) || live.kovetkezo_merendo === null;
  $("settingsButton").disabled = busy;
  $("resetButton").disabled = busy || !live;
  $("startButton").disabled = busy;
  $("randomButton").disabled = busy;
  $("closeSettings").disabled = busy;
  if (historical) $("controlHint").textContent = "Folytatás az élő futásban.";
  else if (!live) $("controlHint").textContent = "";
  else if (finished) $("controlHint").textContent = "Kész.";
  else if (phaseParticipant(live) && live.kovetkezo_merendo === null) $("controlHint").textContent = "Minden qubit megmérve.";
  else if (phaseParticipant(live)) $("controlHint").textContent = "Egy kattintás: egy qubit.";
  else $("controlHint").textContent = "";
}

function render() {
  const state = shownState();
  const phaseIndex = phases.findIndex(p => p.id === state?.fazis);
  const phase = phases[Math.max(phaseIndex,0)];
  const historical = Boolean(viewPhase && viewPhase !== responseState.allapot?.fazis);
  const participant = phaseParticipant(state);
  const measured = participant ? state.poziciok.filter(p => p[participant]?.[1] !== null).length : 0;
  const index = state ? Math.min(selectedIndex ?? Math.max(measured-1,0), state.poziciok.length-1) : 0;
  drawNav(state);
  $("phaseNumber").textContent = String(Math.max(phaseIndex,0)+1).padStart(2,"0");
  $("stageTitle").textContent = phase.name;
  $("stageDescription").textContent = state ? phase.description : "Állítsd be a kísérletet az indításhoz.";
  $("historyBanner").hidden = !historical;
  $("runSummary").textContent = responseState.allapot ? `${responseState.allapot.poziciok.length} qubit · Eve ${responseState.allapot.eve_aktiv ? "aktív" : "kikapcsolva"} · ${responseState.allapot.mintaszazalek}% minta` : "Nincs aktív kísérlet.";
  $("qubitLabel").textContent = state ? `${String(index+1).padStart(2,"0")}. POZÍCIÓ` : "KVANTUMCSATORNA";
  $("measurementProgress").textContent = participant ? `${measured} / ${state.poziciok.length} megmérve` : "";
  drawActors(state,index);
  drawTable(state,index);
  $("results").hidden = state?.fazis !== "eredmenyek";
  if (state?.fazis === "eredmenyek") {
    $("qberValue").textContent = state.hibaarany === null ? "—" : `${(state.hibaarany*100).toLocaleString("hu-HU",{maximumFractionDigits:2})}%`;
    $("qberDescription").textContent = state.hibaarany === null ? "Nincs ellenőrző minta." : state.hibaarany === 0 ? "A mintában nincs eltérés." : "Eltérés a mintában.";
    $("aliceKey").textContent = state.alice_kulcs.join("") || "Üres";
    $("bobKey").textContent = state.bob_kulcs.join("") || "Üres";
  }
  drawControls();
}

async function api(path, data) {
  const options = data === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)};
  const response = await fetch(`/api/${path}`, {...options, credentials:"same-origin",cache:"no-store"});
  const result = await response.json();
  if (!response.ok) throw new Error(result.hiba || "A művelet nem sikerült.");
  return result;
}

async function mutate(path, data={}) {
  if (busy) return;
  busy = true;
  $("globalError").hidden = true;
  $("formError").hidden = true;
  drawControls();
  const before = responseState.allapot;
  try {
    responseState = await api(path,data);
    viewPhase = null;
    selectedIndex = null;
    if (path === "inditas") $("settingsDialog").close();
    const after = responseState.allapot;
    if (after && before && ["eve_merese","bob_merese"].includes(after.fazis)) {
      const who = after.fazis === "eve_merese" ? "eve" : "bob";
      if (after.poziciok.some((p,i) => p[who]?.[1] !== null && before.poziciok[i]?.[who]?.[1] == null)) {
        $("apparatus").classList.remove("animate-eve","animate-bob");
        void $("apparatus").offsetWidth;
        $("apparatus").classList.add(`animate-${who}`);
      }
    }
    $("announcement").textContent = after ? `${phases.find(p=>p.id===after.fazis).name}. ${after.poziciok.filter(p=>p.bob[1]!==null).length} Bob-mérés készült el.` : "Új kísérlet indítható.";
  } catch (error) {
    const target = $("settingsDialog").open ? $("formError") : $("globalError");
    target.textContent = error.message === "Failed to fetch" ? "A helyi szerver nem érhető el. Ellenőrizd, hogy az app.py fut-e." : error.message;
    target.hidden = false;
  } finally {
    busy = false;
    render();
  }
}

$("settingsButton").addEventListener("click", () => { $("formError").hidden=true; $("settingsDialog").showModal(); });
$("closeSettings").addEventListener("click", () => $("settingsDialog").close());
$("settingsDialog").addEventListener("cancel", event => {if (busy) event.preventDefault();});
$("eveEnabled").addEventListener("change", () => { $("eveBases").disabled = !$("eveEnabled").checked; $("eveBases").required = $("eveEnabled").checked; });
$("randomButton").addEventListener("click", () => {
  const count = Number($("qubitCount").value);
  if (!Number.isInteger(count) || count < 1 || count > 256) {$("qubitCount").reportValidity();return;}
  // Csak a bemeneti választásokat generáljuk itt; a mérési eredményeket a Python sorsolja.
  for (const id of ["aliceBits","aliceBases","bobBases","eveBases"]) {
    const random = crypto.getRandomValues(new Uint8Array(count));
    const alphabet = id === "aliceBits" ? "01" : "ZX";
    $(id).value = Array.from(random, value => alphabet[value % 2]).join("");
  }
});
$("settingsForm").addEventListener("submit", event => {
  event.preventDefault();
  mutate("inditas", {darab:Number($("qubitCount").value),mintaszazalek:Number($("samplePercent").value),alice_bitek:$("aliceBits").value,alice_bazisok:$("aliceBases").value,bob_bazisok:$("bobBases").value,eve_aktiv:$("eveEnabled").checked,eve_bazisok:$("eveBases").value});
});
$("nextButton").addEventListener("click", () => mutate("kovetkezo"));
$("allButton").addEventListener("click", () => mutate("osszes"));
$("resetButton").addEventListener("click", () => mutate("uj"));
$("liveButton").addEventListener("click", () => {viewPhase=null;selectedIndex=null;render();});
$("phaseNav").addEventListener("click", event => {
  const button=event.target.closest("button[data-phase]");
  if (!button || busy || button.disabled) return;
  viewPhase=button.dataset.phase === responseState.allapot.fazis ? null : button.dataset.phase;
  selectedIndex=null;
  render();
});
$("positionRows").addEventListener("click", event => {
  const row=event.target.closest("tr[data-qubit]");
  if (!row) return;
  selectedIndex=Number(row.dataset.qubit);
  render();
});

render();
api("allapot").then(data=>{responseState=data;render();}).catch(()=>{
  $("globalError").textContent="A szerver állapota nem kérhető le. Frissítsd az oldalt, ha a szerver már fut.";
  $("globalError").hidden=false;
});
