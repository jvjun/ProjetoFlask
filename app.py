from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)

# Configurações do aplicativo
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua_chave_secreta'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Modelo do Banco de Dados
class Medicao(db.Model):
    __tablename__ = 'medicao'
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # FK para usuários
    agente = db.Column(db.String(100))
    ponto_grupo = db.Column(db.String(100))
    data = db.Column(db.Date)
    hora = db.Column(db.Time)
    ativa_c = db.Column(db.Float)
    qualidade = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.now())  # Data/hora de criação

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Criar tabelas no banco de dados (caso ainda não existam)
with app.app_context():
    try:
        db.create_all()
        print("Banco de dados conectado com sucesso! ✅")
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

# Rota inicial para renderizar a página de login
@app.route('/')
def login_redirect():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and bcrypt.check_password_hash(usuario.password, password):
            session['user_id'] = usuario.id
            return redirect(url_for('home'))
        return "Usuário ou senha inválidos!", 400
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        if Usuario.query.filter_by(username=username).first():
            return "Usuário já cadastrado!", 400
        novo_usuario = Usuario(username=username, password=password)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/medicoes_dashboard')
def medicoes_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    per_page = 50
    paginacao = Medicao.query.filter_by(user_id=session['user_id']).paginate(page=page, per_page=per_page)
    return render_template(
        'medicoes_dashboard.html',
        medicoes=paginacao.items,
        page=page,
        total_pages=paginacao.pages
    )

# API para listar medições
@app.route('/api/medicoes', methods=['GET'])
def listar_medicoes_api():
    medicoes = Medicao.query.all()
    resultado = [
        {
            "user_id": medicao.user_id,
            "agente": medicao.agente,
            "ponto_grupo": medicao.ponto_grupo,
            "data": medicao.data.strftime('%Y-%m-%d'),
            "hora": medicao.hora.strftime('%H:%M:%S'),
            "ativa_c": medicao.ativa_c,
            "qualidade": medicao.qualidade,
            "timestamp": medicao.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for medicao in medicoes
    ]
    return jsonify(resultado), 200

# Inicializar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
