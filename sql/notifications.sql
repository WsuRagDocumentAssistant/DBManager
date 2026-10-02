-- ================================================
-- notifications.sql
-- ================================================
-- 사용자 알림. 상단 종 아이콘 목록이 이 테이블을 읽는다.
-- 서버가 만드는 것(문서 색인 완료·실패, 기능 개선 요청 답변)과 화면 작업 결과(검색어 저장 등)를
-- 모두 여기 둔다 — 브라우저를 바꾸거나 닫았다 열어도 같은 알림이 보인다.

CREATE TABLE IF NOT EXISTS notifications (
    id         bigserial   PRIMARY KEY,
    user_id    uuid        NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    message    text        NOT NULL,
    type       text        NOT NULL DEFAULT 'info' CHECK (type IN ('success', 'error', 'info')),
    link       text,
    created_at timestamptz NOT NULL DEFAULT now(),
    read_at    timestamptz
);

CREATE INDEX IF NOT EXISTS notifications_user_idx ON notifications (user_id, created_at DESC);


-- 알림 하나 만들기
CREATE OR REPLACE FUNCTION insert_notification(
    p_user_id uuid, p_message text, p_type text, p_link text)
RETURNS SETOF notifications
LANGUAGE sql AS $$
    INSERT INTO notifications (user_id, message, type, link)
    VALUES (p_user_id, p_message, COALESCE(p_type, 'info'), p_link)
    RETURNING *;
$$;


-- 내 알림 최신순 p_limit 개
CREATE OR REPLACE FUNCTION list_notifications(p_user_id uuid, p_limit integer)
RETURNS SETOF notifications
LANGUAGE sql STABLE AS $$
    SELECT * FROM notifications
    WHERE user_id = p_user_id
    ORDER BY created_at DESC, id DESC
    LIMIT p_limit;
$$;


-- 읽음 처리. p_ids 가 NULL 이면 내 알림 전부. 남의 알림은 건드리지 않는다. 바꾼 개수를 돌려준다
CREATE OR REPLACE FUNCTION mark_notifications_read(p_user_id uuid, p_ids bigint[])
RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    n integer;
BEGIN
    UPDATE notifications SET read_at = now()
    WHERE user_id = p_user_id AND read_at IS NULL
      AND (p_ids IS NULL OR id = ANY(p_ids));
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$;


-- 오래된 알림 정리: 사용자마다 최신 p_keep 개만 남긴다. 지운 개수를 돌려준다
CREATE OR REPLACE FUNCTION prune_notifications(p_keep integer)
RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    n integer;
BEGIN
    DELETE FROM notifications WHERE id IN (
        SELECT id FROM (
            SELECT id, row_number() OVER (PARTITION BY user_id ORDER BY created_at DESC, id DESC) AS rn
            FROM notifications
        ) ranked WHERE rn > p_keep
    );
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$;
