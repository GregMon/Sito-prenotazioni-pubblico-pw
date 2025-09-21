from database.db_models import Utente
from utils.extensions import db
from utils.enums import RuoloUtente
import re
import bcrypt
from dotenv import load_dotenv
import os
import jwt
from datetime import datetime, timedelta, timezone 

############################################################# gestione utenti #################################################################

def creaUtente(nome, email):
    if not isinstance(nome, str) or not isinstance(email, str):
        return None, "Nome ed email sono obbligatori"

    # Rimuove spazi iniziali e finali e converte l'email in minuscolo
    nome = nome.strip()
    email = email.strip().lower()

    if not nome or not emailValida(email):
        return None, "Nome ed email non validi"
    
    utente = Utente.query.filter_by(email=email).first()
    if utente:
        return utente, None

    if '@' not in email:
        return None, "Email non valida"
    
    nuovo_utente = Utente(nome=nome, email=email)
    print(nuovo_utente)
    db.session.add(nuovo_utente)
    db.session.commit()
    return nuovo_utente, None

def rimuoviUtente(utente_id):
    utente = Utente.query.get(utente_id)
    if not utente:
        return None, "Utente non trovato"

    db.session.delete(utente)
    db.session.commit()
    return utente, None

def emailValida(email):

    #espressione regolare per validare l'email
    pattern = r'^[\w\.-]{2,}@[\w\.-]{2,}\.\w{2,}$'

    #controlla se l'email corrisponde al pattern
    return re.match(pattern, email) is not None

def listaUtenti():
    utenti = Utente.query.all()
    if not utenti:
        return None, "Nessun utente ha effettuato una prenotazione"
    lista_utenti = [u.to_dict() for u in utenti]

    return lista_utenti, None

def getUtentebyId(utente_id):
    return Utente.query.get(utente_id)

def getUtentebyEmail(email):
    return Utente.query.filter_by(email=email).first()

########################################################### gestione admin #################################################################

#Metodo per la creazione di un Admin
def creaAdmin():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'variables.env'))

    nome = os.getenv("ADMIN_NAME")
    email = os.getenv("ADMIN_EMAIL")
    pwd = os.getenv("ADMIN_PASSWORD")

    if not all([nome, email, pwd]):
        return None, "Variabili d'ambiente mancanti"

    utente = getUtentebyEmail(email)

    if utente:
        utente.ruolo = RuoloUtente.ADMIN
        utente.passwordHashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        return "Admin aggiornato", None

    # Altrimenti crea nuovo utente
    utente, errore = creaUtente(nome, email)
    if errore:
        return None, errore

    utente.ruolo = RuoloUtente.ADMIN
    utente.passwordHashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.session.commit()
    return "Admin generato", None

def getPrimaVolta(utente_id):
    utente = getUtentebyId(utente_id)
    if not utente:
        return None, "Utente non trovato"
    return utente.prima_volta, None

def changePassword(utente, new_password):

    if not utente:
        return None, "Utente non trovato"
    
    if utente.ruolo != RuoloUtente.ADMIN:
        return None, "Solo l'admin può cambiare la password"
    
    if not is_password_valid(new_password):
        return None, "La password deve contenere almeno 8 caratteri, una maiuscola, una minuscola, un numero e un carattere speciale"
    
    utente.passwordHashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    utente.prima_volta = False
    db.session.add(utente)
    db.session.commit()
    return "Password aggiornata", None

#verifica se la password contiene almeno 8 caratteri, una maiuscola, una minuscola, un numero e un carattere speciale
def is_password_valid(pwd):
    return (
        len(pwd) >= 8 and
        re.search(r"[A-Z]", pwd) and
        re.search(r"[a-z]", pwd) and
        re.search(r"[0-9]", pwd) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd)
    )

def verificaPassword(utente, password):
    if not utente:
        return False, "Utente non trovato"
    
    if not utente.passwordHashed:
        return False, "Utente non ha una password impostata"

    if bcrypt.checkpw(password.encode('utf-8'), utente.passwordHashed.encode('utf-8')):
        return True, None
    else:
        return False, "Password errata"

def generate_jwt(utente):
    if utente.ruolo != RuoloUtente.ADMIN:
        return None, "Solo l'admin può generare un token di sessione"
    
    secret_key = getSecretKey()
    if not secret_key:
        return None, "Chiave segreta non impostata"
    
    payload = {
        'user_id': utente.id,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)  # Token valido per 1 ora
    }

    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

def getSecretKey():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'variables.env'))
    return os.getenv("SECRET_KEY")