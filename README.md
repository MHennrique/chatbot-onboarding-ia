🛡️ Zortea IA Solutions - Plataforma SaaS de Onboarding Inteligente

A Zortea IA Solutions é uma estrutura de software como serviço (SaaS) de última geração, projetada para revolucionar o onboarding e o treinamento corporativo. A plataforma permite que empresas criem sua própria "Nuvem de Processos", onde uma Inteligência Artificial (Google Gemini) é treinada em tempo real com os documentos (PDF/TXT) enviados pelos administradores.

✨ Funcionalidades Avançadas

🏢 Arquitetura Multi-Tenant (Nuvem Privada)

Isolamento de Dados: Cada empresa possui sua própria base de usuários e documentos.

Identidade Visual Customizada: Interface limpa e profissional focada na experiência do colaborador.

💬 IA com Tecnologia RAG (Retrieval-Augmented Generation)

Leitura Dinâmica: A IA não apenas conversa, ela "estuda" os manuais e documentos enviados para a pasta documentos/.

Links Inteligentes: Ao responder uma dúvida, o Guia Zortea fornece automaticamente um link direto para a página de visualização do documento de origem.

Modelo Estável: Utilização do Gemini 1.5 Flash para respostas ultra-rápidas e precisas.

📂 Gestão de Processos e Cloud

Upload Automatizado: Painel administrativo para envio de manuais organizados por setores (Institucional, Comercial, Logística, etc.).

Visualizador Próprio: Sistema integrado para leitura de PDFs e arquivos de texto sem sair da plataforma.

Organização Física: Armazenamento inteligente na raiz do projeto (/documentos/{company_id}/{setor}).

👥 Gestão Administrativa e Segurança

Controle de Acessos (RBAC): Diferenciação total entre administradores de sistema e colaboradores.

Segurança de Dados: Senhas criptografadas com hash de alta segurança e proteção de rotas via decoradores Python.

Central de Suporte: Canais dedicados para suporte técnico da plataforma e consultoria estratégica.

🛠️ Tecnologias Utilizadas

Backend

Python / Flask: Core da aplicação SaaS.

SQLAlchemy: ORM para gestão de banco de dados relacional.

PostgreSQL: Persistência de dados escalável.

Google Generative AI: Integração com o modelo Gemini 1.5 Flash.

PyPDF2: Extração e processamento de texto de arquivos PDF.

Frontend

HTML5 / CSS3: Layout moderno com design "Apple-like" e responsividade total.

JavaScript (Vanilla): Lógica de chat em tempo real, manipulação de DOM e integração de API.

Marked.js: Renderização de respostas da IA em Markdown.

🚀 Como Executar o Projeto

1. Pré-requisitos

Python 3.9+

PostgreSQL

Chave de API do Google AI Studio

2. Instalação

Instale as dependências necessárias:

pip install flask flask-sqlalchemy flask-cors psycopg2-binary python-dotenv google-generativeai PyPDF2


3. Configuração do Ambiente (.env)

Crie um arquivo .env na raiz do projeto:

GOOGLE_API_KEY="SUA_CHAVE_AQUI"
DATABASE_URL="postgresql://postgres:SENHA@localhost:5432/zortea_saas_db"
SECRET_KEY="sua_chave_secreta_para_sessoes"


4. Inicialização

Inicie a aplicação:

python app.py


O sistema criará automaticamente a estrutura de pastas e os usuários administradores iniciais no primeiro acesso.

🌐 Infraestrutura e Deploy

O projeto está preparado para rodar em servidores VPS (Ubuntu 22.04 LTS) com as seguintes camadas:

Gunicorn: Servidor de aplicação WSGI.

Nginx: Proxy reverso e gerenciamento de certificados SSL.

Certbot: Segurança via HTTPS.

✒️ Evolução e Autor

Este projeto evoluiu do protótipo "Guia Rocha" para uma solução SaaS robusta sob a marca Zortea IA Solutions.

Desenvolvido por: Marcos Henrique (MHennrique)
Propósito: Escalabilidade corporativa e democratização da IA em processos internos.

© 2026 Zortea IA Solutions | Inteligência Artificial Aplicada.