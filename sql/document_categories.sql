-- ================================================
-- document_categories.sql
-- ================================================
-- 문서 등록(비정형) 화면의 입력 카테고리. 설정 관리 > 문서 카테고리 관리에서 추가·삭제한다.
--
-- 한 테이블에 네 종류를 담는다 (kind):
--   work_category : 업무구분                     parent ''
--   task          : 수행업무 (짝지어진 수행부서) parent = 업무구분, pair = 수행부서
--   department    : 수행부서                     parent = 업무구분 (수행업무 없이 부서를 고르는 업무구분)
--   report_type   : 보고서명                     parent ''
-- parent 는 NULL 대신 '' 를 써서 UNIQUE (kind, parent, value) 가 중복을 막게 한다.
--
-- 기존 *_options 테이블(문서 등록 때 자동으로 쌓이는 값)과는 별개다 — 이쪽은 관리자가 정한 선택지다.
-- 끝의 INSERT 는 지금까지 화면 코드(RagWeb shared/dummy.js)에 고정돼 있던 값이다. 다시 실행해도 안전하다.

CREATE TABLE IF NOT EXISTS document_categories (
    id         bigserial   PRIMARY KEY,
    kind       text        NOT NULL CHECK (kind IN ('work_category', 'task', 'department', 'report_type')),
    parent     text        NOT NULL DEFAULT '',
    value      text        NOT NULL CHECK (btrim(value) <> ''),
    pair       text,
    sort_order integer     NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (kind, parent, value)
);


-- 전체 목록 (종류 · 상위 · 순서대로)
CREATE OR REPLACE FUNCTION list_document_categories()
RETURNS SETOF document_categories
LANGUAGE sql STABLE AS $$
    SELECT * FROM document_categories ORDER BY kind, parent, sort_order, id;
$$;


-- 추가 또는 수정(같은 kind·parent·value 면 pair 만 바꾼다). 관리자만 — 아니면 빈 결과.
-- 새 값은 같은 묶음의 맨 뒤에 붙는다.
CREATE OR REPLACE FUNCTION save_document_category(
    p_admin_user_id uuid, p_kind text, p_parent text, p_value text, p_pair text)
RETURNS SETOF document_categories
LANGUAGE sql AS $$
    INSERT INTO document_categories (kind, parent, value, pair, sort_order)
    SELECT p_kind, COALESCE(p_parent, ''), btrim(p_value), NULLIF(btrim(COALESCE(p_pair, '')), ''),
           COALESCE((SELECT max(sort_order) + 1 FROM document_categories
                     WHERE kind = p_kind AND parent = COALESCE(p_parent, '')), 0)
    WHERE EXISTS (SELECT 1 FROM users WHERE user_id = p_admin_user_id AND role = 'admin')
    ON CONFLICT (kind, parent, value) DO UPDATE SET pair = EXCLUDED.pair
    RETURNING *;
$$;


-- 삭제. 관리자만. 업무구분을 지우면 그 아래 수행업무·수행부서도 같이 지운다. 지웠으면 true
CREATE OR REPLACE FUNCTION delete_document_category(p_admin_user_id uuid, p_id bigint)
RETURNS boolean
LANGUAGE plpgsql AS $$
DECLARE
    target document_categories;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = p_admin_user_id AND role = 'admin') THEN
        RETURN false;
    END IF;
    DELETE FROM document_categories WHERE id = p_id RETURNING * INTO target;
    IF target.id IS NULL THEN
        RETURN false;
    END IF;
    IF target.kind = 'work_category' THEN
        DELETE FROM document_categories WHERE kind IN ('task', 'department') AND parent = target.value;
    END IF;
    RETURN true;
END;
$$;


