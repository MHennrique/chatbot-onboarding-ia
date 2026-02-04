document.addEventListener('DOMContentLoaded', () => {

    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    
    let conversationHistory = [];
    
    // Mensagens personalizadas por rota para o Guia Zortea
    const pageMessages = {
        '/': 'Olá! Sou o **Guia Zortea IA Solutions**, seu assistente virtual. Digite sua dúvida sobre nossos processos e documentos ou utilize as pastas na lateral para navegar.',
        '/ferias': 'Bem-vindo(a) à página de **Solicitação de Férias**. Se tiver dúvidas sobre algum termo ou prazo aqui descrito, me pergunte! Caso a dúvida persista, sugiro contatar o RH.',
        '/beneficios': 'Bem-vindo(a) à página de **Benefícios Corporativos**. Quer saber a diferença entre os planos disponíveis? Estou aqui para explicar.',
        '/contato': 'Esta é a página de **Contato e Suporte**. Se a sua dúvida for sobre o Chatbot (Bug/Erro), use o formulário da Zortea. Se for sobre a empresa, use o formulário do RH.',
        '/mvv': 'Conhecendo a **História e Identidade** da Zortea IA Solutions. Se precisar de uma explicação sobre nossa cultura, me diga!',
        '/cadastro-cliente': 'Processo de **Cadastro de Cliente**. Precisa de ajuda com o significado de termos técnicos ou liberação financeira? É só perguntar!',
        '/orcamento-pedido': 'Fluxo de **Orçamento e Pedido**. Se tiver dúvidas sobre a sequência de etapas entre os setores, me pergunte!',
        '/baixa-consumo': 'Regras de **Baixa de Uso e Consumo**. Estou aqui para ajudar a entender a responsabilidade de cada setor no fluxo logístico.',
        '/cadastro-produto': 'Processo de **Cadastro de Produto**. Se precisar de uma definição fiscal (NCM, CEST), me pergunte antes de acionar o setor!',
        '/emissao-nf': 'Fluxo de **Emissão de Nota Fiscal**. Dúvidas sobre DANFE, prazos ou cancelamentos? Eu explico em detalhes.'
    };
    
    // Efeito de digitação para as respostas do bot
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
                // Após digitar tudo, renderiza o Markdown se o Marked estiver disponível
                if (window.marked) {
                    targetElement.innerHTML = marked.parse(message);
                }
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 20); // Velocidade da digitação
    }

    // Função para adicionar balões de mensagem
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
        
        // Criamos o parágrafo interno para conter o texto
        const pElement = document.createElement('p');
        messageElement.appendChild(pElement);
        chatMessages.appendChild(messageElement);
        
        if (sender === 'bot' && animate) {
            typeText(pElement, message);
        } else if (sender === 'bot' && window.marked) {
            pElement.innerHTML = marked.parse(message);
        } else {
            pElement.textContent = message;
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Define qual mensagem mostrar ao carregar a página
    function displayInitialMessage() {
        let currentPath = window.location.pathname;

        // Limpa barras extras no final do caminho
        if (currentPath.length > 1 && currentPath.endsWith('/')) {
            currentPath = currentPath.slice(0, -1);
        }
        
        const initialMessage = pageMessages[currentPath] || pageMessages['/'];
        addMessage(initialMessage, 'bot', true, true);
    }
    
    // Envio de mensagem para a API do Flask
    async function sendMessageToBot() {
        const question = userInput.value.trim();
        if (question === '') return;

        addMessage(question, 'user');
        userInput.value = '';
        
        // Ativa indicador de "digitando..."
        typingIndicator.style.display = 'block';
        chatMessages.appendChild(typingIndicator); // Mantém no final
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: question,
                    history: conversationHistory 
                })
            });

            if (!response.ok) { 
                throw new Error("Erro de conexão com a Cloud Zortea.");
            }

            const data = await response.json();
            addMessage(data.answer, 'bot', true); 

        } catch (error) {
            console.error('Erro:', error);
            addMessage(`Desculpe, a **Zortea IA** encontrou uma instabilidade técnica. Detalhe: ${error.message}`, 'bot');
            conversationHistory.pop(); // Remove a última pergunta do histórico para evitar erros em cascata
        } finally {
            typingIndicator.style.display = 'none';
        }
    }

    // Eventos de clique e teclado
    sendBtn.addEventListener('click', sendMessageToBot);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessageToBot();
    });

    // Lógica de Busca: Filtra pastas e links na barra lateral
    const searchInput = document.getElementById('article-search');
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const folders = document.querySelectorAll('.sector-folder');

            folders.forEach(folder => {
                const links = folder.querySelectorAll('.sub-article-link');
                let folderHasMatch = false;

                links.forEach(link => {
                    const text = link.textContent.toLowerCase();
                    if (text.includes(term)) {
                        link.style.display = 'block';
                        folderHasMatch = true;
                    } else {
                        link.style.display = 'none';
                    }
                });

                // Mostra/Esconde a pasta inteira baseada nos links internos
                folder.style.display = (folderHasMatch || term === "") ? 'block' : 'none';
                
                // Se estiver buscando, expande a pasta automaticamente
                if (term !== "" && folderHasMatch) {
                    folder.classList.add('active');
                } else if (term === "") {
                    folder.classList.remove('active');
                }
            });
        });
    }

    // Inicia o chat chamando a mensagem de boas-vindas
    displayInitialMessage();
});