-- ================================================
-- document_uploads.sql
-- ================================================
-- 문서를 누가, 어느 등록에서 올렸는지. 내부 문서 등록 화면이 "내가 마지막으로 등록한 문서"만
-- 보여 주는 데 쓴다(문서 목록 화면은 그대로 전체).
--
-- batch_id 는 등록 버튼 한 번에 같이 올린 문서 묶음이다(클라이언트가 만들어 보낸다).
-- 같은 파일을 다시 올리면 문서 행이 그대로라(source_path) 올린 사람·묶음을 새 값으로 덮는다.
--
-- documents 테이블은 정의가 운영 DB 에만 있어 컬럼을 더하지 않고 표를 따로 둔다.
-- 문서 행이 지워지면 같이 지워진다(ON DELETE CASCADE). 다시 실행해도 안전하다.

CREATE TABLE IF NOT EXISTS document_uploads (
    document_id bigint      PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    user_id     uuid        NOT NULL,
    batch_id    text,
    uploaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_uploads_user_idx ON document_uploads (user_id, uploaded_at DESC);


-- 올린 사람·묶음 기록(있으면 덮어쓴다)
CREATE OR REPLACE FUNCTION save_document_upload(p_document_id bigint, p_user_id uuid, p_batch_id text)
RETURNS SETOF document_uploads
LANGUAGE sql AS $$
    INSERT INTO document_uploads (document_id, user_id, batch_id)
    VALUES (p_document_id, p_user_id, NULLIF(btrim(COALESCE(p_batch_id, '')), ''))
    ON CONFLICT (document_id) DO UPDATE
        SET user_id = EXCLUDED.user_id, batch_id = EXCLUDED.batch_id, uploaded_at = now()
    RETURNING *;
$$;


-- 전체 기록
CREATE OR REPLACE FUNCTION list_document_uploads()
RETURNS SETOF document_uploads
LANGUAGE sql STABLE AS $$
    SELECT * FROM document_uploads;
$$;
