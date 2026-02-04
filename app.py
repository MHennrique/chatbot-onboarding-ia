import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import google.generativeai as genai

# --- CONFIGURAÇÕES ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
CORS(app)
# Atualizada a chave secreta para refletir a nova marca
app.secret_key = os.getenv("SECRET_KEY", "zortea_ia_solutions_key_2026")

# Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Uploads
UPLOAD_FOLDER = 'uploads'
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

# --- FUNÇÃO DE INICIALIZAÇÃO (SEED) ---
def seed_data():
    """Garante a criação da Zortea IA Solutions e seus administradores."""
    company_name = "Zortea IA Solutions"
    company = Company.query.filter_by(name=company_name).first()
    if not company:
        company = Company(name=company_name)
        db.session.add(company)
        db.session.commit()
        print(f">>> Empresa '{company_name}' criada com sucesso.")

    admins = [
        {
            "full_name": "Marcos Henrique dos Santos Rosario",
            "email": "suporte@zorteaiasolutions.com.br",
            "job_title": "CEO & Founder"
        },
        {
            "full_name": "Eschiley Raquel Rocha Zortea",
            "email": "eschiley@zorteaiasolutions.com.br",
            "job_title": "CFO & Admin"
        }
    ]

    for data in admins:
        admin = User.query.filter_by(email=data['email']).first()
        if not admin:
            admin = User(
                company_id=company.id,
                full_name=data['full_name'],
                email=data['email'],
                job_title=data['job_title'],
                password_hash=generate_password_hash("123"),
                role="admin",
                must_change_password=False
            )
            db.session.add(admin)
            print(f">>> Administrador {data['full_name']} criado.")
    
    db.session.commit()

