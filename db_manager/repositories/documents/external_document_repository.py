"""
ExternalDocumentRepository

external_documents 테이블(sql/external_documents.sql)을 담당하는 Repository.
이 표에 id 가 있는 문서가 외부 문서다(외부 문서 등록 화면으로 올린 것). 나머지는 내부 문서.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class ExternalDocumentRepository(BaseDatabaseInterface):

    async def select_many(self, **kwargs) -> list[int]:
        """
        외부 문서 id 목록.

        반환: list[int]
        """
        rows = await self._fetch_many("SELECT * FROM list_external_documents()")
        return [row["document_id"] for row in rows]

    async def update(self, **kwargs) -> bool:
        """
        외부 문서로 표시하거나 표시를 뗀다.

        필수 kwargs: document_id (int), external (bool)
        반환: True
        """
        query = "SELECT set_external_document($1::bigint, $2::boolean) AS done"
        row = await self._fetch_one(query, kwargs["document_id"], kwargs["external"])
        return bool(row and row["done"])

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("external_documents는 select_many로 조회한다")

    async def insert(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("external_documents는 update(external=True)로 표시한다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("external_documents는 update(external=False)로 뗀다")
