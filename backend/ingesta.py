from llama_index.core import VectorStoreIndex, Document, Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
from huggingface_hub import login
from typing import List
import fitz
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ── Configuración ──
QDRANT_URL   = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLECCION    = "leyes_peru"
DIMENSION    = 768
CARPETA_PDFS = "./documentos_legales"

# ── Embedding personalizado ──
class EmbeddingPersonalizado(BaseEmbedding):
    _modelo: SentenceTransformer = None

    def __init__(self, nombre_modelo: str, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_modelo',
            SentenceTransformer(nombre_modelo))

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._modelo.encode(query).tolist()

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._modelo.encode(text).tolist()

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._modelo.encode(texts).tolist()

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

def extraer_texto_pdf(ruta: str) -> str:
    doc = fitz.open(ruta)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    doc.close()
    return texto

def main():
    # 1. Login HuggingFace
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        login(token=hf_token)
        print("✅ HuggingFace autenticado")
    else:
        print("⚠ Sin token HuggingFace — descarga anónima")

    # 2. Cargar modelo de embeddings
    print("⏳ Cargando modelo de embeddings...")
    Settings.embed_model = EmbeddingPersonalizado(
        nombre_modelo="paraphrase-multilingual-mpnet-base-v2"
    )
    Settings.llm = None
    Settings.node_parser = SentenceSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    print("✅ Modelo listo")

    # 3. Conectar a Qdrant
    print(f"⏳ Conectando a Qdrant en {QDRANT_URL}...")
    cliente = QdrantClient(url=QDRANT_URL)
    print("✅ Qdrant conectado")

    # 4. Eliminar colección si existe y recrear limpia
    colecciones = [c.name for c in cliente.get_collections().collections]
    if COLECCION in colecciones:
        print(f"🗑 Eliminando colección anterior '{COLECCION}'...")
        cliente.delete_collection(COLECCION)

    cliente.create_collection(
        collection_name=COLECCION,
        vectors_config=VectorParams(
            size=DIMENSION,
            distance=Distance.COSINE
        )
    )
    print(f"✅ Colección '{COLECCION}' creada")

    # 5. Leer PDFs
    if not os.path.exists(CARPETA_PDFS):
        os.makedirs(CARPETA_PDFS)
        print(f"❌ Carpeta '{CARPETA_PDFS}' creada pero vacía")
        print(f"   Pon tus PDFs ahí y vuelve a correr el script")
        sys.exit(1)

    pdfs = [f for f in os.listdir(CARPETA_PDFS) if f.endswith('.pdf')]
    if not pdfs:
        print(f"❌ No hay PDFs en '{CARPETA_PDFS}'")
        sys.exit(1)

    print(f"\n📚 PDFs encontrados: {len(pdfs)}")
    for pdf in pdfs:
        print(f"   - {pdf}")

    # 6. Preparar vector store con storage context
    vector_store = QdrantVectorStore(
        client=cliente,
        collection_name=COLECCION
    )
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    # 7. Procesar cada PDF
    documentos = []
    for pdf in pdfs:
        ruta = os.path.join(CARPETA_PDFS, pdf)
        print(f"\n📄 Procesando: {pdf}")

        texto = extraer_texto_pdf(ruta)
        if not texto.strip():
            print(f"   ⚠ Sin texto extraíble, saltando...")
            continue

        print(f"   Caracteres: {len(texto)}")

        doc = Document(
            text=texto,
            metadata={
                "filename": pdf,
                "fuente":   pdf.replace('.pdf', '').replace('_', ' ').title(),
                "tipo":     "ley_peruana"
            }
        )
        documentos.append(doc)

    if not documentos:
        print("❌ No se pudo procesar ningún PDF")
        sys.exit(1)

    # 8. Indexar en Qdrant con storage_context
    print(f"\n⏳ Indexando {len(documentos)} documentos en Qdrant...")
    print("   Esto puede tardar varios minutos...")

    VectorStoreIndex.from_documents(
        documentos,
        storage_context=storage_context,  # ← clave para guardar en Qdrant
        show_progress=True
    )

    # 9. Verificar
    info   = cliente.get_collection(COLECCION)
    puntos = info.points_count or 0

    print(f"\n✅ Ingesta completa")
    print(f"   Colección:        {COLECCION}")
    print(f"   Puntos indexados: {puntos}")

    if puntos > 0:
        print(f"\n🎉 La base legal está lista para consultas")
    else:
        print(f"\n⚠ No se indexaron puntos — revisa los PDFs")

if __name__ == "__main__":
    main()