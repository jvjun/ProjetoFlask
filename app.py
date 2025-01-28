from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/medicoes')
def medicoes_dashboard():
    # Dados fictícios para exibição no template
    agentes = ['Agente A', 'Agente B']
    pontos_grupo = ['Ponto 1', 'Ponto 2']
    medições = [
        {'agente': 'Agente A', 'ponto_grupo': 'Ponto 1', 'data': '2025-01-01', 'hora': '10:00', 'ativa_c': 123.45},
        {'agente': 'Agente B', 'ponto_grupo': 'Ponto 2', 'data': '2025-01-01', 'hora': '11:00', 'ativa_c': 678.90},
    ]
    return render_template(
        'medicoes_dashboard.html',
        agentes=agentes,
        pontos_grupo=pontos_grupo,
        medições=medições
    )

if __name__ == '__main__':
    app.run(debug=True)
