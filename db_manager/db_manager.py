"""
db_manager.py
==============

TaskController와 동일한 패턴(Process + task_queue + result_queue)을 따르는 DB 매니저.

Control Manager가 task_queue에 (task_name, args) 형태로 작업을 넣으면,
이 프로세스가 그걸 받아서 알맞은 Repository 메서드를 호출하고,
결과를 result_queue에 담아 돌려준다.
"""

import asyncio
from multiprocessing import Process, Queue

from ai_rag_comm import Controller, load_config, setup_logging
from .repositories import ApiDataRepository, CredentialRepository, MessageRepository, SessionRepository


class DBManager(Process):
    """
    별도 프로세스로 동작하는 DB 매니저.
    TaskController와 동일하게 Process를 상속하고, task_queue/result_queue로 통신한다.
    """

    def __init__(self, result_queue: Queue = None):
        super().__init__()
        self.task_queue = Queue()
        self.result_queue = result_queue

    def run(self) -> None:
        asyncio.run(self._main())

    async def _main(self) -> None:
        config = load_config()
        setup_logging(config.server.log_level)

        controller = Controller(config=config)
        await controller.init()
        db = controller.get_services()["db"]

        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        credential_repo = CredentialRepository(db)
        api_data_repo = ApiDataRepository(db)

        handlers = {
            "get_or_create_session": session_repo.select_one,
            "list_sessions": session_repo.select_many,
            "update_overall_summary": session_repo.update,
            "insert_message": message_repo.insert,
            "get_recent_messages": message_repo.select_many,
            "get_session_context": session_repo.get_context,
            "update_current_topic": session_repo.update_topic,
            "get_credential": credential_repo.select_one,
            "list_api_credentials": credential_repo.select_many,
            "insert_api_credential": credential_repo.insert,
            "delete_api_credential": credential_repo.delete,
            "get_api_data": api_data_repo.select_one,
            "list_api_data": api_data_repo.select_many,
            "insert_api_data": api_data_repo.insert,
            "delete_api_data": api_data_repo.delete,
        }

        loop = asyncio.get_event_loop()

        try:
            while True:
                task_name, args = await loop.run_in_executor(None, self.task_queue.get)

                handler = handlers.get(task_name)
                if handler is None:
                    self.result_queue.put({"ok": False, "error": f"알 수 없는 task: {task_name}"})
                    continue

                try:
                    result = await handler(**args)
                    self.result_queue.put({"ok": True, "result": result})
                except Exception as e:
                    self.result_queue.put({"ok": False, "error": str(e)})
        finally:
            await controller.close()
