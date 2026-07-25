import json

from wapitiCore.attack.modules.passive.base import PassiveModule


def test_should_report_defaults_to_report_once_per_key():
    module = PassiveModule()

    assert module.should_report(("host", "type")) is True
    # Same key again is suppressed with the default LIMIT of 1
    assert module.should_report(("host", "type")) is False
    assert module.should_report(("host", "type")) is False
    # A different key is reported independently
    assert module.should_report(("host", "other")) is True

    assert module.suppressed_findings == 2


def test_limit_allows_several_occurrences_before_suppressing():
    module = PassiveModule()
    module.LIMIT = 2

    assert module.should_report("k") is True
    assert module.should_report("k") is True
    assert module.should_report("k") is False

    assert module.suppressed_findings == 1


class _FindingA:
    @staticmethod
    def name():
        return "Category A"


class _FindingB:
    @staticmethod
    def name():
        return "Category B"


def test_suppressions_are_tallied_per_finding_category():
    module = PassiveModule()

    # First occurrence of each key is reported, subsequent ones are suppressed
    # and counted against the finding class category.
    assert module.should_report("a", _FindingA) is True
    assert module.should_report("a", _FindingA) is False
    assert module.should_report("a", _FindingA) is False
    assert module.should_report("b", _FindingB) is True
    assert module.should_report("b", _FindingB) is False

    assert module.suppressed_findings == 3
    assert dict(module.suppressed_by_category) == {"Category A": 2, "Category B": 1}


def test_suppressions_without_category_only_bump_the_total():
    module = PassiveModule()

    assert module.should_report("k") is True
    assert module.should_report("k") is False

    assert module.suppressed_findings == 1
    assert not module.suppressed_by_category


def test_state_round_trip_preserves_dedup_and_counters():
    module = PassiveModule()

    module.should_report("a", _FindingA)  # reported, occurrences[a] = 1
    module.should_report("a", _FindingA)  # suppressed
    module.should_report("b", _FindingB)  # reported

    state = module.get_state()

    # A fresh module loaded with that state must behave as the original: the
    # already-seen keys stay capped and the counters are preserved.
    restored = PassiveModule()
    restored.load_state(state)

    assert restored.suppressed_findings == 1
    assert dict(restored.suppressed_by_category) == {"Category A": 1}
    # Key "a" already reached LIMIT -> still suppressed (no duplicate alert on resume)
    assert restored.should_report("a", _FindingA) is False
    # Key "b" reported once -> now capped too
    assert restored.should_report("b", _FindingB) is False
    assert restored.suppressed_findings == 3


def test_state_round_trip_through_json_with_tuple_keys():
    # Most modules deduplicate on tuple keys (e.g. (host, header, ...)), which JSON
    # cannot use as object keys. The state must survive a real serialize/deserialize.
    module = PassiveModule()
    module.should_report(("example.com", "CSP", "Missing"), _FindingA)  # reported
    module.should_report(("example.com", "CSP", "Missing"), _FindingA)  # suppressed
    module.should_report("plain-string-key", _FindingB)  # reported

    # Persistence path: get_state -> json blob -> back to a dict -> load_state
    restored = PassiveModule()
    restored.load_state(json.loads(json.dumps(module.get_state())))

    assert restored.suppressed_findings == 1
    assert dict(restored.suppressed_by_category) == {"Category A": 1}
    # The tuple key is hashable again and still matches -> stays capped, no duplicate
    assert restored.should_report(("example.com", "CSP", "Missing"), _FindingA) is False
    # A plain string key round-trips as a string, not a tuple
    assert restored.should_report("plain-string-key", _FindingB) is False
    assert restored.suppressed_findings == 3


def test_load_state_tolerates_missing_keys():
    module = PassiveModule()
    module.load_state({})

    assert module.suppressed_findings == 0
    assert not module.suppressed_by_category
    # Empty state behaves like a fresh module: nothing already capped.
    assert module.should_report("fresh") is True
    assert module.should_report("fresh") is False
