import os
import sys
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
from rag_agent import RAGAgent
from log import get_logger

logger = get_logger(__name__)

sys.path.insert(0, '/mnt/user-data/uploads')
app = Flask(__name__)
CORS(app)

rag_agent = None

def init_rag_agent():
    """Inicializa o RAG Agent de forma lazy"""
    global rag_agent
    if rag_agent is None:
        logger.info("Inicializando RAG Agent...")
        rag_agent = RAGAgent()
        logger.info("RAG Agent inicializado com sucesso!")
    return rag_agent

@app.route('/')
def index():
    """Renderiza a interface principal"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ThreatRAG Sentinel'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_logs():
    """Endpoint principal para análise de logs"""
    try:
        data = request.get_json()
        
        if not data or 'logs' not in data:
            return jsonify({
                'error': 'Campo "logs" é obrigatório'
            }), 400
        
        raw_logs = data['logs']
        
        if not raw_logs.strip():
            return jsonify({
                'error': 'Logs não podem estar vazios'
            }), 400
        
        logger.info(f"Iniciando análise de {len(raw_logs)} caracteres de logs...")
        
        # Inicializar e executar o agente
        agent = init_rag_agent()
        result = agent.execute(raw_logs)
        
        logger.info("Análise concluída com sucesso!")
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'results': {
                'cleaned_logs': result.get('cleaned_logs', ''),
                'retrieved_context': result.get('retrieved_context', ''),
                'analysis_report': result.get('analysis_report', '')
            }
        })
        
    except Exception as e:
        logger.error(f"Erro durante análise: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Erro ao processar logs: {str(e)}'
        }), 500

@app.route('/api/sample', methods=['GET'])
def get_sample_logs():
    """Retorna logs de exemplo para teste"""
    sample = """192.168.1.10 - - [12/Feb/2026:10:00:01] "GET /index.php HTTP/1.1" 200 452
10.0.0.5 - - [12/Feb/2026:10:00:05] "GET /admin' OR '1'='1 HTTP/1.1" 404 120
192.168.1.10 - - [12/Feb/2026:10:00:10] "GET /style.css HTTP/1.1" 200 1240
203.0.113.45 - - [12/Feb/2026:10:00:15] "GET /../../../etc/passwd HTTP/1.1" 403 89
192.168.1.10 - - [12/Feb/2026:10:00:20] "GET /script.js HTTP/1.1" 200 3456
10.0.0.8 - - [12/Feb/2026:10:00:25] "POST /login.php HTTP/1.1" 500 234
198.51.100.22 - - [12/Feb/2026:10:00:30] "GET /admin/config.php HTTP/1.1" 404 156
192.168.1.10 - - [12/Feb/2026:10:00:35] "GET /images/logo.png HTTP/1.1" 200 8923
45.33.32.156 - - [12/Feb/2026:10:00:40] "GET /wp-admin/admin-ajax.php?action=revslider_show_image&img=../wp-config.php HTTP/1.1" 403 78
"""
    return jsonify({
        'sample_logs': sample
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas do sistema"""
    try:
        agent = init_rag_agent()
        
        # Verificar se o vector store existe
        persist_dir = os.environ.get("RAG_PERSIST_DIR", "./rag_store")
        kb_dir = os.environ.get("RAG_KB_DIR", "./knowledge_base")
        
        stats = {
            'vector_store_exists': os.path.exists(persist_dir),
            'knowledge_base_path': kb_dir,
            'model': 'google/gemma-3-12b',
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'status': 'operational'
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    # Configurações de ambiente
    os.environ.setdefault('RAG_PERSIST_DIR', './rag_store')
    os.environ.setdefault('RAG_KB_DIR', './knowledge_base')
    
    # Criar diretórios necessários
    os.makedirs('./rag_store', exist_ok=True)
    os.makedirs('./knowledge_base', exist_ok=True)
    os.makedirs('./logs', exist_ok=True)
    
    logger.info("Iniciando servidor Flask...")
    app.run(host='0.0.0.0', port=5000, debug=True)
