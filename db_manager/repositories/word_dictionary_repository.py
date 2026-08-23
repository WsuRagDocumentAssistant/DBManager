"""
WordDictionaryRepository

word_dictionary 테이블을 담당하는 Repository.
단어(word)와 그 대체어(replacement)를 등록/검색/전체조회한다.
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class WordDictionaryRepository(BaseDatabaseInterface):
    """
    word_dictionary 테이블 전담 Repository.
    BaseDatabaseInterface가 이미 BaseRepositoryInterface를 상속하므로 별도로 다시 상속하지 않음.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        단어 하나를 정확히 일치하는 것만 검색한다 (부분일치 아님).

        필수 kwargs: word (str)
        반환: {"id": ..., "word": ..., "replacement": ...} 또는 None
        """
        word = kwargs["word"]
        query = "SELECT * FROM search_word($1::text)"
        return await self._fetch_one(query, word)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        등록된 단어 전체를 조회한다 (전체검색).

        반환: list[dict]
        """
        query = "SELECT * FROM list_all_words()"
        return await self._fetch_many(query)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        새 단어/대체어 쌍을 등록한다.

        필수 kwargs: word (str), replacement (str)
        반환: 등록된 row (dict)
        """
        word = kwargs["word"]
        replacement = kwargs["replacement"]
        query = "SELECT * FROM insert_word($1::text, $2::text)"
        return await self._fetch_one(query, word, replacement)

    async def update(self, **kwargs) -> Optional[dict]:
        """
        현재 요구사항에는 수정 기능이 없다.
        """
        raise NotImplementedError("word_dictionary는 현재 수정 기능을 제공하지 않음")

    async def delete(self, **kwargs) -> bool:
        """
        현재 요구사항에는 삭제 기능이 없다.
        """
        raise NotImplementedError("word_dictionary는 현재 삭제 기능을 제공하지 않음")
