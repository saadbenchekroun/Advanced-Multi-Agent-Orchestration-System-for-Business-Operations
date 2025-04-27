"""Memory management for the agent system"""

from google.adk.memory import MemoryStore, VectorMemory

def setup_memory(config: dict) -> MemoryStore:
    """Set up the memory store for agents"""
    memory_config = config.get("memory_settings", {})
    return VectorMemory(
        path=memory_config.get("vector_db_path", "./vector_db"),
        dimension=memory_config.get("dimension", 1536)
    )