import { inizializzaTavoli, inizializzaTV, valutaVisibilitaTavoli } from './mappautils.js';

const params = new URLSearchParams(window.location.search);
const persone = params.get("persone");
const giorno = params.get("giorno");
const orario = params.get("orario");

let tavoloSelezionato = null;

window.addEventListener('load', () => {
  const container = document.getElementById('mappa-container');
  const planimetria = container.querySelector('img');

  // Aggiunta dei campi hidden nel momento giusto
  const form = document.querySelector("#formPrenotazione");

  const hiddenData = document.createElement("input");
  hiddenData.type = "hidden";
  hiddenData.name = "data";
  hiddenData.value = giorno;
  form.appendChild(hiddenData);

  const hiddenOrario = document.createElement("input");
  hiddenOrario.type = "hidden";
  hiddenOrario.name = "ora_inizio";
  hiddenOrario.value = orario;
  form.appendChild(hiddenOrario);

  const hiddenPersone = document.createElement("input");
  hiddenPersone.type = "hidden";
  hiddenPersone.name = "numero_persone";
  hiddenPersone.value = persone;
  form.appendChild(hiddenPersone);

  // Caricamento tavoli disponibili
  fetch(`/api/tavoli?persone=${persone}&giorno=${giorno}&orario=${orario}`)
    .then(res => res.json())
    .then(tavoliDisponibili => {
      if (!Array.isArray(tavoliDisponibili)) {
        console.error('Dati disponibilità non validi:', tavoliDisponibili);
        return;
      }

      const aggiornaSelezione = numero => {
        tavoloSelezionato = numero;
      };

      if (planimetria.complete) {
        inizializzaTavoli(container, tavoliDisponibili, aggiornaSelezione);
        inizializzaTV(container);
        setTimeout(() => {
          valutaVisibilitaTavoli(container);
        }, 1000); 

      } else {
        planimetria.addEventListener('load', () => {
          inizializzaTavoli(container, tavoliDisponibili, aggiornaSelezione);
          inizializzaTV(container);
          
          setTimeout(() => {
            valutaVisibilitaTavoli(container);
          }, 1000);

        });
      }
    })
    .catch(error => console.error('Errore nel caricamento disponibilità:', error));
});

// Gestione invio form
document.getElementById('formPrenotazione').addEventListener('submit', function(e) {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);

  if (!tavoloSelezionato) {
    document.getElementById('risultato').innerText = 'Seleziona un tavolo prima di inviare.';
    return;
  }

  // Aggiungi il tavolo selezionato, il nome e l'email ai dati da inviare
  formData.append('tavolo', tavoloSelezionato);
  formData.append('nome', form.nome.value);
  formData.append('email', form.email.value);

  fetch(form.action, {
    method: form.method,
    body: formData
  })
  .then(response => {
    if (!response.ok) throw new Error('Errore nella risposta');
    return response.json();
  })
  .then(data => {
    document.getElementById('risultato').innerText = data.msg || `Prenotazione inviata con successo per il tavolo ${tavoloSelezionato}!`;

    // Nascondi feedback dopo invio
    document.getElementById('feedback-tavolo').classList.add('hidden');
  })
  .catch(error => {
    document.getElementById('risultato').innerText = 'Errore nella prenotazione.';
    console.error(error);
  });
});
