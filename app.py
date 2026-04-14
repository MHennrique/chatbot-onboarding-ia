import os
from functools import wraps
from dotenv import load_dotenv

# Dependências do Flask
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Dependências de Segurança e Arquivos
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Dependências da Inteligência Artificial
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PyPDF2 import PdfReader

# ==============================================================================
# 1. CONFIGURAÇÕES INICIAIS E AMBIENTE
# ==============================================================================

load_dotenv()

# Configuração da Google API
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "zortea_ia_solutions_key_2026")

# Configuração da Base de Dados (PostgreSQL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Gestão de Ficheiros (Uploads)
UPLOAD_FOLDER = 'documentos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ==============================================================================
# 2. MODELOS DE DADOS (DATABASE)
# ==============================================================================

class Company(db.Model):
    """Representa uma empresa cliente no modelo Multi-Tenant."""
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Relacionamentos
    users = db.relationship('User', backref='company', lazy=True)
    documents = db.relationship('Document', backref='company', lazy=True)

class User(db.Model):
    """Representa um colaborador ou administrador do sistema."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    full_name = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user') # 'admin' ou 'user'
    
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Document(db.Model):
    """Representa um manual ou processo carregado na nuvem."""
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    sector = db.Column(db.String(100), nullable=False) 
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# ==============================================================================
# 3. DECORADORES DE PROTEÇÃO (MIDDLEWARES)
# ==============================================================================

def login_required(f):
    """Garante que apenas utilizadores autenticados acedam à rota."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: 
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Garante que apenas administradores acedam à rota."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin': 
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# 4. FUNÇÕES AUXILIARES E DIAGNÓSTICO
# ==============================================================================

def verificar_disponibilidade_ia():
    """Valida a ligação com o Google AI Studio no arranque do servidor."""
    print("\n" + "="*50)
    print("🚀 DIAGNÓSTICO DE IA ZORTEA SOLUTIONS")
    print("="*50)
    
    if not api_key:
        print("❌ ERRO: GOOGLE_API_KEY não encontrada no seu .env")
        return
    
    try:
        modelos = genai.list_models()
        print("✅ Ligação com Google Cloud: ESTABELECIDA")
        print("📋 Modelos ativos para esta chave:")
        for m in modelos:
            if 'generateContent' in m.supported_generation_methods:
                print(f"   - {m.name}")
    except Exception as e:
        print(f"❌ FALHA DE CONEXÃO: {str(e)}")
    print("="*50 + "\n")

def seed_data():
    """Cria os dados base (Empresa Zortea e Admins) no primeiro arranque."""
    company_name = "Zortea IA Solutions"
    company = Company.query.filter_by(name=company_name).first()
    
    if not company:
        company = Company(name=company_name)
        db.session.add(company)
        db.session.commit()
    
    admins = [
        {"name": "Marcos Henrique dos Santos Rosario", "email": "suporte@zorteaiasolutions.com.br"},
        {"name": "Eschiley Raquel Rocha Zortea", "email": "eschiley@zorteaiasolutions.com.br"}
    ]
    
    for adm in admins:
        user = User.query.filter_by(email=adm['email']).first()
        if not user:
            new_adm = User(
                company_id=company.id,
                full_name=adm['name'],
                email=adm['email'],
                password_hash=generate_password_hash("123"),
                role="admin"
            )
            db.session.add(new_adm)
    db.session.commit()

