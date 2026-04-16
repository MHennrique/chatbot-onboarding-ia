import os
from functools import wraps
from datetime import timedelta
from dotenv import load_dotenv

# Dependências do Flask
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Middleware e Segurança
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Inteligência Artificial e PDFs
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PyPDF2 import PdfReader

# ==========================================
# 1. CONFIGURAÇÕES E AMBIENTE
# ==========================================
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)

# Correção de Proxy para Render (HTTPS)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Sessão e Cookies
app.secret_key = os.getenv("SECRET_KEY", "zortea_ia_solutions_key_2026")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ==========================================
# 2. BANCO DE DADOS
# ==========================================
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuração Absoluta da Pasta de Documentos (Vital para o Render)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'documentos')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    sector = db.Column(db.String(100), nullable=False) 
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# ==========================================
# 3. DECORADORES E AUXILIARES
# ==========================================
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

def seed_data():
    company = Company.query.first()
    if not company:
        company = Company(name="Zortea IA Solutions")
        db.session.add(company)
        db.session.commit()
    
    admin_email = "suporte@zorteaiasolutions.com.br"
    user = User.query.filter_by(email=admin_email).first()
    if not user:
        new_adm = User(
            company_id=company.id,
            full_name="Marcos Henrique dos Santos Rosario",
            email=admin_email,
            password_hash=generate_password_hash("123"),
            role="admin"
        )
        db.session.add(new_adm)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

# ==========================================
# 4. ROTAS DE AUTENTICAÇÃO
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        pwd = request.form.get('password', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, pwd):
            session.clear()
            session['user_id'] = user.id
            session['company_id'] = user.company_id
            session['user_name'] = user.full_name
            session['role'] = user.role
            session.permanent = True
            
            if user.role == 'admin':
                return redirect(url_for('admin_panel'))
            return redirect(url_for('index'))
            
        flash("Credenciais inválidas.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
# 5. ROTAS DO USUÁRIO (CHAT)
# ==========================================
@app.route('/')
@login_required
def index():
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    company = db.session.get(Company, user.company_id)
    docs = Document.query.filter_by(company_id=user.company_id).all()
    
    docs_by_sector = {}
    for d in docs:
        if d.sector not in docs_by_sector: docs_by_sector[d.sector] = []
        docs_by_sector[d.sector].append(d)
        
    return render_template('index.html', 
                           user_name=user.full_name, 
                           company_name=company.name, 
                           docs_by_sector=docs_by_sector, 
                           role=user.role)

def extrair_conteudo_documentos(company_id):
    texto_consolidado = ""
    docs = Document.query.filter_by(company_id=company_id).all()
    for doc in docs:
        try:
            abs_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filepath.split('documentos/', 1)[-1])
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
    return "Erro de conexão na IA."

@app.route('/ask', methods=['POST'])
@login_required
def ask_chatbot():
    try:
        dados = request.json
        base = extrair_conteudo_documentos(session.get('company_id'))
        user_name = session.get('user_name')
        company = db.session.get(Company, session.get('company_id'))
        resposta = obter_resposta_ia(dados.get('question'), base, user_name, company.name)
        return jsonify({"answer": resposta})
    except Exception as e:
        return jsonify({"answer": f"Erro técnico: {str(e)}"})

# ==========================================
# 6. ROTAS ADMINISTRATIVAS
# ==========================================
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    company = db.session.get(Company, session.get('company_id'))
    users = User.query.filter_by(company_id=company.id).order_by(User.full_name).all()
    return render_template('admin.html', company=company, users=users)

@app.route('/admin/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    try:
        new_user = User(
            company_id=session.get('company_id'),
            full_name=request.form.get('full_name'),
            email=request.form.get('email'),
            password_hash=generate_password_hash(request.form.get('password')),
            role=request.form.get('role'),
            job_title=request.form.get('job_title')
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Usuário cadastrado com sucesso!")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao cadastrar: {str(e)}")
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("Usuário não encontrado.")
        return redirect(url_for('admin_panel'))

    try:
        nome = request.form.get('full_name')
        if nome and nome.strip() != "": user.full_name = nome
        
        email = request.form.get('email')
        if email and email.strip() != "": user.email = email
        
        cargo = request.form.get('job_title')
        if cargo is not None: user.job_title = cargo
        
        nivel = request.form.get('role')
        if nivel: user.role = nivel
        
        nova_senha = request.form.get('password')
        if nova_senha and nova_senha.strip() != "":
            user.password_hash = generate_password_hash(nova_senha)
            
        db.session.commit()
        flash(f"Usuário {user.full_name} atualizado!")
    except Exception as e:
        db.session.rollback()
        flash("Erro ao atualizar dados do usuário.")
        
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.id != session.get('user_id'):
        db.session.delete(user)
        db.session.commit()
        flash("Usuário removido!")
    return redirect(url_for('admin_panel'))

# ==========================================
# 7. GESTÃO DE DOCUMENTOS
# ==========================================
@app.route('/admin/processos')
@login_required
@admin_required
def admin_processos():
    company = db.session.get(Company, session.get('company_id'))
    setores = ["Institucional", "Comercial", "Compras", "Diretoria", "Logística", "Limpeza", "Compliance"]
    docs = Document.query.filter_by(company_id=company.id).all()
    return render_template('processos.html', company=company, setores=setores, documents=docs)

@app.route('/admin/upload_doc', methods=['POST'])
@login_required
@admin_required
def upload_doc():
    sector = request.form.get('sector')
    file = request.files.get('file')
    if file and sector:
        filename = secure_filename(file.filename)
        rel_dir = os.path.join(str(session.get('company_id')), sector)
        
        # Cria caminho absoluto para salvar
        abs_dir = os.path.join(app.config['UPLOAD_FOLDER'], rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        file.save(os.path.join(abs_dir, filename))
        
        # Salva caminho relativo para a URL
        db_path = f"documentos/{rel_dir}/{filename}".replace('\\', '/')
        db.session.add(Document(company_id=session.get('company_id'), filename=filename, filepath=db_path, sector=sector))
        db.session.commit()
        flash("Documento enviado com sucesso!")
    return redirect(url_for('admin_processos'))

@app.route('/admin/delete_doc/<int:doc_id>')
@login_required
@admin_required
def delete_doc(doc_id):
    doc = db.session.get(Document, doc_id)
    if doc and doc.company_id == session.get('company_id'):
        # Tenta remover o ficheiro físico
        try:
            rel_path = doc.filepath.split('documentos/', 1)[-1]
            abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
            if os.path.exists(abs_path): os.remove(abs_path)
        except: pass
        
        db.session.delete(doc)
        db.session.commit()
        flash("Documento excluído.")
    return redirect(url_for('admin_processos'))

@app.route('/documentos/<path:filename>')
@login_required
def servir_documento(filename): 
    # Log de diagnóstico para o terminal do Render
    print(f"--- DEBUG: Servindo arquivo {filename} de {app.config['UPLOAD_FOLDER']} ---")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processo/<int:doc_id>')
@login_required
def visualizar_processo(doc_id):
    doc = db.session.get(Document, doc_id)
    if not doc or doc.company_id != session.get('company_id'): return redirect(url_for('index'))
    return render_template('view_processo.html', doc=doc)

if __name__ == '__main__':
    app.run(debug=True)
