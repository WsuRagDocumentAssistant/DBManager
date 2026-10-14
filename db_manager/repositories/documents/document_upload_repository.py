"""
DocumentUploadRepository

document_uploads 테이블(sql/document_uploads.sql)을 담당하는 Repository.
문서를 누가, 어느 등록(batch_id — 등록 버튼 한 번에 같이 올린 묶음)에서 올렸는지 기록한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class DocumentUploadRepository(BaseDatabaseInterface):

    async def select_many(self, **kwargs) -> list[dict]:
        """
        전체 기록.

        반환: list[dict], 키: document_id, user_id, batch_id, uploaded_at
        """
        return await self._fetch_many("SELECT * FROM list_document_uploads()")

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        올린 사람·묶음을 기록한다(있으면 덮어쓴다 — 같은 파일을 다시 올린 경우).

        필수 kwargs: document_id (int), user_id (str)
        선택 kwargs: batch_id (str)
        반환: 저장된 행 (dict)
        """
        query = "SELECT * FROM save_document_upload($1::bigint, $2::uuid, $3::text)"
        return await self._fetch_one(query, kwargs["document_id"], kwargs["user_id"],
                                     kwargs.get("batch_id"))

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("document_uploads는 select_many로 조회한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("document_uploads는 insert(있으면 덮어쓰기)로 바꾼다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("document_uploads는 문서를 지우면 같이 지워진다(ON DELETE CASCADE)")
