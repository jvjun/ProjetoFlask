from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from dotenv import load_dotenv

# 🔹 Carregar variáveis do .env
load_dotenv()

app = Flask(__name__)

# 🔹 Configuração de segurança
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma_chave_super_secreta')  
app.config['SESSION_COOKIE_SECURE'] = True  # 🔹 Cookies seguros (HTTPS obrigatório no Render)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 🔹 Protege contra scripts maliciosos
app.config['SESSION_USE_SIGNER'] = True  # 🔹 Assina os cookies para evitar manipulação
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # PostgreSQL no Render
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db = SQLAlchemy(app)

# 🔹 Senha fixa definida no .env ou padrão
SENHA_ACESSO = os.getenv('ACCESS_PASSWORD', 'senha_super_segura')

# 🔹 Decorador para verificar autenticação via Cookies
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get('user_id'):  # 🔹 Se o cookie 'user_id' não existir, redireciona para login
            flash("⚠ Você precisa fazer login para acessar esta página.", "warning")
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

# 🔹 Página de login única com senha fixa
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        senha_digitada = request.form.get("senha")

        if senha_digitada == SENHA_ACESSO:
            response = make_response(redirect(url_for("home")))
            response.set_cookie('user_id', '12345', httponly=True, secure=True, max_age=3600)  # 🔹 Cria cookie seguro
            flash("✅ Login realizado com sucesso!", "success")
            return response
        else:
            flash("❌ Senha incorreta. Tente novamente.", "error")

    return render_template("login.html")

# 🔹 Página inicial protegida
@app.route("/home")
@login_required
def home():
    return render_template("home.html")

# 🔹 Rota para o dashboard de medições (Protegida)
@app.route("/medicoes_dashboard")
@login_required
def medicoes_dashboard():
    page = request.args.get("page", 1, type=int)  
    per_page = 50  

    # 🔹 Consulta paginada no banco de dados
    paginacao = Medicao.query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "medicoes_dashboard.html",
        medicoes=paginacao.items,
        page=page,
        total_pages=paginacao.pages
    )

# 🔹 API para listar medições (Protegida)
@app.route("/api/medicoes", methods=["GET"])
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

# 🔹 Rota para logout
@app.route("/logout")
@login_required
def logout():
    response = make_response(redirect(url_for("login")))
    response.delete_cookie('user_id')  # 🔹 Remove o cookie de autenticação
    flash("🔒 Você saiu do sistema.", "info")
    return response

# 🔹 Inicializar o servidor Flask
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # 🔹 Garante que as tabelas existam antes de rodar
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
