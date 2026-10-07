from services.ai import get_openrouter_model_candidates, is_insufficient_quota_error


def test_get_model_candidates_prioritizes_configured_model_and_adds_safe_fallbacks():
    candidates = get_openrouter_model_candidates("deepseek/deepseek-chat-v3.1")

    assert candidates[0] == "deepseek/deepseek-chat-v3.1"
    assert "openai/gpt-4o-mini" in candidates
    assert "google/gemini-2.0-flash-001" in candidates


def test_insufficient_quota_error_is_detected():
    payload = {
        "error": {
            "message": "You have no credits remaining. Add credits to continue using the API at https://platform.openai.com/settings/organization/billing/.",
            "type": "insufficient_quota",
            "code": "credit_balance_exhausted",
        }
    }

    assert is_insufficient_quota_error(payload) is True
