"""5.3：SQLite 长期记忆，默认内存演示；显式子命令才持久写入。"""
import argparse
import json
import sqlite3
import time
from lab.config import RUNTIME, cli


def connect(path=":memory:"):
    db = sqlite3.connect(path)
    db.execute("""CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY, content TEXT NOT NULL, kind TEXT NOT NULL,
        source TEXT NOT NULL, confidence REAL NOT NULL,
        created_at REAL NOT NULL, expires_at REAL NOT NULL)""")
    return db


def put(db, key, content, ttl_days=30, confirmed=False):
    if not confirmed:
        raise ValueError("仅保存用户确认的偏好；请添加 --confirmed。")
    if not key.strip() or not content.strip() or len(content) > 1000 or not 1 <= ttl_days <= 365:
        raise ValueError("id/内容不能为空，内容最多 1000 字，ttl-days 为 1–365。")
    now = time.time()
    with db:
        db.execute("INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (key, content, "preference", "user_confirmed", 1.0, now, now + ttl_days * 86400))


def recall(db, now=None):
    now = time.time() if now is None else now
    rows = db.execute("SELECT id, content FROM memories WHERE expires_at > ? ORDER BY created_at DESC", (now,)).fetchall()
    return [{"id": key, "content": content} for key, content in rows]


def forget(db, key):
    with db:
        return db.execute("DELETE FROM memories WHERE id = ?", (key,)).rowcount


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="demo", choices=["demo", "set", "list", "delete"])
    parser.add_argument("--id", default="writing-language")
    parser.add_argument("--content", default="回答用中文，代码注释用英文")
    parser.add_argument("--ttl-days", type=int, default=30)
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args()
    if args.action == "demo":
        db = connect()
        try:
            put(db, args.id, args.content, confirmed=True)
            print("写入后：" + json.dumps(recall(db), ensure_ascii=False))
            print("31 天后可读取：" + str(len(recall(db, time.time() + 31 * 86400))))
            print("删除条数：" + str(forget(db, args.id)))
            print("删除后：" + json.dumps(recall(db), ensure_ascii=False))
        finally:
            db.close()
        return
    RUNTIME.mkdir(exist_ok=True)
    db = connect(RUNTIME / "memory.sqlite3")
    try:
        if args.action == "set":
            put(db, args.id, args.content, args.ttl_days, args.confirmed)
            print("已保存；同 id 的新偏好会覆盖旧值。")
        elif args.action == "delete":
            print("删除条数：" + str(forget(db, args.id)))
        else:
            print(json.dumps(recall(db), ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    cli(main)
