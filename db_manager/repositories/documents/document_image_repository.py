"""
DocumentImageRepository

document_images 테이블을 담당하는 Repository.
문서에 속한 이미지 등록/문서명 기준 검색을 처리한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class DocumentImageRepository(BaseDatabaseInterface):
    """
    document_images 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

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
