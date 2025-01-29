from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Alterar para uma chave segura

# Configurar PostgreSQL do Render
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # Configuração com variável de ambiente
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Modelo do Banco de Medições
class Medicao(db.Model):
    __tablename__ = 'medicao'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    agente = db.Column(db.String(100))
    ponto_grupo = db.Column(db.String(100))
    data = db.Column(db.Date)
    hora = db.Column(db.Time)
    ativa_c = db.Column(db.Float)
    qualidade = db.Column(db.String(50))
    origem = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.now())

# Modelo de Usuários
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

# Rota inicial para Login
@app.route('/')
def home():
    return redirect(url_for('login'))  # Redireciona para login automaticamente

# Rota para a página de registro de usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        # Verifica se o usuário já existe
        if Usuario.query.filter_by(username=username).first():
            return "Usuário já cadastrado!", 400

        # Cria o novo usuário
        novo_usuario = Usuario(username=username, password=password)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Rota para Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and bcrypt.check_password_hash(usuario.password, password):
            session['user_id'] = usuario.id
            return redirect(url_for('dashboard'))
        return "Usuário ou senha inválidos!", 400
    return render_template('login.html')

# Rota para Dashboard (onde o usuário pode adicionar e visualizar medições)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        novo_dado = Medicao(
            user_id=session['user_id'],
            agente=request.form['agente'],
            ponto_grupo=request.form['ponto_grupo'],
            data=request.form['data'],
            hora=request.form['hora'],
            ativa_c=request.form['ativa_c'],
            qualidade=request.form['qualidade'],
            origem=request.form['origem']
        )
        db.session.add(novo_dado)
        db.session.commit()

    # Buscar medições apenas do usuário logado
    dados = Medicao.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', dados=dados)

# Rota para Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Inicializar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
