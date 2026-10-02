"""
DocumentCategoryRepository

document_categories 테이블(sql/document_categories.sql)을 담당하는 Repository.
문서 등록(비정형) 화면의 입력 카테고리. 설정 관리 > 문서 카테고리 관리에서 추가·삭제한다.

kind 네 가지
  work_category : 업무구분                      parent ''
  task          : 수행업무 (pair = 짝 수행부서)   parent = 업무구분
  department    : 수행부서                      parent = 업무구분
  report_type   : 보고서명                      parent ''
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class DocumentCategoryRepository(BaseDatabaseInterface):

    async def select_many(self, **kwargs) -> list[dict]:
        """
        전체 카테고리 (종류 · 상위 · 순서대로).

        반환: list[dict], 키: id, kind, parent, value, pair, sort_order, created_at
        """
        return await self._fetch_many("SELECT * FROM list_document_categories()")

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        카테고리를 추가한다(같은 kind·parent·value 가 있으면 pair 만 바꾼다). 관리자만.

        필수 kwargs: admin_user_id (str), kind (str), value (str)
        선택 kwargs: parent (str, 기본 ''), pair (str)
        반환: 저장된 행 (dict), 관리자가 아니면 None
        """
        query = "SELECT * FROM save_document_category($1::uuid, $2::text, $3::text, $4::text, $5::text)"
        return await self._fetch_one(query, kwargs["admin_user_id"], kwargs["kind"],
                                     kwargs.get("parent") or "", kwargs["value"], kwargs.get("pair"))

    async def delete(self, **kwargs) -> bool:
        """
        카테고리를 지운다. 업무구분이면 그 아래 수행업무·수행부서도 같이 지운다. 관리자만.

        필수 kwargs: admin_user_id (str), id (int)
        반환: 지웠으면 True, 없거나 관리자가 아니면 False
        """
        query = "SELECT delete_document_category($1::uuid, $2::bigint) AS deleted"
        row = await self._fetch_one(query, kwargs["admin_user_id"], kwargs["id"])
        return bool(row and row["deleted"])

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("document_categories는 select_many로 조회한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("document_categories는 insert(같은 값이면 pair 갱신)로 바꾼다")
