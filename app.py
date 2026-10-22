from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from functools import wraps
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from admin_reports import init_report_routes

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'asistencia.db')
app = Flask(__name__)
app.secret_key = os.environ.get('LINKX_SECRET_KEY', 'CAMBIAR-ESTA-CLAVE-ANTES-DE-USAR')
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

def db():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row; return c

def init_db():
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT \'employee\', active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, movement TEXT NOT NULL, timestamp TEXT NOT NULL, note TEXT DEFAULT \'\', FOREIGN KEY(user_id) REFERENCES users(id))')
        if not c.execute('SELECT id FROM users WHERE email=?', ('admin@linkx.local',)).fetchone():
            c.execute('INSERT INTO users(name,email,password_hash,role,active,created_at) VALUES(?,?,?,?,1,?)', ('Administrador LINK X','admin@linkx.local',generate_password_hash('Admin123!'),'admin',datetime.now().isoformat(timespec='seconds')))

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get('user_id'): return redirect(url_for('login'))
        return f(*a, **k)
    return w

def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get('user_id'): return redirect(url_for('login'))
        if session.get('role') != 'admin': abort(403)
        return f(*a, **k)
    return w

@app.context_processor
def context(): return {'current_user': session.get('name'), 'current_role': session.get('role')}

@app.route('/')
def home(): return redirect(url_for('dashboard' if session.get('user_id') else 'login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        with db() as c: u=c.execute('SELECT * FROM users WHERE email=? AND active=1',(email,)).fetchone()
        if u and check_password_hash(u['password_hash'], password):
            session.clear(); session.update(user_id=u['id'], name=u['name'], role=u['role']); return redirect(url_for('dashboard'))
        flash('Correo o contraseña incorrectos, o cuenta desactivada.', 'error')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    with db() as c:
        last=c.execute('SELECT movement,timestamp FROM attendance WHERE user_id=? ORDER BY id DESC LIMIT 1',(session['user_id'],)).fetchone()
        if last and last['movement']=='Entrada' and last['timestamp'][:10]==date.today().isoformat():
            c.execute('INSERT INTO attendance(user_id,movement,timestamp,note) VALUES(?,?,?,?)',(session['user_id'],'Salida',datetime.now().isoformat(timespec='seconds'),'Salida al cerrar sesión'))
    session.clear(); return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    uid=session['user_id']; today=date.today().isoformat()
    with db() as c:
        if session['role']=='admin':
            stats={'today':c.execute('SELECT COUNT(*) FROM attendance WHERE substr(timestamp,1,10)=?',(today,)).fetchone()[0], 'employees':c.execute("SELECT COUNT(*) FROM users WHERE role='employee' AND active=1").fetchone()[0], 'entries':c.execute("SELECT COUNT(*) FROM attendance WHERE movement='Entrada' AND substr(timestamp,1,10)=?",(today,)).fetchone()[0], 'exits':c.execute("SELECT COUNT(*) FROM attendance WHERE movement='Salida' AND substr(timestamp,1,10)=?",(today,)).fetchone()[0]}
            records=c.execute('SELECT a.*,u.name,u.email FROM attendance a JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 12').fetchall()
        else:
            stats={'today':c.execute('SELECT COUNT(*) FROM attendance WHERE user_id=? AND substr(timestamp,1,10)=?',(uid,today)).fetchone()[0], 'employees':None, 'entries':c.execute("SELECT COUNT(*) FROM attendance WHERE user_id=? AND movement='Entrada' AND substr(timestamp,1,10)=?",(uid,today)).fetchone()[0], 'exits':c.execute("SELECT COUNT(*) FROM attendance WHERE user_id=? AND movement='Salida' AND substr(timestamp,1,10)=?",(uid,today)).fetchone()[0]}
            records=c.execute('SELECT a.*,u.name,u.email FROM attendance a JOIN users u ON u.id=a.user_id WHERE user_id=? ORDER BY a.id DESC LIMIT 12',(uid,)).fetchall()
    return render_template('dashboard.html',stats=stats,records=records,now=datetime.now().strftime('%d/%m/%Y'))

@app.route('/marcar/<movement>',methods=['POST'])
@login_required
def mark(movement):
    if movement not in ('Entrada','Salida','Inicio de comida','Fin de comida'): abort(400)
    with db() as c: c.execute('INSERT INTO attendance(user_id,movement,timestamp,note) VALUES(?,?,?,?)',(session['user_id'],movement,datetime.now().isoformat(timespec='seconds'),''))
    flash(f'{movement} registrada correctamente.','success'); return redirect(url_for('dashboard'))

@app.route('/admin/usuarios',methods=['GET','POST'])
@admin_required
def users_admin():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password',''); role=request.form.get('role','employee')
        if not name or not email or len(password)<8 or role not in ('admin','employee'): flash('Completa los campos. Contraseña mínima de 8 caracteres.','error')
        else:
            try:
                with db() as c: c.execute('INSERT INTO users(name,email,password_hash,role,active,created_at) VALUES(?,?,?,?,1,?)',(name,email,generate_password_hash(password),role,datetime.now().isoformat(timespec='seconds')))
                flash('Usuario creado correctamente.','success')
            except sqlite3.IntegrityError: flash('Ese correo ya está registrado.','error')
        return redirect(url_for('users_admin'))
    with db() as c: users=c.execute('SELECT id,name,email,role,active FROM users ORDER BY name').fetchall()
    return render_template('users.html',users=users)

@app.errorhandler(403)
def forbidden(e): return render_template('403.html'),403

init_report_routes(app, db, admin_required)
if __name__=='__main__':
    init_db()
    app.run(host='127.0.0.1',port=5000,debug=False)
