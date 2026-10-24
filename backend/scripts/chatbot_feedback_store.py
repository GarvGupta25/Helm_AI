"""Inspect or export the separate chatbot feedback store as a local operator."""
import argparse
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[2]
key = root/'.runtime'/'research-test.key'
if key.exists() and not os.getenv('RESEARCH_STATE_KEY'):
    os.environ['RESEARCH_STATE_KEY'] = key.read_text().strip()

from sqlalchemy import func, select  # noqa: E402

from app.chatbot_feedback import ChatFeedback, feedback_db, purge_feedback  # noqa: E402

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, help='Write decrypted submitted feedback to a new private local JSON file')
    parser.add_argument('--purge-expired', action='store_true')
    args = parser.parse_args()
    store = feedback_db()
    db = next(store)
    try:
        if args.purge_expired:
            count = purge_feedback(db)
            db.commit()
            print(json.dumps({'expired_feedback_deleted': count}))
        if args.export:
            rows = db.scalars(select(ChatFeedback).order_by(ChatFeedback.created_at.desc()).limit(5000)).all()
            with args.export.open('x', encoding='utf-8') as output:
                json.dump([{'reference': row.id, 'kind': row.kind, 'rating': row.rating, 'category': row.category, 'status': row.status, 'created_at': row.created_at.isoformat(), **row.data} for row in rows], output, indent=2)
            print(json.dumps({'exported': len(rows)}))
        else:
            groups = db.execute(select(ChatFeedback.kind, ChatFeedback.rating, ChatFeedback.category, func.count()).group_by(ChatFeedback.kind, ChatFeedback.rating, ChatFeedback.category)).all()
            print(json.dumps({'summary': [{'kind': k, 'rating': r, 'category': c, 'count': n} for k, r, c, n in groups]}))
    finally:
        store.close()
