from flask import Blueprint, render_template, request, jsonify
from utils.enums import ValutazioneStato
from controllers import prenotazioni_controller, tavoli_controller, utenti_controller
from flask import current_app as app
from controllers.prenotazioni_controller import verifica_recaptcha
from datetime import datetime, time, timedelta
import json
import logging

prenotazioni_bp = Blueprint('prenotazioni', __name__)
prenotazioni_html = Blueprint('prenotazioni_html', __name__)

@prenotazioni_bp.route('/prenotazioni', methods=['POST'])
def crea_prenotazione():

    print("Richiesta POST /prenotazioni")

    #Aggiunta questa condizione per disabilitare reCAPTCHA in locale senza secret key
    if app.config['RECAPTCHA_SECRET_KEY'] != "0":  
        token = request.form.get('g-recaptcha-response')
        if not token or not verifica_recaptcha(token):
            print(" Errore: reCAPTCHA fallito")
            return jsonify({'errore': 'Verifica reCAPTCHA fallita'}), 400
    
    try:
        data = datetime.strptime(request.form.get('data'), "%Y-%m-%d").date()
        ora_inizio = datetime.strptime(request.form.get('ora_inizio'), "%H:%M").time()
        ora_fine = (datetime.combine(data, ora_inizio) + timedelta(hours=1)).time()
        nome = request.form.get('nome')
        email = request.form.get('email')
        numero_persone = int(request.form.get('numero_persone'))
        numeri_tavoli = [int(n) for n in request.form.get('tavolo').split(",")]

        prenotazione, errore = prenotazioni_controller.creaPrenotazione(
            data=data, ora_inizio=ora_inizio,
            stato="in_attesa", nome=nome, email=email,
            numero_persone=numero_persone, ora_fine=ora_fine, numeri_tavoli=numeri_tavoli
        )

        if errore:
            print(" Errore:", errore)
            return jsonify({'errore': errore}), 400

        return jsonify({'msg': 'Prenotazione creata', 'id': prenotazione.id}), 200

    except Exception as e:
        print(" Errore nella richiesta:", e)
        return jsonify({'errore': 'Dati non validi'}), 400

# Route per la pagina web di selezione del tavolo desiderato e di conferma della prenotazione
@prenotazioni_bp.route("/seleziona-tavolo")
def seleziona_tavolo():
    persone = request.args.get("persone")
    giorno_str = request.args.get("giorno")

    try:
        giorno = datetime.strptime(giorno_str, "%Y-%m-%d")
    except (TypeError, ValueError):
        giorno = None  # oppure gestisci l'errore

    orario = request.args.get("orario")
    return render_template("mappa.html", persone=persone, giorno=giorno, orario=orario)

# Route per il passaggio del json della mappa allo script di gestione del tavolo
@prenotazioni_bp.route('/mappa', methods=['GET'])
def get_mappa():
    try:
        lista, errore = tavoli_controller.listaTavoli()
        if errore:
            return jsonify({'errore': errore}), 404
        return jsonify(lista)
        
    except Exception as e:
        print(f"Errore nel caricamento della mappa: {e}")
        return jsonify({'errore': 'Impossibile caricare la mappa'}), 500
    
# Route per il passaggio del json delle tv allo script di gestione del tavolo
@prenotazioni_bp.route('/tv', methods=['GET'])
def get_tv():
    try:
        lista, errore = tavoli_controller.listaTV()
        if errore:
            return jsonify({'errore': errore}), 404
        return jsonify(lista)
        
    except Exception as e:
        print(f"Errore nel caricamento delle tv: {e}")
        return jsonify({'errore': 'Impossibile caricare le tv'}), 500
    
# Route per la comunicazione dei tavoli disponibili alla pagina web di selezione del tavolo
@prenotazioni_bp.route('/tavoli', methods=['GET'])
def get_tavoli_disponibili(): 
    try:
        data_str = request.args.get('giorno')
        ora_str = request.args.get('orario')
        numero_persone = int(request.args.get('persone'))

        if not data_str or not ora_str or not numero_persone:
            return jsonify({'errore': 'Parametri mancanti'}), 400

        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        ora = datetime.strptime(ora_str, "%H:%M").time()

        tavoli_disponibili, errore = tavoli_controller.listaTavoliDisponibili(
            data=data, ora=ora, numero_persone=numero_persone
        )

        if errore:
            return jsonify({'errore': errore}), 400

        return jsonify(tavoli_disponibili), 200

    except Exception as e:
        print(f"Errore nel recupero dei tavoli disponibili: {e}")  

#Conferma la prenotazione tramite il token ricevuto via email
@prenotazioni_bp.route('/confermaToken', methods=['POST']) 
def conferma():
    data = request.get_json() or {}
    token = data.get('token')

    errore = prenotazioni_controller.confermaPrenotazione(token)
    if errore:
        return {"error": errore}, 400

    return {"message": "Prenotazione confermata!"}, 200

