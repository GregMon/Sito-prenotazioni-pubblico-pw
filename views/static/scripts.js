// Elementi principali
const giorniDropdown = document.getElementById('giorniDropdown');
const giornoSelezionato = document.getElementById('giornoSelezionato');
let giornoAttivo = null;
const disponibilitaFasce = {};

// Genera i bottoni delle fasce orarie
function generaBottoniFasceOrarie() {
  const container = document.querySelector('.fasce-orarie');
  container.innerHTML = ''; // Pulisce eventuali bottoni precedenti

  const fasceOrarie = ["19:00", "19:30", "20:00", "20:30"];

  fasceOrarie.forEach(ora => {
    const btn = document.createElement('button');
    btn.textContent = ora;
    btn.dataset.ora = ora;
    container.appendChild(btn);

    btn.addEventListener('click', () => {
      document.querySelectorAll('.fasce-orarie button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

}

// Aggiorna i bottoni delle fasce orarie con la disponibilità
function aggiornaUIFasce(data) {
  const bottoni = document.querySelectorAll("button[data-ora]");

  bottoni.forEach(btn => {
    const ora = btn.dataset.ora;
    const fascia = data.tavoli_disponibili.find(f => f.ora === ora);
    const disponibile = fascia ? fascia.disponibile : false;

    if (disponibile) {
      btn.disabled = false;
      btn.classList.remove("disattivato");
    } else {
      btn.disabled = true;
      console.log(`Fascia ${ora} non disponibile`);
      btn.classList.add("disattivato");
    }
  });
}

// Genera bottoni dei giorni e carica disponibilità solo al click
function generaBottoniGiorni() {
  const oggi = new Date();

  for (let i = 0; i < 7; i++) {
    const giorno = new Date(oggi);
    giorno.setDate(giorno.getDate() + i);
    const dataStr = giorno.toISOString().split('T')[0];

    const btn = document.createElement('button');
    btn.textContent = giorno.toLocaleDateString('it-IT', {
      weekday: 'short',
      day: 'numeric',
      month: 'short'
    });
    btn.dataset.giorno = dataStr;

    //verifica la disponibiità di tavoli cliccando sul selettore
    btn.addEventListener('click', async () => {
      giornoAttivo = dataStr;
      giornoSelezionato.textContent = btn.textContent;
      giorniDropdown.classList.add('hidden');

      document.querySelectorAll('#giorniDropdown button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      try {
        const res = await fetch(`/api/disponibilita?giorno=${dataStr}`);
        const data = await res.json();
        disponibilitaFasce[dataStr] = data;

        generaBottoniFasceOrarie();
        aggiornaUIFasce(data);
      } catch (err) {
        console.error(`Errore nel caricamento disponibilità per ${dataStr}:`, err);
      }
    });

    giorniDropdown.appendChild(btn);

    // Se è il primo giorno, selezionalo subito
    if (i === 0) {
      giornoAttivo = dataStr;
      btn.classList.add('active');
      giornoSelezionato.textContent = btn.textContent;

      fetch(`/api/disponibilita?giorno=${dataStr}`)
        .then(res => res.json())
        .then(data => {
          disponibilitaFasce[dataStr] = data;
          generaBottoniFasceOrarie();
          aggiornaUIFasce(data);
        })
        .catch(err => console.error(`Errore iniziale per ${dataStr}:`, err));
    }
  }

  console.log("Bottoni giorni generati");
}

// Mostra/nasconde il dropdown
giornoSelezionato.addEventListener('click', () => {
  giorniDropdown.classList.toggle('hidden');
});

// Chiude il dropdown se si clicca fuori
document.addEventListener('click', (e) => {
  const isClickInside = giorniDropdown.contains(e.target) || giornoSelezionato.contains(e.target);
  
  if (!isClickInside) {
    giorniDropdown.classList.add('hidden');
  }
});

// Esegui la generazione dei bottoni al caricamento
window.addEventListener("DOMContentLoaded", () => {
  generaBottoniGiorni();
});

// Animazione pulsanti + e -
document.querySelectorAll('.plus, .minus').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.classList.add('pulsing');
    setTimeout(() => btn.classList.remove('pulsing'), 200);
  });
});

// Gestione contatore persone
let count = 2;
const countDisplay = document.getElementById('count');
const plusBtn = document.querySelector('.plus');
const minusBtn = document.querySelector('.minus');

plusBtn.addEventListener('click', () => {
  if (count < 6) count++;
  countDisplay.textContent = count;
});

minusBtn.addEventListener('click', () => {
  if (count > 1) count--;
  countDisplay.textContent = count;
});

// Navigazione alla pagina di selezione tavolo
document.getElementById('vedi-tavoli').addEventListener('click', () => {
  const persone = count;
  const giorno = giornoAttivo;
  const orario = document.querySelector('.fasce-orarie button.active')?.textContent;

  if (!persone || !giorno || !orario) {
    alert("Compila tutti i campi!");
    return;
  }

  // Naviga verso la nuova pagina con i parametri
  const url = `/api/seleziona-tavolo?persone=${encodeURIComponent(persone)}&giorno=${encodeURIComponent(giorno)}&orario=${encodeURIComponent(orario)}`;
  window.location.href = url;
});

//form per inviare l'email con il token di modifica
document.addEventListener('DOMContentLoaded', () => {
    const mostraLink = document.getElementById('mostraModifica');
    const modificaForm = document.getElementById('modifica-form');
    const inviaBtn = document.getElementById('inviaLinkModifica');
    const emailInput = document.getElementById('emailModifica');
    const messaggio = document.getElementById('messaggioModifica');

    // Mostra/nascondi il form al click del link
    mostraLink.addEventListener('click', (e) => {
        e.preventDefault();
        modificaForm.classList.toggle('hidden');
    });

    // Gestione invio link modifica
    inviaBtn.addEventListener('click', async () => {
        const email = emailInput.value.trim();
        if (!email) {
            messaggio.innerText = "Inserisci un indirizzo email valido.";
            return;
        }

        messaggio.innerText = " Invio in corso...";
        try {
            const response = await fetch('/api/invia_link_modifica', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();
            if (data.message) {
                messaggio.innerText = "Invio riuscito" + data.message;
            } else if (data.error) {
                messaggio.innerText = "Errore" + data.error;
            } else {
                messaggio.innerText = "Operazione completata.";
            }
        } catch (err) {
            messaggio.innerText = "Errore di connessione al server.";
        }
    });
});