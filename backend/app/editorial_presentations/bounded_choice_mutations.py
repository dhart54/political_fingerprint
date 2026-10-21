"""Check this transaction's DML, including trigger effects, across user tables."""

from .bounded_choice_review import require


def transaction_counts(conn):
    return {
        (row["schemaname"], row["relname"]): tuple(
            row[field] for field in ("n_tup_ins", "n_tup_upd", "n_tup_del")
        )
        for row in conn.execute(
            "SELECT schemaname,relname,n_tup_ins,n_tup_upd,n_tup_del "
            "FROM pg_stat_xact_user_tables"
        ).fetchall()
    }


def require_transaction_delta(conn, before, expected):
    # Deferred constraint triggers must run before measuring, not after commit.
    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
    after = transaction_counts(conn)
    changes = {}
    for key in before.keys() | after.keys():
        delta = tuple(
            a - b for a, b in zip(after.get(key, (0, 0, 0)), before.get(key, (0, 0, 0)))
        )
        if delta != (0, 0, 0):
            changes[key] = delta
    require(
        changes == {("public", table): counts for table, counts in expected.items()},
        "transaction mutations exceed exact bounded caps",
    )
