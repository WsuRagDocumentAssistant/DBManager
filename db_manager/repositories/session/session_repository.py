"""
SessionRepository

sessions 테이블을 담당하는 Repository.
BaseRepositoryInterface의 5개 추상 메서드(select_one/select_many/insert/update/delete)를
sessions 테이블 기준으로 구현한다. 메시지 관련 작업은 MessageRepository가 담당한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class SessionRepository(BaseDatabaseInterface):
    """
    sessions 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        기존 세션을 이어가거나, 없으면 새로 만든다 (get-or-create).
        타임아웃 로직은 DB 함수에서 제거되어, 더 이상 시간 경과로 새 세션을
        만들지 않는다 (그런 용도는 create_new_session을 사용).

        필수 kwargs: user_id (str)
        반환: {"session_id": ...} 또는 None
        """
        user_id = kwargs["user_id"]
        query = "SELECT get_or_create_session($1::uuid) AS session_id"
        return await self._fetch_one(query, user_id)

    async def create_new(self, **kwargs) -> Optional[dict]:
        """
        "새채팅" 전용 — 시간 상관없이 무조건 새 세션을 생성한다.
        get_or_create_session과 달리 30분 타임아웃 체크를 하지 않는다.

        필수 kwargs: user_id (str)
        반환: {"session_id": ...}
        """
        user_id = kwargs["user_id"]
        query = "SELECT create_new_session($1::uuid) AS session_id"
        return await self._fetch_one(query, user_id)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        특정 사용자의 세션 목록을 최근 활동순으로 반환한다.

        필수 kwargs: user_id (str)
        반환: list[dict], 각 dict 키: session_id, user_id, created_at, updated_at, overall_summary
        """
        user_id = kwargs["user_id"]
        query = """
            SELECT session_id, user_id, title, created_at, updated_at, overall_summary
            FROM sessions
            WHERE user_id = $1::uuid
            ORDER BY updated_at DESC
        """
        return await self._fetch_many(query, user_id)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        타임아웃 판단 없이 무조건 새 세션을 만든다.
        (보통은 select_one의 get-or-create를 쓰고, 이건 강제로 새 세션이 필요할 때만 사용)

        필수 kwargs: user_id (str)
        반환: 새로 생성된 세션 row (dict), 키: session_id, user_id, created_at, updated_at, overall_summary
        """
        user_id = kwargs["user_id"]
        query = """
            INSERT INTO sessions (user_id)
            VALUES ($1)
            RETURNING session_id, user_id, created_at, updated_at, overall_summary
        """
        return await self._fetch_one(query, user_id)

    async def update(self, **kwargs) -> Optional[dict]:
        """
        세션 전체 요약(overall_summary)을 갱신한다.

        필수 kwargs: session_id (str), summary (str)
        반환: 갱신된 세션 row (dict), 키: session_id, user_id, created_at, updated_at, overall_summary
        """
        session_id = kwargs["session_id"]
        summary = kwargs["summary"]
        await self._execute("CALL update_overall_summary($1::uuid, $2::text)", session_id, summary)
        query = """
            SELECT session_id, user_id, created_at, updated_at, overall_summary
            FROM sessions WHERE session_id = $1::uuid
        """
        return await self._fetch_one(query, session_id)

    async def delete(self, **kwargs) -> bool:
        """
        세션을 삭제한다.

        주의: messages.session_id FK에 ON DELETE CASCADE가 설정되어 있지 않음.
              세션에 딸린 메시지가 남아있으면 FK 제약 위반으로 실패한다.

        필수 kwargs: session_id (str)
        반환: 실제로 삭제된 행이 있으면 True
        """
        session_id = kwargs["session_id"]
        result = await self._execute("DELETE FROM sessions WHERE session_id = $1::uuid", session_id)
        affected = int(result.split()[-1]) if result else 0
        return affected > 0

    async def get_context(self, **kwargs) -> Optional[dict]:
        """
        세션의 전체 요약(overall_summary)과 현재 토픽(current_topic)을 한 번에 조회한다.
        LLM 프롬프트 조립 시 "장기 기억"으로 쓰기 위한 조회 전용 메서드다.

        필수 kwargs: session_id (str)
        반환: {"overall_summary": ..., "current_topic": ...} 또는 None
        """
        session_id = kwargs["session_id"]
        query = "SELECT * FROM get_session_context($1::uuid)"
        return await self._fetch_one(query, session_id)

    async def update_topic(self, **kwargs) -> Optional[dict]:
        """
        지금 이 순간 얘기 중인 주제(current_topic)를 갱신한다.
        overall_summary(전체 누적 요약)와는 별개로, 짧은 주제 라벨만 덮어쓴다.
        BaseRepositoryInterface가 요구하는 필수 메서드는 아니고, 필요해서 추가한 메서드다.

        필수 kwargs: session_id (str), topic (str)
        반환: 갱신된 세션 row (dict), 키: session_id, user_id, created_at, updated_at, overall_summary, current_topic
        """
        session_id = kwargs["session_id"]
        topic = kwargs["topic"]
        await self._execute("CALL update_current_topic($1::uuid, $2::text)", session_id, topic)
        query = """
            SELECT session_id, user_id, created_at, updated_at, overall_summary, current_topic
            FROM sessions WHERE session_id = $1::uuid
        """
        return await self._fetch_one(query, session_id)

    async def update_title(self, **kwargs) -> Optional[dict]:
        """
        세션의 제목(title)을 갱신한다. ChatGPT 대화목록 제목처럼 짧은 제목이다.

        필수 kwargs: session_id (str), title (str)
        반환: 갱신된 세션 row (dict)
        """
        session_id = kwargs["session_id"]
        title = kwargs["title"]
        await self._execute("CALL update_session_title($1::uuid, $2::text)", session_id, title)
        query = """
            SELECT session_id, user_id, title, created_at, updated_at, overall_summary, current_topic
            FROM sessions WHERE session_id = $1::uuid
        """
        return await self._fetch_one(query, session_id)
