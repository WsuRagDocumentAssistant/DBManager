"""
DocumentRepository

documents 테이블을 담당하는 Repository.
문서 등록/조회/검색/수정/삭제를 처리한다. 등록/수정 시 분류값(업무구분/수행업무/
수행부서/보고서명)에 대한 옵션 테이블 upsert는 DB 함수(register_document) 내부에서
처리되므로, 이 Repository에서 별도로 옵션 테이블을 건드리지 않는다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class DocumentRepository(BaseDatabaseInterface):
    """
    documents 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        문서를 등록한다. 등록과 동시에 DB 함수 내부에서 업무구분/수행업무/수행부서/
        보고서명 옵션 테이블에도 자동으로 upsert된다.

        필수 kwargs: production_year (int), file_path (str)
        선택 kwargs: work_category (str, None 가능), p_task_name (str, None 가능),
                     department (str, None 가능), report_type (str, None 가능),
                     registered_at (str, None이면 DB 함수가 오늘 날짜로 자동 설정)
        반환: {"id": ..., "filename": ...}

        주의: 이 kwarg는 "task_name"이 아니라 "p_task_name"이다. DBManager.call()
        자신의 파라미터 이름이 task_name이라, 같은 이름으로 kwargs를 넘기면
        TypeError(got multiple values for argument 'task_name')가 나기 때문이다.
        """
        production_year = kwargs["production_year"]
        work_category = kwargs.get("work_category")
        task_name = kwargs.get("p_task_name")
        department = kwargs.get("department")
        report_type = kwargs.get("report_type")
        file_path = kwargs["file_path"]
        registered_at = kwargs.get("registered_at")
        query = "SELECT * FROM register_document($1::integer, $2::text, $3::text, $4::text, $5::text, $6::text, $7::date)"
        return await self._fetch_one(
            query, production_year, work_category, task_name, department, report_type, file_path, registered_at
        )

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        문서를 id로 단건 조회한다.

        필수 kwargs: id (int)
        반환: dict 또는 None. 키: id, filename, file_path, production_year, work_category,
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
        파일명(파일 경로의 마지막 부분) 기준으로 부분일치 검색한다.
        BaseRepositoryInterface가 요구하는 필수 메서드는 아니고, 필요해서 추가한 메서드다.

        필수 kwargs: query (str)
        반환: list[dict], 키: id, filename, file_path, registered_at (최근 등록순)
        """
        search_query = kwargs["query"]
        query = "SELECT * FROM search_documents_by_filename($1::text)"
        return await self._fetch_many(query, search_query)
