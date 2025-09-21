from datetime import date, time, datetime
from flask import current_app as app, jsonify, request
from controllers import tavoli_controller
from utils.enums import ValutazioneStato
from database.db_models import Utente, Prenotazione, Tavolo
from controllers import utenti_controller
from utils.extensions import mail, db
from utils.config import RECAPTCHA_SECRET_KEY
from flask_mail import Message
import os
import requests
import secrets


#Funzione per la verifica del reCAPTCHA di Google
def verifica_recaptcha(token):
    secret_key = app.config['RECAPTCHA_SECRET_KEY']
    payload = {
        'secret': secret_key,
        'response': token
    }
    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
    result = r.json()
    return result.get('success', False)

#Funzione per l'invio di email di conferma con Mailtrap
def invia_email_conferma(nome, email_destinatario, token_conferma):

    #Seleziona il link da utilizzare in base all'ambiente
    if "localhost" in request.host or "127.0.0.1" in request.host:
        link_conferma = f"http://localhost:5000/manage#{token_conferma}"
    else:
        link_conferma = f"https://project-work-progetto-sito-prenotazioni.onrender.com/manage#{token_conferma}"


    corpo_email = f"""
Ciao {nome},

Grazie per aver effettuato una prenotazione!

Per confermare la tua prenotazione, clicca qui:
{link_conferma}

Ignora questa mail se non sei stato tu ad effettuare questa prenotazione.

Ti aspettiamo!
J. Pub
"""

    msg = Message(
        subject="Conferma la tua prenotazione",
        sender="hello@tesipub.cloud",
        recipients=[email_destinatario],
        body=corpo_email
    )
    mail.send(msg)

def invia_email_modifica(email):
    utente = utenti_controller.getUtentebyEmail(email)

    if not utente:
        return None, "Utente non trovato"
    
    prenotazione = Prenotazione.query.filter_by(utente_id=utente.id).first()
    
    if not prenotazione:
        return None, "Prenotazione non trovata"
    
    #Seleziona il link da utilizzare in base all'ambiente
    if "localhost" in request.host or "127.0.0.1" in request.host:
        link_modifica = f"http://localhost:5000/manage#{prenotazione.token_modifica}"
    else:
        link_modifica = f"https://project-work-progetto-sito-prenotazioni.onrender.com/manage#{prenotazione.token_modifica}"

    corpo_email = f"""
Ciao {utente.nome},

Se vuoi modificare la tua prenotazione, clicca qui:
{link_modifica}

Ignora questa mail se non sei stato tu ad effettuare questa prenotazione.

Ti aspettiamo!
J. Pub
"""
    msg = Message(
        subject="Modifica la tua prenotazione",
        sender="hello@tesipub.cloud",
        recipients=[email],
        body=corpo_email
    )
    mail.send(msg)

    return "Email inviata correttamente", None


#Funzione principale per la creazione di una nuova prenotazione
def creaPrenotazione(data, ora_inizio, ora_fine, stato, nome, email, numero_persone, numeri_tavoli):
    print("Inizio creaPrenotazione")

    if not isinstance(data, date) or not isinstance(ora_inizio, time) or not isinstance(ora_fine, time):
        print("Data o orari non validi")
        return None, "Data e orari non validi"

    if ora_inizio >= ora_fine:
        print("Orario di inizio >= fine")
        return None, "Orario di inizio deve precedere quello di fine"

    utente, err = utenti_controller.creaUtente(nome, email)
    print(f"Utente creato o recuperato: {utente.nome} ({utente.email})")

    tavoli = []
    errori = []

    #Creazione dei token utilizzando il prefisso per differenziare i due tipi
    token = "C_" + secrets.token_urlsafe(16)
    token_modifica= "M_" + secrets.token_urlsafe(16)

    for numero in numeri_tavoli:
        tavolo = Tavolo.query.get(numero)
        print(f"Controllo tavolo {numero}")
        if not tavolo:
            errori.append(f"Tavolo {numero} non trovato")
        elif tavolo.get_stato(data, ora_inizio) == "Occupato":
            errori.append(f"Tavolo {numero} occupato")
        else:
            tavoli.append(tavolo)

    if errori:
        print("Errori tavoli:", errori)
        return None, "; ".join(errori)

    nuova_prenotazione = Prenotazione(
        data=data,
        ora_inizio=ora_inizio,
        ora_fine=ora_fine,
        stato=stato,
        utente_id=utente.id,
        numero_persone=numero_persone,
        tavoli=tavoli,
        token_conferma=token,
        token_modifica=token_modifica
    )

    # Se non è disponibile una secret key, attiva direttamente la prenotazione e salta l'invio dell'email (per testing in locale)
    if app.config['MAIL_PASSWORD'] != "0":  
        invia_email_conferma(nome, email, token)
    else:
        nuova_prenotazione.stato = 'confermata'
        nuova_prenotazione.token_conferma = None
        print(f"Modalità di sviluppo: prenotazione confermata senza email, per modificarla usa il token http://localhost:5000/manage#{token_modifica}")

    try:
        db.session.add(nuova_prenotazione)
        db.session.commit()
        print(f"Prenotazione registrata con ID: {nuova_prenotazione.id}")
        return nuova_prenotazione, None
    except Exception as e:
        print("Errore nel salvataggio:", e)
        db.session.rollback()
        return None, "Errore nel salvataggio"

