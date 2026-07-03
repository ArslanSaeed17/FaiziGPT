"""
A minimal in-memory fake that mimics the subset of the supabase-py
query-builder chain actually used by BrallGPT's services:
  table(x).select(...).eq(...).eq(...).order(...).limit(...).execute()
  table(x).insert({...}).execute()
  table(x).update({...}).eq(...).execute()
  table(x).delete().eq(...).execute()

This is NOT a replacement for testing against real Supabase — it exists
purely to validate the backend's own logic (hashing, JWT, auth gating,
ownership checks) in an environment with no network access to Supabase.
"""
import uuid
from datetime import datetime, timezone


class _Result:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class _Query:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self.rows = list(store[table_name])
        self._insert_payload = None
        self._update_payload = None
        self._delete = False
        self._count_mode = None
        self._limit = None
        self._order_field = None
        self._order_desc = False

    def select(self, *_args, count=None):
        self._count_mode = count
        return self

    def eq(self, field, value):
        self.rows = [r for r in self.rows if r.get(field) == value]
        return self

    def order(self, field, desc=False):
        self._order_field = field
        self._order_desc = desc
        return self

    def limit(self, n):
        self._limit = n
        return self

    def insert(self, payload):
        self._insert_payload = payload
        return self

    def update(self, payload):
        self._update_payload = payload
        return self

    def delete(self):
        self._delete = True
        return self

    def execute(self):
        table = self.store[self.table_name]

        if self._insert_payload is not None:
            row = dict(self._insert_payload)
            row.setdefault("id", str(uuid.uuid4()))
            row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            if self.table_name == "chats":
                row.setdefault("updated_at", row["created_at"])
            if self.table_name == "users":
                row.setdefault("is_admin", False)
            table.append(row)
            return _Result([row])

        if self._update_payload is not None:
            updated = []
            for r in table:
                if r in self.rows:
                    r.update(self._update_payload)
                    updated.append(r)
            return _Result(updated)

        if self._delete:
            for r in list(self.rows):
                table.remove(r)
            return _Result(self.rows)

        rows = self.rows
        if self._order_field:
            rows = sorted(rows, key=lambda r: r.get(self._order_field) or "", reverse=self._order_desc)
        if self._limit:
            rows = rows[: self._limit]

        if self._count_mode == "exact":
            return _Result(rows, count=len(rows))
        return _Result(rows)


class FakeSupabase:
    def __init__(self):
        self.store = {
            "users": [],
            "chats": [],
            "messages": [],
            "feedback": [],
            "password_reset_tokens": [],
            "subscriptions": [],
            "ai_tools": [],
        }

    def table(self, name):
        return _Query(self.store, name)
