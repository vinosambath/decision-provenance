from app.ingest.lexicons import score


def test_commitment_phrase_raises_decision_density() -> None:
    density, _, _ = score("Priya: Alright, let's go with Kafka. Final call.")
    assert density > 0


def test_status_update_has_zero_density() -> None:
    density, has_alternatives, has_objection = score("Tom: finished the billing export, no blockers")
    assert density == 0
    assert not has_alternatives
    assert not has_objection


def test_alternative_marker_detected() -> None:
    _, has_alternatives, _ = score("Daniel: what about Kinesis instead of Kafka?")
    assert has_alternatives


def test_objection_marker_detected() -> None:
    _, _, has_objection = score("Wei Lin: my concern is the consumer-group limit.")
    assert has_objection


def test_density_is_normalized_by_line_count() -> None:
    one_line = "Priya: let's go with Kafka."
    three_lines = "Priya: let's go with Kafka.\nDaniel: works for me.\nAna: sounds good."

    short_density, _, _ = score(one_line)
    long_density, _, _ = score(three_lines)

    assert short_density > long_density
