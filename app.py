# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from functools import wraps
import os
from dotenv import load_dotenv
import pandas as pd

# 🔹 Carregar variáveis do .env
load_dotenv()

app = Flask(__name__)

# 🔹 Configuração de segurança
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma_chave_super_secreta')
SENHA_ACESSO = os.getenv('ACCESS_PASSWORD', 'senha_super_segura')

# 🔹 Caminho do arquivo CSV
CSV_PATH = r"C:\Users\joaoj\Desktop\Pessoal\ProjetoFlask\tarifas-homologadas-distribuidoras-energia-eletrica (1).csv"

# 🔹 Decorador para verificar autenticação via Cookies
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get('user_id'):
            flash("⚠  Insira a senha correta para acessar esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def ler_csv(filters, page=1, per_page=50):
    df = pd.read_csv(CSV_PATH, delimiter=';', encoding='latin1', low_memory=False)

    # Aplicar filtros conforme as colunas existentes
    for column, value in filters.items():
        if value and value != 'Todos' and column in df.columns:
            df = df[df[column] == value]

    total_pages = (len(df) // per_page) + 1
    start = (page - 1) * per_page
    end = start + per_page

    return df.iloc[start:end].to_dict(orient='records'), total_pages


# 🔹 Página de login
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        senha_digitada = request.form.get("senha")
        if senha_digitada == SENHA_ACESSO:
            response = make_response(redirect(url_for("home")))
            response.set_cookie('user_id', '12345', httponly=True, max_age=3600)
            flash("✅ Login realizado com sucesso!", "success")
            return response
        else:
            flash("❌ Senha incorreta. Tente novamente.", "error")
    return render_template("login.html")


# 🔹 Página inicial
@app.route("/home")
@login_required
def home():
    return render_template("home.html")


@app.route('/medicoes_dashboard')
@login_required
def medicoes_dashboard():
    page = int(request.args.get('page', 1))

    # Captura os filtros da URL
    filters = {
        'SigAgente': request.args.get('SigAgente', 'Todos'),
        'DscBaseTarifaria': request.args.get('DscBaseTarifaria', 'Todos'),
        'DscSubGrupo': request.args.get('DscSubGrupo', 'Todos'),
        'DscModalidadeTarifaria': request.args.get('DscModalidadeTarifaria', 'Todos'),
        'DscClasse': request.args.get('DscClasse', 'Todos'),
        'DscSubClasse': request.args.get('DscSubClasse', 'Todos'),
        'DscDetalhe': request.args.get('DscDetalhe', 'Todos'),
        'NomPostoTarifario': request.args.get('NomPostoTarifario', 'Todos'),
        'DscUnidadeTerciaria': request.args.get('DscUnidadeTerciaria', 'Todos')
    }

    medicoes, total_pages = ler_csv(filters=filters, page=page)

    df = pd.read_csv(CSV_PATH, delimiter=';', encoding='latin1', low_memory=False)
    dropdown_options = {col: ['Todos'] + list(df[col].dropna().unique()) for col in filters.keys()}

    return render_template('medicoes_dashboard.html', medicoes=medicoes, total_pages=total_pages, page=page,
                           dropdown_options=dropdown_options, filters=filters)


# 🔹 Logout
@app.route("/logout")
@login_required
def logout():
    response = make_response(redirect(url_for("login")))
    response.delete_cookie('user_id')
    flash("🔒 Você saiu do sistema.", "info")
    return response


# 🔹 Inicializar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
