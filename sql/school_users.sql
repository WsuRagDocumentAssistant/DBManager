-- ================================================
-- school_users.sql
-- ================================================
-- 학교 Oracle 사용자 뷰(WS_VIEW.AIKEY_USER_V)의 사본 테이블과 DB 함수. 교직원만 담는다(학생 제외 —
-- 거르는 건 동기화가 읽을 때 SchoolViewRepository 가 한다).
-- 타이머가 주기적으로 뷰 전체를 읽어 sync_school_users 로 통째로 맞춘다.
-- 관리자 화면(소속 표시·사용자 검색)은 학교 DB 대신 이 사본을 읽는다.
--
-- 비밀번호(PWD)는 복사하지 않는다.

CREATE TABLE IF NOT EXISTS school_users (
    user_id    text        PRIMARY KEY,   -- 학번/교번
    name       text,
    department text,                      -- 소속
    college    text,
    status     text,                      -- 학생/교원/직원
    email      text,
    synced_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS school_users_email_idx ON school_users (lower(email));


-- 뷰 전체(jsonb 배열)로 사본을 맞춘다. 새 행은 넣고, 있던 행은 갱신하고, 뷰에서 사라진 행은 지운다.
-- 함수 하나가 한 트랜잭션이라 도중에 실패하면 이전 사본이 그대로 남는다. 반영한 행 수를 돌려준다.
CREATE OR REPLACE FUNCTION sync_school_users(p_rows jsonb)
RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    n integer;
BEGIN
    INSERT INTO school_users (user_id, name, department, college, status, email, synced_at)
    SELECT r->>'user_id', r->>'name', r->>'department', r->>'college', r->>'status', r->>'email', now()
    FROM jsonb_array_elements(p_rows) r
    ON CONFLICT (user_id) DO UPDATE
    SET name = EXCLUDED.name, department = EXCLUDED.department, college = EXCLUDED.college,
        status = EXCLUDED.status, email = EXCLUDED.email, synced_at = EXCLUDED.synced_at;
    GET DIAGNOSTICS n = ROW_COUNT;

    DELETE FROM school_users
    WHERE user_id NOT IN (SELECT r->>'user_id' FROM jsonb_array_elements(p_rows) r);

    RETURN n;
END;
$$;


-- 학번/교번·이름·소속에 keyword 가 들어간 사용자 (이름순)
CREATE OR REPLACE FUNCTION search_school_users(p_keyword text, p_limit integer)
RETURNS SETOF school_users
LANGUAGE sql STABLE AS $$
    SELECT * FROM school_users
    WHERE user_id ILIKE '%' || p_keyword || '%'
       OR name ILIKE '%' || p_keyword || '%'
       OR department ILIKE '%' || p_keyword || '%'
    ORDER BY name
    LIMIT p_limit;
$$;


-- 사본 상태: 행 수와 마지막 동기화 시각. 관리자 화면이 "동기화 전" 과 "검색 결과 없음" 을 구분한다
CREATE OR REPLACE FUNCTION school_users_status()
RETURNS TABLE (count bigint, synced_at timestamptz)
LANGUAGE sql STABLE AS $$
    SELECT count(*), max(synced_at) FROM school_users;
$$;


-- 학번/교번 또는 이메일(대소문자 무시) 목록에 해당하는 사용자
CREATE OR REPLACE FUNCTION get_school_users(p_ids text[])
RETURNS SETOF school_users
LANGUAGE sql STABLE AS $$
    SELECT * FROM school_users
    WHERE user_id = ANY(p_ids)
       OR lower(email) IN (SELECT lower(x) FROM unnest(p_ids) x);
$$;
