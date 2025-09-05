# 🤖 Chatbot de Onboarding com IA

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![GitHub License](https://img.shields.io/badge/license-MIT-blue)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?logo=python)
![Framework](https://img.shields.io/badge/framework-Flask-black?logo=flask)

Um chatbot inteligente projetado para facilitar o processo de onboarding de novos funcionários em uma empresa. Utilizando a API do Google Gemini, o bot responde a perguntas com base em uma base de conhecimento personalizada, extraída de documentos da empresa (.pdf, .docx, .csv).

## 🎬 Demonstração

Aqui você pode adicionar um GIF do seu chatbot em ação! Ferramentas como **ScreenToGif** ou **LICEcap** são ótimas e fáceis de usar para gravar a tela.

![Demonstração do Chatbot](https://i.imgur.com/vHqJ9Uj.png) 
*(Substitua esta imagem por um GIF do seu projeto)*

---

## ✨ Funcionalidades Principais

-   **Inteligência Artificial Conversacional:** Utiliza o poder do Google Gemini para entender e gerar respostas naturais.
-   **Base de Conhecimento Personalizada:** Aprende a partir de documentos `PDF`, `DOCX`, e planilhas `CSV` fornecidos pela empresa.
-   **Memória de Conversa:** Lembra do contexto das últimas mensagens para responder a perguntas de acompanhamento.
-   **Interface Web Amigável:** Um layout de central de ajuda limpo e responsivo com um componente de chat.
-   **Feedback em Tempo Real:** Indicador de "digitando..." para melhorar a experiência do usuário.
-   **Suporte a Markdown:** Exibe respostas formatadas com listas, negrito e outros elementos para melhor legibilidade.

---

## 🛠️ Tecnologias Utilizadas

O projeto foi construído com as seguintes tecnologias:

-   **Backend:**
    -   ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
    -   ![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
    -   ![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
-   **Frontend:**
    -   ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
    -   ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
    -   ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
-   **Ferramentas:**
    -   ![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
    -   ![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

---

## 🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e rodar o projeto localmente.

### Pré-requisitos

-   [Python 3.9+](https://www.python.org/downloads/)
-   [Git](https://git-scm.com/downloads)
-   Uma chave de API do **Google AI Studio** (Gemini).

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/MHennrique/chatbot-onboarding-ia.git](https://github.com/MHennrique/chatbot-onboarding-ia.git)
    cd chatbot-onboarding-ia
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    *Primeiro, certifique-se de que o arquivo `requirements.txt` está atualizado (veja o Passo 2 abaixo).*
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure suas variáveis de ambiente:**
    -   Renomeie o arquivo `.env.example` (se houver) para `.env`.
    -   Abra o arquivo `.env` e insira sua chave de API do Google:
        ```
        GOOGLE_API_KEY="SUA_CHAVE_DE_API_AQUI"
        ```

5.  **Adicione os documentos da empresa:**
    -   Coloque os arquivos `.pdf`, `.docx`, e `.csv` que o chatbot deve aprender na pasta `documentos/`.

### Executando

1.  **Inicie o servidor backend (Flask):**
    ```bash
    python app.py
    ```
    O servidor estará rodando em `http://127.0.0.1:5000`.

2.  **Abra o frontend:**
    -   Abra o arquivo `index.html` diretamente no seu navegador.
    -   Ou, se estiver usando o VS Code com a extensão "Live Server", clique em "Go Live".

---

## ✒️ Autor

Projeto desenvolvido por **Marcos Henrique (MHennrique)**.

[![GitHub](https://img.shields.io/badge/GitHub-Profile-181717?style=for-the-badge&logo=github)](https://github.com/MHennrique)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Profile-0A66C2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/marcosrosario/)