"""
SchoolUserRepository

학교 Oracle DB의 사용자 뷰(WS_VIEW.AIKEY_USER_V)를 읽는 Repository. 조회만 한다.
관리자 화면이 계정의 소속을 채우고(USER_LIST), 학교 구성원을 찾는(SCHOOL_USER_SEARCH) 데 쓴다.

- 비밀번호 컬럼(PWD)은 절대 조회하지 않는다. 그래서 SELECT * 대신 쓸 컬럼만 적는다.
- 뷰 컬럼명(대문자)을 화면에서 쓰는 이름으로 바꿔서 돌려준다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseOracleDatabaseInterface

VIEW = "AIKEY_USER_V"

# 뷰 컬럼 -> 돌려줄 키
COLUMNS = {
    "USER_ID": "user_id",         # 학번/교번
    "NM": "name",
    "USER_DEPT_NM": "department",  # 소속
    "POSI_COLG_NM": "college",
    "STTS_DIV_NM": "status",      # 학생/교원/직원
    "EMAIL": "email",
}

# Oracle IN 목록 한도
_IN_LIMIT = 1000


def _row(raw: dict) -> dict:
    return {key: raw.get(col) for col, key in COLUMNS.items()}


class SchoolUserRepository(BaseOracleDatabaseInterface):

    @property
    def _select(self) -> str:
        return f"SELECT {', '.join(COLUMNS)} FROM {self._qualify(VIEW)}"

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        학번/교번 하나로 조회한다.

        필수 kwargs: user_id (str)
        반환: dict 또는 None
        """
        row = await self._fetch_one(f"{self._select} WHERE USER_ID = :1", kwargs["user_id"])
        return _row(row) if row else None

    async def select_many(self, **kwargs) -> list[dict]:
        """
        학번/교번·이름·소속에 keyword가 들어간 사용자를 찾는다.

        필수 kwargs: keyword (str)
        선택 kwargs: limit (int, 기본 50)
        반환: list[dict] (이름순)
        """
        query = (
            f"{self._select} "
            "WHERE USER_ID LIKE :kw OR NM LIKE :kw OR USER_DEPT_NM LIKE :kw "
            "ORDER BY NM FETCH FIRST :lim ROWS ONLY"
        )
        rows = await self._fetch_many(query, {"kw": f"%{kwargs['keyword']}%", "lim": kwargs.get("limit", 50)})
        return [_row(r) for r in rows]

    async def select_by_ids(self, **kwargs) -> list[dict]:
        """
        학번/교번 목록에 해당하는 사용자를 한 번에 조회한다 (없는 번호는 빠진다).
        계정 login_id 가 이메일인 예전 계정도 있어서 EMAIL 로도 맞춘다(대소문자 무시).

        필수 kwargs: user_ids (list[str]) — 학번/교번 또는 이메일
        반환: list[dict]
        """
        ids = list(dict.fromkeys(kwargs["user_ids"]))
        found = []
        for start in range(0, len(ids), _IN_LIMIT):
            binds = {f"k{i}": value for i, value in enumerate(ids[start:start + _IN_LIMIT])}
            marks = ", ".join(f":{name}" for name in binds)
            lowered = ", ".join(f"LOWER(:{name})" for name in binds)
            query = f"{self._select} WHERE USER_ID IN ({marks}) OR LOWER(EMAIL) IN ({lowered})"
            found += await self._fetch_many(query, binds)
        return [_row(r) for r in found]

    async def insert(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("학교 DB 뷰는 조회만 한다")
