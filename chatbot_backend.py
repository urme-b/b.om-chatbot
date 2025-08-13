import os
from flask import Flask

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_together import Together
from langchain_core.runnables.base import RunnableSequence
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import langchain

from dotenv import load_dotenv
from uuid import uuid4

import json
import glob
import yaml
from langchain.schema import Document
from typing import Optional

import logging
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

langchain.debug = True

load_dotenv()

template = """
Your role is to assist users by answering questions related to both B·OM (the company) and Permaculture (the sustainable agriculture practice). You will provide accurate, trustworthy answers about B·OM's values, brands, and mission, as well as about permaculture, sustainable agriculture, tree planting, composting, and related topics.

Your responses should be clear, concise, friendly, and practical. Only answer using the documents and information provided. Do not make up answers or guess.

🔒 Core Instructions:
Answer only using the retrieved documents or explicitly supplied context.
If you don’t have information about the query, say:
“I don’t have information about that based on the materials I have. You may want to consult an expert or ask your mentor.”
Keep answers concise—avoid long explanations unless they are absolutely necessary.
Use simple, supportive, and respectful language.
Add brief source attribution when possible (e.g., “According to the Soil Guide PDF…”).
🧠 Contextual Awareness:
If a user asks a broad question (e.g., “What is permaculture?”), ask clarifying questions like:
“Where are you located?”
“Do you know the soil type or climate in your area?”
“What type of tree do you want to plant?”
If the information isn’t already in the conversation, ask the user to clarify.
Always reuse information already provided by the user when possible.
✅ Example:
Q: “How do I plant a tree?”
→ A: “Great question! Could you tell me where you’re located and what kind of tree you’re thinking of planting?”
Q: “I’m in southern Portugal, near the coast.”
→ A: “Thanks! Based on coastal Portugal’s Mediterranean climate, you’ll want to plant in early spring, dig a hole twice the width of the root ball, and mulch well... (continues).”

🚫 Forbidden Behaviors:
Do not invent facts, names, historical references, or quotes.
Avoid answering questions outside the domain of B·OM and permaculture. For example, if asked about something unrelated like politics or sports, say:
“I’m designed to help with permaculture, sustainability, and B·OM-related topics. I can’t assist with that.”
💡 Tone & Style:
Be friendly, concise, and clear.
Use simple language, avoid jargon, and be brief.
When unsure, say so and suggest where the user might find more information.
Use Markdown formatting for structured, readable responses:
Use ### for section titles.
Use - for bullet points or 1. for numbered steps.
Keep answers short, clear, and scannable.
Keep answers as concise as possible, especially when there's no information available. For instance, avoid adding unnecessary sections like "Next Steps" unless it's relevant.

Context:
{context}

Conversation so far:
{history}

User's question:
{question}

Respond with a helpful, accurate answer based only on the context above.
"""

# ---------- CONFIG ----------
DATA_DIR = "data"
BOM_DIR = os.path.join(DATA_DIR, "b-om")
PERM_DIR = os.path.join(DATA_DIR, "Permaculture")
VECTOR_DB_DIR = "faiss_store"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 150

BOM_KEYWORDS = {"b·om", "bom", "b-om", "platform", "habitat", "si-pe", "sipe",
                "experience", "study permaculture", "vision", "values", "mission", "brand"}
PERM_KEYWORDS = {"permaculture", "mollison", "pdc", "water harvesting",
                 "saddle dam", "swale", "guild", "agroforestry", "compost"}

chat_history = []

app = Flask(__name__)


# ---------- LOAD JSONL CHUNKS ----------
def load_jsonl_chunks(path: str, domain=None) -> list[Document]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            text = rec.get("text", "")
            meta = {
                "source": rec.get("doc_id", "unknown_doc"),
                "doc_id": rec.get("doc_id"),
                "chunk_id": rec.get("chunk_id"),
                "page_start": rec.get("page_start"),
                "page_end": rec.get("page_end"),
                "prechunked": True,   # <- important: skip re-splitting later
                "type": "jsonl_chunk"
            }
            docs.append(Document(page_content=text, metadata=meta))
    return docs


# ---------- LOAD YAML CARDS ----------
def load_yaml_cards(dir_path: str, domain=None) -> list[Document]:
    docs = []
    for path in glob.glob(os.path.join(dir_path, "*.yml")) + glob.glob(os.path.join(dir_path, "*.yaml")):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        content = data.get("content", "")
        meta = {
            "source": os.path.basename(path),
            "description": data.get("description"),
            "template": data.get("template"),
            "example": data.get("example"),
            "type": "yaml_card",
            "prechunked": False  # we’ll let the splitter chunk these (they’re short anyway)
        }
        # Use the content as the body; put description/template/example in metadata
        docs.append(Document(page_content=content, metadata=meta))
    return docs


# ---------- LOAD DOCUMENTS ----------
def load_dir_standard_files(dir_path: str, domain: str) -> list[Document]:
    docs = []
    for filename in os.listdir(dir_path):
        path = os.path.join(dir_path, filename)
        if filename.endswith(".pdf"):
            for d in PyPDFLoader(path).load():
                d.metadata.update({"domain": domain, "type": "pdf"})
                docs.append(d)
        elif filename.endswith(".txt"):
            for d in TextLoader(path).load():
                d.metadata.update({"domain": domain, "type": "txt"})
                docs.append(d)
        elif filename.endswith(".csv"):
            for d in CSVLoader(file_path=path).load():
                d.metadata.update({"domain": domain, "type": "csv"})
                docs.append(d)
        elif filename.endswith(".md"):
            for d in DirectoryLoader(dir_path, glob="*.md").load():
                d.metadata.update({"domain": domain, "type": "md"})
                docs.append(d)
    return docs


