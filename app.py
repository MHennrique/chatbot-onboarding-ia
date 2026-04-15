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

# --- CONFIGURAÇÕES ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "zortea_ia_solutions_key_2026")

# --- CORREÇÃO DE DIALETO POSTGRES (CRÍTICO PARA RENDER) ---
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Pasta de documentos
UPLOAD_FOLDER = 'documentos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- MODELOS ---

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', backref='company', lazy=True)
    documents = db.relationship('Document', backref='company', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    sector = db.Column(db.String(100), nullable=False) 
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- DECORADORES ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: 
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin': 
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- INICIALIZAÇÃO AUTOMÁTICA ---

def seed_data():
    """Cria os dados base no primeiro arranque."""
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

# Inicializa banco e dados base fora do __main__ para o Gunicorn (Render)
with app.app_context():
    db.create_all()
    seed_data()
    print("🚀 Sistema Zortea inicializado com sucesso!")

# --- MOTOR DE IA ---

def extrair_conteudo_documentos(company_id):
    texto_consolidado = ""
    docs = Document.query.filter_by(company_id=company_id).all()
    for doc in docs:
        try:
            abs_path = os.path.join(app.root_path, doc.filepath)
            if not os.path.exists(abs_path): continue
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
                texto_consolidado += f"\n[DOC ID: {doc.id} NOME: {doc.filename}]\n{content}\n"
        except Exception: continue
    return texto_consolidado

def obter_resposta_ia(pergunta, base_conhecimento, user_name, company_name):
    model_list = ['models/gemini-2.5-flash', 'models/gemini-1.5-flash']
    safety_settings = {cat: HarmBlockThreshold.BLOCK_NONE for cat in [HarmCategory.HARM_CATEGORY_HARASSMENT, HarmCategory.HARM_CATEGORY_HATE_SPEECH, HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT]}
    prompt_sistema = f"Você é o Guia Zortea da empresa {company_name}. Usuário: {user_name}. Responda apenas com base nisto: {base_conhecimento}"

    for model_name in model_list:
        try:
            model = genai.GenerativeModel(model_name=model_name, safety_settings=safety_settings)
            return model.generate_content(prompt_sistema + "\n\nPergunta: " + pergunta).text
        except: continue
    return "Erro de quota na IA."

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        pwd = request.form.get('password').strip()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, pwd):
            # Limpa sessão anterior e define novos dados
            session.clear()
            session['user_id'] = user.id
            session['company_id'] = user.company_id
            session['user_name'] = user.full_name
            session['role'] = user.role
            session.permanent = True # Mantém o login ativo
            return redirect(url_for('index'))
        flash("E-mail ou senha incorretos.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ROTAS DO CHAT (PRINCIPAL) ---

@app.route('/')
@login_required
def index():
    """ Rota do Chat. Se não logado, o decorador envia para o login. """
    try:
        # Busca explícita para evitar erros de relacionamento no Render
        user_id = session.get('user_id')
        company_id = session.get('company_id')
        
        user = db.session.get(User, user_id)
        company = db.session.get(Company, company_id)
        
        if not user or not company:
            session.clear()
            return redirect(url_for('login'))

        docs = Document.query.filter_by(company_id=company_id).all()
        docs_by_sector = {}
        for d in docs:
            if d.sector not in docs_by_sector: 
                docs_by_sector[d.sector] = []
            docs_by_sector[d.sector].append(d)
            
        return render_template('index.html', 
                               user_name=user.full_name, 
                               company_name=company.name, 
                               docs_by_sector=docs_by_sector, 
                               role=user.role)
    except Exception as e:
        print(f"Erro na rota index: {e}")
        return redirect(url_for('login'))

@app.route('/ask', methods=['POST'])
@login_required
def ask_chatbot():
    try:
        dados = request.json
        base = extrair_conteudo_documentos(session.get('company_id'))
        user_name = session.get('user_name')
        
        # Busca nome da empresa para o prompt
        company = db.session.get(Company, session.get('company_id'))
        company_name = company.name if company else "Zortea IA"
        
        resposta = obter_resposta_ia(dados.get('question'), base, user_name, company_name)
        return jsonify({"answer": resposta})
    except Exception as e:
        return jsonify({"answer": "Erro ao processar sua pergunta. Tente novamente."})

@app.route('/documentos/<path:filename>')
@login_required
def servir_documento(filename): 
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processo/<int:doc_id>')
@login_required
def visualizar_processo(doc_id):
    try:
        doc = db.session.get(Document, doc_id)
        if not doc or doc.company_id != session.get('company_id'): 
            return redirect(url_for('index'))
        return render_template('view_processo.html', doc=doc)
    except:
        return redirect(url_for('index'))

# --- ROTAS ADMINISTRATIVAS ---

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    company = db.session.get(Company, session.get('company_id'))
    users = User.query.filter_by(company_id=company.id).all()
    return render_template('admin.html', company=company, users=users)

@app.route('/admin/processos')
@login_required
@admin_required
def admin_processos():
    company = db.session.get(Company, session.get('company_id'))
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
    job_title = request.form.get('job_title')
    
    new_user = User(
        company_id=session.get('company_id'), 
        full_name=full_name, 
        email=email, 
        password_hash=generate_password_hash(password), 
        role=role,
        job_title=job_title
    )
    db.session.add(new_user)
    db.session.commit()
    flash(f"Usuário {full_name} cadastrado!")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.id != session.get('user_id'):
        db.session.delete(user)
        db.session.commit()
        flash("Usuário removido.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/upload_doc', methods=['POST'])
@login_required
@admin_required
def upload_doc():
    sector = request.form.get('sector')
    file = request.files.get('file')
    if file and sector:
        filename = secure_filename(file.filename)
        rel_dir = os.path.join(str(session.get('company_id')), sector)
        abs_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        file.save(os.path.join(abs_dir, filename))
        db_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_dir, filename).replace('\\', '/')
        db.session.add(Document(company_id=session.get('company_id'), filename=filename, filepath=db_path, sector=sector))
        db.session.commit()
        flash("Documento armazenado!")
    return redirect(url_for('admin_processos'))

@app.route('/admin/delete_doc/<int:doc_id>')
@login_required
@admin_required
def delete_doc(doc_id):
    doc = db.session.get(Document, doc_id)
    if doc and doc.company_id == session.get('company_id'):
        abs_path = os.path.join(app.root_path, doc.filepath)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        db.session.delete(doc)
        db.session.commit()
        flash("Documento removido.")
    return redirect(url_for('admin_processos'))

if __name__ == '__main__':
    app.run(debug=True)
