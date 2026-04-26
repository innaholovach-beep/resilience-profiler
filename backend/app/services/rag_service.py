"""
RAG-сервіс для Resilience Profiler.

Як це працює:
  1. При старті: завантажує документи з knowledge_base/, ділить на chunks,
     перетворює на embeddings і зберігає у ChromaDB.
  2. При запиті: знаходить top-K найближчих chunks до запиту користувача,
     формує prompt = профіль + знайдені фрагменти + запит,
     надсилає у LLM (Ollama або OpenAI), повертає відповідь.

Залежності:
  pip install chromadb sentence-transformers ollama
  (або pip install openai якщо використовуєш OpenAI)
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

# ── Константи ─────────────────────────────────────────────────────────────────

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
CHROMA_PERSIST_DIR = Path(__file__).parent.parent.parent / "chroma_db"
COLLECTION_NAME    = "resilience_knowledge"

# Модель для embeddings (завантажується автоматично ~90MB)
EMBED_MODEL = "all-MiniLM-L6-v2"

# LLM налаштування
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")   # "ollama" або "openai"
LLM_MODEL    = os.getenv("LLM_MODEL", "llama3")       # для ollama
OPENAI_KEY   = os.getenv("OPENAI_API_KEY", "")

CHUNK_SIZE    = 500   # символів
CHUNK_OVERLAP = 50
TOP_K         = 3     # скільки фрагментів витягувати

# ── Назви вимірів ─────────────────────────────────────────────────────────────

DIMENSION_NAMES = {
    "emotional_regulation": "Емоційна регуляція",
    "cognitive_flexibility": "Когнітивна гнучкість",
    "social_support":        "Соціальна підтримка",
    "self_efficacy":         "Самоефективність",
    "meaning_making":        "Осмислення досвіду",
}


# ── Клієнт ChromaDB ───────────────────────────────────────────────────────────

def _get_client_and_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return client, collection


# ── Завантаження та індексація документів ─────────────────────────────────────

def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Ділить текст на перекриваючі фрагменти."""
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if len(c) > 50]


def index_knowledge_base(force: bool = False) -> int:
    """
    Читає всі .txt і .md файли з knowledge_base/ та індексує їх у ChromaDB.
    Повертає кількість проіндексованих chunks.
    Якщо force=False і колекція вже не порожня — пропускає.
    """
    _, collection = _get_client_and_collection()

    if not force and collection.count() > 0:
        return collection.count()

    if not KNOWLEDGE_BASE_DIR.exists():
        KNOWLEDGE_BASE_DIR.mkdir(parents=True)
        _seed_demo_knowledge()

    docs, ids, metas = [], [], []
    doc_id = 0

    for filepath in KNOWLEDGE_BASE_DIR.glob("**/*"):
        if filepath.suffix not in (".txt", ".md"):
            continue

        text = filepath.read_text(encoding="utf-8", errors="ignore")
        chunks = _chunk_text(text)

        for chunk in chunks:
            docs.append(chunk)
            ids.append(f"doc_{doc_id}")
            metas.append({
                "source":   filepath.name,
                "filepath": str(filepath),
            })
            doc_id += 1

    if docs:
        # Додаємо пакетами по 100
        for i in range(0, len(docs), 100):
            collection.add(
                documents=ids[i:i+100],
                ids=ids[i:i+100],
                metadatas=metas[i:i+100],
            )
            # ChromaDB зберігає documents в окремому полі
            collection.update(
                ids=ids[i:i+100],
                documents=docs[i:i+100],
            )

    return doc_id


# ── Пошук релевантних фрагментів ──────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Знаходить top_k найбільш семантично схожих фрагментів.
    Повертає список {"text": ..., "source": ..., "distance": ...}
    """
    _, collection = _get_client_and_collection()

    if collection.count() == 0:
        index_knowledge_base()

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "distance": round(dist, 4),
        })
    return chunks


# ── Формування prompt ─────────────────────────────────────────────────────────

def _build_prompt(
    query: str,
    profile: dict,
    chunks: list[dict],
) -> str:
    dims = profile.get("dimensions", {})
    profile_lines = "\n".join(
        f"  - {DIMENSION_NAMES.get(k, k)}: {v:.1f}/5.0"
        for k, v in dims.items()
    )

    context_text = "\n\n---\n\n".join(
        f"[Джерело: {c['source']}]\n{c['text']}"
        for c in chunks
    )

    return f"""Ти — психологічний асистент, який спеціалізується на резильєнтності та психологічному благополуччі.
