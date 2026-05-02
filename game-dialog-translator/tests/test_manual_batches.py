from src.manual_batches import PROMPT_TEMPLATE, build_next_manual_batch
from src.models import ParsedLine


def test_build_next_manual_batch_handles_literal_json_braces_in_template():
    assert "{\n  \"items\"" in PROMPT_TEMPLATE

    lines = [
        ParsedLine(
            line_number=1,
            raw_line="zh====Hello",
            chinese_part="zh",
            english_part="Hello {General}!",
            separator="====",
            has_separator=True,
        )
    ]

    batch = build_next_manual_batch(
        lines=lines,
        progress={},
        batch_size=1,
        file_hash="test-hash-manual-batches",
        source_name="sample.txt",
    )

    assert batch is not None
    assert '"line_number": 1' in batch.prompt
    assert '"english_text": "Hello __PH_0001__!"' in batch.prompt
