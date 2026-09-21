from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer


DOCS_DIR = Path("docs")

model = SentenceTransformer(
    "sentence-transformers/multi-qa-mpnet-base-cos-v1"
)


def load_chunks():
    chunks = []

    for path in DOCS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")

        # 第一版就按空行切，先别研究高级 chunking
        paragraphs = [
            p.strip()
            for p in text.split("\n\n")
            if p.strip()
        ]

        for paragraph in paragraphs:
            chunks.append({
                "source": path.name,
                "text": paragraph,
            })

    return chunks


chunks = load_chunks()

texts = [chunk["text"] for chunk in chunks]

document_embeddings = model.encode_document(
    texts,
    convert_to_tensor=True,
)


def retrieve(query: str, top_k: int = 3):
    query_embedding = model.encode_query(
        query,
        convert_to_tensor=True,
    )

    scores = model.similarity(
        query_embedding,
        document_embeddings,
    )[0]

    top_k = min(top_k, len(chunks))

    values, indices = torch.topk(scores, k=top_k)

    results = []

    for score, index in zip(values, indices):
        chunk = chunks[index.item()]

        results.append({
            "score": score.item(),
            "source": chunk["source"],
            "text": chunk["text"],
        })

    return results

if __name__ == "__main__":
#     results = retrieve("RAG 和普通调用大模型有什么区别？")

#     for result in results:
#         print(result["score"])
#         print(result["source"])
#         print(result["text"])
#         print()

    from openai import OpenAI
    import os

    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )


    def ask(question: str):
        results = retrieve(question)

        context = "\n\n".join(
            f"[来源: {r['source']}]\n{r['text']}"
            for r in results
        )

        response = client.responses.create(
            model="deepseek-flash",
            input=f"""
    请仅根据下面提供的资料回答问题。

    资料：
    {context}

    问题：
    {question}
    """
        )

        return response.output_text

    print(ask("RAG 和普通调用大模型有什么区别？"))