Відповідай українською мовою, тепло і підтримуючи. Давай конкретні, практичні поради.
Не вигадуй факти — спирайся лише на наданий контекст і профіль користувача.

=== ПРОФІЛЬ КОРИСТУВАЧА ===
Загальний бал резильєнтності: {profile.get('overall_score', '?')}/5.0
Тип профілю: {profile.get('profile_type', '?')}

Виміри:
{profile_lines}

=== РЕЛЕВАНТНІ МАТЕРІАЛИ З БАЗИ ЗНАНЬ ===
{context_text}

=== ЗАПИТАННЯ КОРИСТУВАЧА ===
{query}

=== ТВОЯ ВІДПОВІДЬ ==="""


# ── Генерація відповіді через LLM ─────────────────────────────────────────────

def _generate_ollama(prompt: str) -> str:
    try:
        import ollama
        response = ollama.generate(model=LLM_MODEL, prompt=prompt)
        return response["response"].strip()
    except Exception as e:
        return f"[Ollama недоступна: {e}. Встанови Ollama: https://ollama.ai та запусти: ollama pull {LLM_MODEL}]"


def _generate_openai(prompt: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[OpenAI помилка: {e}]"


def _generate_fallback(prompt: str, chunks: list[dict]) -> str:
    """Fallback без LLM: повертає найбільш релевантні фрагменти напряму."""
    if not chunks:
        return "Наразі база знань порожня. Додайте .txt або .md файли у папку knowledge_base/."
    best = chunks[0]
    return (
        f"На основі бази знань (джерело: {best['source']}):\n\n"
        f"{best['text']}\n\n"
        f"(LLM недоступна — встанови Ollama або додай OpenAI ключ у .env)"
    )


# ── Публічний API ─────────────────────────────────────────────────────────────

def ask(query: str, profile: dict) -> dict:
    """
    Головна функція RAG.

    Args:
        query:   запит користувача
        profile: словник з overall_score, profile_type, dimensions

    Returns:
        {
            "answer":  str,
            "sources": [{"source": str, "distance": float}],
            "chunks_used": int,
        }
    """
    chunks = retrieve(query, top_k=TOP_K)
    prompt = _build_prompt(query, profile, chunks)

    if LLM_PROVIDER == "openai" and OPENAI_KEY:
        answer = _generate_openai(prompt)
    elif LLM_PROVIDER == "ollama":
        answer = _generate_ollama(prompt)
    else:
        answer = _generate_fallback(prompt, chunks)

    return {
        "answer":      answer,
        "sources":     [{"source": c["source"], "distance": c["distance"]} for c in chunks],
        "chunks_used": len(chunks),
    }


# ── Демо-контент для бази знань ───────────────────────────────────────────────

def _seed_demo_knowledge():
    """Створює демонстраційні файли у knowledge_base/ якщо папка порожня."""
    articles = {
        "resilience_basics.txt": """
Психологічна резильєнтність — це здатність людини успішно адаптуватися до важких життєвих обставин,
травм, трагедій, загроз або серйозних джерел стресу.

Резильєнтність не означає, що людина не переживає труднощів або дистресу. Емоційний біль і сум
є поширеними у людей, які пережили великі нещастя. Резильєнтність — це процес, а не риса.

П'ять ключових компонентів резильєнтності:
1. Емоційна регуляція — здатність керувати сильними почуттями та імпульсами.
2. Когнітивна гнучкість — здатність мислити гнучко, знаходити альтернативні рішення.
3. Соціальна підтримка — наявність надійних стосунків та соціальних зв'язків.
4. Самоефективність — впевненість у власній здатності справлятися з викликами.
5. Осмислення досвіду — здатність знаходити сенс навіть у важких ситуаціях.

Дослідження показують, що резильєнтність можна розвивати протягом усього життя.
        """,
        "emotional_regulation.txt": """
Емоційна регуляція — це процес, за допомогою якого люди впливають на власні емоції,
коли вони виникають, як довго тривають і як виражаються.

Практичні техніки емоційної регуляції:

