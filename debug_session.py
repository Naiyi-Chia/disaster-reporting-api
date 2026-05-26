from services.session_service import _parse_text_entities, _determine_source, _collect_missing_fields
from models.session import SessionORM
import json
from datetime import datetime

content = '我這邊淹水了，好像需要水跟食物'
entities = _parse_text_entities(content)
print('entities', entities)
source_type, source_context = _determine_source(content, None)
print('source', source_type, source_context)
session = SessionORM(
    session_id='test',
    platform='LINE',
    sender_id='U200',
    group_id=None,
    source_type=source_type,
    source_context=source_context,
    current_state='RECEIVED',
    raw_events=json.dumps([{'content': content, 'timestamp': datetime.utcnow().isoformat()}]),
    normalized_messages=json.dumps([{'content': content, 'timestamp': datetime.utcnow().isoformat(), 'message_type': 'text'}]),
    extracted_entities=json.dumps(entities),
    updated_at=datetime.utcnow(),
)
print('missing', _collect_missing_fields(session))
