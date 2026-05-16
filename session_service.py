from uuid import uuid4


def create_session_id() -> str:
    return str(uuid4())