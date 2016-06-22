from logging import getLogger
from logging.config import fileConfig
import os
directory = os.path.dirname(__file__)
fileConfig(os.path.join(directory, "log_config.ini"))

