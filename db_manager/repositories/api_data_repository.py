"""
ApiDataRepository

api_datas 테이블을 담당하는 Repository.
data_pipeline이 만든 ApiEntity(metadata, json)를 저장한다.
전 사용자 공용 참고자료라 user_id는 다루지 않는다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class ApiDataRepository(BaseDatabaseInterface):
    """
    api_datas 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        id로 단건 조회한다.

        필수 kwargs: id (int)
        반환: dict 또는 None
        """
        id_ = kwargs["id"]
        query = "SELECT * FROM get_api_data($1::bigint)"
        return await self._fetch_one(query, id_)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        전체 데이터 목록을 최신순으로 반환한다.

        반환: list[dict]
        """
        query = "SELECT * FROM list_api_data()"
        return await self._fetch_many(query)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        ApiEntity(metadata, json)를 저장한다.
        entity.json은 이미 직렬화된 JSON 문자열이므로 json.dumps()를 다시 하지 않는다.

        필수 kwargs:
            metadata (str)  — entity.metadata 그대로
            json (str)      — entity.json 그대로 (이미 JSON 문자열)
        반환: 저장된 row (dict)
        """
        metadata = kwargs["metadata"]
        json_data = kwargs["json"]  # entity.json은 이미 문자열이라 그대로 넘김 (json.dumps 하지 않음)
        query = "SELECT * FROM insert_api_data($1::text, $2::jsonb)"
        return await self._fetch_one(query, metadata, json_data)

    async def update(self, **kwargs) -> Optional[dict]:
        """
        수집 데이터는 수정하지 않고 다시 수집(insert)하는 방식을 쓴다.
        """
        raise NotImplementedError("api_datas는 재수집(insert) 방식을 사용하며 수정을 지원하지 않음")

    async def delete(self, **kwargs) -> bool:
        """
        데이터를 삭제한다.

        필수 kwargs: id (int)
        반환: 실제로 삭제됐으면 True
        """
        id_ = kwargs["id"]
        query = "SELECT delete_api_data($1::bigint) AS deleted"
        row = await self._fetch_one(query, id_)
        return bool(row["deleted"]) if row else False
