
from apscheduler.schedulers.background import BackgroundScheduler
from controllers import prenotazioni_controller

def controlloTemporalePrenotazioni(app):
    with app.app_context():
        print("Verifica prenotazioni scadute...")
        
        scadute = prenotazioni_controller.getExpiredPrenotazioni()
        for p in scadute:
            prenotazioni_controller.deletePrenotazione(p.id)

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: controlloTemporalePrenotazioni(app), 'interval', minutes=2)
    scheduler.start()


