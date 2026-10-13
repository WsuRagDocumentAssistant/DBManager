-- ================================================
-- external_documents.sql
-- ================================================
-- 외부 문서 표시. 문서 등록 화면이 둘이다 — 내부 문서 등록(메타데이터 입력) / 외부 문서 등록(메타데이터 없음).
-- 색인·검색·뷰어는 같은 documents 를 쓰고, 이 표에 id 가 있으면 외부 문서다.
--
-- documents 테이블은 정의가 운영 DB 에만 있어 컬럼을 더하지 않고 표를 따로 둔다.
-- 문서 행이 지워지면 같이 지워진다(ON DELETE CASCADE). 다시 실행해도 안전하다.

CREATE TABLE IF NOT EXISTS external_documents (
    document_id bigint      PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    created_at  timestamptz NOT NULL DEFAULT now()
);


-- 외부 문서로 표시하거나(p_external = true) 표시를 뗀다(false — 같은 파일을 내부 문서로 다시 올린 경우).
CREATE OR REPLACE FUNCTION set_external_document(p_document_id bigint, p_external boolean)
RETURNS boolean
LANGUAGE plpgsql AS $$
BEGIN
    IF p_external THEN
        INSERT INTO external_documents (document_id) VALUES (p_document_id)
        ON CONFLICT (document_id) DO NOTHING;
    ELSE
        DELETE FROM external_documents WHERE document_id = p_document_id;
    END IF;
    RETURN true;
END;
$$;


-- 외부 문서 id 목록
CREATE OR REPLACE FUNCTION list_external_documents()
RETURNS TABLE (document_id bigint)
LANGUAGE sql STABLE AS $$
    SELECT document_id FROM external_documents ORDER BY document_id;
$$;
