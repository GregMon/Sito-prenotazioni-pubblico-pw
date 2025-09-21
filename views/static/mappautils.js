/* In questo javascript sono contenuti gli script per la generazione della mappa comuni tra prenotazione.js, modifica.js e dashboard.js.
   Il posizionamento degli oggetti sulla mappa avviene normalizzando la posizione del backend al container nel frontend. */

export function inizializzaTavoli(container, tavoliDisponibili, onSelezione, onRenderComplete, modifica = false) {
  const baseWidth = 1000;
  const baseHeight = 600;
  const fixedSize = 150;

  fetch('/api/mappa')
    .then(response => response.json())
    .then(tavoli => {
      if (!Array.isArray(tavoli)) {
        console.error('Dati mappa non validi:', tavoli);
        return;
      }

      const disponibiliSet = new Set(tavoliDisponibili.map(t => t.numero));
      let tavoliRenderizzati = 0;

      tavoli.forEach(tavolo => {
        if (!disponibiliSet.has(tavolo.numero)) return;

        const x = parseFloat(tavolo.posizioneX) * baseWidth;
        const y = parseFloat(tavolo.posizioneY) * baseHeight;

        if (x < 0 || x > baseWidth || y < 0 || y > baseHeight) {
          console.warn(`Tavolo ${tavolo.numero} fuori scala: (${x}, ${y})`);
          return;
        }

        const img = document.createElement('img');
        img.src = `/static/maps/table${tavolo.capienza_massima}.svg`;
        img.alt = `Tavolo ${tavolo.numero}`;
        img.className = 'tavolo';
        img.dataset.numero = tavolo.numero;
        img.style.position = 'absolute';
        img.style.left = `${x}px`;
        img.style.top = `${y}px`;
        img.style.width = `${fixedSize}px`;
        img.style.height = `${fixedSize}px`;
        img.style.transform = `translate(-50%, -50%) rotate(${tavolo.rotazione || 0}deg)`;

        if (modifica) {
          abilitaDrag(img, container);
        }

        img.addEventListener('click', () => {
          document.querySelectorAll('.tavolo').forEach(el => el.classList.remove('selected'));
          img.classList.add('selected');

          animaTavolo(img);

          if (typeof onSelezione === 'function') {
            onSelezione(tavolo.numero);
          }

          const feedback = document.getElementById('feedback-tavolo');
          feedback.innerText = `Hai selezionato il tavolo ${tavolo.numero}`;
          feedback.classList.remove('hidden');
        });

        container.appendChild(img);
        tavoliRenderizzati++;
      });

      if (typeof onRenderComplete === 'function' && tavoliRenderizzati > 0) {
        onRenderComplete();
      }
    })
    .catch(error => console.error('Errore nel caricamento della mappa:', error));
}

export async function inizializzaTV(container, modifica = false) {
  const baseWidth = 1000;
  const baseHeight = 600;
  const fixedWidth = 100;
  const fixedHeight = 36;

  const response = await fetch('/api/tv');
  const tvList = await response.json();

  if (!Array.isArray(tvList)) {
    console.error('Dati TV non validi:', tvList);
    return;
  }

  tvList.forEach(tv => {
    const x = parseFloat(tv.posizioneX) * baseWidth;
    const y = parseFloat(tv.posizioneY) * baseHeight;
    const rotazione = tv.rotation || 0;

    const wrapper = document.createElement('div');
    wrapper.className = 'tv-wrapper';
    wrapper.dataset.id = tv.id;
    wrapper.dataset.rotazione = rotazione;
    wrapper.style.position = 'absolute';
    wrapper.style.left = `${x}px`;
    wrapper.style.top = `${y}px`;
    wrapper.style.width = `${fixedWidth}px`;
    wrapper.style.height = `${fixedHeight}px`;
    wrapper.style.transform = `translate(-50%, -50%) rotate(${rotazione}deg)`;

    const img = document.createElement('img');
    img.src = '/static/maps/tv.svg';
    img.alt = `TV ${tv.id}`;
    img.className = 'tv';
    img.style.width = '100%';
    img.style.height = '100%';
    img.draggable = false;

    // Freccia che indica la direzione della TV
    const freccia = document.createElement('div');
    freccia.className = 'tv-freccia';
    freccia.dataset.id = tv.id;
    freccia.style.position = 'absolute';
    freccia.style.top = '-12px';
    freccia.style.left = '50%';
    freccia.style.transform = 'translateX(-50%)';
    freccia.style.width = '0';
    freccia.style.height = '0';
    freccia.style.border = '10px solid transparent';
    freccia.style.borderBottomColor = '#333';
    freccia.style.pointerEvents = 'none';

    wrapper.appendChild(img);
    wrapper.appendChild(freccia);
    container.appendChild(wrapper);

    if (modifica) {
      abilitaDrag(wrapper, container);

      wrapper.addEventListener('click', () => {
        document.querySelectorAll('.tv-wrapper').forEach(el => el.classList.remove('selected'));
        wrapper.classList.add('selected');
        mostraPannelloTV(tv, wrapper);
      });
    }
  });
}


