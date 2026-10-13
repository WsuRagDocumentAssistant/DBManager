"""
SchoolViewRepository

학교 Oracle DB의 사용자 뷰(WS_VIEW.AIKEY_USER_V)를 읽는 Repository. 조회만 한다.
사본 동기화(sync_school_users)가 뷰 전체를 읽는 데만 쓴다 — 화면 요청은 PostgreSQL 사본
(SchoolUserRepository)을 읽는다.

- 비밀번호 컬럼(PWD)은 절대 조회하지 않는다. 그래서 SELECT * 대신 쓸 컬럼만 적는다.
  로그인(verify_login)도 PWD 를 가져오지 않고, 입력 비밀번호를 학교 DB 의 암호화 함수로 바꿔
  WHERE 절에서 대조만 한다 — 비밀번호 해시가 우리 서버로 넘어오지 않는다.
- 뷰 컬럼명(대문자)을 사본 테이블 컬럼명으로 바꿔서 돌려준다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseOracleDatabaseInterface

VIEW = "AIKEY_USER_V"

# 가져오지 않는 구분(STTS_DIV_NM). 뷰의 구분은 학생 / 교원 / 직원 이다.
EXCLUDED_STATUS = "학생"

# 학교 DB 의 비밀번호 암호화 함수. 학교가 알려준 대로 스키마 없이 부른다
# (SELECT CSYW_ENCODESHA256_SF('1111') FROM DUAL).
HASH_FUNCTION = "CSYW_ENCODESHA256_SF"

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

    async def verify_login(self, **kwargs) -> Optional[dict]:
        """
        학번/교번 + 비밀번호를 학교 DB 로 검증한다. 맞으면 그 사람의 행, 틀리면 None.

        비교는 학교 DB 안에서 한다: PWD = 암호화함수(입력 비밀번호). PWD 를 가져와 서버에서
        비교하지 않는다(모듈 설명). 학생은 RAG 사용자가 아니라 동기화처럼 뺀다.

        필수 kwargs: user_id (str), password (str)
        반환: dict(키: user_id, name, department, college, status, email) 또는 None
        """
        user_id, password = kwargs["user_id"], kwargs["password"]
        if not user_id or not password:
            return None
        query = (f"SELECT {', '.join(COLUMNS)} FROM {self._qualify(VIEW)} "
                 f"WHERE USER_ID = :user_id AND PWD = {HASH_FUNCTION}(:password) "
                 f"AND (STTS_DIV_NM IS NULL OR STTS_DIV_NM <> :student)")
        row = await self._fetch_one(query, {"user_id": user_id, "password": password,
                                            "student": EXCLUDED_STATUS})
        return {key: row.get(col) for col, key in COLUMNS.items()} if row else None

    async def insert(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")