-- 초기값 (기존 화면 코드의 값)
INSERT INTO document_categories (kind, parent, value, pair, sort_order) VALUES
    ('work_category', '', '재정지원사업', NULL, 0),
    ('work_category', '', '대학평가', NULL, 1),
    ('work_category', '', '행정부서', NULL, 2),
    ('work_category', '', '행정부서(학과)', NULL, 3),
    ('work_category', '', '기타', NULL, 4),
    ('task', '재정지원사업', 'SW 중심대학사업', 'SW 중심대학사업단', 0),
    ('task', '재정지원사업', '바이오헬스(coss) 첨단분야 혁신융합대학', '바이오헬스(coss) 첨단분야 혁신융합대학 사업단', 1),
    ('task', '재정지원사업', 'CAMPUS Asia-AIMS', '엔디컷국제대학', 2),
    ('task', '재정지원사업', '대학혁신지원사업', '대학혁신지원사업단', 3),
    ('task', '재정지원사업', '글로벌철도 연수과정지원사업', '글로벌철도 연수과정지원사업단', 4),
    ('task', '재정지원사업', '첨단산업 인재양성 부트캠프(반도체)', '부트캠프 사업단', 5),
    ('task', '재정지원사업', 'RISE 사업', 'RISE 사업단', 6),
    ('task', '재정지원사업', '바이오헬스 아카데미', '바이오헬스 아카데미 사업단', 7),
    ('task', '재정지원사업', '4단계 학교기업지원사업', '외식조리학과', 8),
    ('task', '재정지원사업', '고교-대학 연계 사업', '엔디컷국제대학', 9),
    ('task', '재정지원사업', '글로벌 인재취업 선도대학사업', '취업지원센터', 10),
    ('task', '재정지원사업', '채용연계형 SW전문인재양성사업', 'SW 중심대학사업단', 11),
    ('task', '재정지원사업', '지방대학활성화사업', '지방대학활성화사업단', 12),
    ('task', '재정지원사업', 'SW개발 벤처스타트업 사업', 'SW 중심대학사업단', 13),
    ('task', '재정지원사업', 'LINC 3.0 사업', 'RISE 사업단', 14),
    ('task', '대학평가', '기관인증평가', '기획처', 0),
    ('task', '대학평가', '세계대학평가', '기획처', 1),
    ('task', '대학평가', '대학정보공시', '기획처', 2),
    ('task', '대학평가', '고등교육통계', '고등교육통계센터', 3),
    ('task', '대학평가', '대학편제단위', '기획처', 4),
    ('department', '행정부서', '기획처', NULL, 0),
    ('department', '행정부서', '대학혁신본부', NULL, 1),
    ('department', '행정부서', '고등교육평가센터', NULL, 2),
    ('department', '행정부서', 'ESG센터', NULL, 3),
    ('department', '행정부서', '인사기획처', NULL, 4),
    ('department', '행정부서', '대외협력처', NULL, 5),
    ('department', '행정부서', '교무처', NULL, 6),
    ('department', '행정부서', '대학원', NULL, 7),
    ('department', '행정부서', '교수학습개발센터', NULL, 8),
    ('department', '행정부서', '입학처', NULL, 9),
    ('department', '행정부서', '학생복지처', NULL, 10),
    ('department', '행정부서', '학생상담센터', NULL, 11),
    ('department', '행정부서', '장애학생지원센터', NULL, 12),
    ('department', '행정부서', '사회봉사단', NULL, 13),
    ('department', '행정부서', '인권센터', NULL, 14),
    ('department', '행정부서', 'RISE 혁신지원센터', NULL, 15),
    ('department', '행정부서', '국제교류처', NULL, 16),
    ('department', '행정부서', '총무처', NULL, 17),
    ('department', '행정부서', '인사관리과', NULL, 18),
    ('department', '행정부서', '시설처', NULL, 19),
    ('department', '행정부서', '산학협력단', NULL, 20),
    ('department', '행정부서', '취업지원센터', NULL, 21),
    ('department', '행정부서', '창업자원종합관리센터', NULL, 22),
    ('department', '행정부서', '유학생동문지원센터', NULL, 23),
    ('department', '행정부서', '평생교육원', NULL, 24),
    ('department', '행정부서', '우송정보센터', NULL, 25),
    ('department', '행정부서', '외국어교육원', NULL, 26),
    ('department', '행정부서', '우송IT교육센터', NULL, 27),
    ('department', '행정부서', '우송비즈니스교육센터', NULL, 28),
    ('department', '행정부서', '학생군사교육단', NULL, 29),
    ('department', '행정부서', '지역상생협력센터', NULL, 30),
    ('department', '행정부서', '동구 통합가족 지원센터', NULL, 31),
    ('department', '행정부서', '한국어교육원', NULL, 32),
    ('department', '행정부서', '현장실습지원센터', NULL, 33),
    ('department', '행정부서(학과)', '철도경영학과', NULL, 0),
    ('department', '행정부서(학과)', '철도시스템학부 철도전기시스템전공', NULL, 1),
    ('department', '행정부서(학과)', '철도시스템학부 철도소프트웨어전공', NULL, 2),
    ('department', '행정부서(학과)', '철도건설시스템학부 철도건설시스템전공', NULL, 3),
    ('department', '행정부서(학과)', '철도건설시스템학부 글로벌철도학과', NULL, 4),
    ('department', '행정부서(학과)', '철도건설시스템학부 건축공학전공', NULL, 5),
    ('department', '행정부서(학과)', '철도차량시스템학과', NULL, 6),
    ('department', '행정부서(학과)', '철도자율전공', NULL, 7),
    ('department', '행정부서(학과)', '소프트웨어학부 컴퓨터공학전공', NULL, 8),
    ('department', '행정부서(학과)', '소프트웨어학부 컴퓨터·소프트웨어전공', NULL, 9),
    ('department', '행정부서(학과)', '게임멀티미디어학부 게임소프트웨어전공', NULL, 10),
    ('department', '행정부서(학과)', '게임멀티미디어학부 게임그래픽전공', NULL, 11),
    ('department', '행정부서(학과)', '테크노미디어융합학부 미디어디자인·영상전공', NULL, 12),
    ('department', '행정부서(학과)', '테크노미디어융합학부 글로벌미디어영상학과', NULL, 13),
    ('department', '행정부서(학과)', '보건의료경영학과', NULL, 14),
    ('department', '행정부서(학과)', '물리치료학과', NULL, 15),
    ('department', '행정부서(학과)', '사회복지학과', NULL, 16),
    ('department', '행정부서(학과)', '작업치료학과', NULL, 17),
    ('department', '행정부서(학과)', '언어치료·청각재활학과', NULL, 18),
    ('department', '행정부서(학과)', '스포츠건강재활학과', NULL, 19),
    ('department', '행정부서(학과)', '유아교육과', NULL, 20),
    ('department', '행정부서(학과)', '뷰티디자인경영학과', NULL, 21),
    ('department', '행정부서(학과)', '응급구조학과', NULL, 22),
    ('department', '행정부서(학과)', '소방·안전학부', NULL, 23),
    ('department', '행정부서(학과)', '간호학과', NULL, 24),
    ('department', '행정부서(학과)', '동물관리학부 동물의료관리학과', NULL, 25),
    ('department', '행정부서(학과)', '동물관리학부 토탈펫케어학과', NULL, 26),
    ('department', '행정부서(학과)', '보건복지자율전공', NULL, 27),
    ('department', '행정부서(학과)', '외식조리학부 외식조리전공', NULL, 28),
    ('department', '행정부서(학과)', '외식조리학부 한식·조리과학전공', NULL, 29),
    ('department', '행정부서(학과)', '외식조리학부 외식,조리경영전공', NULL, 30),
    ('department', '행정부서(학과)', '외식조리학부 제과제빵·조리전공', NULL, 31),
    ('department', '행정부서(학과)', '외식조리영양학과', NULL, 32),
    ('department', '행정부서(학과)', '호텔관광경영학과', NULL, 33),
    ('department', '행정부서(학과)', '글로벌조리학부 글로벌조리전공', NULL, 34),
    ('department', '행정부서(학과)', '글로벌조리학부 Lyfe조리전공', NULL, 35),
    ('department', '행정부서(학과)', '글로벌조리학부 글로벌외식,조리경영', NULL, 36),
    ('department', '행정부서(학과)', '외식조리자율전공', NULL, 37),
    ('department', '행정부서(학과)', '휴먼디지털인터페이스학부(HADI)', NULL, 38),
    ('department', '행정부서(학과)', '솔브릿지경영학부', NULL, 39),
    ('department', '행정부서(학과)', 'AI경영학과', NULL, 40),
    ('department', '행정부서(학과)', 'AI·빅데이터학과', NULL, 41),
    ('department', '행정부서(학과)', '글로벌호스피탈리티·디지털매니지먼트학과', NULL, 42),
    ('department', '행정부서(학과)', '자유전공학부', NULL, 43),
    ('report_type', '', '신청계획서', NULL, 0),
    ('report_type', '', '수정사업계획서', NULL, 1),
    ('report_type', '', '사업계획서', NULL, 2),
    ('report_type', '', '연간보고서', NULL, 3),
    ('report_type', '', '성과보고서', NULL, 4),
    ('report_type', '', '결과보고서', NULL, 5),
    ('report_type', '', '우수사례 보고서', NULL, 6),
    ('report_type', '', '모니터링보고서', NULL, 7),
    ('report_type', '', '자체평가보고서', NULL, 8),
    ('report_type', '', '승인신청서', NULL, 9),
    ('report_type', '', '운영계획', NULL, 10),
    ('report_type', '', '시행계획', NULL, 11),
    ('report_type', '', '기타', NULL, 12)
ON CONFLICT (kind, parent, value) DO NOTHING;