def load_documents():
    docs = []
    # b·om (company)
    docs += load_dir_standard_files(BOM_DIR, domain="bom")
    docs += load_yaml_cards(BOM_DIR, domain="bom")  # YAML cards

    # Permaculture (book + jsonl + any yaml)
    docs += load_dir_standard_files(PERM_DIR, domain="permaculture")
    docs += load_yaml_cards(PERM_DIR, domain="permaculture")

    # JSONL chunks in Permaculture
    for jsonl_path in glob.glob(os.path.join(PERM_DIR, "*.jsonl")):
        docs += load_jsonl_chunks(jsonl_path, domain="permaculture")

    return docs


# ---------- SPLIT TEXT ----------
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Only split docs that are NOT prechunked
    to_split, already_chunked = [], []
     
    for d in documents:
        if d.metadata.get("prechunked"):
            already_chunked.append(d)
        else:
            to_split.append(d)

    split_chunks = splitter.split_documents(to_split) if to_split else []
    for d in split_chunks:
        d.metadata.setdefault("domain", "unknown")
    chunks = already_chunked + split_chunks

    print(f"Split {len(to_split)} docs into {len(split_chunks)} chunks; "
          f"kept {len(already_chunked)} pre-chunked items")
    return chunks


def route_domain(query: str) -> Optional[dict]:
    q = query.lower()
    bom_hit = any(k in q for k in BOM_KEYWORDS)
    perm_hit = any(k in q for k in PERM_KEYWORDS)
    if bom_hit and not perm_hit:
        return {"domain": "bom"}
    if perm_hit and not bom_hit:
        return {"domain": "permaculture"}
    # default: search both
    return None


# ---------- EMBED & SAVE ----------
def create_or_load_vectorstore(_docs):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    if os.path.exists(VECTOR_DB_DIR):
        db = FAISS.load_local(VECTOR_DB_DIR, embeddings,
                              allow_dangerous_deserialization=True)
    else:
        db = FAISS.from_documents(_docs, embeddings)
        db.save_local(VECTOR_DB_DIR)

    return db


# ---------- CHAT HISTORY ----------
def handle_user_message(user_message):
    # Add the user's message to the history
    chat_history.append({"role": "user", "content": user_message})

    # Get the assistant's response
    answer = get_answer(user_message, chat_history)

    # Add the assistant's response to the history
    chat_history.append({"role": "assistant", "content": answer["content"]})

    return answer


# ---------- INITIALIZATION ----------
# llm = Together(
#     model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
#     temperature=0.7,
#     max_tokens=300,
#     together_api_key=os.getenv("TOGETHER_API_KEY")
# )

llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=1,
    max_tokens=300,
    openai_api_key=os.getenv("OPENAI_API_KEY")  # make sure this is set in your .env
)

if os.path.exists(VECTOR_DB_DIR):
    print("Vectorstore found. Loading from disk...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    db = FAISS.load_local(VECTOR_DB_DIR, embeddings,
                          allow_dangerous_deserialization=True)

else:
    print("No vectorstore found. Loading and splitting documents...")
    raw_docs = load_documents()
    docs = split_documents(raw_docs)
    db = create_or_load_vectorstore(docs)

qa_prompt = PromptTemplate(
    input_variables=["context", "history", "question"],
    template=template,
)

retriever = db.as_retriever(search_kwargs={"k": 3})

qa_chain = RunnableSequence(qa_prompt | llm)

# qa_chain = LLMChain(
#     llm=llm,
#     prompt=qa_prompt
# )

# qa = RetrievalQA.from_chain_type(
#     llm=llm,
#     retriever=db.as_retriever(search_kwargs={"k": 3}),
#     return_source_documents=True,
#     chain_type="stuff",
#     chain_type_kwargs={"prompt": qa_prompt}
# )


# ---------- GET ANSWER ----------
def get_answer(query):
    # route
    filt = route_domain(query)
    if filt:
        retr = db.as_retriever(search_kwargs={"k": 4, "filter": filt})
    else:
        retr = db.as_retriever(search_kwargs={"k": 4})

    docs = retr.invoke(query)
    logging.debug(f"Loaded {len(docs)} documents.")

    context = "\n\n".join([doc.page_content for doc in docs])
    citations = []
    for doc in docs:
        m = doc.metadata or {}
        if m.get("type") == "jsonl_chunk":
            citations.append(f"{m.get('doc_id','doc')} pp.{m.get('page_start')}-{m.get('page_end')}")
        else:
            citations.append(m.get("source", "Unknown"))

    logging.debug(f"Chat history length: {len(chat_history)}")
    history = "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in chat_history[:-1]])

    start_time = time.time()

    logging.debug(f"Context: {context}")
    logging.debug(f"History: {history}")

    response = qa_chain.invoke({
        "context": context or "No context available",
        "history": history or "No history available",
        "question": query
    })

    # ✅ Convert AIMessage to string safely
    if hasattr(response, "content"):
        answer_text = response.content
    elif isinstance(response, dict) and "text" in response:
        answer_text = response["text"]
    else:
        answer_text = str(response)

    end_time = time.time()
    logging.debug(f"Response length: {len(answer_text)}")
    logging.debug(f"Response time: {end_time - start_time} seconds")
    logging.debug(f"Response from QA Chain: {answer_text}")

    return {
        "role": "assistant",
        "content": answer_text + "\n\n**Sources:** " + "; ".join(dict.fromkeys(citations)),
        "sources": citations
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
