import logging
import os
import shutil
import traceback
from src.main.fb_objects import FBObjects as FbObj


def setup_custom_logger(name):

    try:
        if not os.path.exists(FbObj.parser.get('common', 'log_path')):
            os.makedirs(FbObj.parser.get('common', 'log_path'))
        else:
            shutil.rmtree(FbObj.parser.get('common', 'log_path'))
            os.makedirs(FbObj.parser.get('common', 'log_path'))
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        if FbObj.parser.get('common','log_level').lower() == "info":
            log_level = logging.INFO
        elif FbObj.parser.get('common','log_level').lower() == "debug":
            log_level = logging.DEBUG
        elif FbObj.parser.get('common','log_level').lower() == "error":
            log_level = logging.ERROR
        elif FbObj.parser.get('common','log_level').lower() == "warn":
            log_level = logging.WARN
        else:
            log_level = logging.INFO
        logfile = FbObj.parser.get('common', 'log_path')+os.sep+"feedbot.log"
        handler = logging.FileHandler(logfile)
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.addHandler(handler)
        return logger
    except Exception as ex:
        logger.error(ex)
        logger.error(traceback.format_exc())

    return None
