"""
FeatureRequestRepository

feature_requests 테이블을 담당하는 Repository.
기능 개선 요청 게시판의 글을 등록/조회/수정/삭제하고, 관리자 답변을 저장한다.
작성자 이름(author_name)은 DB 함수가 users 테이블과 조인해서 채운다.
수정/삭제/답변 권한은 DB 함수가 호출자 user_id로 검증하고, 권한이 없으면 행을 돌려주지 않는다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class FeatureRequestRepository(BaseDatabaseInterface):
    """
    feature_requests 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        요청 글 하나를 id로 조회한다.

        필수 kwargs: id (int)
        반환: dict 또는 None. 키: id, title, content, is_secret, author_id, author_name,
              created_at, status, answer, answered_at
        """
        id_ = kwargs["id"]
        query = "SELECT * FROM get_feature_request($1::bigint)"
        return await self._fetch_one(query, id_)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        전체 요청 글을 최신순으로 조회한다. 비밀글도 그대로 반환한다 (가리는 건 호출하는 쪽 몫).

        반환: list[dict], 각 dict 키는 select_one과 동일
        """
        query = "SELECT * FROM list_feature_requests()"
        return await self._fetch_many(query)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        새 요청 글을 등록한다. status는 'received'로 시작한다.

        필수 kwargs: author_id (str), title (str), content (str), is_secret (bool)
        반환: 등록된 행 (dict), 키는 select_one과 동일
        """
        author_id = kwargs["author_id"]
        title = kwargs["title"]
        content = kwargs["content"]
        is_secret = kwargs["is_secret"]
        query = "SELECT * FROM insert_feature_request($1::uuid, $2::text, $3::text, $4::boolean)"
        return await self._fetch_one(query, author_id, title, content, is_secret)

    async def update(self, **kwargs) -> Optional[dict]:
        """
        요청 글의 제목/내용/비밀글 여부를 수정한다. 작성자 본인만 수정할 수 있다.
        status와 answer는 건드리지 않는다.

        필수 kwargs: id (int), user_id (str), title (str), content (str), is_secret (bool)
        반환: 수정된 행 (dict), 글이 없거나 작성자가 아니면 None
        """
        id_ = kwargs["id"]
        user_id = kwargs["user_id"]
        title = kwargs["title"]
        content = kwargs["content"]
        is_secret = kwargs["is_secret"]
        query = "SELECT * FROM update_feature_request($1::bigint, $2::uuid, $3::text, $4::text, $5::boolean)"
        return await self._fetch_one(query, id_, user_id, title, content, is_secret)

    async def delete(self, **kwargs) -> bool:
        """
        요청 글을 삭제한다. 작성자 본인이나 관리자만 삭제할 수 있다.

        필수 kwargs: id (int), user_id (str)
        반환: 실제로 삭제됐으면 True, 글이 없거나 권한이 없으면 False
        """
        id_ = kwargs["id"]
        user_id = kwargs["user_id"]
        query = "SELECT delete_feature_request($1::bigint, $2::uuid) AS success"
        row = await self._fetch_one(query, id_, user_id)
        return bool(row["success"]) if row else False

    async def update_answer(self, **kwargs) -> Optional[dict]:
        """
        관리자가 처리 상태를 바꾸고 답변을 남긴다.
        answer가 빈 문자열이면 상태만 바꾸고, 기존 답변과 answered_at은 그대로 둔다.
        answer가 있으면 answered_at을 현재 시각으로 채운다.

        필수 kwargs: id (int), admin_user_id (str), status (str, 'received' | 'in_progress' | 'done' | 'rejected'),
                     answer (str)
        반환: 갱신된 행 (dict), 글이 없거나 호출자가 관리자가 아니면 None
        """
        id_ = kwargs["id"]
        admin_user_id = kwargs["admin_user_id"]
        status = kwargs["status"]
        answer = kwargs["answer"]
        query = "SELECT * FROM answer_feature_request($1::bigint, $2::uuid, $3::text, $4::text)"
        return await self._fetch_one(query, id_, admin_user_id, status, answer)
