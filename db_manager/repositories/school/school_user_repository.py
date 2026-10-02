"""
SchoolUserRepository

school_users 테이블(학교 사용자 뷰의 PostgreSQL 사본, sql/school_users.sql)을 담당하는 Repository.
관리자 화면이 계정의 소속을 채우고(USER_LIST), 학교 구성원을 찾는(SCHOOL_USER_SEARCH) 데 쓴다.
학교 DB가 꺼져 있어도 마지막으로 동기화한 사본으로 동작한다.
"""

import json
from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class SchoolUserRepository(BaseDatabaseInterface):

    async def select_many(self, **kwargs) -> list[dict]:
        """
        학번/교번·이름·소속에 keyword가 들어간 사용자를 이름순으로 찾는다.

        필수 kwargs: keyword (str)
        선택 kwargs: limit (int, 기본 50)
        반환: list[dict]
        """
        query = "SELECT * FROM search_school_users($1::text, $2::int)"
        return await self._fetch_many(query, kwargs["keyword"], kwargs.get("limit", 50))

    async def select_by_ids(self, **kwargs) -> list[dict]:
        """
        학번/교번 또는 이메일 목록에 해당하는 사용자를 한 번에 조회한다 (없는 번호는 빠진다).
        계정 login_id 가 이메일인 예전 계정도 있어서 이메일로도 맞춘다(대소문자 무시).

        필수 kwargs: user_ids (list[str])
        반환: list[dict]
        """
        query = "SELECT * FROM get_school_users($1::text[])"
        return await self._fetch_many(query, list(kwargs["user_ids"]))

    async def insert(self, **kwargs) -> int:
        """
        뷰 전체로 사본을 맞춘다 (새 행 추가·갱신, 뷰에서 사라진 행 삭제).

        필수 kwargs: rows (list[dict]) — SchoolViewRepository.select_many 결과
        반환: 반영한 행 수
        """
        rows = kwargs["rows"]
        # 빈 결과로 맞추면 사본이 통째로 지워진다. 뷰가 비어 오는 건 장애일 가능성이 커서 막는다.
        if not rows:
            raise ValueError("학교 DB에서 받은 사용자가 없어 사본을 그대로 둡니다")
        return await self._fetch_val("SELECT sync_school_users($1::jsonb)", json.dumps(rows, ensure_ascii=False))

    async def select_one(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("school_users는 select_many / select_by_ids로 조회한다")

    async def update(self, **kwargs) -> Optional[dict]:
        raise NotImplementedError("school_users는 insert(동기화)로만 바꾼다")

    async def delete(self, **kwargs) -> bool:
        raise NotImplementedError("school_users는 insert(동기화)로만 바꾼다")
