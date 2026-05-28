_config: dict = {}

def set_config(config: dict) -> None:
    global _config
    _config = config

def get_config() -> dict:
    return _config
