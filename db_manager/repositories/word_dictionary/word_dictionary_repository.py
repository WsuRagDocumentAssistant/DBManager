"""
WordDictionaryRepository

word_dictionary 테이블을 담당하는 Repository.
word 자체가 PK다 (별도 id 없음).
"""

from typing import Optional

from ai_rag_comm.interface import BaseDatabaseInterface


class WordDictionaryRepository(BaseDatabaseInterface):
    """
    word_dictionary 테이블 전담 Repository.
    """

    async def select_one(self, **kwargs) -> Optional[dict]:
        """
        단어 하나를 정확히 일치하는 것만 검색한다 (부분일치 아님).

        필수 kwargs: word (str)
        반환: {"word": ..., "replacement": ...} 또는 None
        """
        word = kwargs["word"]
        query = "SELECT * FROM search_word($1::text)"
        return await self._fetch_one(query, word)

    async def select_many(self, **kwargs) -> list[dict]:
        """
        등록된 단어 전체를 조회한다 (전체검색).

        반환: list[dict], 각 dict 키: word, replacement
        """
        query = "SELECT * FROM list_all_words()"
        return await self._fetch_many(query)

    async def insert(self, **kwargs) -> Optional[dict]:
        """
        새 단어/대체어 쌍을 등록한다.

        필수 kwargs: word (str), replacement (str)
        반환: {"word": ..., "replacement": ...}
        """
        word = kwargs["word"]
        replacement = kwargs["replacement"]
        query = "SELECT * FROM insert_word($1::text, $2::text)"
        return await self._fetch_one(query, word, replacement)

    async def update(self, **kwargs) -> Optional[dict]:
        """
        기존 단어(word)를 찾아서, 그 대체어(replacement)만 수정한다.
        word 자체가 PK라서 word 값 자체를 바꾸는 기능은 제공하지 않는다.

        필수 kwargs: word (str), new_replacement (str)
        반환: {"word": ..., "replacement": ...} 또는 해당 word가 없으면 None
        """
        word = kwargs["word"]
        new_replacement = kwargs["new_replacement"]
        query = "SELECT * FROM update_word($1::text, $2::text)"
        return await self._fetch_one(query, word, new_replacement)

    async def delete(self, **kwargs) -> bool:
        """
        현재 요구사항에는 삭제 기능이 없다.
        """
        raise NotImplementedError("word_dictionary는 현재 삭제 기능을 제공하지 않음")
