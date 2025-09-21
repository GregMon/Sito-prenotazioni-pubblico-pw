from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, jsonify
from utils.enums import RuoloUtente
from controllers import utenti_controller, prenotazioni_controller, tavoli_controller
import jwt


admin_bp = Blueprint('admin', __name__, template_folder='views')

@admin_bp.route('/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'msg': 'Formato JSON non valido'}), 400
    
    print("Content-Type:", request.content_type)
    print("Raw data:", request.data)

    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'msg': 'Email e password sono obbligatori'}), 400

    utente = utenti_controller.getUtentebyEmail(email)

    if not utente:
        return jsonify({'success': False, 'msg': 'Email errata'}), 400
    
    if utente.ruolo != RuoloUtente.ADMIN:
        return jsonify({'success': False, 'msg': 'L email inserita non corrisponde con quella dell amministratore'}), 403

    is_valid, error_msg = utenti_controller.verificaPassword(utente, password)

    if not is_valid:
        return jsonify({'success': False, 'msg': error_msg or 'Password errata'}), 400
    
    if utente.prima_volta:
        return jsonify({'success': False, 'msg': 'Accesso non consentito, cambia la password al primo accesso'}), 403
        
    
    token = utenti_controller.generate_jwt(utente)

    response = jsonify({
        'success': True,
        'msg': 'Login effettuato con successo',
    })

    response.set_cookie('access_token', token, httponly=True, secure=True, samesite='Strict')
    return response, 200

    
@admin_bp.route('/change_password', methods=['POST'])
def change_password_admin():

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'msg': 'Email e password sono obbligatori'}), 400
    
    utente = utenti_controller.getUtentebyEmail(email)

    if not utente:
        return jsonify({'success': False, 'msg': 'Email errata'}), 400
    
    if utente.ruolo != RuoloUtente.ADMIN:
        return jsonify({'success': False, 'msg': 'L email inserita non corrisponde con quella dell amministratore'}), 403

    utenti_controller.changePassword(utente, password)
    return jsonify({'success': True, 'msg': 'Password cambiata con successo'}), 200

# Decorator per la verifica del token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')

        if not token:
            return jsonify({'success': False, 'msg': 'Token mancante'}), 401

        try:
            payload = jwt.decode(token, utenti_controller.getSecretKey(), algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'msg': 'Token scaduto'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'msg': 'Token non valido'}), 403

        return f(*args, **kwargs, payload=payload)
    return decorated

#route per l'area riservata dell'amministratore
@admin_bp.route('/dashboard', methods=['GET'])
@token_required
def area_riservata(payload):
    nome = payload.get('nome', 'Admin')
    return render_template('dashboard.html', nome=nome)

@admin_bp.route('/logout', methods=['GET'])
def logout_admin():
    flash('Logout effettuato con successo', 'success')
    response = redirect('/login')
    response.delete_cookie('access_token')
    return response, 302


# route per popolare la dashboard dell'amministratore con utenti e prenotazioni
@admin_bp.route('/elenco_utenti', methods=['GET'])
def get_utenti():
    lista, errore = utenti_controller.listaUtenti()
    if errore:
        return jsonify({ "success": False, "msg": errore }), 404
    return jsonify({ "success": True, "data": lista }), 200


@admin_bp.route('/elenco_prenotazioni', methods=['GET'])
def get_prenotazioni():
    lista, errore = prenotazioni_controller.listaPrenotazioni()
    if errore:
        return jsonify({ "success": False, "msg": errore }), 404
    return jsonify({ "success": True, "data": lista }), 200

#aggiorna i tavoli e le tv con le nuove posizioni
@admin_bp.route('/update', methods=['POST'])
def update_posizoni():
    data = request.get_json()

    if not data or 'tv' not in data or 'tavoli' not in data:
        return jsonify({'error': 'Dati incompleti'}), 400
    
    for tv_data in data['tv']:
        tavoli_controller.modificaPosizioneTV(tv_data['id'], tv_data['posizioneX'], tv_data['posizioneY'], tv_data['rotazione'])
    
    for tavolo_data in data['tavoli']:
        tavoli_controller.modificaPosizioneTavolo(tavolo_data['numero'], tavolo_data['posizioneX'], tavolo_data['posizioneY'])

    return jsonify({'success': True, 'message': 'Posizioni aggiornate'})


@admin_bp.route('/elimina_prenotazioni/<int:id>', methods=['DELETE'])
def elimina_prenotazione(id):
    result, err = prenotazioni_controller.deletePrenotazione(id)
    if err:
        return jsonify({ "success": False, "msg": err }), 404
    return jsonify({ "success": True, "data": result }), 200

