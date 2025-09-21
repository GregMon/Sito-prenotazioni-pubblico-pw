from flask import Flask, render_template
from database.db_models import Tavolo, Utente
from routes.prenotazioni import prenotazioni_bp, prenotazioni_html
from routes.admin import admin_bp
from utils import seeds
from controllers import utenti_controller
import os
from dotenv import load_dotenv
from utils.enums import RuoloUtente
from utils.extensions import mail, db
import scheduler

dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'variables.env')
load_dotenv(dotenv_path)

app = Flask(__name__, template_folder="views", static_folder="views/static")
app.register_blueprint(prenotazioni_bp, url_prefix='/api')
app.register_blueprint(prenotazioni_html)
app.register_blueprint(admin_bp, url_prefix='/api/admin')

app.config.from_object('utils.config')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('RECAPTCHA_SECRET_KEY')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

mail.init_app(app)
db.init_app(app)
scheduler.start_scheduler(app)

with app.app_context():
    db.create_all()


@app.route('/')
def home():
    #per testing drop del database ad ogni refresh
    #db.drop_all()
    #db.create_all()
    
    #seeds.generaTavoli()
    #seeds.generaTV()
    #seeds.generaUtenti()
    #seeds.generaPrenotazioni()

    #print(f'Admin creato: {admin}, errore: {err}')
    return render_template('index.html')

@app.route('/prototipo')
def prototipo_form():
    return render_template('prototipo.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/manage')
def manage():
    return render_template('manage.html')

def inizializzaDati():
    if not db.session.query(Tavolo).first():
        seeds.generaTavoli()
        seeds.generaTV()
    
    admin_esistente = db.session.query(Utente).filter_by(ruolo=RuoloUtente.ADMIN).first()
    if not admin_esistente:
        admin, err = utenti_controller.creaAdmin()

with app.app_context():
    inizializzaDati()

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)

    

