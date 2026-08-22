"""
db_manager.py
==============

프로세스/큐 없이, 그냥 파이썬 모듈(클래스)로 동작하는 DB 매니저.
호출하는 쪽(Control Manager)이 같은 이벤트 루프 안에서 직접 await로 호출한다.
"""

from ai_rag_comm import Controller, load_config, setup_logging
from .repositories import ApiDataRepository, MessageRepository, SessionRepository


class DBManager:
    """
    DB 작업을 처리하는 매니저. 더 이상 별도 프로세스가 아니라 평범한 클래스다.

    사용법:
        manager = DBManager()
        await manager.init()
        result = await manager.call("get_or_create_session", user_id=...)
        await manager.close()
    """

    def __init__(self):
        self._controller = None
        self._handlers = None

    async def init(self) -> None:
        """
        DB 연결을 준비하고, task_name → Repository 메서드 매핑(handlers)을 구성한다.
        `call()`을 쓰기 전에 반드시 한 번 호출해야 한다.
        """
        config = load_config()
        setup_logging(config.server.log_level)

        self._controller = Controller(config=config)
        await self._controller.init()
        db = self._controller.get_services()["db"]

        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        api_data_repo = ApiDataRepository(db)

        self._handlers = {
            "get_or_create_session": session_repo.select_one,
            "list_sessions": session_repo.select_many,
            "update_overall_summary": session_repo.update,
            "insert_message": message_repo.insert,
            "get_recent_messages": message_repo.select_many,
            "get_session_context": session_repo.get_context,
            "update_current_topic": session_repo.update_topic,
            "get_api_data": api_data_repo.select_one,
            "list_api_data": api_data_repo.select_many,
            "insert_api_data": api_data_repo.insert,
            "delete_api_data": api_data_repo.delete,
        }

    async def call(self, task_name: str, **kwargs):
        """
        task_name에 해당하는 Repository 메서드를 직접 호출한다.
        큐 왕복 없이 await 하나로 끝난다.

        필수: init()을 먼저 호출해야 한다 (안 하면 RuntimeError).
        task_name이 handlers에 없으면 ValueError를 낸다.
        나머지 kwargs는 그대로 해당 Repository 메서드에 전달되며,
        Repository 쪽에서 발생한 예외는 감싸지 않고 그대로 전파된다.
        """
        if self._handlers is None:
            raise RuntimeError("DBManager.init()을 먼저 호출해야 합니다.")

        handler = self._handlers.get(task_name)
        if handler is None:
            raise ValueError(f"알 수 없는 task: {task_name}")

        return await handler(**kwargs)

    async def close(self) -> None:
        """
        DB 연결(Controller)을 정리한다. 사용이 끝나면 호출한다.
        init()이 호출된 적 없으면(=아직 연결이 없으면) 아무 일도 하지 않는다.
        """
        if self._controller is not None:
            await self._controller.close()