# --- DECORADORES ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        user = db.session.get(User, session['user_id'])
        if user and user.must_change_password and request.endpoint not in ['change_password', 'logout']:
            return redirect(url_for('change_password'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin': return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- LÓGICA DA IA (REBRANDING PERSONA) ---

def obter_resposta_ia(pergunta, base_conhecimento, historico, user_name, company_name):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Atualizada a Persona para Zortea IA Solutions
    instrucao = f"""
    Você é o **Guia Zortea IA Solutions**, o assistente virtual inteligente da {company_name}. 
    Seu objetivo é auxiliar o colaborador {user_name} com informações precisas sobre processos internos, 
    políticas e manuais da empresa.
    
    Responda sempre de forma profissional, cordial e baseando-se estritamente no conteúdo fornecido.
    Se não souber a resposta, sugira que o usuário entre em contato com o suporte através da página de contato.
    """
    
    historico_formatado = [{"role": "user", "parts": [instrucao]}]
    historico_formatado.append({"role": "model", "parts": ["Entendido. O Guia Zortea está pronto para ajudar."] })
    historico_formatado.extend(historico)

    try:
        chat = model.start_chat(history=historico_formatado)
        response = chat.send_message(pergunta)
        return response.text
    except Exception as e:
        return f"Erro na IA Zortea: {str(e)}"

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['company_id'] = user.company_id
            session['user_name'] = user.full_name
            session['role'] = user.role
            
            if user.must_change_password:
                return redirect(url_for('change_password'))
                
            return redirect(url_for('admin_panel' if user.role == 'admin' else 'index'))
        flash("Credenciais inválidas para o portal Zortea.")
    return render_template('login.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_pwd = request.form.get('password')
        conf_pwd = request.form.get('confirm_password')
        if new_pwd != conf_pwd:
            flash("As senhas não coincidem.")
            return render_template('change_password.html')
        user = db.session.get(User, session['user_id'])
        user.password_hash = generate_password_hash(new_pwd)
        user.must_change_password = False
        db.session.commit()
        session.clear() 
        flash("Sua senha Zortea foi atualizada! Faça login novamente.")
        return redirect(url_for('login'))
    return render_template('change_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ROTAS DE CONTEÚDO ---

@app.route('/')
@login_required
def index():
    user = db.session.get(User, session['user_id'])
    all_docs = Document.query.filter_by(company_id=session['company_id']).all()
    docs_by_sector = {}
    for doc in all_docs:
        if doc.sector not in docs_by_sector: docs_by_sector[doc.sector] = []
        docs_by_sector[doc.sector].append(doc)
        
    return render_template('index.html', 
                           user_name=session['user_name'], 
                           company_name=user.company.name,
                           docs_by_sector=docs_by_sector,
                           role=session.get('role'))

# --- ROTAS ADMIN ---

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    company = db.session.get(Company, session['company_id'])
    users = User.query.filter_by(company_id=company.id).order_by(User.created_at.desc()).all()
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
    job_title = request.form.get('job_title')
    role = request.form.get('role')
    must_change = 'must_change_password' in request.form
    if User.query.filter_by(email=email).first():
        flash("Este e-mail já está cadastrado em nossa base.")
    else:
        new_user = User(company_id=session['company_id'], full_name=full_name, email=email, job_title=job_title, password_hash=generate_password_hash(password), role=role, must_change_password=must_change)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Colaborador {full_name} cadastrado com sucesso!")
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    user.full_name = request.form.get('full_name')
    user.job_title = request.form.get('job_title')
    user.role = request.form.get('role')
    user.must_change_password = 'must_change_password' in request.form
    new_pwd = request.form.get('password')
    if new_pwd and new_pwd.strip() != "":
        user.password_hash = generate_password_hash(new_pwd)
    db.session.commit()
    flash("Cadastro Zortea atualizado!")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user.id != session['user_id']:
        db.session.delete(user)
        db.session.commit()
        flash("Usuário removido da base de dados.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/upload_doc', methods=['POST'])
@login_required
@admin_required
def upload_doc():
    sector = request.form.get('sector')
    if 'file' not in request.files or not sector:
        flash("Erro: Selecione o arquivo e o setor de destino.")
        return redirect(url_for('admin_processos'))
    file = request.files['file']
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        company_path = os.path.join(app.config['UPLOAD_FOLDER'], str(session['company_id']), sector)
        if not os.path.exists(company_path): os.makedirs(company_path)
        filepath = os.path.join(company_path, filename)
        file.save(filepath)
        new_doc = Document(company_id=session['company_id'], filename=filename, filepath=filepath, sector=sector)
        db.session.add(new_doc)
        db.session.commit()
        flash(f"Documento '{filename}' armazenado na Cloud Zortea!")
    return redirect(url_for('admin_processos'))

# --- ROTAS DE ARTIGOS ---
@app.route('/mvv')
@login_required
def mvv_page(): return render_template('mvv_historia.html')

@app.route('/ferias')
@login_required
def ferias_page(): return render_template('artigo_ferias.html')

@app.route('/beneficios')
@login_required
def beneficios_page(): return render_template('artigo_beneficios.html')

@app.route('/contato')
@login_required
def contato_page(): return render_template('contato.html')

@app.route('/cadastro-cliente')
@login_required
def cadastro_cliente_page(): return render_template('artigo_cadastro_cliente.html')

@app.route('/orcamento-pedido')
@login_required
def orcamento_pedido_page(): return render_template('artigo_orcamento_pedido.html')

@app.route('/baixa-consumo')
@login_required
def baixa_consumo_page(): return render_template('artigo_baixa_consumo.html')

@app.route('/cadastro-produto')
@login_required
def cadastro_produto_page(): return render_template('artigo_cadastro_produto.html')

@app.route('/emissao-nf')
@login_required
def emissao_nf_page(): return render_template('artigo_emissao_nf.html')

@app.route('/ask', methods=['POST'])
@login_required
def ask_chatbot():
    dados = request.json
    pergunta = dados.get('question')
    historico = dados.get('history', [])
    try:
        from knowledge_base import CONTEUDO_EMPRESA
    except ImportError:
        CONTEUDO_EMPRESA = "Base de conhecimento Zortea em manutenção."
    user = db.session.get(User, session['user_id'])
    resposta = obter_resposta_ia(pergunta, CONTEUDO_EMPRESA, historico, user.full_name, user.company.name)
    return jsonify({"answer": resposta})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)