"""
ReportTypeOptionRepository

report_type_options 테이블을 담당하는 Repository.
문서 등록 화면의 "보고서명" 드롭다운 후보값을 조회한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class ReportTypeOptionRepository(BaseDatabaseInterface):
    """
    report_type_options 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_many(self, **kwargs) -> list[str]:
        """
        보고서명 드롭다운 후보 목록을 조회한다 (엑셀 원본 값으로 미리 시드되어 있고,
        register_document 호출 시 새 값이 자동으로 추가된다).

        반환: list[str] (정렬된 값 목록)
        """
        query = "SELECT * FROM get_report_type_options()"
        rows = await self._fetch_many(query)
        return [row["value"] for row in rows]

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 단건 조회 기능이 없다.
        """
        raise NotImplementedError("report_type_options는 현재 단건 조회 기능을 제공하지 않음")

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 별도 등록 기능이 없다.
        (등록은 register_document 호출 시 DB 함수 내부에서 자동으로 upsert됨)
        """
        raise NotImplementedError("report_type_options는 register_document 내부에서 자동 upsert되며, 별도 등록 기능을 제공하지 않음")

    async def update(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 수정 기능이 없다.
        """
        raise NotImplementedError("report_type_options는 현재 수정 기능을 제공하지 않음")

    async def delete(self, **kwargs) -> bool:
        """
        현재 요구사항에는 삭제 기능이 없다.
        """
        raise NotImplementedError("report_type_options는 현재 삭제 기능을 제공하지 않음")
