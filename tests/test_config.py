from pathlib import Path

from app.utils.config import Settings


def test_config_loads_from_env_example() -> None:
    env_example = Path(__file__).resolve().parents[1] / ".env.example"

    loaded = Settings.from_env(env_example)

    assert loaded.embedding_model == "BAAI/bge-m3"
    assert loaded.ollama_model == "qwen2.5:7b"
    assert loaded.top_k == 5
    assert loaded.chunk_size == 800
    assert loaded.chunk_overlap == 150
