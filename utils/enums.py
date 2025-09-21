import enum

class ValutazioneVisibilita(enum.Enum):
    OTTIMA = "Ottima"
    MEDIA = "Media"
    SCARSA = "Scarsa"

class ValutazioneStato(enum.Enum):
    DISPONIBILE = "Disponibile"
    OCCUPATO = "Occupato"
    IN_ATTESA = "In attesa"
    CONFERMATA = "Confermata"
    ANNULLATA = "Annullata"
    FUORI_SERVIZIO = "Fuori servizio"

class RuoloUtente(enum.Enum):
    CLIENTE = "cliente"
    ADMIN = "admin"