def deletePrenotazione(prenotazione_id):
    prenotazione = Prenotazione.query.get(prenotazione_id)
    if not prenotazione:
        return None, "Prenotazione non trovata"

    try:
        db.session.delete(prenotazione)
        db.session.commit()
        print(f"Prenotazione {prenotazione.id} cancellata con successo.")
        return { "id": prenotazione.id }, None
    except Exception as e:
        db.session.rollback()
        return None, "Errore nella cancellazione"

# Se la prenotazione esiste (token), la imposta sullo stato confermata
def confermaPrenotazione(token):
    prenotazione = Prenotazione.query.filter_by(token_conferma=token).first()
    if not prenotazione:
        return "Token non valido"

    if prenotazione.stato != 'in_attesa':
        return "Prenotazione già confermata o annullata"

    try:
        prenotazione.stato = 'confermata'
        prenotazione.token_conferma = None
        db.session.commit()
        print(f"Prenotazione {prenotazione.id} confermata con successo.")
        return None
    
    except Exception as e:
        db.session.rollback()
        return "Errore nella conferma"
    
#Funzione che modifica la prenotazione aggiornando i dati selezionati dall'utente
def modificaPrenotazione(token, tavolo, data, ora_inizio, numero_persone):
    prenotazione = getPrenotazioneByToken(token)
    if not prenotazione or prenotazione.stato in [ValutazioneStato.ANNULLATA.value, ValutazioneStato.IN_ATTESA.value]:
        return {'errore': 'Token non valido o prenotazione non modificabile'}

    try:
        tavolo_obj = Tavolo.query.get(tavolo)
        if not tavolo_obj:
            return {'errore': 'Tavolo non trovato'}
        prenotazione.tavoli = [tavolo_obj]
        prenotazione.data = data
        prenotazione.ora_inizio = ora_inizio
        prenotazione.numero_persone = numero_persone
        token = "M_" + secrets.token_urlsafe(16)
        prenotazione.token_modifica = token
        db.session.commit()
        print("Prenotazione aggiornata:", prenotazione.id, prenotazione.data, prenotazione.ora_inizio, prenotazione.tavoli)
        print(tavoli_controller.listaTavoliDisponibili(data, ora_inizio, numero_persone))
        return True
    
    except Exception as e:
        db.session.rollback()
        return {'errore': 'Impossibile modificare la prenotazione'}

def annullaPrenotazione(token):
    prenotazione = getPrenotazioneByToken(token)

    print("Prenotazione trovata:", prenotazione)
    print("Stato:", prenotazione.stato)

    if not prenotazione or prenotazione.stato in [ValutazioneStato.ANNULLATA.value, ValutazioneStato.IN_ATTESA.value]:
        return {'errore': 'Token non valido o prenotazione già annullata'}
    try:
        prenotazione.stato = ValutazioneStato.ANNULLATA.value
        prenotazione.tavoli = []
        prenotazione.token_modifica = None
        db.session.commit()
        return {'successo': True}
    
    except Exception as e:
        db.session.rollback()
        print("Errore durante annullamento prenotazione:", e)
        return {'errore': 'Impossibile eliminare la prenotazione'}

      
def getPrenotazioneByToken(token):
    prenotazione = Prenotazione.query.filter_by(token_modifica=token).first()
    return prenotazione


def getExpiredPrenotazioni():
    now = datetime.now()
    scadute = Prenotazione.query.filter(
        Prenotazione.expires_at < now,
        Prenotazione.stato == 'in_attesa'
    ).all()
    return scadute

def verificaDisponibilita(data, ora_inizio, ora_fine):
    if not isinstance(data, date) or not isinstance(ora_inizio, time) or not isinstance(ora_fine, time):
        return "Data e orari non validi"

    tavoli = Tavolo.query.all()
    tavoli_disponibili = False

    for tavolo in tavoli:
        if tavolo.get_stato(data, ora_inizio) == "Disponibile":
            tavoli_disponibili = True

    return tavoli_disponibili

def listaPrenotazioni():
    prenotazioni = Prenotazione.query.all()
    if not prenotazioni:
        return None, "Nessun utente ha effettuato una prenotazione"
    lista_prenotazioni = [p.to_dict() for p in prenotazioni]

    return lista_prenotazioni, None