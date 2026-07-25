import types
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from pathlib import Path

import pytest

from wapitiCore.attack.passive_scanner import PassiveScanner
from wapitiCore.net.sql_persister import SqlPersister

# pylint: disable=redefined-outer-name,protected-access


@pytest.fixture
def mock_persister():
    return MagicMock(spec=SqlPersister)


@patch("pathlib.Path.glob", return_value=[Path("mod_broken.py")])
@patch("wapitiCore.main.log.logging.error")
def test_import_error_is_handled(mock_log_error, _, mock_persister):
    """Test that a module raising ImportError is skipped and the error is logged."""
    scanner = PassiveScanner(persister=mock_persister)

    assert len(scanner._modules) == 0
    mock_log_error.assert_called_with(
        "[!] Unable to import module %s: %s", "mod_broken", ANY
    )


@patch("pathlib.Path.glob", return_value=[])
@patch("wapitiCore.attack.passive_scanner.log_blue")
def test_log_summary_reports_only_modules_with_suppressed_findings(mock_log_blue, _, mock_persister):
    """Only modules that actually suppressed alerts are logged."""
    scanner = PassiveScanner(persister=mock_persister)

    noisy = MagicMock()
    noisy.suppressed_findings = 3
    silent = MagicMock()
    silent.suppressed_findings = 0
    scanner._modules = {"noisy": noisy, "silent": silent}

    scanner.log_summary()

    # A header plus exactly one detail line for the only noisy module.
    mock_log_blue.assert_any_call(
        "    {0}: {1} similar alert(s) suppressed", "noisy", 3
    )
    detail_calls = [
        call for call in mock_log_blue.call_args_list
        if call.args and call.args[0].startswith("    {0}")
    ]
    assert len(detail_calls) == 1


@patch("pathlib.Path.glob", return_value=[])
@patch("wapitiCore.attack.passive_scanner.log_blue")
def test_log_summary_stays_silent_when_nothing_suppressed(mock_log_blue, _, mock_persister):
    """No output at all (not even a header) when no alert was suppressed."""
    scanner = PassiveScanner(persister=mock_persister)

    silent = MagicMock()
    silent.suppressed_findings = 0
    scanner._modules = {"silent": silent}

    scanner.log_summary()

    mock_log_blue.assert_not_called()


@patch("pathlib.Path.glob", return_value=[])
def test_get_state_snapshots_every_module(_, mock_persister):
    scanner = PassiveScanner(persister=mock_persister)

    first = MagicMock()
    first.get_state.return_value = {"occurrences": {"a": 1}}
    second = MagicMock()
    second.get_state.return_value = {"occurrences": {}}
    scanner._modules = {"csp": first, "https_redirect": second}

    assert scanner.get_state() == {
        "csp": {"occurrences": {"a": 1}},
        "https_redirect": {"occurrences": {}},
    }


@patch("pathlib.Path.glob", return_value=[])
def test_load_state_dispatches_and_ignores_unknown_modules(_, mock_persister):
    scanner = PassiveScanner(persister=mock_persister)

    csp = MagicMock()
    scanner._modules = {"csp": csp}

    scanner.load_state({"csp": {"occurrences": {"a": 1}}, "gone": {"occurrences": {}}})

    csp.load_state.assert_called_once_with({"occurrences": {"a": 1}})


@pytest.mark.asyncio
@patch("pathlib.Path.glob", return_value=[])
async def test_persist_state_writes_full_snapshot_unconditionally(_, mock_persister):
    mock_persister.set_passive_scanner_state = AsyncMock()
    scanner = PassiveScanner(persister=mock_persister)

    module = MagicMock()
    module.get_state.return_value = {"occurrences": {"a": 1}, "suppressed_findings": 0}
    scanner._modules = {"csp": module}

    await scanner.persist_state()

    mock_persister.set_passive_scanner_state.assert_awaited_once_with(
        {"csp": {"occurrences": {"a": 1}, "suppressed_findings": 0}}
    )


@pytest.mark.asyncio
@patch("pathlib.Path.glob", return_value=[])
async def test_restore_state_loads_stored_snapshot(_, mock_persister):
    mock_persister.get_passive_scanner_state = AsyncMock(
        return_value={"csp": {"occurrences": {"a": 1}}}
    )
    scanner = PassiveScanner(persister=mock_persister)

    module = MagicMock()
    scanner._modules = {"csp": module}

    await scanner.restore_state()

    module.load_state.assert_called_once_with({"occurrences": {"a": 1}})


@pytest.mark.asyncio
@patch("pathlib.Path.glob", return_value=[])
async def test_restore_state_is_a_noop_without_stored_state(_, mock_persister):
    mock_persister.get_passive_scanner_state = AsyncMock(return_value={})
    scanner = PassiveScanner(persister=mock_persister)

    module = MagicMock()
    scanner._modules = {"csp": module}

    await scanner.restore_state()

    module.load_state.assert_not_called()


@patch("pathlib.Path.glob", return_value=[Path("mod_broken.py")])
@patch("wapitiCore.attack.passive_scanner.import_module")
@patch("wapitiCore.main.log.logging.error")
@patch("wapitiCore.main.log.logging.exception")
def test_broken_module_is_skipped(
    mock_log_exc, mock_log_err, mock_import_module, _, mock_persister
):
    """Test that a module raising an unexpected error during instantiation is skipped."""
    fake_module = types.SimpleNamespace()

    def broken_getattr(name):
        raise AttributeError("Simulated broken module")

    fake_module.__getattribute__ = broken_getattr
    mock_import_module.return_value = fake_module

    scanner = PassiveScanner(persister=mock_persister)

    # No modules should be loaded
    assert not scanner._modules

    # Logs should have been called
    mock_log_err.assert_not_called()
    mock_log_exc.assert_called_with(
        "[!] Module %s seems broken and will be skipped", "mod_broken"
    )
