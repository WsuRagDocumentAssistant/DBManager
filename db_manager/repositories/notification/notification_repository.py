"""
NotificationRepository

notifications 테이블(sql/notifications.sql)을 담당하는 Repository. 사용자 알림(상단 종 아이콘).
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class NotificationRepository(BaseDatabaseInterface):

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        알림을 만든다.

        필수 kwargs: user_id (str), message (str)
        선택 kwargs: type (str: success/error/info, 기본 info), link (str)
        반환: 만든 행 (dict)
        """
        query = "SELECT * FROM insert_notification($1::uuid, $2::text, $3::text, $4::text)"
        return await self._fetch_one(query, kwargs["user_id"], kwargs["message"],
                                     kwargs.get("type"), kwargs.get("link"))

    async def select_many(self, **kwargs) -> list[dict]:
        """
        내 알림 최신순.

        필수 kwargs: user_id (str) / 선택 kwargs: limit (int, 기본 50)
        반환: list[dict], 키: id, user_id, message, type, link, created_at, read_at
        """
        query = "SELECT * FROM list_notifications($1::uuid, $2::int)"
        return await self._fetch_many(query, kwargs["user_id"], kwargs.get("limit", 50))

    async def update(self, **kwargs) -> int:
        """
        읽음 처리. ids 를 안 주면 내 알림 전부.

        필수 kwargs: user_id (str) / 선택 kwargs: ids (list[int])
        반환: 읽음으로 바꾼 개수
        """
        ids = kwargs.get("ids")
        query = "SELECT mark_notifications_read($1::uuid, $2::bigint[])"
        return await self._fetch_val(query, kwargs["user_id"], list(ids) if ids is not None else None)

    async def delete(self, **kwargs) -> int:
        """
        오래된 알림 정리. 사용자마다 최신 keep 개만 남긴다.

        선택 kwargs: keep (int, 기본 200)
        반환: 지운 개수
        """
        return await self._fetch_val("SELECT prune_notifications($1::int)", kwargs.get("keep", 200))

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("notifications는 select_many로 조회한다")
