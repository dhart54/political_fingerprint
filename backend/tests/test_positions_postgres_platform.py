"""Offline platform-boundary checks, separate from the 146-case readiness gate."""
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from backend.tests import positions_disposable_postgres as fixture


@pytest.mark.parametrize('platform,bin_path,suffix,socket_options', [
    ('win32', 'C:/Program Files/PostgreSQL/17/bin', '.exe', ''),
    ('linux', '/usr/lib/postgresql/16/bin', '', ' -c unix_socket_directories='),
])
def test_fixed_platform_program_and_sanitized_child_environment(monkeypatch, platform, bin_path, suffix, socket_options):
    monkeypatch.setattr(fixture.sys, 'platform', platform)
    server = fixture.DisposablePostgres(Path(__file__).resolve().parents[2] / '.tmp/positions-reuse/platform-mock')
    assert server.bin == Path(bin_path)
    assert server.socket_options == socket_options
    monkeypatch.setenv('PGHOSTADDR', '192.0.2.1')
    monkeypatch.setenv('DATABASE_URL', 'forbidden-fixture-input')
    run = Mock(return_value=Mock(returncode=0))
    with patch.object(Path, 'open', mock_open()), patch.object(fixture.subprocess, 'run', run):
        server.command('initdb', '-D', server.directory)
    command = run.call_args.args[0]
    assert command == [str(Path(bin_path) / ('initdb' + suffix)), '-D', str(server.directory)]
    assert not any(k.upper().startswith('PG') or k.upper() == 'DATABASE_URL'
                   for k in run.call_args.kwargs['env'])
    assert run.call_args.kwargs['timeout'] == 35


def test_unknown_platform_refused_before_any_command(monkeypatch):
    monkeypatch.setattr(fixture.sys, 'platform', 'unsupported')
    with patch.object(fixture.subprocess, 'run') as run:
        with pytest.raises(RuntimeError, match='Unsupported'):
            fixture.DisposablePostgres(Path('.tmp/positions-reuse/platform-mock'))
        run.assert_not_called()
