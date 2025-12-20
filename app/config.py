"""
config.py
Configurazioni globali per CoreX
"""

from pathlib import Path
from typing import Final

# Percorsi
BASE_DIR: Final = Path(__file__).parent.parent
DATA_DIR: Final = BASE_DIR / "data"
SYLLABUS_DIR: Final = DATA_DIR / "syllabus"
EXTRACTED_DIR: Final = DATA_DIR / "extracted"
OUTPUT_DIR: Final = DATA_DIR / "outputs"

# Assicura che le directory esistano
for dir_path in [SYLLABUS_DIR, EXTRACTED_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Soglie di classificazione
THRESHOLD_CORE: Final = 0.85
THRESHOLD_COMUNE: Final = 0.40

# NLP Settings
SPACY_MODEL: Final = "it_core_news_sm"
MIN_CONCEPT_LENGTH: Final = 3
MAX_NGRAM_SIZE: Final = 4

# LLM Settings (OpenAI)
OPENAI_MODEL: Final = "gpt-4o"
MAX_TOKENS_DISAMBIGUATION: Final = 1024

# Clustering Settings
MIN_CLUSTER_SIZE: Final = 3
TARGET_N_MODULES: Final = 15