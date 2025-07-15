# logging_config.py

import logging

def setup_logging(log_level=logging.DEBUG, log_file="gasops.log"):
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            logging.StreamHandler()
        ]
    )
