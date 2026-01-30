from typing import List
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os
import logging
from config import BASE_DIR

# Отключаем лишние предупреждения при загрузке модели
logging.getLogger("transformers").setLevel(logging.ERROR)

class InterviewKnowledgeBase:
    def __init__(self):
        # База вопросов по уровням
        self.topics = {
            "python": {
                "junior": ["What are the basic data types in Python?", "Explain list vs tuple.", "What is a decorator?"],
                "middle": ["Explain the Global Interpreter Lock (GIL).", "How does memory management work?", "Generators vs Iterators."],
                "senior": ["Metaclasses usage.", "Asyncio internals.", "Python optimization techniques."]
            },
            "sql": {
                "junior": ["SELECT vs SELECT DISTINCT", "What is a primary key?", "Basic JOINs."],
                "middle": ["Index types.", "ACID properties.", "Normalization."],
                "senior": ["Query optimization.", "Transaction isolation levels.", "Sharding strategies."]
            },
            "general": {
                "junior": ["What is Git?", "HTTP methods."],
                "middle": ["REST vs SOAP.", "Docker basics."],
                "senior": ["System Design basics.", "Microservices patterns."]
            }
        }
        
        
        # Инициализация векторной базы знаний (RAG)
        print("Инициализация базы знаний... Это может занять пару секунд.")
        # Используем локальную модель эмбеддингов (она небольшая, ~100MB)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Используем локальную базу ChromaDB.
        # Если она пустая - наполним её данными.
        self.vector_store = Chroma(
            collection_name="interview_facts",
            embedding_function=self.embeddings,
            persist_directory=str(BASE_DIR / "chroma_db")
        )
        
        self._populate_db()

    def _populate_db(self):
        """
        Проверяем, пуста ли база. Если да - загружаем начальные факты.
        """
        # Простая проверка: если в коллекции нет элементов - наполняем.
        try:
            # count() показывает количество записей
            count = self.vector_store._collection.count()
            if count > 0:
                print(f"База знаний загружена. Фактов: {count}.")
                return
        except Exception:
            # Если ошибка доступа - считаем базу пустой
            pass

        print("Наполняем базу знаний...")
        facts = [
            # Python Core
            "Python 4.0 сейчас не планируется. Гвидо ван Россум сказал, что это вряд ли случится скоро.",
            "The Global Interpreter Lock (GIL) prevents multiple native threads from executing Python bytecodes at once in CPython.",
            "Lists are mutable arrays. Tuples are immutable sequences. Using tuples can be slightly faster and safer for fixed data.",
            "Decorators are functions that modify the behavior of other functions or methods. They use the @syntax.",
            "Generators are iterators that yield results one by one using `yield`, saving memory compared to lists.",
            "Context managers (with statement) ensure resources like files or locks are properly managed (opened/closed).",
            
            # Databases / SQL
            "ACID stands for Atomicity, Consistency, Isolation, Durability - properties that guarantee database transaction reliability.",
            "Indexing improves read speed but slows down write operations (INSERT/UPDATE/DELETE).",
            "Normalization is the process of organizing data to reduce redundancy. Denormalization is used for performance optimization.",
            "Sharding is horizontal scaling where data is distributed across multiple servers (shards), often by a shard key.",
            "CAP Theorem: A distributed system can provide only two of three: Consistency, Availability, Partition Tolerance.",
            "N+1 problem occurs when code explicitly executes a query for each child record instead of fetching them in a single query.",
            
            # Architecture / General
            "REST APIs typically use standard HTTP methods (GET, POST, PUT, DELETE) and commonly return JSON.",
            "Microservices architecture splits a monolithic app into smaller, independent services communicating via APIs.",
            "Docker containers package code and dependencies together to ensure consistency across environments.",
            "CI/CD (Continuous Integration/Continuous Deployment) automates testing and deployment pipelines.",
            "SOLID principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.",
            
            # Specifics mentioned in scenarios
            "Python's asyncio uses an event loop to run asynchronous tasks on a single thread.",
            "In Django, `select_related` performs a SQL join to fetch related objects, while `prefetch_related` does a separate lookup.",
            "Metaclasses in Python allow you to customize class creation. They are 'classes of classes'.",
        ]
        
        docs = [Document(page_content=f, metadata={"source": "init_data"}) for f in facts]
        self.vector_store.add_documents(docs)
        print("База знаний успешно наполнена.")

    def get_questions(self, topic: str, level: str) -> List[str]:
        return self.topics.get(topic.lower(), {}).get(level.lower(), [])

    def verify_fact(self, query: str) -> str:
        """
        Ищет похожие факты в векторной базе.
        """
        if not query or len(query.strip()) < 5:
            return "Запрос слишком короткий для проверки."
            
        # Ищем 2 самых похожих факта
        try:
            results = self.vector_store.similarity_search(query, k=2)
            
            if not results:
                return "В базе знаний ничего не найдено."
                
            formatted_results = "\n".join([f"- {doc.page_content}" for doc in results])
            return formatted_results
        except Exception as e:
            return f"Ошибка поиска в базе знаний: {str(e)}"

    def get_all_topics(self) -> List[str]:
        return list(self.topics.keys())

if __name__ == "__main__":
    print("Настройка базы знаний...")
    kb = InterviewKnowledgeBase()
    
    # Тестовые вопросы для проверки
    test_queries = [
        "What is the GIL?",
        "How do python lists differ from tuples?",
        "Tell me about database sharding",
        "Python 4.0 release date"
    ]
    
    print("\n--- Проверка поиска ---")
    for q in test_queries:
        print(f"\nВопрос: {q}")
        print(f"Результат:\n{kb.verify_fact(q)}")
    
    print("\nБаза знаний готова к работе.")
