import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- CONFIGURAÇÕES ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "zortea_ia_solutions_key_2026")

# Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Pasta de documentos na raiz conforme solicitado
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

# --- FUNÇÕES AUXILIARES ---

def seed_data():
    """Garante a criação da Zortea IA Solutions e seus administradores."""
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
    """Extrai texto dos PDFs e TXTs para alimentar o contexto da IA."""
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
                texto_consolidado += f"\n[ID_DOCUMENTO: {doc.id} | NOME: {doc.filename}]\n"
                texto_consolidado += content + "\n"
        except Exception as e:
            print(f"Erro ao ler {doc.filename}: {e}")
    return texto_consolidado

# --- DECORADORES ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin': return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- LÓGICA DA IA ---

def obter_resposta_ia(pergunta, base_conhecimento, historico, user_name, company_name):
    # Usando o modelo gemini-1.5-flash
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt_sistema = f"""
    És o Guia Zortea IA Solutions da empresa {company_name}.
    Utilizador: {user_name}.
    
    REGRAS CRÍTICAS:
    1. Baseia-te EXCLUSIVAMENTE nos documentos fornecidos abaixo.
    2. Se a resposta estiver num documento, resume-a e inclui obrigatoriamente o link no final:
       [Ver documento completo: NOME](/processo/ID)
    3. Nunca menciones 'Rocha Alimentos' ou 'Guia Rocha'. Tua identidade é Guia Zortea.
    4. Sê profissional, tecnológico e cordial.
    
    CONTEÚDO DOS DOCUMENTOS:
    {base_conhecimento}
    """
    
    try:
        response = model.generate_content(prompt_sistema + "\n\nPergunta do utilizador: " + pergunta)
        return response.text
    except Exception as e:
        return f"Erro na IA Zortea: {str(e)}"

# --- ROTAS DE AUTENTICAÇÃO ---

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
        flash("E-mail ou palavra-passe incorretos.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ROTAS DE CONTEÚDO ---

@app.route('/')
@login_required
def index():
    user = db.session.get(User, session['user_id'])
    docs = Document.query.filter_by(company_id=session['company_id']).all()
    docs_by_sector = {}
    for d in docs:
        if d.sector not in docs_by_sector: docs_by_sector[d.sector] = []
        docs_by_sector[d.sector].append(d)
    return render_template('index.html', user_name=session['user_name'], company_name=user.company.name, docs_by_sector=docs_by_sector, role=session.get('role'))

@app.route('/documentos/<path:filename>')
@login_required
def servir_documento(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processo/<int:doc_id>')
@login_required
def visualizar_processo(doc_id):
    doc = db.session.get(Document, doc_id)
    if not doc or doc.company_id != session['company_id']:
        flash("Acesso negado.")
        return redirect(url_for('index'))
    return render_template('view_processo.html', doc=doc)

@app.route('/contato')
@login_required
def contato_page():
    return render_template('contato.html')

@app.route('/mvv')
@login_required
def mvv_page():
    return render_template('mvv_historia.html')

# Rotas de artigos adicionais para evitar BuildError
@app.route('/ferias')
@login_required
def ferias_page(): return render_template('artigo_ferias.html')

@app.route('/beneficios')
@login_required
def beneficios_page(): return render_template('artigo_beneficios.html')

# --- ROTAS ADMIN ---

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
    flash(f"Utilizador {full_name} registado!")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.id != session['user_id']:
        db.session.delete(user)
        db.session.commit()
        flash("Utilizador removido.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/upload_doc', methods=['POST'])
@login_required
@admin_required
def upload_doc():
    sector = request.form.get('sector')
    if 'file' not in request.files or sector == "": 
        flash("Seleciona o ficheiro e o setor.")
        return redirect(url_for('admin_processos'))
    
    file = request.files['file']
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        rel_dir = os.path.join(str(session['company_id']), sector)
        abs_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], rel_dir)
        
        if not os.path.exists(abs_dir): os.makedirs(abs_dir)
        
        filepath_abs = os.path.join(abs_dir, filename)
        file.save(filepath_abs)
        
        db_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_dir, filename).replace('\\', '/')
        new_doc = Document(company_id=session['company_id'], filename=filename, filepath=db_path, sector=sector)
        db.session.add(new_doc)
        db.session.commit()
        flash("Documento armazenado com sucesso!")
    return redirect(url_for('admin_processos'))

@app.route('/ask', methods=['POST'])
@login_required
def ask_chatbot():
    dados = request.json
    pergunta = dados.get('question')
    historico = dados.get('history', [])
    base = extrair_conteudo_documentos(session['company_id'])
    user = db.session.get(User, session['user_id'])
    resposta = obter_resposta_ia(pergunta, base, historico, user.full_name, user.company.name)
    return jsonify({"answer": resposta})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)