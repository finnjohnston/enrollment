import os
from pathlib import Path
import json

# === BASE DIRECTORY ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === REDIS CONFIGURATION ===
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# === DATABASE CONFIGURATION ===
DB_USER = os.getenv('POSTGRES_USER', 'finnjohnston')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'Ricknash2019!')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'enrollment')
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)

# === DATA FILE PATHS ===
DATA_DIR = BASE_DIR / 'db' / 'data'
COURSES_RAW_PATH = os.getenv('COURSES_RAW_PATH', str(DATA_DIR / 'courses' / 'raw.json'))
COURSES_PARSED_PATH = os.getenv('COURSES_PARSED_PATH', str(DATA_DIR / 'courses' / 'parsed.json'))
PROGRAMS_PATH = os.getenv('PROGRAMS_PATH', str(DATA_DIR / 'programs' / 'majors.json'))
POLICY_PATH = os.getenv('POLICY_PATH', str(DATA_DIR / 'policy' / 'policy.json'))

# === POLICY ENGINE CONFIGURATION ===
def load_policy_config(path=POLICY_PATH):
    with open(path, 'r') as f:
        return json.load(f)

POLICY_CONFIG = load_policy_config()

# === SEMESTER DEFAULTS ===
DEFAULT_START_SEMESTER = os.getenv('DEFAULT_START_SEMESTER', 'Fall')
DEFAULT_START_YEAR = int(os.getenv('DEFAULT_START_YEAR', 2024))

# === EXPORTS ===
CATALOG_URL = os.getenv('CATALOG_URL', 'https://www.vanderbilt.edu/catalogs/kuali/undergraduate-24-25.php#/courses')

__all__ = [
    'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB', 'REDIS_PASSWORD',
    'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'DATABASE_URL',
    'COURSES_RAW_PATH', 'COURSES_PARSED_PATH', 'PROGRAMS_PATH', 'POLICY_PATH',
    'POLICY_CONFIG', 'DEFAULT_START_SEMESTER', 'DEFAULT_START_YEAR', 'CATALOG_URL'
] 