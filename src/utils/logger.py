import logging
import os
import yaml

def get_logger(name):
    """
    Configures and returns a standard logger.
    """

    # Load config to get log path
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.paht.join(log_dir, 'project_execution.log')

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create formatters and handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handlers to logger if they do not exist
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger