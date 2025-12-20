# CoreX - Core Extractor

Estrazione automatica di framework disciplinari da programmi d'esame universitari.

## Installazione

```bash
cd CoreX
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure: venv\Scripts\activate  # Windows

pip install -r requirements.txt
python -m spacy download it_core_news_lg