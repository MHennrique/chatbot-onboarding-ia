document.addEventListener('DOMContentLoaded', () => {
   /* const navLinks = document.querySelectorAll('nav a');
    const sections = document.querySelectorAll('.page-section');
    function showSection(targetId) {
        sections.forEach(section => {
            section.style.display = (section.id === targetId) ? 'block' : 'none';
        });
    }
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            showSection(targetId);
        });
    });
    showSection('inicio');*/

    // --- CÓDIGO DO CHATBOT ---
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');

    // MUDANÇA 1: Array para guardar o histórico da conversa
    let conversationHistory = [];

    function addMessage(message, sender) {
        if (sender === 'user') {
            conversationHistory.push({ role: 'user', parts: [message] });
        } else if (sender === 'bot') {
            conversationHistory.push({ role: 'model', parts: [message] });
        }
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        const pElement = document.createElement('p');
        if (sender === 'bot' && window.marked) {
            pElement.innerHTML = marked.parse(message);
        } else {
            pElement.textContent = message;
        }
        messageElement.appendChild(pElement);
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessageToBot() {
        const question = userInput.value.trim();
        if (question === '') return;

        addMessage(question, 'user');
        userInput.value = '';
        typingIndicator.style.display = 'block';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('http://127.0.0.1:5000/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: question,
                    history: conversationHistory.slice(0, -1) 
                })
            });

            if (!response.ok) { throw new Error('A resposta da rede não foi OK.'); }

            const data = await response.json();
            addMessage(data.answer, 'bot');
        } catch (error) {
            console.error('Erro ao buscar resposta:', error);
            addMessage('Desculpe, não consegui me conectar ao meu cérebro.', 'bot');
            conversationHistory.pop();
        } finally {
            typingIndicator.style.display = 'none';
        }
    }

    sendBtn.addEventListener('click', sendMessageToBot);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') { sendMessageToBot(); }
    });
});