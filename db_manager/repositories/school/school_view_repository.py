"""
SchoolViewRepository

학교 Oracle DB의 사용자 뷰(WS_VIEW.AIKEY_USER_V)를 읽는 Repository. 조회만 한다.
사본 동기화(sync_school_users)가 뷰 전체를 읽는 데만 쓴다 — 화면 요청은 PostgreSQL 사본
(SchoolUserRepository)을 읽는다.

- 비밀번호 컬럼(PWD)은 절대 조회하지 않는다. 그래서 SELECT * 대신 쓸 컬럼만 적는다.
- 뷰 컬럼명(대문자)을 사본 테이블 컬럼명으로 바꿔서 돌려준다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseOracleDatabaseInterface

VIEW = "AIKEY_USER_V"

# 가져오지 않는 구분(STTS_DIV_NM). 뷰의 구분은 학생 / 교원 / 직원 이다.
EXCLUDED_STATUS = "학생"

# 뷰 컬럼 -> 사본 컬럼
COLUMNS = {
    "USER_ID": "user_id",         # 학번/교번
    "NM": "name",
    "USER_DEPT_NM": "department",  # 소속
    "POSI_COLG_NM": "college",
    "STTS_DIV_NM": "status",      # 학생/교원/직원
    "EMAIL": "email",
}


class SchoolViewRepository(BaseOracleDatabaseInterface):

    async def select_many(self, **kwargs) -> list[dict]:
        """
        뷰에서 교직원(학생 제외)을 읽는다.

        학생은 RAG 시스템 사용자가 아니라서 가져오지 않는다 — 학생 개인정보를 사본으로 둘 이유도 없다.
        구분이 비어 있는 행은 학생인지 알 수 없어 남긴다.

        반환: list[dict], 키: user_id, name, department, college, status, email
        """
        query = (f"SELECT {', '.join(COLUMNS)} FROM {self._qualify(VIEW)} "
                 f"WHERE STTS_DIV_NM IS NULL OR STTS_DIV_NM <> :student")
        rows = await self._fetch_many(query, {"student": EXCLUDED_STATUS})
        return [{key: row.get(col) for col, key in COLUMNS.items()} for row in rows]

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("동기화는 뷰 전체만 읽는다 (select_many)")

    async def insert(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")
