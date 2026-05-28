def get_checkpointer(config: dict):
    """Return a LangGraph checkpointer if checkpoint_enabled, else None."""
    if not config.get("checkpoint_enabled", False):
        return None
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
