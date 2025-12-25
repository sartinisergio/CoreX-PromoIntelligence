"""
Setup cartella Programmi per CoreX
"""

from pathlib import Path

# Crea cartella principale
programmi_dir = Path("Programmi")
programmi_dir.mkdir(exist_ok=True)

# Crea file README
readme_content = []
readme_content.append("# Cartella Programmi")
readme_content.append("")
readme_content.append("Organizza qui i programmi scaricati dai siti degli atenei.")
readme_content.append("")
readme_content.append("## Struttura")
readme_content.append("")
readme_content.append("Programmi/")
readme_content.append("    Nome_Materia/")
readme_content.append("        Classe_Laurea/")
readme_content.append("            NomeAteneo_Docente.pdf")
readme_content.append("")
readme_content.append("## Esempio")
readme_content.append("")
readme_content.append("Programmi/")
readme_content.append("    Chimica_Organica/")
readme_content.append("        L-13/")
readme_content.append("            UniMilano_Rossi.pdf")
readme_content.append("            UniRoma_Bianchi.pdf")
readme_content.append("        L-27/")
readme_content.append("            UniPadova_Neri.pdf")
readme_content.append("")
readme_content.append("## Come aggiungere programmi")
readme_content.append("")
readme_content.append("1. Naviga sul sito dell'ateneo")
readme_content.append("2. Trova il programma del corso")
readme_content.append("3. Se PDF: scaricalo direttamente")
readme_content.append("4. Se pagina web: Stampa > Salva come PDF")
readme_content.append("5. Salvalo nella cartella corretta")
readme_content.append("6. Nomina il file: Ateneo_Docente.pdf")

readme_text = "\n".join(readme_content)

with open(programmi_dir / "README.md", "w", encoding="utf-8") as f:
    f.write(readme_text)

# Crea materia di esempio
esempio = programmi_dir / "Chimica_Organica" / "L-13"
esempio.mkdir(parents=True, exist_ok=True)
(esempio / ".gitkeep").touch()

print("Cartella Programmi creata!")
print("Percorso:", programmi_dir.absolute())
print("")
print("Struttura:")
print("  Programmi/")
print("    README.md")
print("    Chimica_Organica/")
print("      L-13/")
print("")
print("Ora puoi creare altre cartelle materia/classe.")
