-- ================================================
-- user_permissions.sql
-- ================================================
-- 역할(admin/user)과 별개로 계정마다 켜고 끄는 권한.
-- 관리자는 역할과 상관없이 모든 권한을 가진 것으로 본다(화면·서버가 판단) — 여기에는
-- 일반 사용자에게 따로 준 권한만 저장한다.
--
-- 권한 이름
--   document_input : 문서 정보 입력 (문서 등록(비정형) 화면)

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id    uuid        NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    permission text        NOT NULL CHECK (permission IN ('document_input')),
    granted_by uuid        REFERENCES users(user_id),
    granted_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, permission)
);


-- 전체 권한 목록 (p_user_id 를 주면 그 사람 것만)
CREATE OR REPLACE FUNCTION list_user_permissions(p_user_id uuid DEFAULT NULL)
RETURNS TABLE (user_id uuid, permission text)
LANGUAGE sql STABLE AS $$
    SELECT p.user_id, p.permission FROM user_permissions p
    WHERE p_user_id IS NULL OR p.user_id = p_user_id
    ORDER BY p.user_id, p.permission;
$$;


-- 권한 주기/회수. 호출자가 관리자일 때만. update_user_role 과 같은 {success, message} 모양
CREATE OR REPLACE FUNCTION set_user_permission(
    p_admin_user_id uuid, p_target_user_id uuid, p_permission text, p_enabled boolean)
RETURNS TABLE (success boolean, message text)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE users.user_id = p_admin_user_id AND role = 'admin') THEN
        RETURN QUERY SELECT false, '관리자만 권한을 바꿀 수 있습니다.';
        RETURN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM users WHERE users.user_id = p_target_user_id) THEN
        RETURN QUERY SELECT false, '대상 계정이 없습니다.';
        RETURN;
    END IF;

    IF p_enabled THEN
        INSERT INTO user_permissions (user_id, permission, granted_by)
        VALUES (p_target_user_id, p_permission, p_admin_user_id)
        ON CONFLICT (user_id, permission) DO NOTHING;
    ELSE
        DELETE FROM user_permissions
        WHERE user_permissions.user_id = p_target_user_id AND permission = p_permission;
    END IF;
    RETURN QUERY SELECT true, '권한을 변경했습니다.';
END;
$$;