//metodi che vengono richiamati per aggiornare le posizioni modificate dalla dashboard nel database backend
export function raccogliPosizioniTV(container) {
  const baseWidth = 1000;
  const baseHeight = 600;

  return Array.from(container.querySelectorAll('.tv-wrapper')).map(tv => {
    const id = tv.dataset.id;
    const rotazione = parseInt(tv.dataset.rotazione || '0');
    const left = parseFloat(tv.style.left);
    const top = parseFloat(tv.style.top);

    return {
      id,
      posizioneX: (left / baseWidth).toFixed(4),
      posizioneY: (top / baseHeight).toFixed(4),
      rotazione
    };
  });
}

export function raccogliPosizioniTavoli(container) {
  const baseWidth = 1000;
  const baseHeight = 600;

  return Array.from(container.querySelectorAll('.tavolo')).map(tavolo => {
    const numero = tavolo.dataset.numero;
    const transform = tavolo.style.transform || '';
    const rotazioneMatch = transform.match(/rotate\((\d+)deg\)/);
    const rotazione = rotazioneMatch ? parseInt(rotazioneMatch[1]) : 0;
    const left = parseFloat(tavolo.style.left);
    const top = parseFloat(tavolo.style.top);

    return {
      numero,
      posizioneX: (left / baseWidth).toFixed(4),
      posizioneY: (top / baseHeight).toFixed(4),
      rotazione
    };
  });
}


function mostraPannelloTV(tv, wrapper) {
  const pannello = document.getElementById('pannello-modifica');
  const info = document.getElementById('modifica-info');
  const btnRuota = document.getElementById('btn-ruota-tv');

  pannello.classList.remove('hidden');
  info.innerText = `TV ${tv.id}`;

  btnRuota.onclick = () => {
    const currentRotation = tv.rotation || 0;
    const newRotation = (currentRotation + 90) % 360;

    wrapper.style.transform = `translate(-50%, -50%) rotate(${newRotation}deg)`;
    tv.rotation = newRotation;
    wrapper.dataset.rotazione = newRotation;
  };

}

function aggiornaPosizione(elemento, container, x, y, offsetX, offsetY) {
  const halfWidth = elemento.offsetWidth / 2;
  const halfHeight = elemento.offsetHeight / 2;

  const minX = halfWidth - offsetX;
  const maxX = container.offsetWidth - halfWidth + offsetX;
  const minY = halfHeight - offsetY;
  const maxY = container.offsetHeight - halfHeight + offsetY;

  const clampedX = Math.max(minX, Math.min(x, maxX));
  const clampedY = Math.max(minY, Math.min(y, maxY));

  elemento.style.left = `${clampedX}px`;
  elemento.style.top = `${clampedY}px`;
}

