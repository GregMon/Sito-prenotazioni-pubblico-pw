import { inizializzaTavoli, inizializzaTV, valutaVisibilitaTavoli, raccogliPosizioniTV, raccogliPosizioniTavoli } from './mappautils.js';


document.addEventListener("DOMContentLoaded", () => {

    const container = document.getElementById('mappa-admin');

    document.getElementById('btn-salva-mappa').addEventListener('click', () => {

        const datiTV = raccogliPosizioniTV(container);
        const datiTavoli = raccogliPosizioniTavoli(container);

        fetch('/api/admin/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tv: datiTV, tavoli: datiTavoli })
        })
        .then(res => res.ok ? res.json() : Promise.reject('Errore nel salvataggio'))
        .then(data => alert('Mappa salvata con successo!'))
        .catch(err => alert('Errore nel salvataggio della mappa'));
    });

  // Inizializza la TV
    inizializzaTV(container, true);

    // Inizializza tutti i tavoli (senza filtro prenotazioni)
    fetch('/api/mappa')
        .then(res => res.json())
        .then(tavoli => {
            if (!Array.isArray(tavoli)) {
                console.error("Dati tavoli non validi");
                return;
            }
            // Passa tutti i tavoli come disponibili
            inizializzaTavoli(container, tavoli, null, () => {
                valutaVisibilitaTavoli(container);
            }, true); // attiva modalità modifica

        });
    
    // GET utenti
    fetch('/api/admin/elenco_utenti')
        .then(res => res.json())
        .then(response => {
            if (!response.success) {
                alert(response.msg || "Errore nel caricamento utenti");
                return;
            }
            const lista = document.getElementById('lista-utenti');
            response.data.forEach(utente => {
            const div = document.createElement('div');
            div.className = 'utente';
            div.textContent = `${utente.nome} (${utente.email})`;
            lista.appendChild(div);
            });
        });

  // GET prenotazioni
    fetch('/api/admin/elenco_prenotazioni')
        .then(res => res.json())
        .then(response => {
            if (!response.success) {
                alert(response.msg || "Errore nel caricamento prenotazioni");
                return;
            }
            const container = document.getElementById('lista-prenotazioni');
            response.data.forEach(pren => {
            const div = document.createElement('div');
            div.className = 'prenotazione';

            const info = document.createElement('div');
            info.className = 'info';
            info.textContent = `${pren.utente.nome}, il ${pren.data} alle ${pren.ora_inizio} \n
                                tavolo ${pren.tavoli[0]} per ${pren.numero_persone} persone`;

            const btn = document.createElement('button');
            btn.className = 'cestino';
            btn.innerHTML = '🗑️';
            btn.onclick = () => {
                fetch(`/api/admin/elimina_prenotazioni/${pren.id}`, { method: 'DELETE' })
                .then(res => {
                    if (res.ok) div.remove();
                    else alert("Errore nella cancellazione");
                });
            };

            div.appendChild(info);
            div.appendChild(btn);
            container.appendChild(div);
            });
        });

});