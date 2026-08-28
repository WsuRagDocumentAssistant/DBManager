"""
CredentialRepository

user_api_credentials 테이블을 담당하는 Repository.
BaseRepositoryInterface의 5개 추상 메서드 중 select_one/select_many/insert/delete를
user_api_credentials 테이블 기준으로 구현한다. update는 지원하지 않는다.
"""

import json
from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class CredentialRepository(BaseDatabaseInterface):
    """
    user_api_credentials 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        특정 사용자의 API 키를 조회한다 (provider로 필터링 가능).

        필수 kwargs: user_id (str)
        선택 kwargs: provider (str)
        반환: dict 또는 None
        """
        user_id = kwargs["user_id"]
        provider = kwargs.get("provider")
        query = "SELECT * FROM get_credential($1::uuid, $2::text)"
        return await self._fetch_one(query, user_id, provider)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        특정 사용자가 등록한 API 키 전체 목록을 반환한다.

        필수 kwargs: user_id (str)
        반환: list[dict]
        """
        user_id = kwargs["user_id"]
        query = "SELECT * FROM list_api_credentials($1::uuid)"
        return await self._fetch_many(query, user_id)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        새 API 키를 등록한다. api_key는 반드시 암호화된 값으로 넘겨야 한다.

        필수 kwargs: user_id (str), api_data (dict)
        선택 kwargs: metadata (str)
        반환: 등록된 row (dict)
        """
        user_id = kwargs["user_id"]
        metadata = kwargs.get("metadata")
        api_data = kwargs["api_data"]
        query = "SELECT * FROM insert_api_credential($1::uuid, $2::text, $3::jsonb)"
        return await self._fetch_one(query, user_id, metadata, json.dumps(api_data))

    async def update(self, **kwargs) -> Optional[dict]:
        """
        키 자체를 수정하는 기능은 지원하지 않는다.
        """
        raise NotImplementedError("API 키는 수정 대신 재등록(insert)+삭제(delete) 방식을 사용함")

    async def delete(self, **kwargs) -> bool:
        """
        API 키를 삭제한다.

        필수 kwargs: credential_id (str)
        반환: 실제로 삭제됐으면 True
        """
        credential_id = kwargs["credential_id"]
        query = "SELECT delete_api_credential($1::uuid) AS deleted"
        row = await self._fetch_one(query, credential_id)
        return bool(row["deleted"]) if row else False
