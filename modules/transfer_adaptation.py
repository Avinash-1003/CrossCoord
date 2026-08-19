import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

class TransferAdaptationModule:
    """
    RAG-based Transfer Adaptation Module.
    Uses FAISS and SentenceTransformers to retrieve domain-specific
    Standard Operating Procedures (SOPs) based on semantic search.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print("[Transfer/RAG] Initializing Embedding Model...")
        self.encoder = SentenceTransformer(model_name)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        
        # FAISS Index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        self.documents = []
        self.document_metadata = []
        self.registered_domains = set()
        
        self.stats = {
            "total_transfers": 0,
            "known_domain": 0,
            "zero_shot": 0
        }
        
        # Load local knowledge base
        self._load_knowledge_base()
        
    def _load_knowledge_base(self):
        kb_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "domain_knowledge")
        if not os.path.exists(kb_path):
            print(f"[Transfer/RAG] Knowledge base path {kb_path} not found.")
            return

        for filename in os.listdir(kb_path):
            if filename.endswith(".txt"):
                domain = filename.replace(".txt", "")
                filepath = os.path.join(kb_path, filename)
                
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                # Split by sections for finer retrieval
                sections = content.split("## ")
                for i, section in enumerate(sections):
                    if not section.strip():
                        continue
                    text = "## " + section if i > 0 else section
                    self._add_document(text.strip(), {"domain": domain, "section_id": i})
                    
                self.registered_domains.add(domain)
                print(f"[Transfer/RAG] Indexed domain knowledge: '{domain}'")

    def _add_document(self, text, metadata):
        embedding = self.encoder.encode([text])
        faiss.normalize_L2(embedding)
        self.index.add(embedding)
        self.documents.append(text)
        self.document_metadata.append(metadata)

    def retrieve_context(self, query, k=3):
        """
        Semantic search for the top-k most relevant SOP sections.
        """
        if self.index.ntotal == 0:
            return "No domain knowledge available."
            
        query_emb = self.encoder.encode([query])
        faiss.normalize_L2(query_emb)
        
        distances, indices = self.index.search(query_emb, k)
        
        retrieved = []
        for idx in indices[0]:
            if idx != -1:
                meta = self.document_metadata[idx]
                doc = self.documents[idx]
                retrieved.append(f"[{meta['domain'].upper()}] {doc}")
                
        return "\n\n".join(retrieved)

    def transfer_to_domain(self, target_domain, config):
        """
        Constructs the Prompt/Bundle for the LLM using RAG.
        If the domain is unseen, it retrieves the most semantically similar
        knowledge from known domains (Zero-Shot Transfer).
        """
        self.stats["total_transfers"] += 1
        query = f"Operational protocols, hazards, and agent roles for {target_domain.replace('_', ' ')}."
        
        if target_domain in self.registered_domains:
            print(f"[Transfer/RAG] ✅ Known domain '{target_domain}'. Retrieving direct SOPs.")
            transfer_type = "known_domain"
            self.stats["known_domain"] += 1
        else:
            print(f"[Transfer/RAG] 🔄 Unseen domain '{target_domain}'. Performing semantic retrieval for Zero-Shot Transfer.")
            transfer_type = "zero_shot"
            self.stats["zero_shot"] += 1

        context = self.retrieve_context(query, k=2)
        
        bundle = {
            "domain": target_domain,
            "transfer_type": transfer_type,
            "retrieved_context": context,
            "config": config
        }
        return bundle

    def get_metrics(self):
        return {
            "total_transfers": self.stats["total_transfers"],
            "known_domain": self.stats["known_domain"],
            "zero_shot": self.stats["zero_shot"],
            "registered_domains": list(self.registered_domains),
            "total_documents": len(self.documents)
        }

if __name__ == "__main__":
    # Test the RAG module
    tam = TransferAdaptationModule()
    
    # Test known domain
    bundle1 = tam.transfer_to_domain("logistics", {})
    print("\n--- Logistics Retrieval ---")
    print(bundle1["retrieved_context"][:300] + "...")
    
    # Test zero-shot transfer for a completely new domain
    bundle2 = tam.transfer_to_domain("underwater_construction", {})
    print("\n--- Zero-Shot Retrieval (Underwater Construction) ---")
    print(bundle2["retrieved_context"][:300] + "...")
