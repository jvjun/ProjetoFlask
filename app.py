from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from dotenv import load_dotenv
import requests
from flask import Response
from config import Config

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
            flash("⚠  Insira a senha correta para acessar esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

# 🔹 Rota da página protegida do Power BI
@app.route("/dashboard_powerbi")
@login_required
def dashboard_powerbi():
    return render_template("dashboard_powerbi.html")  # 🔹 Removemos a passagem direta da URL

@app.route("/proxy_powerbi")
def proxy_powerbi():
    power_bi_url = os.getenv("POWER_BI_URL")
    headers = {"User-Agent": "Mozilla/5.0"}  # Simula um navegador
    try:
        response = requests.get(power_bi_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Adicione cabeçalhos de CORS para permitir recursos externos
        proxied_response = Response(response.content, content_type=response.headers.get('Content-Type'))
        proxied_response.headers["Access-Control-Allow-Origin"] = "*"
        proxied_response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        proxied_response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return proxied_response
    except requests.exceptions.RequestException as e:
        return f"Erro ao carregar o dashboard: {e}", 500

# 🔹 API segura para retornar a URL do Power BI
@app.route("/get_powerbi_url", methods=["GET"])
@login_required
def get_powerbi_url():
    powerbi_url = Config.POWER_BI_URL
    if not powerbi_url:
        return jsonify({"error": "⚠ O link do Power BI não foi configurado."}), 500

    return jsonify({"url": powerbi_url})  # 🔹 Envia a URL de forma segura

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
