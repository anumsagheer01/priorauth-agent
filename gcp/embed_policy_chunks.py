"""Generate Vertex embeddings for policy chunks, one model for the index.

--verify-only embeds one short text and prints the model and dimension,
so Cloud Shell can confirm the model exists before any paid indexing.
Full run writes data/policy_chunk_embeddings.json (chunk_id, model,
dimension, vector) for audit, and is the input for BigQuery VECTOR_SEARCH
loading in a follow-up step. It never mixes embedding models.
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from priorauth.cloud_clients import CloudConfig
ROOT = Path(__file__).resolve().parents[1]
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    config = CloudConfig()
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    vertexai.init(project=config.project, location=config.location)
    model = TextEmbeddingModel.from_pretrained(config.embedding_model)
    probe = model.get_embeddings(["Prior authorization documentation readiness."])[0].values
    print(f"embedding_model={config.embedding_model} dimension={len(probe)}")
    if args.verify_only:
        return 0
    chunks = json.loads((ROOT / "data" / "policy_chunks.json").read_text())
    chunks = chunks["chunks"] if isinstance(chunks, dict) else chunks
    out = []
    for chunk in chunks:
        emb = model.get_embeddings([chunk.get("text", "")])[0].values
        assert len(emb) == len(probe), "Embedding dimension changed mid-run. Stop, do not mix dimensions."
        out.append({"chunk_id": chunk.get("chunk_id", ""), "policy_id": chunk.get("policy_id", ""),
                    "model": config.embedding_model, "dimension": len(emb), "vector": list(emb)})
        print(f"embedded {chunk.get('chunk_id', '')} dim={len(emb)}")
    (ROOT / "data" / "policy_chunk_embeddings.json").write_text(json.dumps(out))
    print(f"Wrote {len(out)} embeddings.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
