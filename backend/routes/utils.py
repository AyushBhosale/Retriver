from database import db_dependency
from models import Conversation, message
def add_conversations(db, userId:int,filename, title):
    data = {}
    data['user_id'] = userId
    data['file_name'] = filename
    data['title'] = title
    data=Conversation(**data)
    db.add(data)
    db.commit()
    db.refresh(data)
    return data.id

def add_chat(db,conversation_id,content,sender):
    data = {}
    data['conversation_id'] = conversation_id
    data['content'] = content
    data['sender'] = sender
    data=message(**data)
    db.add(data)
    db.commit()
    db.refresh(data)