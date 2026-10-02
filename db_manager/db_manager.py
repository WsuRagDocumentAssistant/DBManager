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
import sys

from ai_rag_comm import Controller, OracleDatabaseService, load_config, setup_logging
from .repositories import ApiDataRepository, MessageRepository, SessionRepository, WordDictionaryRepository
from .repositories import (
    DocumentRepository,
    DocumentImageRepository,
    WorkCategoryOptionRepository,
    TaskNameOptionRepository,
    DepartmentOptionRepository,
    ReportTypeOptionRepository,
    DocumentCategoryRepository,
)
from .repositories import UserRepository, PermissionRepository
from .repositories import VocabRepository
from .repositories import FeatureRequestRepository
from .repositories import SchoolUserRepository, SchoolViewRepository
from .repositories import NotificationRepository


class _SchoolSync:
    """학교 뷰 전체를 읽어 PostgreSQL 사본에 맞추는 작업. 반영한 행 수를 돌려준다.

    학교 DB 연결이 없으면 부를 때마다 다시 붙어 본다. 기동할 때 학교 DB가 잠깐 안 됐다고
    서버를 재시작할 때까지 동기화가 멈추면 안 된다. 읽다가 실패하면 연결을 버리고 다음에 새로 붙는다.

    실패는 이유를 담은 RuntimeError 로 올린다 — 설정이 꺼졌는지, 접속 정보가 빠졌는지,
    접속이 거절됐는지를 관리자 화면과 로그에서 바로 알 수 있게.
    """

    def __init__(self, oracle_config, school_db, user_repo: SchoolUserRepository):
        self._config = oracle_config
        self._school_db = school_db
        self._user_repo = user_repo

    async def __call__(self, **kwargs) -> int:
        if self._school_db is None:
            self._school_db = await self._connect()
        try:
            rows = await SchoolViewRepository(self._school_db).select_many()
        except Exception as e:
            await self.close()
            raise RuntimeError(f"학교 DB 조회 실패: {type(e).__name__}: {e}") from e
        return await self._user_repo.insert(rows=rows)

    async def _connect(self) -> OracleDatabaseService:
        c = self._config
        if not c.enabled:
            raise RuntimeError("학교 DB 동기화가 꺼져 있습니다 (SCHOOL_SYNC_ENABLED 가 true 가 아님)")
        missing = [name for name, value in (("SCHOOL_ORACLE_HOST", c.host),
                                            ("SCHOOL_ORACLE_SERVICE_NAME", c.service_name),
                                            ("SCHOOL_ORACLE_USER", c.user),
                                            ("SCHOOL_ORACLE_PASSWORD", c.password)) if not value]
        if missing:
            raise RuntimeError(f"학교 DB 접속 정보가 비어 있습니다: {', '.join(missing)}")

        # oracledb 가 없으면 생성자가 RuntimeError(설치 안내)를 그대로 올린다.
        school_db = OracleDatabaseService(
            host=c.host, port=c.port, service_name=c.service_name, user=c.user, password=c.password,
            owner=c.owner or None, min_size=c.pool_min, max_size=c.pool_max,
        )
        try:
            await school_db.init()
        except Exception as e:
            raise RuntimeError(f"학교 DB 접속 실패 ({c.host}:{c.port}/{c.service_name}): "
                               f"{type(e).__name__}: {e}") from e
        return school_db

    async def close(self) -> None:
        if self._school_db is not None:
            try:
                await self._school_db.close()
            except Exception:
                pass
            self._school_db = None


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
        self._school_sync = None
        # 인스턴스 생성 시 딱 한 번만 만듦. Windows 기본(Proactor) 루프에서는 학교 Oracle
        # 드라이버(python-oracledb async)가 접속 중 멈춰서 Selector 루프를 쓴다 (asyncpg도 동작함).
        self._loop = asyncio.SelectorEventLoop() if sys.platform == "win32" else asyncio.new_event_loop()

    def init(self) -> None:
        """DB 연결을 준비하고 handlers를 구성한다 (동기 호출)."""
        self._loop.run_until_complete(self._async_init())

    async def _async_init(self) -> None:
        config = load_config()
        setup_logging(config.server.log_level)

        self._controller = Controller(config=config)
        await self._controller.init()
        services = self._controller.get_services()
        db = services["db"]
        # 학교 DB는 SCHOOL_SYNC_ENABLED=false 거나 접속에 실패하면 None 이다. 그때는 동기화만
        # 이유를 밝히며 실패하고(다음 동기화 때 다시 붙어 본다), 조회는 마지막으로 동기화한
        # 사본(PostgreSQL)으로 계속한다.
        school_user_repo = SchoolUserRepository(db)
        self._school_sync = _SchoolSync(config.school_oracle, services["school_db"], school_user_repo)

        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        api_data_repo = ApiDataRepository(db)
        word_dict_repo = WordDictionaryRepository(db)
        document_repo = DocumentRepository(db)
        document_image_repo = DocumentImageRepository(db)
        work_category_option_repo = WorkCategoryOptionRepository(db)
        task_name_option_repo = TaskNameOptionRepository(db)
        department_option_repo = DepartmentOptionRepository(db)
        report_type_option_repo = ReportTypeOptionRepository(db)
        document_category_repo = DocumentCategoryRepository(db)
        user_repo = UserRepository(db)
        permission_repo = PermissionRepository(db)
        notification_repo = NotificationRepository(db)
        vocab_repo = VocabRepository(db)
        feature_request_repo = FeatureRequestRepository(db)

        self._handlers = {
            "get_or_create_session": session_repo.select_one,
            "create_new_session": session_repo.create_new,
            "list_sessions": session_repo.select_many,
            "update_overall_summary": session_repo.update,
            "insert_message": message_repo.insert,
            "get_recent_messages": message_repo.select_many,
            "get_session_context": session_repo.get_context,
            "update_current_topic": session_repo.update_topic,
            "insert_api_data": api_data_repo.insert,
            "select_all_api_data": api_data_repo.select_many,
            "update_api_data_date": api_data_repo.update,
            "update_api_data_meta": api_data_repo.update_meta,
            "delete_api_data" : api_data_repo.delete,
            "save_api_data_vector": api_data_repo.save_vector,
            "search_api_data_vector": api_data_repo.search_vector,
            "search_word": word_dict_repo.select_one,
            "list_all_words": word_dict_repo.select_many,
            "insert_word": word_dict_repo.insert,
            "update_word": word_dict_repo.update,
            "register_document": document_repo.insert,
            "get_document": document_repo.select_one,
            "list_documents": document_repo.select_many,
            "search_documents_by_filename": document_repo.search_by_filename,
            "update_document": document_repo.update,
            "delete_document": document_repo.delete,
            "create_document_image": document_image_repo.insert,
            "search_document_images": document_image_repo.search_by_title,
            "get_document_image": document_image_repo.select_one,
            "list_document_images": document_image_repo.select_many,
            "update_document_image": document_image_repo.update,
            "save_document_image_vector": document_image_repo.save_vector,
            "search_document_image_vector": document_image_repo.search_vector,
            "get_work_category_options": work_category_option_repo.select_many,
            "get_task_name_options": task_name_option_repo.select_many,
            "get_department_options": department_option_repo.select_many,
            "get_report_type_options": report_type_option_repo.select_many,
            "list_document_categories": document_category_repo.select_many,
            "save_document_category": document_category_repo.insert,
            "delete_document_category": document_category_repo.delete,
            "update_session_title": session_repo.update_title,
            "login": user_repo.select_one,
            "create_user_account": user_repo.insert,
            "update_user_role": user_repo.update_role,
            "list_users": user_repo.select_many,
            "list_user_permissions": permission_repo.select_many,
            "set_user_permission": permission_repo.update,
            "index_document": document_repo.index_document,
            "create_pending_document": document_repo.create_pending,
            "set_document_status": document_repo.set_status,
            "search_documents_vector": document_repo.search_vector,
            "search_documents_lexical": document_repo.search_lexical,
            "search_documents_hybrid": document_repo.search_hybrid,
            "count_documents": document_repo.count_index_stats,
            "load_vocab": vocab_repo.select_many,
            "save_vocab_pairs": vocab_repo.insert,
            "delete_session": session_repo.delete,
            "list_feature_requests": feature_request_repo.select_many,
            "get_feature_request": feature_request_repo.select_one,
            "insert_feature_request": feature_request_repo.insert,
            "update_feature_request": feature_request_repo.update,
            "delete_feature_request": feature_request_repo.delete,
            "answer_feature_request": feature_request_repo.update_answer,
            "search_school_users": school_user_repo.select_many,
            "get_school_users": school_user_repo.select_by_ids,
            "school_users_status": school_user_repo.status,
            "insert_notification": notification_repo.insert,
            "list_notifications": notification_repo.select_many,
            "mark_notifications_read": notification_repo.update,
            "prune_notifications": notification_repo.delete,
            "sync_school_users": self._school_sync,
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
        if self._school_sync is not None:
            # 기동 뒤에 다시 붙은 학교 DB 연결은 컨트롤러가 모른다. 컨트롤러가 이미 닫은 것이면 그냥 넘어간다.
            self._loop.run_until_complete(self._school_sync.close())
        self._loop.close()
