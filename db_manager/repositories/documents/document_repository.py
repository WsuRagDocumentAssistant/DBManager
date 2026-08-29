"""
DocumentRepository

documents 테이블을 담당하는 Repository.
문서 등록/조회/검색/수정/삭제를 처리한다. 등록/수정 시 분류값(업무구분/수행업무/
수행부서/보고서명)에 대한 옵션 테이블 upsert는 DB 함수(register_document) 내부에서
처리되므로, 이 Repository에서 별도로 옵션 테이블을 건드리지 않는다.
"""

import json
from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


def _to_vector_literal(query_vector: list[float]) -> str:
    """
    asyncpg는 pgvector의 vector 타입에 대한 코덱을 등록하지 않은 상태라, python list를
    그대로 바인딩하면 DataError가 난다. pgvector의 텍스트 리터럴 형식('[1,2,3]')으로
    직접 변환해서 넘겨야 한다.
    """
    return "[" + ",".join(str(x) for x in query_vector) + "]"


class DocumentRepository(BaseDatabaseInterface):
    """
    documents 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        이미 임베딩이 끝난 문서(source_path로 식별)에 업무 분류값을 등록한다.
        더 이상 새 문서를 만들지 않고, 기존 행을 찾아 업데이트한다. 해당 source_path의
        문서가 없으면(= save_document_json으로 먼저 색인되지 않았으면) DB 함수가
        예외를 던지며, 이 Repository는 감싸지 않고 그대로 전파한다.

        필수 kwargs: source_path (str), production_year (int)
        선택 kwargs: work_category (str, None 가능), task (str, None 가능) — "수행업무" 값,
                     department (str, None 가능), report_type (str, None 가능),
                     registered_at (str, None이면 DB 함수가 오늘 날짜로 자동 설정)
        반환: {"id": ..., "filename": ...}

        주의: 이 kwarg는 "task_name"이 아니라 "task"다. DBManager.call()
        자신의 파라미터 이름이 task_name이라, 같은 이름으로 kwargs를 넘기면
        TypeError(got multiple values for argument 'task_name')가 나기 때문이다.
        """
        source_path = kwargs["source_path"]
        production_year = kwargs["production_year"]
        work_category = kwargs.get("work_category")
        task = kwargs.get("task")  # "task_name" 아님 — 충돌 방지
        department = kwargs.get("department")
        report_type = kwargs.get("report_type")
        registered_at = kwargs.get("registered_at")
        query = "SELECT * FROM register_document($1::text, $2::integer, $3::text, $4::text, $5::text, $6::text, $7::date)"
        return await self._fetch_one(
            query, source_path, production_year, work_category, task, department, report_type, registered_at
        )

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        문서를 id로 단건 조회한다.

        필수 kwargs: id (int)
        반환: dict 또는 None. 키: id, filename, source_path, production_year, work_category,
              task_name, department, report_type, registered_at
        """
        id_ = kwargs["id"]
        query = "SELECT * FROM get_document($1::integer)"
        return await self._fetch_one(query, id_)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        최근 등록순으로 문서 목록을 페이지네이션해서 조회한다.

        선택 kwargs: limit (int, 기본 50), offset (int, 기본 0)
        반환: list[dict], 각 dict 키는 select_one과 동일
        """
        limit = kwargs.get("limit", 50)
        offset = kwargs.get("offset", 0)
        query = "SELECT * FROM list_documents($1::integer, $2::integer)"
        return await self._fetch_many(query, limit, offset)

    async def update(self, **kwargs) -> Optional[int]:
        """
        문서의 분류 필드(생산연도/업무구분/수행업무/수행부서/보고서명)를 수정한다.
        존재하지 않는 id로 호출하면 DB 함수가 예외를 던지며, 이 Repository는 감싸지 않고
        그대로 전파한다.

        필수 kwargs: id (int), production_year (int)
        선택 kwargs: work_category (str, None 가능), p_task_name (str, None 가능),
                     department (str, None 가능), report_type (str, None 가능)
        반환: 수정된 문서의 id (int)

        주의: 이 kwarg는 "task_name"이 아니라 "p_task_name"이다. DBManager.call()
        자신의 파라미터 이름이 task_name이라, 같은 이름으로 kwargs를 넘기면
        TypeError(got multiple values for argument 'task_name')가 나기 때문이다.
        """
        id_ = kwargs["id"]
        production_year = kwargs["production_year"]
        work_category = kwargs.get("work_category")
        task_name = kwargs.get("p_task_name")
        department = kwargs.get("department")
        report_type = kwargs.get("report_type")
        query = "SELECT update_document($1::integer, $2::integer, $3::text, $4::text, $5::text, $6::text) AS id"
        row = await self._fetch_one(
            query, id_, production_year, work_category, task_name, department, report_type
        )
        return row["id"] if row else None

    async def delete(self, **kwargs) -> Optional[int]:
        """
        문서를 id로 삭제한다. 존재하지 않는 id로 호출하면 DB 함수가 예외를 던지며,
        이 Repository는 감싸지 않고 그대로 전파한다.

        필수 kwargs: id (int)
        반환: 삭제된 문서의 id (int)
        """
        id_ = kwargs["id"]
        query = "SELECT delete_document($1::integer) AS id"
        row = await self._fetch_one(query, id_)
        return row["id"] if row else None

    async def search_by_filename(self, **kwargs) -> list[dict]:
        """
        파일명(filename) 기준으로 부분일치 검색한다.
        BaseRepositoryInterface가 요구하는 필수 메서드는 아니고, 필요해서 추가한 메서드다.

        필수 kwargs: query (str)
        반환: list[dict], 키: id, filename, source_path, registered_at (최근 등록순)
        """
        search_query = kwargs["query"]
        query = "SELECT * FROM search_documents_by_filename($1::text)"
        return await self._fetch_many(query, search_query)

    async def index_document(self, **kwargs) -> Optional[int]:
        """
        RAG 파이프라인이 파싱한 문서를 색인한다 (UPSERT — 같은 source_path면
        RAG 컬럼만 갱신하고 업무 분류값은 보존됨).

        필수 kwargs: document (dict, JSON으로 직렬화 가능한 구조 —
                     source_path/filename/title/creator/... + parents[].children[])
        선택 kwargs: sparse_dim (int, 기본 250002)
        반환: 색인된 documents.id
        """
        document = kwargs["document"]
        sparse_dim = kwargs.get("sparse_dim", 250002)
        query = "SELECT save_document_json($1::jsonb, $2::integer) AS id"
        result = await self._fetch_one(query, json.dumps(document), sparse_dim)
        return result["id"] if result else None

    async def search_vector(self, **kwargs) -> list[dict]:
        """
        dense(임베딩 벡터) 유사도 검색.

        필수 kwargs: query_vector (list[float])
        선택 kwargs: top_k (int, 기본 5), document_id (int)
        반환: list[dict]
        """
        query_vector = kwargs["query_vector"]
        top_k = kwargs.get("top_k", 5)
        document_id = kwargs.get("document_id")
        query = "SELECT * FROM search_documents_vector($1::vector, $2::integer, $3::integer)"
        return await self._fetch_many(query, _to_vector_literal(query_vector), top_k, document_id)

    async def search_lexical(self, **kwargs) -> list[dict]:
        """
        sparse(어휘) 유사도 검색.

        필수 kwargs: query_weights (dict, {"토큰id": 가중치})
        선택 kwargs: sparse_dim (int, 기본 250002), top_k (int, 기본 5)
        반환: list[dict]
        """
        query_weights = kwargs["query_weights"]
        sparse_dim = kwargs.get("sparse_dim", 250002)
        top_k = kwargs.get("top_k", 5)
        query = "SELECT * FROM search_documents_lexical($1::jsonb, $2::integer, $3::integer)"
        return await self._fetch_many(query, json.dumps(query_weights), sparse_dim, top_k)

    async def search_hybrid(self, **kwargs) -> list[dict]:
        """
        dense+sparse를 RRF로 합친 검색.

        필수 kwargs: query_vector (list[float]), query_weights (dict)
        선택 kwargs: sparse_dim (int, 기본 250002), top_k (int, 기본 5),
                     document_id (int), k (int, 기본 60)
        반환: list[dict]
        """
        query_vector = kwargs["query_vector"]
        query_weights = kwargs["query_weights"]
        sparse_dim = kwargs.get("sparse_dim", 250002)
        top_k = kwargs.get("top_k", 5)
        document_id = kwargs.get("document_id")
        k = kwargs.get("k", 60)
        query = """
            SELECT * FROM search_documents_hybrid(
                $1::vector, $2::jsonb, $3::integer, $4::integer, $5::integer, $6::integer
            )
        """
        return await self._fetch_many(
            query, _to_vector_literal(query_vector), json.dumps(query_weights), sparse_dim, top_k, document_id, k
        )

    async def count_index_stats(self, **kwargs) -> Optional[dict]:
        """
        색인 통계(문서/parent/child/embedded/lexical 개수)를 조회한다.

        반환: {"documents": ..., "parents": ..., "children": ..., "embedded": ..., "lexical": ...}
        """
        query = "SELECT * FROM count_documents()"
        return await self._fetch_one(query)