#Route dedicata alla verifica del ReCAPTCHA e alla creazione della prenotazione
@prenotazioni_bp.route('/conferma', methods=['POST'])
def conferma_prenotazione():
    print("Richiesta POST /conferma")

    token = request.form.get('g-recaptcha-response')
    if not token or not verifica_recaptcha(token):
        print(" Errore: reCAPTCHA fallito")
        return jsonify({'errore': 'Verifica reCAPTCHA fallita'}), 400

    return jsonify({'msg': 'Conferma riuscita'}), 200

#Route per l'invio dell'email con il link di modifica della prenotazione
@prenotazioni_bp.route('/invia_link_modifica', methods=['POST'])
def invia_link_modifica():
    data = request.get_json() or {}
    email = data.get('email')

    if not email:
        return {"error": "Indirizzo email non fornito"}, 400

    result, err = prenotazioni_controller.invia_email_modifica(email)

    if err:
        return {"error": "Impossibile inviare l'email: " + err}, 400

    return {"message": " Email di modifica inviata correttamente"}, 200

@prenotazioni_html.route('/pagina_di_modifica', methods=['POST'])
def modifica_prenotazione():

    token = request.form.get('token') 

    prenotazione = prenotazioni_controller.getPrenotazioneByToken(token)
    if not prenotazione or prenotazione.stato in [ValutazioneStato.ANNULLATA, ValutazioneStato.IN_ATTESA]:
        return {"error": "Il token è scaduto oppure non è più valido"}, 400

    utente = utenti_controller.getUtentebyId(prenotazione.utente_id)

    return render_template("modifica.html", prenotazione_json=json.dumps({
        "nome": utente.nome,
        "email": utente.email,
        "data": prenotazione.data.isoformat(),         
        "ora_inizio": prenotazione.ora_inizio.isoformat(),  
        "numero_persone": prenotazione.numero_persone,
        "token": token
    }))



#route per confermare le modifiche ad una prenotazione pre-esistente
@prenotazioni_bp.route('/modifica_prenotazione', methods=['POST'])
def modifica_prenotazione_api():
    token = request.form.get('token')
    nome = request.form.get('nome')
    email = request.form.get('email')
    tavolo = request.form.get('tavolo')
    data_str = request.form.get('data')
    ora_inizio_str = request.form.get('ora_inizio')
    numero_persone = request.form.get('numero_persone')

    if not all([token, nome, email, tavolo, data_str, ora_inizio_str, numero_persone]):
        return jsonify({'errore': 'Dati mancanti'}), 400

    try:
        numero_persone = int(numero_persone)
        data_dt = datetime.strptime(data_str, "%Y-%m-%d").date()
        ora_inizio_dt = datetime.strptime(ora_inizio_str, "%H:%M").time()

    except ValueError:
        return jsonify({'errore': 'Formato dati non valido'}), 400

    result = prenotazioni_controller.modificaPrenotazione(token, tavolo, data_dt, ora_inizio_dt, numero_persone)

    if isinstance(result, dict) and 'errore' in result:
        return jsonify(result), 400

    return jsonify({
        'msg': 'Prenotazione modificata con successo',
        'data': data_dt.isoformat(),
        'ora_inizio': ora_inizio_dt.strftime("%H:%M"),
        'tavolo': tavolo,
        'numero_persone': numero_persone
    })


#cancella la prenotazione selezionata
@prenotazioni_bp.route('/cancella_prenotazione', methods=['POST'])
def cancella_prenotazione():
    print(request.form.to_dict())
    token = request.form.get('token')
    if not token:
        return jsonify({'errore': 'Dati mancanti'}), 400
    
    result = prenotazioni_controller.annullaPrenotazione(token)
    if result.get('errore'):
        return jsonify(result), 400

    return jsonify({
        'msg': 'Prenotazione correttamente eliminata'
    })


@prenotazioni_bp.route('/disponibilita', methods=['GET'])
def verifica_disponibilita():
    try:
        data_str = request.args.get('giorno')

        if not data_str:
            return jsonify({'errore': 'Parametro "data" mancante'}), 400

        data = datetime.strptime(data_str, "%Y-%m-%d").date()

        fasce_orarie = [time(19,00), time(19,30), time(20,00), time(20,30)]
        response = []
        for t in fasce_orarie:
            ora_inizio = datetime.combine(data, t)
            ora_fine = ora_inizio + timedelta(hours=3)
            check = prenotazioni_controller.verificaDisponibilita(
            data=data, ora_inizio=ora_inizio.time(), ora_fine=ora_fine.time()
            )
            response.append({'ora': t.strftime("%H:%M"), 'disponibile': check})

        return jsonify({'tavoli_disponibili': response}), 200

    except Exception:
        return jsonify({'errore': 'Dati non validi'}), 400
