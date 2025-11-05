import os
import glob
import json
import uuid
from sentence_transformers import SentenceTransformer
import chromadb

def unique_id():
    """Génère un identifiant unique pour ChromaDB"""
    return str(uuid.uuid4())

def extract_text_from_jsonl(line):
    """Extrait le texte d'une ligne JSONL"""
    try:
        data = json.loads(line.strip())
        # Essaie plusieurs champs possibles
        if "text" in data:
            return data["text"]
        elif "content" in data:
            return data["content"]
        elif "instruction" in data and "output" in data:
            return f"{data['instruction']} {data['output']}"
        else:
            # Si aucun champ standard, retourne la représentation JSON
            return str(data)
    except json.JSONDecodeError:
        # Si ce n'est pas du JSON valide, retourne la ligne brute
        return line.strip()

def extract_text_from_pdf(file_path):
    """Extrait le texte d'un fichier PDF"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip() if text else f"[PDF vide: {os.path.basename(file_path)}]"
    except Exception as e:
        return f"[Erreur lecture PDF {os.path.basename(file_path)}: {str(e)}]"

def ingest_and_vectorize(dir_path, collection):
    """Ingère et vectorise tous les documents d'un répertoire"""
    print(f"🔍 Début de l'ingestion depuis: {dir_path}")
    
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    batch_size = 16
    total_docs = 0

    def batch_add(texts, source_file):
        """Ajoute un batch de documents à ChromaDB"""
        nonlocal total_docs
        if not texts:
            return
        
        # Filtre les textes vides
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return
            
        embeddings = encoder.encode(valid_texts, batch_size=batch_size, show_progress_bar=False)
        ids = [unique_id() for _ in valid_texts]
        
        # Métadonnées pour traçabilité
        metadatas = [{"source": source_file, "type": os.path.splitext(source_file)[1]} for _ in valid_texts]
        
        collection.add(
            documents=valid_texts,
            embeddings=embeddings.tolist(),
            ids=ids,
            metadatas=metadatas
        )
        
        total_docs += len(valid_texts)
        print(f"  ✅ {len(valid_texts)} documents ajoutés depuis {os.path.basename(source_file)}")

    # Parcours tous les fichiers
    files = glob.glob(os.path.join(dir_path, "*"))
    if not files:
        print(f"⚠️  Aucun fichier trouvé dans {dir_path}")
        return

    for file_path in files:
        filename = os.path.basename(file_path)
        
        try:
            if file_path.endswith('.jsonl'):
                print(f"📄 Traitement JSONL: {filename}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    texts = [extract_text_from_jsonl(line) for line in f if line.strip()]
                
                # Traitement par batch
                for i in range(0, len(texts), batch_size):
                    batch_add(texts[i:i+batch_size], filename)

            elif file_path.endswith('.parquet'):
                print(f"📊 Traitement Parquet: {filename}")
                import pandas as pd
                df = pd.read_parquet(file_path)
                
                # Cherche la colonne de texte
                text_column = None
                for col in ['text', 'content', 'instruction', 'question', 'answer']:
                    if col in df.columns:
                        text_column = col
                        break
                
                if text_column:
                    texts = [str(t) for t in df[text_column].tolist() if pd.notna(t)]
                else:
                    # Concatène toutes les colonnes
                    texts = [' '.join(str(v) for v in row.values if pd.notna(v)) 
                            for _, row in df.iterrows()]
                
                # Traitement par batch
                for i in range(0, len(texts), batch_size):
                    batch_add(texts[i:i+batch_size], filename)

            elif file_path.endswith('.pdf'):
                print(f"📑 Traitement PDF: {filename}")
                doc_text = extract_text_from_pdf(file_path)
                if doc_text:
                    batch_add([doc_text], filename)
            else:
                print(f"⚠️  Type de fichier non supporté: {filename}")
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {filename}: {str(e)}")
            continue

    print(f"\n✨ Ingestion terminée: {total_docs} documents vectorisés au total")

def main():
    """Point d'entrée principal pour la vectorisation"""
    # Récupère le chemin depuis les variables d'environnement
    rag_path = os.getenv("RAG_PATH", "/rag_data")
    agent_name = os.getenv("AGENT_NAME", "AgentX")
    
    print(f"\n{'='*60}")
    print(f"🤖 Agent: {agent_name}")
    print(f"📂 Chemin RAG: {rag_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(rag_path):
        print(f"❌ ERREUR: Le répertoire {rag_path} n'existe pas!")
        return
    
    # Initialisation ChromaDB
    client = chromadb.Client()
    collection = client.get_or_create_collection(name="local_docs")
    
    # Lance l'ingestion
    ingest_and_vectorize(rag_path, collection)
    
    print(f"\n{'='*60}")
    print(f"✅ Vectorisation terminée pour {agent_name}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
