"""
MessageRepository

messages 테이블을 담당하는 Repository.
BaseRepositoryInterface의 5개 추상 메서드를 messages 테이블 기준으로 구현한다.
세션(sessions) 관련 작업은 SessionRepository가 담당한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class MessageRepository(BaseDatabaseInterface):
    """
    messages 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        메시지를 저장하고 순번(turn_index)을 자동 채번한다.

        필수 kwargs: session_id (str), user_query (str), ai_response (str)
        반환: {"out_message_id": ..., "out_turn_index": ...} 또는 None
        """
        session_id = kwargs["session_id"]
        user_query = kwargs["user_query"]
        ai_response = kwargs["ai_response"]
        query = "SELECT * FROM insert_message($1::uuid, $2::text, $3::text)"
        return await self._fetch_one(query, session_id, user_query, ai_response)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        세션 내 최근 N개 대화를, 오래된 순으로 정렬해서 반환한다.

        필수 kwargs: session_id (str)
        선택 kwargs: limit_count (int, 기본 5)
        반환: list[dict]
        """
        session_id = kwargs["session_id"]
        limit_count = kwargs.get("limit_count", 5)
        query = "SELECT * FROM get_recent_messages($1::uuid, $2::integer)"
        return await self._fetch_many(query, session_id, limit_count)

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        메시지 하나를 message_id로 단건 조회한다.

        필수 kwargs: message_id (str)
        반환: dict 또는 None
        """
        message_id = kwargs["message_id"]
        query = "SELECT * FROM messages WHERE message_id = $1::uuid"
        return await self._fetch_one(query, message_id)

    async def update(self, **kwargs) -> Optional[dict]:
        """
        messages는 append-only 로그로 설계되어 수정 기능을 제공하지 않는다.
        """
        raise NotImplementedError("messages는 append-only로 설계되어 수정 기능을 제공하지 않음")

    async def delete(self, **kwargs) -> bool:
        """
        현재 요구사항에는 메시지 삭제 기능이 정의되어 있지 않다.
        """
        raise NotImplementedError("현재 요구사항에는 메시지 삭제 기능이 없음")
