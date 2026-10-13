"""
ApiDataMetaRepository

api_data_meta 테이블(sql/api_data_meta.sql)을 담당하는 Repository.
외부 API 의 추가 정보 — 제공 기관, 기준 연도, 설명. api_datas 와 url 로 1:1 이다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class ApiDataMetaRepository(BaseDatabaseInterface):

    async def select_many(self, **kwargs) -> list[dict]:
        """
        전체 추가 정보.

        반환: list[dict], 키: url, provider, base_year, description, updated_at
        """
        return await self._fetch_many("SELECT * FROM list_api_data_meta()")

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        추가 정보를 저장한다(있으면 덮어쓴다). 빈 문자열은 비운다.

        필수 kwargs: url (str)
        선택 kwargs: provider (str), base_year (int), description (str)
        반환: 저장된 행 (dict)
        """
        query = "SELECT * FROM save_api_data_meta($1::text, $2::text, $3::integer, $4::text)"
        return await self._fetch_one(query, kwargs["url"], kwargs.get("provider"),
                                     kwargs.get("base_year"), kwargs.get("description"))

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("api_data_meta는 select_many로 조회한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("api_data_meta는 insert(있으면 덮어쓰기)로 바꾼다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("api_data_meta는 API를 지우면 같이 지워진다(ON DELETE CASCADE)")
