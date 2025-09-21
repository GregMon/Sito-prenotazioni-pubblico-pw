from datetime import date, time
from database.db_models import TV, db, Tavolo, Utente, Prenotazione
from utils.enums import ValutazioneVisibilita, ValutazioneStato
from controllers import prenotazioni_controller

def generaTavoli():

    LARGHEZZA_MAPPA = 1000
    ALTEZZA_MAPPA = 600

    tavoli_base = [
    {"numero": 1, "posizioneX": 100, "posizioneY": 100, "visibilita": ValutazioneVisibilita.OTTIMA, "capienza_massima": 4},
    {"numero": 2, "posizioneX": 100, "posizioneY": 300, "visibilita": ValutazioneVisibilita.MEDIA, "capienza_massima": 4},
    {"numero": 3, "posizioneX": 100, "posizioneY": 480, "visibilita": ValutazioneVisibilita.SCARSA, "capienza_massima": 4},

    {"numero": 4, "posizioneX": 350, "posizioneY": 80, "visibilita": ValutazioneVisibilita.OTTIMA, "capienza_massima": 6},
    {"numero": 5, "posizioneX": 350, "posizioneY": 250, "visibilita": ValutazioneVisibilita.MEDIA, "capienza_massima": 6},
    {"numero": 6, "posizioneX": 350, "posizioneY": 400, "visibilita": ValutazioneVisibilita.SCARSA, "capienza_massima": 6},

    {"numero": 7, "posizioneX": 750, "posizioneY": 100, "visibilita": ValutazioneVisibilita.OTTIMA, "capienza_massima": 2},
    {"numero": 8, "posizioneX": 750, "posizioneY": 300, "visibilita": ValutazioneVisibilita.MEDIA, "capienza_massima": 2},
    {"numero": 9, "posizioneX": 750, "posizioneY": 430, "visibilita": ValutazioneVisibilita.SCARSA, "capienza_massima": 2}
]
    for tavolo in tavoli_base:
        tavolo["posizioneX"] = round(tavolo["posizioneX"] / LARGHEZZA_MAPPA, 4)
        tavolo["posizioneY"] = round(tavolo["posizioneY"] / ALTEZZA_MAPPA, 4)
        print(f"Tavolo {tavolo['numero']} - Posizione normalizzata: ({tavolo['posizioneX']}, {tavolo['posizioneY']})")

    for t in tavoli_base:
        db.session.add(Tavolo(**t))

    db.session.commit()

def generaTV():

    LARGHEZZA_MAPPA = 1000
    ALTEZZA_MAPPA = 600

    TVs = [
        {"posizioneX": 550, "posizioneY": 15},
        {"posizioneX": 200, "posizioneY": 590}
    ]

    for tv in TVs:
        tv["posizioneX"] = round(tv["posizioneX"] / LARGHEZZA_MAPPA, 4)
        tv["posizioneY"] = round(tv["posizioneY"] / ALTEZZA_MAPPA, 4)

    for tv in TVs:
        db.session.add(TV(**tv))

    db.session.commit()

def generaUtenti():
    utentiBase = [
        {"nome": "Mario Rossi", "email": "mario.rossi@gmail.com"},
    ]
    for u in utentiBase:
        db.session.add(Utente(**u))
    
    db.session.commit()



def generaPrenotazioni():  
    pass