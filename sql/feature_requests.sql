-- ================================================
-- feature_requests.sql
-- ================================================
-- 기능 개선 요청 게시판 테이블과 DB 함수.
-- FeatureRequestRepository 가 부르는 함수 6개를 만든다.
--
-- [적용 전 확인] users 테이블이 user_id(uuid, PK) / name / role('admin' | 'user')
-- 컬럼을 가진다고 가정했다 (verify_login / list_users 가 돌려주는 키 기준).
-- 실제 컬럼 이름이 다르면 아래 users 참조를 맞춰서 고친다.
--
-- 권한 규칙
--   수정 : 작성자 본인만
--   삭제 : 작성자 본인 또는 관리자
--   답변 : 관리자만
-- 권한이 없으면 예외 대신 행을 돌려주지 않는다(삭제는 false).

CREATE TABLE IF NOT EXISTS feature_requests (
    id          bigserial   PRIMARY KEY,
    title       text        NOT NULL,
    content     text        NOT NULL,
    is_secret   boolean     NOT NULL DEFAULT false,
    author_id   uuid        NOT NULL REFERENCES users(user_id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    status      text        NOT NULL DEFAULT 'received'
                CHECK (status IN ('received', 'in_progress', 'done', 'rejected')),
    answer      text,
    answered_at timestamptz
);

-- 함수들이 돌려주는 행 모양. 작성자 이름을 users 에서 붙인다.
CREATE OR REPLACE VIEW feature_request_rows AS
SELECT f.id, f.title, f.content, f.is_secret, f.author_id, u.name AS author_name,
       f.created_at, f.status, f.answer, f.answered_at
FROM feature_requests f
JOIN users u ON u.user_id = f.author_id;


-- 전체 목록 (최신순)
CREATE OR REPLACE FUNCTION list_feature_requests()
RETURNS SETOF feature_request_rows
LANGUAGE sql STABLE AS $$
    SELECT * FROM feature_request_rows ORDER BY created_at DESC;
$$;


-- 한 건 조회
CREATE OR REPLACE FUNCTION get_feature_request(p_id bigint)
RETURNS SETOF feature_request_rows
LANGUAGE sql STABLE AS $$
    SELECT * FROM feature_request_rows WHERE id = p_id;
$$;


-- 새 글 등록. status 는 기본값 'received'
CREATE OR REPLACE FUNCTION insert_feature_request(
    p_author_id uuid, p_title text, p_content text, p_is_secret boolean)
RETURNS SETOF feature_request_rows
LANGUAGE sql AS $$
    WITH f AS (
        INSERT INTO feature_requests (author_id, title, content, is_secret)
        VALUES (p_author_id, p_title, p_content, p_is_secret)
        RETURNING *
    )
    SELECT f.id, f.title, f.content, f.is_secret, f.author_id, u.name,
           f.created_at, f.status, f.answer, f.answered_at
    FROM f JOIN users u ON u.user_id = f.author_id;
$$;


-- 글 수정. 작성자 본인만. status / answer 는 건드리지 않는다
CREATE OR REPLACE FUNCTION update_feature_request(
    p_id bigint, p_user_id uuid, p_title text, p_content text, p_is_secret boolean)
RETURNS SETOF feature_request_rows
LANGUAGE sql AS $$
    WITH f AS (
        UPDATE feature_requests
        SET title = p_title, content = p_content, is_secret = p_is_secret
        WHERE id = p_id AND author_id = p_user_id
        RETURNING *
    )
    SELECT f.id, f.title, f.content, f.is_secret, f.author_id, u.name,
           f.created_at, f.status, f.answer, f.answered_at
    FROM f JOIN users u ON u.user_id = f.author_id;
$$;


-- 글 삭제. 작성자 본인 또는 관리자. 지웠으면 true
CREATE OR REPLACE FUNCTION delete_feature_request(p_id bigint, p_user_id uuid)
RETURNS boolean
LANGUAGE sql AS $$
    WITH d AS (
        DELETE FROM feature_requests
        WHERE id = p_id
          AND (author_id = p_user_id
               OR EXISTS (SELECT 1 FROM users WHERE user_id = p_user_id AND role = 'admin'))
        RETURNING 1
    )
    SELECT EXISTS (SELECT 1 FROM d);
$$;


-- 상태 변경 + 답변. 관리자만.
-- p_answer 가 빈 문자열(또는 NULL)이면 상태만 바꾸고 기존 답변과 answered_at 은 그대로 둔다.
CREATE OR REPLACE FUNCTION answer_feature_request(
    p_id bigint, p_admin_user_id uuid, p_status text, p_answer text)
RETURNS SETOF feature_request_rows
LANGUAGE sql AS $$
    WITH f AS (
        UPDATE feature_requests
        SET status      = p_status,
            answer      = COALESCE(NULLIF(p_answer, ''), answer),
            answered_at = CASE WHEN NULLIF(p_answer, '') IS NULL THEN answered_at ELSE now() END
        WHERE id = p_id
          AND EXISTS (SELECT 1 FROM users WHERE user_id = p_admin_user_id AND role = 'admin')
        RETURNING *
    )
    SELECT f.id, f.title, f.content, f.is_secret, f.author_id, u.name,
           f.created_at, f.status, f.answer, f.answered_at
    FROM f JOIN users u ON u.user_id = f.author_id;
$$;
