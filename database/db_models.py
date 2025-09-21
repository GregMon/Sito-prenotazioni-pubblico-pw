from datetime import date, datetime, time, timedelta, timezone
from flask_sqlalchemy import SQLAlchemy
from utils.enums import ValutazioneVisibilita, ValutazioneStato, RuoloUtente
from utils.extensions import db

#Ponte per associazione molti-a-molti tra Prenotazione e Tavolo
prenotazione_tavolo = db.Table('prenotazione_tavolo',
    db.Column('prenotazione_id', db.Integer, db.ForeignKey('prenotazione.id'), primary_key=True),
    db.Column('tavolo_numero', db.Integer, db.ForeignKey('tavolo.numero'), primary_key=True)
)

#Tabella e attributi per Utente
class Utente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    ruolo = db.Column(db.Enum(RuoloUtente), default=RuoloUtente.CLIENTE)  # "cliente" o "admin"
    passwordHashed = db.Column(db.String(255), nullable=True)  # Password hashed, nullable per utenti senza password
    prima_volta = db.Column(db.Boolean, default=True)  # Indica se è il primo accesso dell'utente
    prenotazioni = db.relationship('Prenotazione', backref='utente', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
        }


#Tabella e attributi per Prenotazione
class Prenotazione(db.Model):

    #Attributi
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    ora_inizio = db.Column(db.Time, nullable=False)
    ora_fine = db.Column(db.Time, nullable=False)
    stato = db.Column(db.String(20), default="in_attesa")                                                # "in_attesa", "confermata", "annullata"
    utente_id = db.Column(db.Integer, db.ForeignKey('utente.id'), nullable=False)
    numero_persone = db.Column(db.Integer, default=1, nullable=False)                                    # Numero di persone per la prenotazione
    tavoli = db.relationship('Tavolo', secondary=prenotazione_tavolo, back_populates='prenotazioni')     # Tavoli associati alla prenotazione
    token_conferma = db.Column(db.String(100), unique=True, nullable=True)                                        # Token per conferma via email
    token_modifica = db.Column(db.String(100), unique=True, nullable=True)                                        # Token per la modifica
    expires_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(minutes=2))

    def to_dict(self):
        return {
            "id": self.id,
            "data": self.data.strftime("%d-%m-%Y"),
            "ora_inizio": self.ora_inizio.strftime("%H:%M"),
            "ora_fine": self.ora_fine.strftime("%H:%M"),
            "stato": self.stato,
            "numero_persone": self.numero_persone,
            "utente": {
                "id": self.utente.id,
                "nome": self.utente.nome
            },
            "tavoli": [t.numero for t in self.tavoli]
        }

#Tabella e attributi per Tavolo
class Tavolo(db.Model):
    #Attributi
    numero = db.Column(db.Integer, primary_key = True)
    posizioneX = db.Column(db.Float, nullable = False)
    posizioneY = db.Column(db.Float, nullable = False)
    visibilita = db.Column(db.Enum(ValutazioneVisibilita), default=ValutazioneVisibilita.OTTIMA, nullable = False) # "Ottima", "Media", "Scarsa"
    capienza_massima = db.Column(db.Integer, default=6, nullable=False)  
    unibile = db.Column(db.Boolean, default=True, nullable=False)  # Indica se il tavolo può essere unito ad altri 
    rotazione = db.Column(db.Integer, default=0, nullable=True)  # Angolo di rotazione del tavolo in gradi (0, 90, 180, 270)
    prenotazioni = db.relationship('Prenotazione', secondary=prenotazione_tavolo, back_populates='tavoli')


    #Funzione per ottenere lo stato del tavolo al momento della prenotazione
    def get_stato(self, data, ora, durata=timedelta(hours=1)):
        prenotazioni = [p for p in self.prenotazioni if p.data == data]
        ora_corrente = datetime.combine(data, ora)
        ora_fine = ora_corrente + durata

        for pren in prenotazioni:
            if pren.stato == "Annullata":
                continue

            inizio = datetime.combine(data, pren.ora_inizio)
            fine = datetime.combine(data, pren.ora_fine)

            # Verifica sovrapposizione
            if inizio < ora_fine and fine > ora_corrente:
                return "Occupato"

        return "Disponibile"

    def to_dict(self):
        return {
            "numero": self.numero,
            "posizioneX": self.posizioneX,
            "posizioneY": self.posizioneY,
            "visibilita": self.visibilita.value,
            "capienza_massima": self.capienza_massima,
            "unibile": self.unibile,
            "rotazione": self.rotazione,
            "stato": self.get_stato(date.today(), time(21, 0)),
            "prenotazioni": [p.to_dict() for p in self.prenotazioni]
        }
    

class TV(db.Model):
    #Attributi
    id = db.Column(db.Integer, primary_key=True)
    posizioneX = db.Column(db.Float, nullable = False)
    posizioneY = db.Column(db.Float, nullable = False)
    rotation = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "posizioneX": self.posizioneX,
            "posizioneY": self.posizioneY,
            "rotation": self.rotation 
        }