"""Owned loopback-only PostgreSQL for the isolated read-scope experiment.

Never accepts a DSN or reads application credentials. Clusters are retained for
the shutdown checkpoint; only the exact cluster started here is stopped here.
"""
import os
from pathlib import Path
import socket
import subprocess
import uuid


class DisposablePostgres:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.directory = self.root / ('pg-' + uuid.uuid4().hex)
        self.bin = Path('C:/Program Files/PostgreSQL/17/bin')
        self.started = False
        self.port = None

    def command(self, name, *args):
        # Windows postgres children can retain PIPE handles after pg_ctl exits.
        # A regular file keeps subprocess.wait bounded without reader threads.
        log_path = self.root / f'{self.directory.name}-{name}-command.log'
        with log_path.open('a', encoding='utf-8') as log:
            result = subprocess.run(
                [str(self.bin / (name + '.exe')), *map(str, args)],
                stdout=log, stderr=subprocess.STDOUT, timeout=35,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                env={k: v for k, v in os.environ.items() if not k.upper().startswith('PG') and k.upper() != 'DATABASE_URL'},
            )
        if result.returncode:
            raise RuntimeError(f'{name} failed: {log_path.read_text()[-2000:]}')

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.directory.mkdir()
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            self.port = reserved.getsockname()[1]
        try:
            self.command('initdb', '-D', self.directory, '-U', 'experiment', '-A', 'trust', '--no-locale', '--encoding=UTF8')
            self.started = True  # Also stop a server that starts but misses -w.
            self.command('pg_ctl', '-D', self.directory, '-l', self.directory / 'server.log', '-o', f'-h 127.0.0.1 -p {self.port}', '-w', '-t', '20', 'start')
            with self.connect() as connection:
                actual = Path(connection.execute("SELECT current_setting('data_directory')").fetchone()[0]).resolve()
                if actual != self.directory:
                    raise RuntimeError('Disposable PostgreSQL ownership mismatch')
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def connect(self):
        import psycopg
        if any(key.upper().startswith('PG') for key in os.environ):
            raise RuntimeError('Inherited libpq configuration is forbidden for this disposable harness')
        # Explicit loopback, port, user, database and empty password; no DSN input.
        if not self.started or self.port is None or self.directory.parent != self.root:
            raise RuntimeError('Disposable PostgreSQL is not owned and active')
        return psycopg.connect(host='127.0.0.1', hostaddr='127.0.0.1', port=self.port,
                               dbname='postgres', user='experiment', password='',
                               passfile=str(self.directory / 'no-password-file'),
                               sslmode='disable', gssencmode='disable',
                               connect_timeout=3)

    def __exit__(self, *args):
        if self.started:
            if (self.directory / 'postmaster.pid').exists():
                self.command('pg_ctl', '-D', self.directory, '-m', 'fast', '-w', '-t', '20', 'stop')
            self.started = False
