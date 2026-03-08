import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
from log import get_logger

logger = get_logger(__name__)

# Garante o carregamento do arquivo .env na raiz do projeto
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


def _get_required_env(name):
    """Retorna variável obrigatória de ambiente ou levanta erro descritivo."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória ausente: {name}. "
            "Verifique o arquivo .env na raiz do projeto."
        )
    return value

def get_db_connection():
    """Estabelece uma conexão com o banco de dados PostgreSQL utilizando parâmetros de ambiente."""
    return psycopg2.connect(
        dbname = _get_required_env("DB_NAME"),
        user = _get_required_env("DB_USER"),
        password = _get_required_env("DB_PASS"),
        host = _get_required_env("DB_HOST"),
        port = _get_required_env("DB_PORT")
    )

def tool_inspect_permissions():
    """Inspecciona as permissões de risco no banco de dados PostgreSQL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT grantee, table_name, privilege_type
    FROM information_schema.role_table_grants 
    WHERE grantee = 'PUBLIC' AND table_schema = 'public';
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    conn.close()

    if not results:
        logger.info("Nenhuma permissão de risco (PUBLIC) encontrada.")
        return "Nenhuma permissão de risco (PUBLIC) encontrada."
    
    report = "Permissões de risco (PUBLIC) encontradas:\n"
    for row in results:
        report += f"Grantee: {row[0]}, Table: {row[1]}, Privilege: {row[2]}\n"
    
    logger.info(report)
    return results  

def tool_execute_containment(sql_command):
    """Executa um comando SQL de contenção no banco de dados PostgreSQL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_command)
        conn.commit()
        logger.info("Comando SQL de contenção executado com sucesso.")
        msg = f"Comando executado com sucesso: {sql_command}"
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao executar comando SQL de contenção: {e}")
        msg = f"Erro ao executar comando SQL de contenção: {e}"
    finally:
        conn.close()

    return msg