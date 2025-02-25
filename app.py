from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from functools import wraps
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma_chave_super_secreta')
SENHA_ACESSO = os.getenv('ACCESS_PASSWORD', 'senha_super_segura')

CSV_PATH = r"C:\Users\joaoj\Desktop\Pessoal\ProjetoFlask\tarifas-homologadas-distribuidoras-energia-eletrica (1).csv"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.cookies.get('user_id'):
            flash("⚠ Insira a senha correta para acessar esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def ler_csv(filters, page=1, per_page=50):
    df = pd.read_csv(CSV_PATH, delimiter=';', encoding='latin1', low_memory=False)

    for column, value in filters.items():
        if value and value != 'Todos' and column in df.columns:
            df = df[df[column] == value]

    total_pages = (len(df) // per_page) + 1
    start = (page - 1) * per_page
    end = start + per_page

    return df.iloc[start:end].to_dict(orient='records'), total_pages

def calcular_media_anual(filters):
    df = pd.read_csv(CSV_PATH, delimiter=';', encoding='latin1', low_memory=False)
    df['DatInicioVigencia'] = pd.to_datetime(df['DatInicioVigencia'], errors='coerce')
    df = df.dropna(subset=['DatInicioVigencia'])

    # Convertendo valores para números
    df['VlrTUSD'] = pd.to_numeric(df['VlrTUSD'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['VlrTE'] = pd.to_numeric(df['VlrTE'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df = df.dropna(subset=['VlrTUSD', 'VlrTE'])

    # Filtra os dados conforme os filtros fornecidos
    for column, value in filters.items():
        if value and value != 'Todos' and column in df.columns:
            df = df[df[column] == value]

    # Adiciona coluna de ano para agrupar os dados
    df['AnoVigencia'] = df['DatInicioVigencia'].dt.year
    df_grouped = df.groupby('AnoVigencia').agg({'VlrTUSD': 'mean', 'VlrTE': 'mean'}).reset_index()

    anos = df_grouped['AnoVigencia'].tolist() if not df_grouped.empty else []
    vlr_tusd = df_grouped['VlrTUSD'].tolist() if not df_grouped.empty else []
    vlr_te = df_grouped['VlrTE'].tolist() if not df_grouped.empty else []

    return anos, vlr_tusd, vlr_te


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        senha_digitada = request.form.get("senha")
        if senha_digitada == SENHA_ACESSO:
            response = make_response(redirect(url_for("home")))
            response.set_cookie('user_id', '12345', httponly=True, max_age=3600)
            flash("Login realizado com sucesso!", "success")
            return response
        else:
            flash("Senha incorreta. Tente novamente.", "error")
    return render_template("login.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route('/medicoes_dashboard')
@login_required
def medicoes_dashboard():
    page = int(request.args.get('page', 1))

    # Define os filtros a partir dos parâmetros da URL
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

    # Lê o CSV e aplica os filtros para exibir a tabela
    medicoes, total_pages = ler_csv(filters=filters, page=page)

    # Lê o CSV novamente para popular os filtros dropdown
    df = pd.read_csv(CSV_PATH, delimiter=';', encoding='latin1', low_memory=False)
    dropdown_options = {col: ['Todos'] + list(df[col].dropna().unique()) for col in filters.keys()}

    # Calcula os dados do gráfico para o agente filtrado
    anos, vlr_tusd, vlr_te = calcular_media_anual(filters)

    return render_template(
        'medicoes_dashboard.html',
        medicoes=medicoes,
        total_pages=total_pages,
        page=page,
        dropdown_options=dropdown_options,
        filters=filters,
        anos=anos,
        vlr_tusd=vlr_tusd,
        vlr_te=vlr_te
    )

@app.route("/logout")
@login_required
def logout():
    response = make_response(redirect(url_for("login")))
    response.delete_cookie('user_id')
    flash("Você saiu do sistema.", "info")
    return response

@app.route('/grafico')
@login_required
def grafico():
    anos, vlr_tusd, vlr_te = calcular_media_anual()
    return render_template('medicoes_dashboard.html', anos=anos, vlr_tusd=vlr_tusd, vlr_te=vlr_te)

if __name__ == '__main__':
    app.run(debug=True)
