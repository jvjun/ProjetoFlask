from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# Configuração da aplicação Flask
app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:*Back1245@127.0.0.1:3306/medicao'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o SQLAlchemy
db = SQLAlchemy(app)

# Modelo da tabela 'medicao'
class Medicao(db.Model):
    __tablename__ = 'medicao'

    id = db.Column(db.Integer, primary_key=True)
    agente = db.Column(db.String(100), nullable=False)
    ponto_grupo = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    ativa_c = db.Column(db.Float, nullable=False)
    qualidade = db.Column(db.String(50), nullable=False)
    origem = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

# Rota inicial para renderizar a página Home
@app.route('/')
def home():
    return render_template('home.html')  # Renderiza o arquivo home.html

# Rota para a página Medições
@app.route('/medicoes_dashboard')
def medicoes_dashboard():
    # Obtendo o número da página a partir dos parâmetros da URL
    page = request.args.get('page', 1, type=int)  # Página padrão é 1
    per_page = 50  # Quantidade de registros por página

    # Consulta ao banco com paginação
    paginacao = Medicao.query.paginate(page=page, per_page=per_page)

    return render_template(
        'medicoes_dashboard.html',
        medicoes=paginacao.items,  # Registros da página atual
        page=page,  # Página atual
        total_pages=paginacao.pages  # Total de páginas
    )

# API para listar medições (opcional)
@app.route('/api/medicoes', methods=['GET'])
def listar_medicoes_api():
    medicoes = Medicao.query.all()
    resultado = [
        {
            "id": medicao.id,
            "agente": medicao.agente,
            "ponto_grupo": medicao.ponto_grupo,
            "data": medicao.data.strftime('%Y-%m-%d'),
            "hora": medicao.hora.strftime('%H:%M:%S'),
            "ativa_c": medicao.ativa_c,
            "qualidade": medicao.qualidade,
            "origem": medicao.origem,
            "timestamp": medicao.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for medicao in medicoes
    ]
    return jsonify(resultado), 200

# Inicializar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