Техніка STOP:
S — Stop (зупинись)
T — Take a breath (зроби вдих)
O — Observe (спостерігай за своїми думками та відчуттями)
P — Proceed (продовжуй усвідомлено)

Дихальна техніка 4-7-8:
- Вдих через ніс — 4 секунди
- Затримка дихання — 7 секунд
- Видих через рот — 8 секунд
Повторити 4 рази. Активує парасимпатичну нервову систему.

Box breathing (використовується у спецназі):
- Вдих — 4 секунди
- Затримка — 4 секунди
- Видих — 4 секунди
- Затримка — 4 секунди

Когнітивне переосмислення:
Замість "Я не можу з цим впоратись" → "Це важко, але я вже долав складні ситуації раніше."
        """,
        "cognitive_flexibility.txt": """
Когнітивна гнучкість — здатність адаптувати мислення до нових ситуацій,
перемикатися між різними концепціями та думати про кілька речей одночасно.

Як розвивати когнітивну гнучкість:

1. Рефреймінг ситуацій:
Запитай себе: "Яким ще чином можна подивитись на цю ситуацію?"
Спробуй знайти мінімум 3 різних інтерпретації однієї події.

2. Техніка "А що якщо?":
"А що якщо це насправді можливість, а не загроза?"
"А що якщо я можу впоратись з цим краще, ніж думаю?"

3. Практика невизначеності:
Навмисно вводь невеликі зміни у повсякденне життя.
Нова дорога на роботу, нова книга у незвичному жанрі.

4. Ментальна симуляція:
Уяви кілька сценаріїв розвитку подій і подумай, як би ти реагував у кожному.
        """,
        "social_support.txt": """
Соціальна підтримка є одним з найважливіших захисних факторів психічного здоров'я.
Дослідження Дж. Хаус виділяє 4 типи соціальної підтримки:

1. Емоційна підтримка — вираження емпатії, турботи, любові.
2. Інструментальна підтримка — конкретна практична допомога.
3. Інформаційна підтримка — поради, інформація, зворотний зв'язок.
4. Оцінювальна підтримка — допомога у самооцінці.

Як зміцнювати соціальну підтримку:
- Регулярно підтримуй контакт з близькими (навіть коротке повідомлення)
- Практикуй активне слухання — повна присутність у розмові
- Не бійся просити допомоги — це ознака сили, не слабкості
- Долучайся до груп за інтересами або волонтерства

Ефект "буфера стресу": соціальна підтримка зменшує негативний вплив стресових подій.
        """,
        "self_efficacy.txt": """
Самоефективність — концепція Альберта Бандури — це переконання людини у своїй здатності
виконувати дії, необхідні для досягнення певних результатів.

Джерела самоефективності (Бандура, 1977):
1. Досвід майстерності — власні успіхи є найпотужнішим джерелом.
2. Вікарний досвід — спостереження за успіхами схожих людей.
3. Соціальне переконання — підбадьорення від авторитетних людей.
4. Фізіологічний стан — управління стресом і фізичними реакціями.

Практики для підвищення самоефективності:
- Ставь маленькі, досяжні цілі і святкуй їх досягнення
- Веди "журнал перемог" — записуй навіть дрібні успіхи щодня
- Оточуй себе людьми, які вірять у тебе
- Аналізуй минулі успіхи перед новими викликами
        """,
        "meaning_making.txt": """
Осмислення досвіду (meaning-making) — це процес інтеграції нового досвіду
(особливо травматичного) у існуючу систему переконань.

Постравматичне зростання (Tedeschi & Calhoun):
Дослідження показують, що багато людей після травматичних подій повідомляють про:
- Нові можливості та шляхи
- Зближення з іншими людьми
- Відчуття особистої сили
- Духовні зміни
- Більшу цінність життя

Практики осмислення:
1. Наративна терапія — запиши свою історію від третьої особи.
2. Gratitude journal — 3 речі вдячності щодня.
3. Пошук "уроків" — "Чого ця ситуація навчила мене?"
4. Медитація loving-kindness — розвиток співчуття до себе і інших.
5. Волонтерство — допомога іншим дає відчуття сенсу.
        """,
    }

    for filename, content in articles.items():
        (KNOWLEDGE_BASE_DIR / filename).write_text(content.strip(), encoding="utf-8")
