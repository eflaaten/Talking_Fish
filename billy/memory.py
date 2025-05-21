import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class MemoryManager:
    """
    Mantella-inspired memory system for Billy.
    Handles episodic (conversation), semantic (facts), and summary (compressed) memories.
    Stores in JSON files for transparency and easy migration to DB if needed.
    """
    def __init__(self, memory_dir: str = "memory/"):
        os.makedirs(memory_dir, exist_ok=True)
        self.memory_dir = memory_dir
        self.episodic_file = os.path.join(memory_dir, "episodic.json")
        self.semantic_file = os.path.join(memory_dir, "semantic.json")
        self.summary_file = os.path.join(memory_dir, "summary.json")
        # Initialize files if missing
        for f in [self.episodic_file, self.semantic_file, self.summary_file]:
            if not os.path.exists(f):
                with open(f, "w") as fp:
                    json.dump([], fp)

    def add_conversation(self, user: str, ai: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "conversation",
            "user": user,
            "ai": ai
        }
        self._append_entry(self.episodic_file, entry)

    def add_fact(self, fact: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "semantic",
            "content": fact
        }
        self._append_entry(self.semantic_file, entry)

    def add_summary(self, summary: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "summary",
            "content": summary
        }
        self._append_entry(self.summary_file, entry)

    def _append_entry(self, file_path: str, entry: Dict):
        with open(file_path, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    def get_recent_conversations(self, n: int = 5) -> List[Dict]:
        with open(self.episodic_file) as f:
            data = json.load(f)
        return data[-n:]

    def get_facts(self, n: int = 5) -> List[Dict]:
        with open(self.semantic_file) as f:
            data = json.load(f)
        return data[-n:]

    def get_summaries(self, n: int = 3) -> List[Dict]:
        with open(self.summary_file) as f:
            data = json.load(f)
        return data[-n:]

    def get_relevant_memories(self, query: str, top_n: int = 5) -> List[Dict]:
        # Naive keyword search; can be replaced with embeddings later
        memories = []
        for file in [self.episodic_file, self.semantic_file, self.summary_file]:
            with open(file) as f:
                data = json.load(f)
                for entry in data:
                    if query.lower() in json.dumps(entry).lower():
                        memories.append(entry)
        # Sort by timestamp, return top_n
        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return memories[:top_n]

    def build_prompt_context(self, query: Optional[str] = None, max_memories: int = 5) -> str:
        """
        Build a context string for the LLM prompt, including relevant memories.
        If query is provided, fetch relevant; else, use most recent.
        """
        if query:
            memories = self.get_relevant_memories(query, top_n=max_memories)
        else:
            # Mix of recent summaries, facts, and conversations
            memories = self.get_summaries(2) + self.get_facts(2) + self.get_recent_conversations(1)
        context = "You remember these things:\n"
        for m in memories:
            if m["type"] == "semantic":
                context += f"- {m['content']}\n"
            elif m["type"] == "conversation":
                context += f"- User: {m['user']} | Billy: {m['ai']}\n"
            elif m["type"] == "summary":
                context += f"- {m['content']}\n"
        return context

    def extract_facts_from_conversation(self, user: str, ai: str, fact_extractor_fn) -> List[str]:
        """
        Use a fact_extractor_fn (e.g., LLM call) to extract facts from a conversation.
        Returns a list of fact strings.
        """
        # fact_extractor_fn should take (user, ai) and return list of facts
        return fact_extractor_fn(user, ai)

    def summarize_conversation(self, conversation: List[Dict], summarizer_fn) -> str:
        """
        Use summarizer_fn (e.g., LLM call) to summarize a conversation.
        Returns a summary string.
        """
        # summarizer_fn should take (conversation) and return summary string
        return summarizer_fn(conversation)

# Example usage (to be integrated in main loop):
# memory = MemoryManager()
# memory.add_conversation(user_text, ai_text)
# facts = memory.extract_facts_from_conversation(user_text, ai_text, your_llm_fact_extractor)
# for fact in facts:
#     memory.add_fact(fact)
# summary = memory.summarize_conversation(recent_conversation, your_llm_summarizer)
# memory.add_summary(summary)
# context = memory.build_prompt_context(prompt)
