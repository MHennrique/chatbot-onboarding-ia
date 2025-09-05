import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import docx
import pandas as pd
import PyPDF2
import google.generativeai as genai

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar a API Key do Google
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Inicializa o Flask, que será nosso servidor web
app = Flask(__name__)
CORS(app, resources={r"/ask": {"origins": "http://127.0.0.1:5500"}})

# --- PARTE 1: LER OS DOCUMENTOS ---
def ler_documentos_pasta(caminho_pasta):
    """Lê todos os arquivos .txt, .docx, .pdf e .csv de uma pasta."""
    base_conhecimento = ""
    print(f"Lendo documentos de: {caminho_pasta}")

    for nome_arquivo in os.listdir(caminho_pasta):
        caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
        try:
            if nome_arquivo.endswith(".txt"):
                with open(caminho_completo, 'r', encoding='utf-8') as f:
                    base_conhecimento += f.read() + "\n"
            elif nome_arquivo.endswith(".docx"):
                doc = docx.Document(caminho_completo)
                for para in doc.paragraphs:
                    base_conhecimento += para.text + "\n"
            elif nome_arquivo.endswith(".pdf"):
                with open(caminho_completo, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        base_conhecimento += page.extract_text() + "\n"
            # NOVO BLOCO para ler arquivos .csv
            elif nome_arquivo.endswith(".csv"):
                df = pd.read_csv(caminho_completo)
                base_conhecimento += df.to_string() + "\n"

            print(f"  - Arquivo '{nome_arquivo}' lido com sucesso.")
        except Exception as e:
            print(f"Erro ao ler o arquivo {nome_arquivo}: {e}")
            
    return base_conhecimento

CONTEUDO_EMPRESA = ler_documentos_pasta('documentos')
print("\nBase de conhecimento carregada com sucesso!")


# --- MUDANÇA 1: FUNÇÃO DE IA ATUALIZADA PARA USAR HISTÓRICO ---
def obter_resposta_ia(pergunta_usuario, base_conhecimento, historico_conversa):
    """Inicia um chat com o Gemini, usando o histórico para manter o contexto."""
    
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Instrução inicial para o chatbot
    instrucao_sistema = f"""
    Você é um chatbot de onboarding. Responda perguntas baseando-se ESTRITAMENTE no CONTEÚDO fornecido abaixo.
    Se a resposta não estiver no CONTEÚDO, diga: 'Desculpe, não encontrei essa informação nos meus documentos.'.
    Não invente informações.

    CONTEÚDO:
    ---
    {base_conhecimento}
    ---
    """
    
    # Prepara o histórico para o modelo, começando com a instrução do sistema
    historico_formatado = [{"role": "user", "parts": [instrucao_sistema]}]
    # O Gemini espera uma resposta do 'model' após a instrução, vamos simular uma.
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

# --- MUDANÇA 2: ROTA DA API ATUALIZADA PARA RECEBER O HISTÓRICO ---
@app.route('/ask', methods=['POST'])
def ask_chatbot():
    """Recebe a pergunta e o histórico do site."""
    dados = request.json
    pergunta = dados.get('question')
    # Recebe o histórico, ou uma lista vazia se não houver
    historico = dados.get('history', [])

    if not pergunta:
        return jsonify({"error": "Nenhuma pergunta foi fornecida"}), 400

    resposta = obter_resposta_ia(pergunta, CONTEUDO_EMPRESA, historico)
    
    return jsonify({"answer": resposta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)