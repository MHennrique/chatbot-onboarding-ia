🤖 Guia Rocha - Chatbot de Onboarding SaaS com IA

O Guia Rocha evoluiu de um protótipo de chatbot para uma estrutura de software como serviço (SaaS). Ele foi projetado para facilitar o onboarding de colaboradores, permitindo que empresas gerenciem seus próprios usuários e processos internos, com uma IA (Google Gemini) treinada especificamente em seus documentos.

✨ Funcionalidades Implementadas

🛡️ Autenticação e Segurança

Login Centralizado: Sistema de autenticação com hash de senha (werkzeug.security).

Níveis de Acesso (RBAC): Diferenciação entre admin (acesso ao painel) e user (acesso ao chat).

Troca de Senha Obrigatória: Recurso para forçar o colaborador a definir uma nova senha no primeiro acesso para garantir a privacidade.

Redirecionamento Inteligente: Admins são levados ao Painel de Controle, enquanto usuários comuns vão direto para a Central de Ajuda.

👥 Gestão Administrativa (Painel Admin)

Dashboard de Usuários: CRUD completo (Criar, Editar, Excluir) de colaboradores.

Gestão de Cargos: Atribuição de cargos para personalização da experiência.

Painel de Processos: Interface organizada por setores (Administrativo, Comercial, Logística, etc.) para futura indexação de documentos.

💬 Inteligência Artificial

IA Contextual: Google Gemini integrado com histórico de conversa e persona "Guia Rocha".

Links Inteligentes: A IA sugere links internos para artigos de ajuda com base no assunto da pergunta.

Suporte a Markdown: Respostas formatadas para melhor leitura técnica.

🛠️ Tecnologias Utilizadas

Backend

Python / Flask: Motor principal da aplicação.

SQLAlchemy: ORM para comunicação com o banco de dados.

PostgreSQL: Banco de dados relacional para persistência de empresas, usuários e documentos.

Google Generative AI: Integração com o modelo Gemini 2.5 Flash.

Frontend

HTML5 / CSS3: Layout responsivo com design focado em produtividade.

JavaScript (Vanilla): Lógica de chat, modais de edição e interatividade na página de processos.

Marked.js: Renderização de Markdown no lado do cliente.

📂 Estrutura do Banco de Dados

O projeto utiliza uma estrutura Multi-Tenant (Multitenat):

Companies (Empresas): Armazena os dados da organização.

Users (Usuários): Vinculados a uma empresa, com campos para e-mail (login), senha criptografada, cargo e permissões.

Documents (Próxima Fase): Registro de caminhos de arquivos vinculados a setores específicos.

🚀 Como Executar o Projeto

Pré-requisitos

Python 3.9+

PostgreSQL instalado e rodando.

Chave de API do Google AI Studio.

Configuração

Instale as dependências:

pip install flask flask-sqlalchemy flask-cors psycopg2-binary python-dotenv google-generativeai


Configure o .env:

GOOGLE_API_KEY="SUA_CHAVE"
DATABASE_URL="postgresql://postgres:SUA_SENHA@localhost:5432/guia_inteligente_db"
SECRET_KEY="uma_chave_segura"


Inicie a Aplicação:

python app.py


O sistema criará as tabelas e o usuário admin automaticamente no primeiro acesso.

✒️ Autor e Evolução do Projeto

Projeto originalmente idealizado por Marcos Henrique (MHennrique).
Atualmente em fase de transformação para modelo de negócio SaaS, focado em escalabilidade corporativa.