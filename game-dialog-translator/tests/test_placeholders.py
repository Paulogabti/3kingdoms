from src.placeholders import protect_placeholders, restore_placeholders


def test_placeholder_roundtrip():
    text = "NI wants to go to PLACE1NAME with SN1MING."
    bundle = protect_placeholders(text)
    restored = restore_placeholders(bundle.protected_text, bundle.token_to_original)
    assert "NI" in restored
    assert "PLACE1NAME" in restored
    assert "SN1MING" in restored
