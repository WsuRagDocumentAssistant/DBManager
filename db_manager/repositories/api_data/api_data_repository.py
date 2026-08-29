"""
ApiDataRepository

api_datas 테이블을 담당하는 Repository.
url을 기본키로 쓰는 ApiEntity 구조에 맞춘다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


def _to_vector_literal(query_vector: list[float]) -> str:
    """
    asyncpg는 pgvector의 vector 타입에 대한 코덱을 등록하지 않은 상태라, python list를
    그대로 바인딩하면 DataError가 난다. pgvector의 텍스트 리터럴 형식('[1,2,3]')으로
    직접 변환해서 넘겨야 한다.
    """
    return "[" + ",".join(str(x) for x in query_vector) + "]"


class ApiDataRepository(BaseDatabaseInterface):
    """
    api_datas 테이블 전담 Repository.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 단건 조회 기능이 없다.
        """
        raise NotImplementedError("api_datas는 현재 단건 조회 기능을 제공하지 않음")

    async def select_many(self, **kwargs) -> list[dict]:
        """
        전체 공공데이터 목록을 최신순으로 반환한다.

        반환: list[dict], 각 dict 키: title, url, source, key, data, data_type, date
        """
        query = "SELECT * FROM select_all_api_data()"
        return await self._fetch_many(query)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        새 공공데이터를 등록한다.

        필수 kwargs: title (str), url (str), source (str), key (str),
                     data (str), data_type (str)
        반환: {"title":..., "url":..., "source":..., "key":..., "data":...,
               "data_type":..., "date":...}
        """
        title = kwargs["title"]
        url = kwargs["url"]
        source = kwargs["source"]
        key = kwargs["key"]
        data = kwargs["data"]
        data_type = kwargs["data_type"]
        query = "SELECT * FROM insert_api_data($1::text, $2::text, $3::text, $4::text, $5::text, $6::text)"
        return await self._fetch_one(query, title, url, source, key, data, data_type)

    async def update(self, **kwargs) -> dict:
        """
        url로 찾아서 data(응답 원문)를 갱신한다. date도 자동으로 현재시각으로 갱신된다.

        필수 kwargs: url (str), data (str)
        반환: {"title": ..., "success": True/False}
              해당 url이 없으면 {"title": None, "success": False}
        """
        url = kwargs["url"]
        data = kwargs["data"]
        query = "SELECT * FROM update_api_data_date($1::text, $2::text)"
        result = await self._fetch_one(query, url, data)
        return dict(result) if result else {"title": None, "success": False}

    async def delete(self, **kwargs) -> bool:
        """
        url로 공공데이터를 삭제한다.

        필수 kwargs: url (str)
        반환: 실제로 삭제됐으면 True, 해당 url이 없으면 False
        """
        url = kwargs["url"]
        query = "SELECT delete_api_data($1::text) AS success"
        result = await self._fetch_one(query, url)
        return result["success"] if result else False

    async def save_vector(self, **kwargs) -> Optional[dict]:
        """
        API 데이터의 임베딩 벡터를 저장/갱신한다 (UPSERT).
        해당 url이 api_datas에 이미 존재해야 한다 (FK 제약).

        필수 kwargs: url (str), embedding (list[float])
        반환: {"url": ...}
        """
        url = kwargs["url"]
        embedding = kwargs["embedding"]
        query = "SELECT * FROM save_api_data_vector($1::text, $2::vector)"
        return await self._fetch_one(query, url, _to_vector_literal(embedding))

    async def search_vector(self, **kwargs) -> list[dict]:
        """
        쿼리 벡터와 의미적으로 유사한 API 데이터를 검색한다.

        필수 kwargs: query_vector (list[float])
        선택 kwargs: top_k (int, 기본 5)
        반환: list[dict], 키: url, title, source, similarity
        """
        query_vector = kwargs["query_vector"]
        top_k = kwargs.get("top_k", 5)
        query = "SELECT * FROM search_api_data_vector($1::vector, $2::integer)"
        return await self._fetch_many(query, _to_vector_literal(query_vector), top_k)
