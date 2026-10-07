from services.ai import get_openrouter_model_candidates


def test_get_model_candidates_prioritizes_configured_model_and_adds_safe_fallbacks():
    candidates = get_openrouter_model_candidates("deepseek/deepseek-chat-v3.1")

    assert candidates[0] == "deepseek/deepseek-chat-v3.1"
    assert "openai/gpt-4o-mini" in candidates
    assert "google/gemini-2.0-flash-001" in candidates
