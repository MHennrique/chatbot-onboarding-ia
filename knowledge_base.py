import os
import docx
import pandas as pd
import PyPDF2

def ler_documentos_pasta(caminho_pasta):
    """Lê todos os arquivos .txt, .docx, .pdf e .csv de uma pasta."""
    base_conhecimento = ""
    print(f"Lendo documentos de: {caminho_pasta}")

    for nome_arquivo in os.listdir(caminho_pasta):
        caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
        try:
            if nome_arquivo.endswith(".txt"):
                with open(caminho_completo, 'r', encoding='utf-8') as f:
                    base_conhecimento += f.read() + "\n"
            elif nome_arquivo.endswith(".docx"):
                doc = docx.Document(caminho_completo)
                for para in doc.paragraphs:
                    base_conhecimento += para.text + "\n"
            elif nome_arquivo.endswith(".pdf"):
                with open(caminho_completo, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        base_conhecimento += page.extract_text() + "\n"
            elif nome_arquivo.endswith(".csv"):
                df = pd.read_csv(caminho_completo)
                base_conhecimento += df.to_markdown(index=False) + "\n" 

            print(f"  - Arquivo '{nome_arquivo}' lido com sucesso.")
        except Exception as e:
            print(f"Erro ao ler o arquivo {nome_arquivo}: {e}")
            
    return base_conhecimento

CONTEUDO_EMPRESA = ler_documentos_pasta('documentos')
print("\nBase de conhecimento carregada com sucesso!")