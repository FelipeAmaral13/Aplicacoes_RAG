import os
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logger(log_directory="logs", log_filename="log.log", level=logging.INFO):
    """
    Configura o logger central da aplicação com rotação de arquivos.
    
    Args:
        log_directory (str): Diretório onde os logs serão salvos
        log_filename (str): Nome do arquivo de log
        level (int): Nível de logging (default: logging.INFO)
    
    Returns:
        logging.Logger: Logger configurado
    """
    # Criar diretório de logs se não existir
    os.makedirs(log_directory, exist_ok=True)
    
    # Criar o logger
    logger = logging.getLogger('RD_Station_Automation')
    logger.setLevel(level)
    
    # Evitar duplicação de handlers
    if not logger.handlers:
        # Configurar formato do log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Handler para arquivo com rotação
        file_handler = RotatingFileHandler(
            os.path.join(log_directory, log_filename),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        
        # Adicionar handlers ao logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logger.info("Logger configurado com sucesso!")
    
    return logger

# Configurar logger global
logger = setup_logger()

def get_logger(name=None):
    """
    Obtém um logger configurado para um módulo específico.
    
    Args:
        name (str): Nome do módulo/componente (opcional)
    
    Returns:
        logging.Logger: Logger configurado
    """
    if name:
        return logging.getLogger(f'RD_Station_Automation.{name}')
    return logger

# logger = get_logger(__name__)
