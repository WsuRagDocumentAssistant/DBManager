"""
db_manager.py
==============

DB 매니저. 내부적으로는 비동기(async) Repository 메서드들을 쓰지만,
밖에서 호출하는 쪽은 await 없이 동기 함수처럼 쓸 수 있다.

이벤트 루프 하나를 인스턴스 생성 시 만들어서 계속 재사용한다
(asyncio.run()을 매번 쓰면 DB 커넥션 풀이 "다른 루프에 묶였다"는
에러가 나므로, 반드시 같은 루프를 계속 써야 한다).
"""

import asyncio

from ai_rag_comm import Controller, load_config, setup_logging
from .repositories import ApiDataRepository, MessageRepository, SessionRepository, WordDictionaryRepository


class DBManager:
    """
    DB 작업을 처리하는 매니저. 동기 인터페이스로 쓸 수 있다.

    사용법:
        manager = DBManager()
        manager.init()
        result = manager.call("get_or_create_session", user_id=...)
        manager.close()
    """

    def __init__(self):
        self._controller = None
        self._handlers = None
        self._loop = asyncio.new_event_loop()  # 인스턴스 생성 시 딱 한 번만 만듦

    def init(self) -> None:
        """DB 연결을 준비하고 handlers를 구성한다 (동기 호출)."""
        self._loop.run_until_complete(self._async_init())

    async def _async_init(self) -> None:
        config = load_config()
        setup_logging(config.server.log_level)

        self._controller = Controller(config=config)
        await self._controller.init()
        db = self._controller.get_services()["db"]

        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        api_data_repo = ApiDataRepository(db)
        word_dict_repo = WordDictionaryRepository(db)

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
            "search_word": word_dict_repo.select_one,
            "list_all_words": word_dict_repo.select_many,
            "insert_word": word_dict_repo.insert,
        }

    def call(self, task_name: str, **kwargs):
        """
        task_name에 해당하는 Repository 메서드를 실행한다 (동기 호출).
        내부적으로는 같은 이벤트 루프를 재사용해서 비동기 메서드를 실행한다.
        """
        if self._handlers is None:
            raise RuntimeError("DBManager.init()을 먼저 호출해야 합니다.")

        handler = self._handlers.get(task_name)
        if handler is None:
            raise ValueError(f"알 수 없는 task: {task_name}")

        return self._loop.run_until_complete(handler(**kwargs))

    def close(self) -> None:
        """DB 연결을 정리한다 (동기 호출)."""
        if self._controller is not None:
            self._loop.run_until_complete(self._controller.close())
        self._loop.close()
