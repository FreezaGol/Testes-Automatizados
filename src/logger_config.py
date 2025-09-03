import logging
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logger():
    """Configura o logger para a aplicação."""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'automacao.log')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s')

    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler com rotação
    # 'midnight' para rotacionar todo dia, backupCount=7 para manter 7 arquivos de log
    fh = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=7, encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logging.info("Logger configurado com sucesso.")