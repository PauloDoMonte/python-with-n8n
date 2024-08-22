from flask import Flask, render_template, request, jsonify
import requests
import re
import pandas as pd
import json

app = Flask(__name__)

# URL do Webhook do n8n
N8N_WEBHOOK_URL = 'http://localhost:5678/webhook-test/v1/chat'

# Carregar dados do CSV
def carregar_dados_csv():
    # Ajuste o caminho conforme necessário
    df = pd.read_csv('data.csv')
    return df

# Função para verificar disponibilidade
def verificar_disponibilidade(df, regiao=None):
    if regiao:
        df = df[df['região'].str.contains(regiao, case=False, na=False)]
    return df[df['disponível'] == 'Sim']

# Função para buscar preço
def buscar_preco(df, tipo, regiao=None):
    if regiao:
        df = df[df['região'].str.contains(regiao, case=False, na=False)]
    return df[['imovel', tipo]]

# Função para encontrar localização
def encontrar_localizacao(df):
    return df[['imovel', 'região']]

def extrair_regiao(pergunta):
    padrao = re.compile(r'região\s*(?:da|de|do)?\s+([\w\s]+)', re.IGNORECASE)
    resultado = padrao.search(pergunta)
    
    if resultado:
        regiao = resultado.group(1).strip()
        return regiao
    else:
        return None

def classificar_pergunta(pergunta):
    """
    Classifica o tipo de pergunta como relacionada à disponibilidade, preço ou localização.
    
    Args:
        pergunta (str): A pergunta do usuário.
        
    Returns:
        str: O tipo de pergunta classificado como 'disponibilidade', 'preço', 'localização', 
        ou 'indefinido' se não for possível classificar.
    """
    pergunta = pergunta.lower()  # Converter para minúsculas para facilitar a correspondência
    
    # Classificar como disponibilidade
    if re.search(r'\b(disponível|disponibilidade|tem disponível|tem vaga|tem estoque|está livre|está disponível|está em estoque|há|existe|está para venda|está para alugar|encontrar|disponibilidade atual)\b', pergunta, re.IGNORECASE):
        return 'disponibilidade'
    
    # Classificar como preço
    elif re.search(r'\b(preço|valor|quanto custa|quanto é|preço de venda|preço de aluguel|qual é o preço|qual o valor|custo|preço estimado|valor estimado|quanto sai)\b', pergunta, re.IGNORECASE):
        return 'preço'
    
    # Classificar como localização
    elif re.search(r'\b(localização|região|onde está|em que região|localização da propriedade|onde fica|qual é a localização|em qual área|em qual bairro|localização exata)\b', pergunta, re.IGNORECASE):
        return 'localização'
    
    # Caso não se enquadre nas categorias acima
    else:
        return 'indefinido'

@app.route('/data', methods=['GET'])
def get_data():
    tipo_pergunta = request.args.get('type')
    regiao = request.args.get('regiao', default=None, type=str)

    print(f"Received type: {tipo_pergunta}")

    # Carregar dados
    df = carregar_dados_csv()

    # Processar a solicitação com base no tipo de pergunta
    if tipo_pergunta == 'disponibilidade':
        resposta = verificar_disponibilidade(df, regiao)
        response_type = 'disponibilidade'
    elif tipo_pergunta == 'preço':
        tipo_preco = 'valor_venda' if 'venda' in request.args else 'valor_aluguel'
        resposta = buscar_preco(df, tipo_preco, regiao)
        response_type = 'preço'
    elif tipo_pergunta == 'localização':
        resposta = encontrar_localizacao(df)
        response_type = 'localização'
    else:
        resposta = {'error': 'Tipo de pergunta não reconhecido'}
        response_type = 'erro'

    # Incluir o tipo de resposta no JSON
    if isinstance(resposta, pd.DataFrame):
        resposta = resposta.to_dict(orient='records')
    
    return jsonify({
        'response_type': response_type,
        'data': resposta
    })


@app.route('/', methods=['GET', 'POST'])
def index():
    response_message = None
    
    if request.method == 'POST':
        text = request.form.get('message')

        if text:
            try:
                tipo_pergunta = classificar_pergunta(text)
                regiao = extrair_regiao(text)
                
                payload = {
                    'question': text,
                    'type': tipo_pergunta,
                    'regiao': regiao
                }
                
                response = requests.post(N8N_WEBHOOK_URL, json=payload)
                
                if response.ok:
                    try:
                        response_text = response.text
                        print("Resposta bruta do N8N:", response_text)  # Depuração

                        # Converter resposta de texto para JSON
                        try:
                            response_json = json.loads(response_text)
                        except json.JSONDecodeError:
                            response_message = 'Erro ao decodificar JSON da resposta do N8N.'
                            return render_template('index.html', response_message=response_message)

                        # Verificar o tipo de resposta
                        response_type = response_json.get('response_type', 'erro')
                        data = response_json.get('data', [])

                        if response_type == 'disponibilidade':
                            # Construir a tabela de disponibilidade
                            formatted_response = (
                                "<table border='1' style='width:100%; border-collapse: collapse;'>"
                                "<tr>"
                                "<th>Imóvel</th>"
                                "<th>Região</th>"
                                "<th>Disponível</th>"
                                "</tr>"
                            )
                            for item in data:
                                imovel = item.get('imovel', 'N/A')
                                regiao = item.get('região', 'N/A')
                                disponivel = item.get('disponível', 'N/A')
                                formatted_response += (
                                    f"<tr>"
                                    f"<td>{imovel}</td>"
                                    f"<td>{regiao}</td>"
                                    f"<td>{disponivel}</td>"
                                    f"</tr>"
                                )
                            formatted_response += "</table>"

                        elif response_type == 'preço':
                            # Construir a tabela de preço
                            formatted_response = (
                                "<table border='1' style='width:100%; border-collapse: collapse;'>"
                                "<tr>"
                                "<th>Imóvel</th>"
                                "<th>Preço</th>"
                                "</tr>"
                            )
                            for item in data:
                                imovel = item.get('imovel', 'N/A')
                                preco = item.get('valor_aluguel', 'N/A') if 'aluguel' in text else item.get('valor_venda', 'N/A')
                                formatted_response += (
                                    f"<tr>"
                                    f"<td>{imovel}</td>"
                                    f"<td>{preco}</td>"
                                    f"</tr>"
                                )
                            formatted_response += "</table>"

                        elif response_type == 'localização':
                            # Construir a tabela de localização
                            formatted_response = (
                                "<table border='1' style='width:100%; border-collapse: collapse;'>"
                                "<tr>"
                                "<th>Imóvel</th>"
                                "<th>Região</th>"
                                "</tr>"
                            )
                            for item in data:
                                imovel = item.get('imovel', 'N/A')
                                regiao = item.get('região', 'N/A')
                                formatted_response += (
                                    f"<tr>"
                                    f"<td>{imovel}</td>"
                                    f"<td>{regiao}</td>"
                                    f"</tr>"
                                )
                            formatted_response += "</table>"

                        else:
                            formatted_response = 'Resposta inválida do N8N.'

                        response_message = formatted_response
                    except ValueError:
                        response_message = 'Resposta inválida do N8N'
                else:
                    response_message = 'Erro na requisição ao N8N'
            except Exception as e:
                response_message = f'Erro ao processar os dados: {e}'
        else:
            response_message = 'Texto vazio enviado.'

    return render_template('index.html', response_message=response_message)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
