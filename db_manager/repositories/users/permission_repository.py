"""
PermissionRepository

user_permissions 테이블(sql/user_permissions.sql)을 담당하는 Repository.
역할(admin/user)과 별개로 계정마다 켜고 끄는 권한(예: document_input = 문서 정보 입력).
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class PermissionRepository(BaseDatabaseInterface):

    async def select_many(self, **kwargs) -> list[dict]:
        """
        권한 목록. user_id 를 주면 그 사람 것만.

        선택 kwargs: user_id (str)
        반환: list[dict], 키: user_id, permission
        """
        return await self._fetch_many("SELECT * FROM list_user_permissions($1::uuid)", kwargs.get("user_id"))

    async def update(self, **kwargs) -> dict:
        """
        권한을 주거나 회수한다. 호출자가 admin 인지 DB에서 검증한다.

        필수 kwargs: admin_user_id (str), target_user_id (str), permission (str), enabled (bool)
        반환: {"success": True/False, "message": "..."}
        """
        query = "SELECT * FROM set_user_permission($1::uuid, $2::uuid, $3::text, $4::boolean)"
        row = await self._fetch_one(query, kwargs["admin_user_id"], kwargs["target_user_id"],
                                    kwargs["permission"], kwargs["enabled"])
        return row or {"success": False, "message": "알 수 없는 오류"}

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("user_permissions는 select_many로 조회한다")

    async def insert(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("user_permissions는 update(enabled=True)로 준다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("user_permissions는 update(enabled=False)로 회수한다")
