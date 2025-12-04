document.addEventListener('DOMContentLoaded', () => {

    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    
    let conversationHistory = [];
    
    const pageMessages = {
        '/': 'Olá! Sou o **Guia Rocha**, seu assistente virtual. Digite sua dúvida sobre processos, benefícios ou use o filtro na lateral para encontrar artigos.',
        '/ferias': 'Bem-vindo(a) à página de **Solicitação de Férias**. Se tiver dúvidas sobre algum termo ou prazo aqui descrito, me pergunte! Caso a dúvida persista, sugiro contatar o RH.',
        '/beneficios': 'Bem-vindo(a) à página de **Benefícios Corporativos**. Quer saber a diferença entre o Plano de Saúde e o Plano Dental? Estou aqui para explicar.',
        '/contato': 'Esta é a página de **Contato e Suporte**. Se a sua dúvida for sobre o Chatbot (Bug/Erro), use o formulário da Zortea. Se for sobre a empresa, use o formulário do RH.',
        '/mvv': 'Conhecendo a **História, Missão e Valores** da Rocha. Se precisar de uma explicação sobre algum valor específico da empresa, me diga!',
        '/cadastro-cliente': 'Processo de **Cadastro de Cliente**. Precisa de ajuda com o significado de "Sintegra" ou "Liberação Financeira"? É só perguntar!',
        '/orcamento-pedido': 'Fluxo de **Orçamento e Pedido**. Se tiver dúvidas sobre a sequência de etapas (Comercial -> Financeiro -> Logística), me pergunte!',
        '/baixa-consumo': 'Regras de **Baixa de Uso e Consumo**. Dúvidas sobre o fluxo Logística -> Fiscal? Estou aqui para ajudar a entender a responsabilidade de cada setor.',
        '/cadastro-produto': 'Processo de **Cadastro de Produto**. Se precisar de uma definição de NCM, CEST ou CFOP, me pergunte antes de acionar o setor Fiscal!',
        '/emissao-nf': 'Fluxo de **Emissão de Nota Fiscal**. Dúvidas sobre o que é DANFE, DACTE ou o prazo de cancelamento? Eu explico em detalhes.'
    };
    
    function typeText(targetElement, message) {
        let i = 0;
        targetElement.textContent = ''; 
        const interval = setInterval(() => {
            if (i < message.length) {
                targetElement.textContent += message.charAt(i);
                i++;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                clearInterval(interval);
                const pElement = targetElement.closest('.message').querySelector('p');
                if (window.marked) {
                    pElement.innerHTML = marked.parse(message);
                }
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 30);
    }

    function addMessage(message, sender, animate = false, isInitial = false) {
        if (!isInitial) {
            if (sender === 'user') {
                conversationHistory.push({ role: 'user', parts: [message] });
            } else if (sender === 'bot') {
                conversationHistory.push({ role: 'model', parts: [message] });
            }
        }
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        const pElement = document.createElement('p');
        
        messageElement.appendChild(pElement);
        chatMessages.appendChild(messageElement);
        
        if (sender === 'bot' && animate) {
            pElement.innerHTML = ''; 
            typeText(pElement, message);
        } else if (sender === 'bot' && window.marked) {
            pElement.innerHTML = marked.parse(message);
        } else {
            pElement.textContent = message;
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function displayInitialMessage() {
        let currentPath = window.location.pathname;

        if (currentPath.endsWith('/')) {
            currentPath = currentPath.slice(0, -1);
        }
        if (currentPath === '') {
            currentPath = '/';
        }

        const initialMessage = pageMessages[currentPath] || pageMessages['/'];

        addMessage(initialMessage, 'bot', true, true);
    }
    
    async function sendMessageToBot() {
        const question = userInput.value.trim();
        if (question === '') return;

        addMessage(question, 'user');
        userInput.value = '';
        typingIndicator.style.display = 'block';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: question,
                    history: conversationHistory.slice(0, -1) 
                })
            });

            if (!response.ok) { 
                const errorText = await response.text();
                throw new Error(`Erro do servidor (${response.status}): ${errorText.substring(0, 100)}...`);
            }

            const data = await response.json();
            addMessage(data.answer, 'bot', true); 

        } catch (error) {
            console.error('Erro ao buscar resposta:', error);
            addMessage(`Desculpe, não consegui me conectar ao meu cérebro. Detalhe: ${error.message}`, 'bot');
            conversationHistory.pop();
        } finally {
            typingIndicator.style.display = 'none';
        }
    }

    sendBtn.addEventListener('click', sendMessageToBot);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') { sendMessageToBot(); }
    });


    const searchInput = document.getElementById('article-search');
    const articleLinks = document.querySelectorAll('#topics-content .article-link');

    if (searchInput) {
        searchInput.addEventListener('keyup', (event) => {
            const searchTerm = event.target.value.toLowerCase();

            articleLinks.forEach(link => {
                const title = link.querySelector('h4').textContent.toLowerCase();
                if (title.includes(searchTerm)) {
                    link.style.display = 'block';
                } else {
                    link.style.display = 'none';
                }
            });
        });
    }

    displayInitialMessage();

});