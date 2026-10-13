-- ================================================
-- api_data_meta.sql
-- ================================================
-- 외부 API 등록(정형)의 추가 정보 — 제공 기관, 기준 연도, 설명.
-- 검색 벡터를 만들 때 제목·소스와 함께 넣어 "2025년 취업 현황" 같은 질의에 걸리게 하고,
-- 답변 프롬프트의 외부 데이터 목록에도 싣는다.
--
-- api_datas 는 정의가 운영 DB 에만 있어 컬럼을 더하지 않고 표를 따로 둔다(url 로 1:1).
-- API 를 지우면 같이 지워진다(ON DELETE CASCADE). 다시 실행해도 안전하다.

CREATE TABLE IF NOT EXISTS api_data_meta (
    url         text        PRIMARY KEY REFERENCES api_datas(url) ON DELETE CASCADE,
    provider    text,
    base_year   integer,
    description text,
    updated_at  timestamptz NOT NULL DEFAULT now()
);


-- 저장(있으면 덮어쓴다). 빈 문자열은 NULL 로.
CREATE OR REPLACE FUNCTION save_api_data_meta(
    p_url text, p_provider text, p_base_year integer, p_description text)
RETURNS SETOF api_data_meta
LANGUAGE sql AS $$
    INSERT INTO api_data_meta (url, provider, base_year, description)
    VALUES (p_url, NULLIF(btrim(COALESCE(p_provider, '')), ''), p_base_year,
            NULLIF(btrim(COALESCE(p_description, '')), ''))
    ON CONFLICT (url) DO UPDATE
        SET provider = EXCLUDED.provider, base_year = EXCLUDED.base_year,
            description = EXCLUDED.description, updated_at = now()
    RETURNING *;
$$;


-- 전체 목록
CREATE OR REPLACE FUNCTION list_api_data_meta()
RETURNS SETOF api_data_meta
LANGUAGE sql STABLE AS $$
    SELECT * FROM api_data_meta;
$$;
