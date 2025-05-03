import json
from pathlib import Path

RECENT_MEM_FILE = Path("/home/eflaaten/billy/billy_recent_memories.json")
CORE_MEM_FILE = Path("/home/eflaaten/billy/billy_core_memories.json")

RECENT_LIMIT = 10
CORE_LIMIT = 100

def load_memories(path, limit):
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
            return data[-limit:]
    return []

def save_memories(path, memories, limit):
    memories = memories[-limit:]
    with open(path, "w") as f:
        json.dump(memories, f)

def add_recent_memory(entry):
    mems = load_memories(RECENT_MEM_FILE, RECENT_LIMIT)
    mems.append(entry)
    save_memories(RECENT_MEM_FILE, mems, RECENT_LIMIT)

def get_recent_memories(n=3):
    return load_memories(RECENT_MEM_FILE, RECENT_LIMIT)[-n:]

def add_core_memory(summary):
    mems = load_memories(CORE_MEM_FILE, CORE_LIMIT)
    mems.append(summary)
    save_memories(CORE_MEM_FILE, mems, CORE_LIMIT)

def get_core_memories(n=3):
    return load_memories(CORE_MEM_FILE, CORE_LIMIT)[-n:]
