from database.db_models import TV, Tavolo
from utils.extensions import db
from utils.enums import ValutazioneVisibilita


def creaTavolo(numero, posizioneX, posizioneY, visibilita, unibile, capienza_massima):
    if not isinstance(numero, int) or not isinstance(posizioneX, int) or not isinstance(posizioneY, int):
        return None, "Numero e posizioni devono essere interi"

    if Tavolo.query.get(numero):
        return None, "Tavolo già esistente"
    
    if not isinstance(capienza_massima, int) or capienza_massima <= 0:
        return None, "Capienza massima non valida"

    if not isinstance(unibile, bool):
        return None, "Il campo 'unibile' deve essere booleano"
    
    if visibilita not in ValutazioneVisibilita:
        return None, "Valore relativo alla visibilità non valido"

    nuovo_tavolo = Tavolo(
        numero=numero,
        posizioneX=posizioneX, 
        posizioneY=posizioneY, 
        visibilita=visibilita, 
        capienza_massima = capienza_massima, 
        unibile=unibile)
    
    db.session.add(nuovo_tavolo)
    db.session.commit()
    return nuovo_tavolo, None

def rimuoviTavolo(numero):
    tavolo = Tavolo.query.get(numero)
    if not tavolo:
        return None, "Tavolo non trovato"

    db.session.delete(tavolo)
    db.session.commit()
    return tavolo, None

def modificaPosizioneTavolo(numero, nuova_posizioneX, nuova_posizioneY):
    tavolo = Tavolo.query.get(numero)
    if not tavolo:
        return None, "Tavolo non trovato"

    try:
        nuova_posizioneX = float(nuova_posizioneX)
        nuova_posizioneY = float(nuova_posizioneY)
    except (ValueError, TypeError):
        return None, "Dati non validi"

    tavolo.posizioneX = nuova_posizioneX
    tavolo.posizioneY = nuova_posizioneY
    db.session.commit()
    return tavolo, None


def modificaPosizioneTV(id, nuova_posizioneX, nuova_posizioneY, rotazione):
    tv = TV.query.get(id)
    if not tv:
        return None, "TV non trovata"

    try:
        nuova_posizioneX = float(nuova_posizioneX)
        nuova_posizioneY = float(nuova_posizioneY)
        rotazione = int(rotazione)
    except (ValueError, TypeError):
        return None, "Dati non validi"

    if not (0 <= nuova_posizioneX <= 1000 and 0 <= nuova_posizioneY <= 600):
        return None, "Coordinate non valide"

    tv.posizioneX = nuova_posizioneX
    tv.posizioneY = nuova_posizioneY
    tv.rotazione = rotazione
    db.session.commit()
    return tv, None


def listaTavoli():
    tavoli =  Tavolo.query.all()
    if not tavoli:
        return None, "Nessun tavolo trovato"
    
    listaTavoli = [t.to_dict() for t in tavoli]

    return listaTavoli, None

def listaTV():
    tv = TV.query.all()
    if not tv:
        return None, "Non sono disponibili TV"
    listaTV = [t.to_dict() for t in tv]

    return listaTV, None

def listaTavoliDisponibili(data, ora, numero_persone):
    tavoli =  Tavolo.query.all()
    if not tavoli:
        return None, "Nessun tavolo trovato"
    
    tavoli_disponibili = [t for t in tavoli if t.get_stato(data, ora) == "Disponibile" and t.capienza_massima >= numero_persone]
    if not tavoli_disponibili:
        return None, "Nessun tavolo disponibile per i criteri selezionati"

    listaTavoli = [t.to_dict() for t in tavoli_disponibili]

    return listaTavoli, None

def getTavolobyNumero(numero):
    return Tavolo.query.get(numero)

