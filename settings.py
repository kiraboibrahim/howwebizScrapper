from decouple import config
import os

DB_HOST = config("DB_HOST")
DB_USER = config("DB_USER")
DB_PWD = config("DB_PWD")
DB_NAME = config("DB_NAME")
DEFAULT_DIR = os.path.expanduser("~") + config("DEFAULT_DIR")