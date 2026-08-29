"""
VocabRepository

vocab_short/vocab_expansion 테이블을 담당하는 Repository.
RAG 파이프라인의 축약어 사전 저장/조회를 다룬다.
"""

import json
from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class VocabRepository(BaseDatabaseInterface):
    """
    vocab_short/vocab_expansion 전담 Repository.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 단건 조회 기능이 없다.
        """
        raise NotImplementedError("vocab은 현재 단건 조회 기능을 제공하지 않음")

    async def select_many(self, **kwargs) -> dict:
        """
        축약어 사전 전체를 {축약어: [확장어, ...]} 형태로 조회한다.

        반환: dict
        """
        query = "SELECT load_vocab() AS vocab"
        result = await self._fetch_one(query)
        return result["vocab"] if result else {}

    async def insert(self, **kwargs) -> int:
        """
        {term, expansion} 쌍 여러 개를 한 번에 등록한다 (upsert).

        필수 kwargs: pairs (list[dict], 각 {"term": ..., "expansion": ...})
        반환: 새로 추가된 확장어 개수
        """
        pairs = kwargs["pairs"]
        query = "SELECT save_vocab_pairs($1::jsonb) AS added"
        result = await self._fetch_one(query, json.dumps(pairs))
        return result["added"] if result else 0

    async def update(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 수정 기능이 없다.
        """
        raise NotImplementedError("vocab은 현재 수정 기능을 제공하지 않음")

    async def delete(self, **kwargs) -> bool:
        """
        현재 요구사항에는 삭제 기능이 없다.
        """
        raise NotImplementedError("vocab은 현재 삭제 기능을 제공하지 않음")
