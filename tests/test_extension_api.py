from nexus.storage.db import NexusDatabase


def test_pairing_and_extension_security():
    db = NexusDatabase()

    # 1. Pairing token generation
    code = db.generate_pairing_code()
    assert len(code) == 8

    # 2. Token verification
    token = db.verify_and_claim_pairing_code(code)
    assert token is not None
    assert db.validate_token(token) is True
    assert db.validate_token("invalid_token") is False

    # 3. Session event recording
    sess = db.record_session_event(
        provider="ChatGPT",
        url="https://chatgpt.com/c/test-session-123",
        title="ML Safety Chat",
        event_type="navigation",
    )
    assert sess["session_id"].startswith("sess_")

    sessions = db.list_tracked_sessions()
    assert any(s["url"] == "https://chatgpt.com/c/test-session-123" for s in sessions)


def test_conversation_import_and_retrieval():
    db = NexusDatabase()

    cid = db.store_conversation(
        provider="Claude",
        title="Architecture Discussion",
        content="Here is the complete conversation about local Gemma deployment.",
        import_method="text",
        source_url="https://claude.ai/chat/456",
    )
    assert cid.startswith("conv_")

    conv = db.get_conversation(cid)
    assert conv is not None
    assert conv["title"] == "Architecture Discussion"
    assert "local Gemma" in conv["content"]

    # Delete test
    assert db.delete_conversation(cid) is True
    assert db.get_conversation(cid) is None
