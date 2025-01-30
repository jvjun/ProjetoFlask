from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
import os

app = Flask(__name__)

# 🔹 Configuração para Sessão via Cookies Seguros
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma_chave_super_secreta')  # Use uma chave forte
app.config['SESSION_TYPE'] = 'filesystem'  # Mantemos para suporte local, mas usaremos cookies
app.config['SESSION_PERMANENT'] = False  # Sessão expira quando o navegador fecha
app.config['SESSION_COOKIE_SECURE'] = True  # 🔹 Cookies seguros (HTTPS obrigatório no Render)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 🔹 Protege contra scripts maliciosos
app.config['SESSION_USE_SIGNER'] = True  # 🔹 Assina os cookies para evitar manipulação
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # PostgreSQL no Render
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 🔹 Decorador para verificar autenticação via Cookies
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:  # Verifica se o usuário está autenticado
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 🔹 Modelo da tabela Medicao
class Medicao(db.Model):
    __tablename__ = 'medicao'
    agente = db.Column(db.String(100), primary_key=True)
    ponto_grupo = db.Column(db.String(100), primary_key=True)
    data = db.Column(db.Date, primary_key=True)
    hora = db.Column(db.Time, primary_key=True)
    ativa_c = db.Column(db.Float)
    qualidade = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.now())

# 🔹 Modelo da tabela Usuario
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# 🔹 Criar tabelas no banco de dados
with app.app_context():
    try:
        db.create_all()
        print("Banco de dados conectado com sucesso! ✅")
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

# 🔹 Rota inicial para redirecionar ao login
@app.route('/')
def login_redirect():
    return redirect(url_for('login'))

# 🔹 Rota para login usando Cookies
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and bcrypt.check_password_hash(usuario.password, password):
            session['user_id'] = usuario.id  # 🔹 Salva o ID do usuário na sessão (cookie)
            response = make_response(redirect(url_for('home')))
            response.set_cookie('user_id', str(usuario.id), httponly=True, secure=True, max_age=3600)  # 🔹 Cookie seguro
            return response
        
        return "Usuário ou senha inválidos!", 400

    return render_template('login.html')

# 🔹 Rota para registro
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

# 🔹 Rota para a página inicial
@app.route('/home')
@login_required
def home():
    return render_template('home.html')

# 🔹 Rota para o dashboard de medições
@app.route('/medicoes_dashboard')
@login_required
def medicoes_dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    paginacao = Medicao.query.paginate(page=page, per_page=50)
    return render_template(
        'medicoes_dashboard.html',
        medicoes=paginacao.items,
        page=page,
        total_pages=paginacao.pages
    )

# 🔹 API para listar medições
@app.route('/api/medicoes', methods=['GET'])
@login_required
def listar_medicoes_api():
    medicoes = Medicao.query.all()
    resultado = [
        {
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

# 🔹 Rota para logout via Cookies
@app.route('/logout')
@login_required
def logout():
    session.clear()  # 🔹 Limpa a sessão do Flask
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('user_id')  # 🔹 Remove o cookie de autenticação
    return response

# 🔹 Inicializar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
