import os
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from langchain_core.messages import HumanMessage

from rag import RAG
from agentes_ia import create_agent
from log import get_logger

logger = get_logger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

agents = {}
chat_histories = {}


def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Renderiza a página principal."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Endpoint para upload de PDF e inicialização do agente RAG."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Apenas arquivos PDF são permitidos'}), 400
        
        # Gerar ID único para a sessão
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{session_id[:8]}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        logger.info(f"Arquivo salvo: {filepath}")
        
        rag = RAG(filepath)
        if rag.retriever is None:
            return jsonify({'error': 'Erro ao processar o PDF'}), 500
        
        agent = create_agent(rag.retriever)
        
        # Armazenar agente e inicializar histórico
        agents[session_id] = agent
        chat_histories[session_id] = []
        
        logger.info(f"Agente criado para sessão: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'message': 'PDF processado com sucesso! Você pode começar a fazer perguntas.'
        })
    
    except Exception as e:
        logger.error(f"Erro no upload: {str(e)}", exc_info=True)
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para processar mensagens do chat."""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensagem não fornecida'}), 400
        
        session_id = session.get('session_id')
        
        if not session_id or session_id not in agents:
            return jsonify({'error': 'Nenhum documento carregado. Por favor, faça upload de um PDF primeiro.'}), 400
        
        user_message = data['message']
        
        # Obter agente e histórico
        agent = agents[session_id]
        history = chat_histories[session_id]
        
        # Adicionar mensagem do usuário ao histórico
        history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Processando mensagem da sessão {session_id}: {user_message}")
        
        # Processar com o agente      
        result = agent.invoke({
            "messages": [HumanMessage(content=user_message)]
        })
        
        # Extrair resposta
        assistant_message = result['messages'][-1].content
        
        # Adicionar resposta ao histórico
        history.append({
            'role': 'assistant',
            'content': assistant_message,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Resposta gerada para sessão {session_id}")
        
        return jsonify({
            'success': True,
            'response': assistant_message
        })
    
    except Exception as e:
        logger.error(f"Erro no chat: {str(e)}", exc_info=True)
        return jsonify({'error': f'Erro ao processar mensagem: {str(e)}'}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Endpoint para obter o histórico de chat."""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in chat_histories:
            return jsonify({'history': []})
        
        return jsonify({
            'success': True,
            'history': chat_histories[session_id]
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro ao obter histórico'}), 500


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """Endpoint para limpar a sessão atual."""
    try:
        session_id = session.get('session_id')
        
        if session_id:
            # Remover agente e histórico
            agents.pop(session_id, None)
            chat_histories.pop(session_id, None)
            session.pop('session_id', None)
            
            logger.info(f"Sessão limpa: {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Sessão limpa com sucesso'
        })
    
    except Exception as e:
        logger.error(f"Erro ao limpar sessão: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro ao limpar sessão'}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handler para arquivos muito grandes."""
    return jsonify({'error': 'Arquivo muito grande. Tamanho máximo: 16MB'}), 413


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
