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
        뷰 전체를 읽는다.

        반환: list[dict], 키: user_id, name, department, college, status, email
        """
        rows = await self._fetch_many(f"SELECT {', '.join(COLUMNS)} FROM {self._qualify(VIEW)}")
        return [{key: row.get(col) for col, key in COLUMNS.items()} for row in rows]

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("동기화는 뷰 전체만 읽는다 (select_many)")

    async def insert(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")
