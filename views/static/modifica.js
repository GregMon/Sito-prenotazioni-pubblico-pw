import { inizializzaTavoli, inizializzaTV, valutaVisibilitaTavoli } from './mappautils.js';

const raw = document.getElementById("prenotazione-data")?.textContent;
const prenotazione = raw ? JSON.parse(raw) : null;

const token = prenotazione.token;

let tavoloSelezionato = null;
let giornoAttivo = null;
let disponibilitaFasce = {};

const form = document.getElementById("formPrenotazione");
const countEl = document.getElementById("count");
const giornoSelezionato = document.getElementById("giornoSelezionato");
const giorniDropdown = document.getElementById("giorniDropdown");

// Inizializza prenotazione esistente
if (prenotazione) {
  form.nome.value = prenotazione.nome;
  form.email.value = prenotazione.email;
  countEl.innerText = prenotazione.numero_persone;
  giornoAttivo = prenotazione.data;
  giornoSelezionato.innerText = formatDataIt(prenotazione.data);
  caricaDisponibilita(prenotazione.data, prenotazione.ora_inizio);
}

// Selettore giorno
giornoSelezionato.addEventListener("click", () => {
  giorniDropdown.classList.toggle("hidden");
});

function generaBottoniGiorni() {
  const oggi = new Date();

  for (let i = 0; i < 7; i++) {
    const giorno = new Date(oggi);
    giorno.setDate(giorno.getDate() + i);
    const dataStr = giorno.toISOString().split("T")[0];

    const btn = document.createElement("button");
    btn.textContent = giorno.toLocaleDateString("it-IT", {
      weekday: "short",
      day: "numeric",
      month: "short"
    });
    btn.dataset.giorno = dataStr;

    btn.addEventListener("click", async () => {
      giornoAttivo = dataStr;
      giornoSelezionato.textContent = btn.textContent;
      giorniDropdown.classList.add("hidden");

      document.querySelectorAll("#giorniDropdown button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      await caricaDisponibilita(dataStr);
    });

    giorniDropdown.appendChild(btn);

    if (i === 0 && !prenotazione) {
      giornoAttivo = dataStr;
      btn.classList.add("active");
      giornoSelezionato.textContent = btn.textContent;
      caricaDisponibilita(dataStr);
    }
  }
}

async function caricaDisponibilita(dataStr, orarioDesiderato = null) {
  try {
    const res = await fetch(`/api/disponibilita?giorno=${dataStr}`);
    const data = await res.json();

    const fasce = data.tavoli_disponibili;
    if (!Array.isArray(fasce)) {
      console.error("Formato disponibilità non valido:", data);
      return;
    }

    disponibilitaFasce[dataStr] = fasce;
    generaBottoniFasceOrarie(fasce);
    selezionaOrario(orarioDesiderato);
    aggiornaTavoli();
  } catch (err) {
    console.error(`Errore nel caricamento disponibilità per ${dataStr}:`, err);
  }
}

function generaBottoniFasceOrarie(fasce) {
  const container = document.getElementById("fasce-orarie");
  container.innerHTML = "";

  fasce.forEach(item => {
    const btn = document.createElement("button");
    btn.textContent = item.ora;
    btn.disabled = !item.disponibile;

    btn.addEventListener("click", () => {
      document.querySelectorAll("#fasce-orarie button").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      aggiornaTavoli();
    });

    container.appendChild(btn);
  });
}

function selezionaOrario(orarioDesiderato) {
  const bottoni = document.querySelectorAll("#fasce-orarie button:not(:disabled)");
  if (!bottoni.length) return;

  let bottone = Array.from(bottoni).find(btn => btn.textContent === orarioDesiderato);
  if (!bottone) bottone = bottoni[0];

  bottone.classList.add("selected");
}

// Selettore persone
document.querySelector(".plus").addEventListener("click", () => {
  let count = parseInt(countEl.innerText);
  countEl.innerText = Math.min(count + 1, 12);
  aggiornaTavoli();
});

document.querySelector(".minus").addEventListener("click", () => {
  let count = parseInt(countEl.innerText);
  countEl.innerText = Math.max(count - 1, 1);
  aggiornaTavoli();
});

function getValoriCorrenti() {
  const persone = countEl.innerText;
  const orario = document.querySelector("#fasce-orarie .selected")?.innerText;
  const giorno = giornoAttivo;
  return { persone, giorno, orario };
}

function aggiornaTavoli() {
  const { persone, giorno, orario } = getValoriCorrenti();
  if (!persone || !giorno || !orario) {
    console.warn("Parametri incompleti per caricare i tavoli:", { persone, giorno, orario });
    return;
  }

  const container = document.getElementById("mappa-container");
  document.querySelectorAll(".tavolo").forEach(el => el.remove());
  tavoloSelezionato = null;
  document.getElementById("feedback-tavolo").classList.add("hidden");

  fetch(`/api/tavoli?persone=${persone}&giorno=${giorno}&orario=${orario}`)
    .then(res => {
      if (!res.ok) throw new Error(`Errore HTTP ${res.status}`);
      return res.json();
    })
    .then(tavoliDisponibili => {
      const aggiornaSelezione = numero => {
        tavoloSelezionato = numero;
      };

      inizializzaTavoli(container, tavoliDisponibili, aggiornaSelezione, async () => {
        await inizializzaTV(container);
        valutaVisibilitaTavoli(container);
      });
    })
    .catch(error => {
      console.error("Errore nel caricamento disponibilità:", error);
    });
}

//chiamata per la conferma della prenotazione
form.addEventListener("submit", function (e) {
  e.preventDefault();

  const formData = new FormData(form);
  const { persone, giorno, orario } = getValoriCorrenti();

  if (!tavoloSelezionato) {
    document.getElementById("risultato").innerText = "Seleziona un tavolo prima di inviare.";
    return;
  }

  formData.append("tavolo", tavoloSelezionato);
  formData.append("nome", form.nome.value);
  formData.append("email", form.email.value);
  formData.append("data", giorno);
  formData.append("ora_inizio", orario);
  formData.append("numero_persone", persone);
  formData.append("token", token);

  fetch("/api/modifica_prenotazione", {
    method: "POST",
    body: formData
  })
    .then(response => {
      if (!response.ok) throw new Error("Errore nella risposta");
      return response.json();
    })
    .then(data => {
      const msg = data.msg || `Prenotazione modificata con successo per il tavolo ${data.tavolo}!`;
      document.getElementById("risultato").innerText = msg;
      document.getElementById("feedback-tavolo").classList.add("hidden");
      const dettagli = `
  Grazie, ${formData.get("nome")} la tua prenotazione è stata correttamente aggiornata con i seguenti dati:
  Data: ${data.data}
  Ora: ${data.ora_inizio}
  Tavolo: ${data.tavolo}
  Persone: ${data.numero_persone}
      `.trim();

      document.getElementById("dettagli-prenotazione").innerText = dettagli;
    })
    .catch(error => {
      document.getElementById("risultato").innerText = "Errore nella modifica.";
      console.error("Errore:", error);
    });

});

// Utility per formattare la data in italiano
function formatDataIt(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleDateString("it-IT", {
    weekday: "short",
    day: "numeric",
    month: "short"
  });
}

document.getElementById("annulla-btn").addEventListener("click", () => {
  const formData = new FormData();
  formData.append("token", token); // il token della prenotazione da annullare

  fetch("/api/cancella_prenotazione", {
    method: "POST",
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      document.getElementById("risultato").innerText = data.msg || data.errore;
    })
    .catch(err => {
      document.getElementById("risultato").innerText = "Errore nell'annullamento.";
      console.error(err);
    });
});

// Avvio iniziale
generaBottoniGiorni();
