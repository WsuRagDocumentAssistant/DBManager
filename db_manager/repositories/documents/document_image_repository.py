"""
DocumentImageRepository

document_images 테이블을 담당하는 Repository.
문서에 속한 이미지 등록/조회/수정과 문서명 기준 검색을 처리한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class DocumentImageRepository(BaseDatabaseInterface):
    """
    document_images 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        이미지를 id로 단건 조회한다.

        필수 kwargs: id (int)
        반환: dict 또는 None
        """
        id_ = kwargs["id"]
        query = "SELECT * FROM get_document_image($1::bigint)"
        return await self._fetch_one(query, id_)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        특정 문서(document_id)에 속한 이미지 전체를 조회한다.
        (기존에 제목 부분일치 검색으로 우회하던 방식 대체 — 제목이 겹치면
        다른 문서의 이미지가 섞이는 버그가 있었음)

        필수 kwargs: document_id (int)
        반환: list[dict]
        """
        document_id = kwargs["document_id"]
        query = "SELECT * FROM list_document_images($1::integer)"
        return await self._fetch_many(query, document_id)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        문서에 이미지를 등록한다.

        필수 kwargs: document_id (int), image_name (str), image_path (str)
        반환: {"id": ..., "document_id": ..., "image_name": ..., "image_path": ...}
        """
        document_id = kwargs["document_id"]
        image_name = kwargs["image_name"]
        image_path = kwargs["image_path"]
        query = "SELECT * FROM create_document_image($1::integer, $2::text, $3::text)"
        return await self._fetch_one(query, document_id, image_name, image_path)

    async def update(self, **kwargs) -> Optional[dict]:
        """
        이미지 설명/메타정보를 수정한다 (이미지 보기 모달의 저장 버튼).
        존재하지 않는 id로 호출하면 DB 함수가 예외를 던지며, 그대로 전파한다.

        필수 kwargs: id (int), image_name (str), image_path (str)
        선택 kwargs: caption (str), major_title (str), mid_title (str),
                     minor_title (str), note (str), ai_summary (str),
                     key_facts (list[str]), key_phrases (list[str])
        반환: 수정된 행 전체 (dict)
        """
        id_ = kwargs["id"]
        image_name = kwargs["image_name"]
        image_path = kwargs["image_path"]
        caption = kwargs.get("caption")
        major_title = kwargs.get("major_title")
        mid_title = kwargs.get("mid_title")
        minor_title = kwargs.get("minor_title")
        note = kwargs.get("note")
        ai_summary = kwargs.get("ai_summary")
        key_facts = kwargs.get("key_facts")
        key_phrases = kwargs.get("key_phrases")
        query = """
            SELECT * FROM update_document_image(
                $1::bigint, $2::text, $3::text, $4::text, $5::text,
                $6::text, $7::text, $8::text, $9::text, $10::text[], $11::text[]
            )
        """
        return await self._fetch_one(
            query, id_, image_name, image_path, caption, major_title,
            mid_title, minor_title, note, ai_summary, key_facts, key_phrases
        )

    async def delete(self, **kwargs) -> bool:
        """
        현재 요구사항에는 삭제 기능이 없다.
        """
        raise NotImplementedError("document_images는 현재 삭제 기능을 제공하지 않음")

    async def search_by_title(self, **kwargs) -> list[dict]:
        """
        문서명(title) 기준으로 부분일치 검색하여 해당 문서들에 속한 이미지 목록을 조회한다.

        필수 kwargs: query (str)
        반환: list[dict], 키: id, document_id, image_name, image_path, document_title
              (document_id, id 순 정렬)
        """
        search_query = kwargs["query"]
        query = "SELECT * FROM search_document_images($1::text)"
        return await self._fetch_many(query, search_query)