def extrair_conteudo_documentos(company_id):
    """
    Motor RAG: Extrai texto dos manuais da empresa para alimentar o prompt da IA.
    """
    texto_consolidado = ""
    docs = Document.query.filter_by(company_id=company_id).all()
    
    for doc in docs:
        try:
            abs_path = os.path.join(app.root_path, doc.filepath)
            if not os.path.exists(abs_path): 
                continue
            
            content = ""
            if doc.filename.lower().endswith('.pdf'):
                reader = PdfReader(abs_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text: content += text + "\n"
            elif doc.filename.lower().endswith('.txt'):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content += f.read() + "\n"
            
            if content:
                texto_consolidado += f"\n[DOC: {doc.filename} | ID: {doc.id}]\n"
                texto_consolidado += content + "\n"
        except Exception as e:
            print(f"⚠️ Erro ao processar '{doc.filename}': {e}")
            
    return texto_consolidado

# ==============================================================================
# 5. MOTOR DE INTELIGÊNCIA ARTIFICIAL (CÉREBRO)
# ==============================================================================

def obter_resposta_ia(pergunta, base_conhecimento, user_name, company_name):
    """
    Lógica de conversação resiliente com fallbacks automáticos.
    """
    # Ordem de modelos baseada nos testes de sucesso anteriores
    model_list = ['models/gemini-2.5-flash', 'models/gemini-1.5-flash', 'models/gemini-2.0-flash']
    
    # Configurações de Segurança: BLOCK_NONE para evitar falsos positivos em contextos corporativos
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    prompt_sistema = f"""
    PERSONALIDADE: Você é o Guia Zortea IA Solutions, assistente de processos da {company_name}.
    INTERLOCUTOR: {user_name}.
    
    BASE DE CONHECIMENTO (ESTUDE ISTO):
    {base_conhecimento if base_conhecimento else "Nenhum manual encontrado na nuvem."}

    DIRETRIZES DE RESPOSTA:
    1. Responda apenas sobre a Zortea IA Solutions e seus processos corporativos.
    2. Se a informação não estiver no contexto acima, responda: "Não encontrei esta informação nos processos internos. Solicite ao administrador verificar se esta informação é válida."
    3. Quando citar um manual, finalize obrigatoriamente com o link: [Ver documento completo: NOME](/processo/ID).
    4. Proibido qualquer menção a "Rocha Alimentos" ou "Guia Rocha".
    5. Seja sempre profissional, tecnológico e acolhedor.
    """

    print(f"\n💬 Processando consulta: {pergunta}")

    for model_name in model_list:
        try:
            print(f"🔄 Tentando modelo: {model_name}...")
            model = genai.GenerativeModel(model_name=model_name, safety_settings=safety_settings)
            response = model.generate_content(prompt_sistema + "\n\nPergunta do Colaborador: " + pergunta)
            print(f"✅ Sucesso com {model_name}")
            return response.text
        except Exception as e:
            print(f"❌ Erro no {model_name}: {str(e)[:100]}...")
            continue 
            
    return ("⚠️ Falha de Comunicação: A chave API é válida, mas os servidores do Google estão instáveis no momento. "
            "Tente novamente em instantes.")

# ==============================================================================
# 6. ROTAS DE NAVEGAÇÃO E AUTENTICAÇÃO
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        pwd = request.form.get('password').strip()
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, pwd):
            session['user_id'] = user.id
            session['company_id'] = user.company_id
            session['user_name'] = user.full_name
            session['role'] = user.role
            return redirect(url_for('admin_panel' if user.role == 'admin' else 'index'))
        
        flash("Credenciais inválidas. Verifique e-mail e senha.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    user = db.session.get(User, session['user_id'])
    docs = Document.query.filter_by(company_id=session['company_id']).all()
    
    # Organização por setores para a sidebar
    docs_by_sector = {}
    for d in docs:
        if d.sector not in docs_by_sector: docs_by_sector[d.sector] = []
        docs_by_sector[d.sector].append(d)
        
    return render_template('index.html', 
                           user_name=session['user_name'], 
                           company_name=user.company.name, 
                           docs_by_sector=docs_by_sector, 
                           role=session.get('role'))

@app.route('/ask', methods=['POST'])
@login_required
def ask_chatbot():
    dados = request.json
    pergunta = dados.get('question')
    
    # RAG dinâmico: extrai os textos atuais antes de perguntar
    base = extrair_conteudo_documentos(session['company_id'])
    user = db.session.get(User, session['user_id'])
    
    resposta = obter_resposta_ia(pergunta, base, user.full_name, user.company.name)
    return jsonify({"answer": resposta})

# ==============================================================================
# 7. GESTÃO DE DOCUMENTOS E VISUALIZAÇÃO
# ==============================================================================

@app.route('/documentos/<path:filename>')
@login_required
def servir_documento(filename):
    """Serve o ficheiro físico do servidor para o navegador."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processo/<int:doc_id>')
@login_required
def visualizar_processo(doc_id):
    """Abre o visualizador customizado (Canvas) para um documento específico."""
    doc = db.session.get(Document, doc_id)
    if not doc or doc.company_id != session['company_id']:
        return redirect(url_for('index'))
    return render_template('view_processo.html', doc=doc)

@app.route('/contato')
@login_required
def contato_page(): 
    return render_template('contato.html')

# ==============================================================================
# 8. PAINEL ADMINISTRATIVO
# ==============================================================================

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    company = db.session.get(Company, session['company_id'])
    users = User.query.filter_by(company_id=company.id).all()
    return render_template('admin.html', company=company, users=users)

@app.route('/admin/processos')
@login_required
@admin_required
def admin_processos():
    company = db.session.get(Company, session['company_id'])
    setores = ["Institucional", "Comercial", "Compras", "Diretoria", "Logística", "Limpeza", "Compliance"]
    docs = Document.query.filter_by(company_id=company.id).all()
    return render_template('processos.html', company=company, setores=setores, documents=docs)

@app.route('/admin/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    
    new_user = User(
        company_id=session['company_id'], 
        full_name=full_name, 
        email=email, 
        password_hash=generate_password_hash(password), 
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.id != session['user_id']:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/upload_doc', methods=['POST'])
@login_required
@admin_required
def upload_doc():
    sector = request.form.get('sector')
    if 'file' not in request.files or sector == "": 
        return redirect(url_for('admin_processos'))
    
    file = request.files['file']
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        
        # Estrutura Cloud: documentos/ID_EMPRESA/SETOR/NOME_ARQUIVO
        rel_dir = os.path.join(str(session['company_id']), sector)
        abs_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], rel_dir)
        
        if not os.path.exists(abs_dir): 
            os.makedirs(abs_dir)
            
        file.save(os.path.join(abs_dir, filename))
        
        # Salva o caminho formatado para a web (com barras /)
        db_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_dir, filename).replace('\\', '/')
        
        new_doc = Document(
            company_id=session['company_id'], 
            filename=filename, 
            filepath=db_path, 
            sector=sector
        )
        db.session.add(new_doc)
        db.session.commit()
        
    return redirect(url_for('admin_processos'))

@app.route('/admin/delete_doc/<int:doc_id>')
@login_required
@admin_required
def delete_doc(doc_id):
    """Remove o documento do banco e apaga o ficheiro físico."""
    doc = db.session.get(Document, doc_id)
    if doc and doc.company_id == session['company_id']:
        abs_path = os.path.join(app.root_path, doc.filepath)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        db.session.delete(doc)
        db.session.commit()
    return redirect(url_for('admin_processos'))

# ==============================================================================
# 9. BLOCO DE EXECUÇÃO PRINCIPAL
# ==============================================================================

if __name__ == '__main__':
    with app.app_context():
        # Cria as tabelas do banco de dados (se não existirem)
        db.create_all()
        # Popula dados iniciais
        seed_data()
        # Executa diagnóstico de IA no arranque
        verificar_disponibilidade_ia()
        
    app.run(debug=True)