function abilitaDrag(elemento, container) {
  const offsetX = 10;
  const offsetY = 5;

  // Mouse drag
  elemento.addEventListener('mousedown', (e) => {
    e.preventDefault();

    // gestisce il movimento in base alle dimensioni attuali della finestra
    function onMouseMove(e) {
      const containerRect = container.getBoundingClientRect(); 
      const x = e.clientX - containerRect.left;
      const y = e.clientY - containerRect.top;

      aggiornaPosizione(elemento, container, x, y, offsetX, offsetY);
    }


    function onMouseUp() {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);

      if (elemento.classList.contains('tv-wrapper')) {
        valutaVisibilitaTavoli(container);
      }
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  });

  //Touch drag
  elemento.addEventListener('touchstart', (e) => {
    e.preventDefault();
    

    // gestisce il movimento in base alle dimensioni attuali della finestra
    function onTouchMove(e) {
      const touch = e.touches[0];
      const containerRect = container.getBoundingClientRect(); 
      const x = touch.clientX - containerRect.left;
      const y = touch.clientY - containerRect.top;

      aggiornaPosizione(elemento, container, x, y, offsetX, offsetY);
    }

    function onTouchEnd() {
      document.removeEventListener('touchmove', onTouchMove);
      document.removeEventListener('touchend', onTouchEnd);

      if (elemento.classList.contains('tv-wrapper')) {
        valutaVisibilitaTavoli(container);
      }
    }

    document.addEventListener('touchmove', onTouchMove);
    document.addEventListener('touchend', onTouchEnd);
  });

  elemento.ondragstart = () => false;
  elemento.style.cursor = 'move';
}

export function animaTavolo(img) {
  if (!img || !img.classList.contains('tavolo')) return;

  img.classList.add('pulsing');
  setTimeout(() => img.classList.remove('pulsing'), 400);
}

export function valutaVisibilitaTavoli(container) {
  const tavoli = Array.from(container.querySelectorAll('.tavolo'));
  const tvs = Array.from(container.querySelectorAll('.tv'));
  const containerRect = container.getBoundingClientRect();

  tavoli.forEach(tavolo => {
    //calcola il centro del tavolo relativo al contenitore della mappa
    const rect1 = tavolo.getBoundingClientRect();
    const x1 = rect1.left - containerRect.left + rect1.width / 2;
    const y1 = rect1.top - containerRect.top + rect1.height / 2;

    let minDist = Infinity;
    let tvVicina = null;

    // Trova la TV più vicina
    tvs.forEach(tv => {
      //calcola il centro della tv relativo al contenitore della mappa
      const rect2 = tv.getBoundingClientRect();
      const x2 = rect2.left - containerRect.left + rect2.width / 2;
      const y2 = rect2.top - containerRect.top + rect2.height / 2;

      //calcolo della distanza
      const dx = x2 - x1;
      const dy = y2 - y1;
      const distanza = Math.sqrt(dx ** 2 + dy ** 2);

      //formula per trovare la tv più vicina
      if (distanza < minDist) {
        minDist = distanza;
        tvVicina = { x: x2, y: y2 };
      }
    });

    // Calcola angolo verso la TV più vicina
    let angoloVersoTV = null;
    if (tvVicina) {
      const dx = tvVicina.x - x1;
      const dy = tvVicina.y - y1;
      angoloVersoTV = Math.atan2(dy, dx) * (180 / Math.PI);
      if (angoloVersoTV < 0) angoloVersoTV += 360; 
    }

    // Formule per il calcolo del punteggio 
    const distanza = minDist;
    const angolo = Math.abs(angoloVersoTV - 90);
    const penalitaDistanza = Math.max(0, (distanza - 300) / 4);
    const penalitaAngolo = Math.max(0, (angolo - 120) / 3);

    const punteggio = Math.max(0, Math.round(100 - penalitaDistanza - penalitaAngolo));

    tavolo.dataset.distanzaTv = minDist.toFixed(1);
    tavolo.dataset.angoloVersoTv = angoloVersoTV?.toFixed(1) ?? '—';
    tavolo.dataset.punteggioTv = punteggio;

    // Colore visivo in base al punteggio
    if (punteggio >= 90) {
      tavolo.style.filter = 'drop-shadow(0 0 6px rgba(0, 255, 0, 0.6))'; // verde
    } else if (punteggio >= 50) {
      tavolo.style.filter = 'drop-shadow(0 0 6px rgba(255, 255, 0, 0.8))'; // giallo
    } else {
      tavolo.style.filter = 'drop-shadow(0 0 6px rgba(255, 0, 0, 0.6))'; // rosso
    }

    //console.log(`Tavolo ${tavolo.dataset.numero || '—'} → distanza: ${minDist.toFixed(1)}px → angolo verso TV: ${angoloVersoTV?.toFixed(1)}° → punteggio: ${punteggio}`);
  });
}











