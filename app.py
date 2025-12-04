import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai

from knowledge_base import CONTEUDO_EMPRESA

load_dotenv()

# Configurar a API Key do Google (usará a variável de ambiente no Railway)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
# CORS simplificado para funcionar no ambiente de produção
CORS(app) 

print(f"Conteúdo da empresa importado (Tamanho: {len(CONTEUDO_EMPRESA)} caracteres)")

def obter_resposta_ia(pergunta_usuario, base_conhecimento, historico_conversa):
    """Inicia um chat com o Gemini, usando o histórico para manter o contexto."""
    
    # O Gemini deve se apresentar como Guia Rocha
    model = genai.GenerativeModel('gemini-2.5-flash')

    instrucao_sistema = f"""
    Você é o **Guia Rocha**, o chatbot de onboarding da Rocha Alimentos. Responda perguntas baseando-se ESTRITAMENTE no CONTEÚDO fornecido abaixo.
    
    Regras de Link:
    1. Se a pergunta for sobre 'férias', 'solicitar férias' ou 'como tirar férias', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
        
        Para o processo completo e detalhado, acesse: [Processo Completo de Férias](/ferias)

    2. Se a pergunta for sobre 'missão', 'visão', 'valores' ou 'história da empresa':
        - Responda apenas com a informação específica solicitada (ex: se perguntar "missão", responda apenas a missão).
        - Em seguida, inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
    
        Para conhecer nossa História, Missão e Valores completos, acesse: [Nossa Identidade](/mvv)

    3. Se a pergunta for sobre 'benefícios', 'plano de saúde', 'vale alimentação' ou 'auxílio educação', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
        
        Para ver o detalhe completo dos benefícios e valores, acesse: [Detalhamento de Benefícios](/beneficios)

    4. Se a pergunta for sobre 'cadastro de cliente', 'como cadastrar um cliente', 'documentos de cliente', 'Serasa' ou 'análise de crédito', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
        
        Para ver o processo detalhado, acesse: [Processo Completo de Cadastro de Cliente](/cadastro-cliente)

    5. Se a pergunta for sobre 'orçamento', 'emissão de pedido', 'liberação financeira de pedido' ou 'pedido de separação', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
        
        Para ver o fluxo completo, acesse: [Fluxo Completo de Orçamento e Pedido](/orcamento-pedido)
    
    # NOVAS REGRAS PARA OS PROCESSOS TÉCNICOS
    6. Se a pergunta for sobre 'baixa de uso e consumo', 'dar baixa', ou 'consumo interno', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
        
        Para ver o processo de baixa detalhado, acesse: [Processo de Baixa de Consumo](/baixa-consumo)

    7. Se a pergunta for sobre 'cadastro de produto', 'como cadastrar um item' ou 'dados do produto', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
        
        Para ver o passo a passo de cadastro de produto, acesse: [Passo a Passo de Cadastro](/cadastro-produto)

    8. Se a pergunta for sobre 'emissão de nota fiscal', 'emitir NF' ou 'cancelamento de nota', inclua OBRIGATORIAMENTE a seguinte linha no final da sua resposta:
        
        Para ver as regras completas de NF, acesse: [Regras de Emissão de Nota Fiscal](/emissao-nf)

    # NOVO COMPORTAMENTO PARA RESPOSTAS NEGATIVAS (RESPOSTA INTELIGENTE)
    Se o conteúdo que você precisa para responder NÃO estiver no CONTEÚDO fornecido:
    - Mantenha sempre a sua persona de "Guia Rocha" da Rocha Alimentos.
    - Diga que o tópico não está nos documentos de onboarding.
    - Sugira ao usuário que use o filtro de artigos ou entre em contato.
    
    Exemplo de resposta negativa inteligente: "Como Guia Rocha, não encontrei a informação sobre [TÓPICO] nos documentos de onboarding da empresa. Você pode usar o filtro na lateral para buscar por um artigo relacionado ou abrir um chamado na página [Contato / Abrir Chamado](/contato)."
    
    Não invente informações.

    CONTEÚDO:
    ---
    {base_conhecimento}
    ---
    """
    
    historico_formatado = [{"role": "user", "parts": [instrucao_sistema]}]
    historico_formatado.append({"role": "model", "parts": ["Entendido. Estou pronto para responder com base no conteúdo fornecido."]})
    
    historico_formatado.extend(historico_conversa)

    try:
        chat = model.start_chat(history=historico_formatado)
        response = chat.send_message(pergunta_usuario)
        return response.text
    except Exception as e:
        print(f"Erro na API do Google Gemini: {e}")
        return "Ocorreu um erro ao me conectar com a inteligência artificial."


# --- ROTAS DA API E NAVEGAÇÃO (TODAS AS ROTAS AQUI!) ---

@app.route('/ask', methods=['POST'])
def ask_chatbot():
    """Recebe a pergunta e o histórico do site."""
    dados = request.json
    pergunta = dados.get('question')
    historico = dados.get('history', [])

    if not pergunta:
        return jsonify({"error": "Nenhuma pergunta foi fornecida"}), 400

    resposta = obter_resposta_ia(pergunta, CONTEUDO_EMPRESA, historico) 
    
    return jsonify({"answer": resposta})


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


@app.route('/cadastro-cliente')
def cadastro_cliente_page():
    """Rota para a página do Processo de Cadastro de Cliente."""
    return render_template('artigo_cadastro_cliente.html')

@app.route('/orcamento-pedido')
def orcamento_pedido_page():
    """Rota para a página do Processo de Orçamento e Pedido."""
    return render_template('artigo_orcamento_pedido.html')

# NOVAS ROTAS TÉCNICAS (CONSOLIDADAS)
@app.route('/baixa-consumo')
def baixa_consumo_page():
    """Rota para a página do processo de Baixa de Uso e Consumo."""
    return render_template('artigo_baixa_consumo.html')

@app.route('/cadastro-produto')
def cadastro_produto_page():
    """Rota para a página do processo de Cadastro de Produto."""
    return render_template('artigo_cadastro_produto.html')

@app.route('/emissao-nf')
def emissao_nf_page():
    """Rota para a página do processo de Emissão da Nota Fiscal."""
    return render_template('artigo_emissao_nf.html')


if __name__ == '__main__':
    # Este bloco é o último no arquivo.
    app.run(host='0.0.0.0', port=5000, debug=True)