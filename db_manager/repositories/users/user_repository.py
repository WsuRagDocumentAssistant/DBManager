"""
UserRepository

users 테이블을 담당하는 Repository.
회원가입 화면은 없고, 계정은 관리자가 미리 만들어두는 방식이다.
로그인 검증(select_one)과 계정 생성(insert)만 지원한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class UserRepository(BaseDatabaseInterface):
    """
    users 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        로그인 아이디+비밀번호를 검증한다.
        일치하면 사용자 정보를 반환하고, 일치하지 않으면 None을 반환한다.

        필수 kwargs: login_id (str), password (str)
        반환: {"user_id": ..., "name": ..., "login_id": ..., "role": ...} 또는 None
        """
        login_id = kwargs["login_id"]
        password = kwargs["password"]
        query = "SELECT * FROM verify_login($1::text, $2::text)"
        return await self._fetch_one(query, login_id, password)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        새 계정을 생성한다 (회원가입이 아니라 관리자가 미리 만들어두는 용도).
        비밀번호는 DB 쪽 프로시저에서 자동으로 암호화되어 저장된다.

        필수 kwargs: name (str), login_id (str), password (str)
        선택 kwargs: role (str, 기본 "user", "admin" 또는 "user"만 허용)
        반환: {"user_id": ..., "name": ..., "login_id": ..., "role": ...}
        """
        name = kwargs["name"]
        login_id = kwargs["login_id"]
        password = kwargs["password"]
        role = kwargs.get("role", "user")
        query = "SELECT * FROM create_user_account($1::text, $2::text, $3::text, $4::text)"
        return await self._fetch_one(query, name, login_id, password, role)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        현재 요구사항에는 사용자 목록 조회 기능이 없다.
        """
        raise NotImplementedError("users는 현재 목록 조회 기능을 제공하지 않음")

    async def update(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 수정 기능이 없다.
        """
        raise NotImplementedError("users는 현재 수정 기능을 제공하지 않음")

    async def delete(self, **kwargs) -> bool:
        """
        현재 요구사항에는 삭제 기능이 없다.
        """
        raise NotImplementedError("users는 현재 삭제 기능을 제공하지 않음")

    async def update_role(self, **kwargs) -> dict:
        """
        관리자가 다른 사용자의 권한(role)을 변경한다.
        호출한 사용자가 실제로 admin 권한인지 DB에서 검증한 뒤 처리된다.

        필수 kwargs: admin_user_id (str), target_user_id (str), new_role (str, 'admin' 또는 'user')
        반환: {"success": True/False, "message": "..."}
        """
        admin_user_id = kwargs["admin_user_id"]
        target_user_id = kwargs["target_user_id"]
        new_role = kwargs["new_role"]
        query = "SELECT * FROM update_user_role($1::uuid, $2::uuid, $3::text)"
        result = await self._fetch_one(query, admin_user_id, target_user_id, new_role)
        return dict(result) if result else {"success": False, "message": "알 수 없는 오류"}
