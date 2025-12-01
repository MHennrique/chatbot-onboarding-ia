# app.py

import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template

# Importa a base de conhecimento pronta do nosso novo módulo
from knowledge_base import CONTEUDO_EMPRESA

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar a API Key do Google
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Inicializa o Flask, que será nosso servidor web
app = Flask(__name__)
CORS(app)#(app, resources={r"/ask": {"origins": "http://127.0.0.1:5500"}})

# Confirma que a base de conhecimento foi carregada (apenas para debug)
print(f"Conteúdo da empresa importado (Tamanho: {len(CONTEUDO_EMPRESA)} caracteres)")


# --- FUNÇÃO DE IA ATUALIZADA PARA USAR HISTÓRICO ---
def obter_resposta_ia(pergunta_usuario, base_conhecimento, historico_conversa):
    """Inicia um chat com o Gemini, usando o histórico para manter o contexto."""
    
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Instrução inicial para o chatbot (mantida a mesma lógica de linkagem)
    instrucao_sistema = f"""
    Você é um chatbot de onboarding da Rocha Alimentos. Responda perguntas baseando-se ESTRITAMENTE no CONTEÚDO fornecido abaixo.
    
    Regras de Link:
    1. Se a pergunta for sobre 'férias', 'solicitar férias' ou 'como tirar férias', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
       
       Para o processo completo e detalhado, acesse: [Processo Completo de Férias](artigo_ferias.html)

    2. Se a pergunta for sobre 'missão', 'visão', 'valores' ou 'história da empresa':
       - Responda apenas com a informação específica solicitada (ex: se perguntar "missão", responda apenas a missão).
       - Em seguida, inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
    
       Para conhecer nossa História, Missão e Valores completos, acesse: [Nossa Identidade](mvv_historia.html)

    3. Se a pergunta for sobre 'benefícios', 'plano de saúde', 'vale alimentação' ou 'auxílio educação', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
       
       Para ver o detalhe completo dos benefícios e valores, acesse: [Detalhamento de Benefícios](artigo_beneficios.html)

    Se a resposta não estiver no CONTEÚDO, diga: 'Desculpe, não encontrei essa informação nos meus documentos.'.
    Não invente informações.

    CONTEÚDO:
    ---
    {base_conhecimento}
    ---
    """
    
    # Prepara o histórico para o modelo, começando com a instrução do sistema
    historico_formatado = [{"role": "user", "parts": [instrucao_sistema]}]
    historico_formatado.append({"role": "model", "parts": ["Entendido. Estou pronto para responder com base no conteúdo fornecido."]})
    
    # Adiciona o histórico da conversa real
    historico_formatado.extend(historico_conversa)

    try:
        # Inicia o chat com o histórico completo
        chat = model.start_chat(history=historico_formatado)
        # Envia a nova pergunta do usuário
        response = chat.send_message(pergunta_usuario)
        return response.text
    except Exception as e:
        print(f"Erro na API do Google Gemini: {e}")
        return "Ocorreu um erro ao me conectar com a inteligência artificial."

# --- ROTA DA API ---
@app.route('/ask', methods=['POST'])
def ask_chatbot():
    """Recebe a pergunta e o histórico do site."""
    dados = request.json
    pergunta = dados.get('question')
    historico = dados.get('history', [])

    if not pergunta:
        return jsonify({"error": "Nenhuma pergunta foi fornecida"}), 400

    # Passa o conteúdo importado para a função
    resposta = obter_resposta_ia(pergunta, CONTEUDO_EMPRESA, historico) 
    
    return jsonify({"answer": resposta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/')
def index():
    """Rota raiz para servir o frontend (index.html)."""
    return render_template('index.html')

@app.route('/mvv')
def mvv_page():
    """Rota para a página Missão, Visão e Valores."""
    return render_template('mvv_historia.html')

@app.route('/ferias')
def ferias_page():
    """Rota para a página de Solicitação de Férias."""
    return render_template('artigo_ferias.html')

@app.route('/beneficios')
def beneficios_page():
    """Rota para a página de Benefícios Corporativos."""
    return render_template('artigo_beneficios.html')

@app.route('/contato')
def contato_page():
    """Rota para a página de Contato e Suporte."""
    return render_template('contato.html')