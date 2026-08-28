# DB Manager 사용법

DB 관련 작업(세션, 메시지, API 키, 공공데이터,단어사전)을 처리하는 모듈.
파이썬 클래스로 바로 호출해서 쓴다.

## 설치 방법

이 프로젝트는 `pyproject.toml` 기준으로 의존성을 관리한다. 아래 명령어로 설치한다:

```bash
pip install -e .
```

이 한 줄로 `ai_rag_comm`, `session_data`, `api-data`를 포함한 모든 의존성이 자동으로 설치된다.
(참고: `requirements.txt`는 더 이상 사용하지 않는다.)

## 기본 사용법

```python
from db_manager import DBManager

manager = DBManager()
manager.init()     # 처음 한 번만 호출 (DB 연결 준비, handlers 구성)

result = manager.call("작업이름", 필요한_인자=값, ...)

manager.close()    # 다 쓰고 나면 호출 (DB 연결 정리)
```

- `init()`을 호출하기 전에 `call()`을 부르면 `RuntimeError`가 발생한다.
- `call()`에 등록되지 않은 작업 이름을 넣으면 `ValueError`가 발생한다.
- Repository 쪽에서 발생한 예외는 감싸지 않고 그대로 전파된다.

## 사용 가능한 작업 목록

`db_manager.py`의 `handlers` 딕셔너리에 등록된 15개 작업이다.

## 세션 관리

### `get_or_create_session`
- **하는 일**: 기존 세션을 이어가거나, 없으면(또는 타임아웃 지났으면) 새로 만든다 (get-or-create).
- **필수 인자**: `user_id (str)`
- **선택 인자**: `timeout_minutes (int, 기본 30)`
- **반환값 예시**: `{"session_id": ...}` 또는 `None`

### `list_sessions`
- **하는 일**: 특정 사용자의 세션 목록을 최근 활동순으로 반환한다.
- **필수 인자**: `user_id (str)`
- **반환값**: `list[dict]`, 각 dict 키: `session_id, user_id, created_at, updated_at, overall_summary`

### `update_overall_summary`
- **하는 일**: 세션 전체 요약(`overall_summary`)을 갱신한다.
- **필수 인자**: `session_id (str)`, `summary (str)`
- **반환값**: 갱신된 세션 row (dict), 키: `session_id, user_id, created_at, updated_at, overall_summary`

### `get_session_context`
- **하는 일**: 세션의 전체 요약(`overall_summary`)과 현재 토픽(`current_topic`)을 한 번에 조회한다. LLM 프롬프트 조립 시 "장기 기억"으로 쓰기 위한 조회 전용 작업이다.
- **필수 인자**: `session_id (str)`
- **반환값 예시**: `{"overall_summary": ..., "current_topic": ...}` 또는 `None`

### `update_current_topic`
- **하는 일**: 지금 이 순간 얘기 중인 주제(`current_topic`)를 갱신한다. `overall_summary`(전체 누적 요약)와는 별개로 짧은 주제 라벨만 덮어쓴다.
- **필수 인자**: `session_id (str)`, `topic (str)`
- **반환값**: 갱신된 세션 row (dict), 키: `session_id, user_id, created_at, updated_at, overall_summary, current_topic`

### `update_session_title`
- **하는 일**: 세션의 제목(`title`)을 갱신한다. ChatGPT 대화목록 제목처럼 짧은 제목이다.
- **필수 인자**: `session_id (str)`, `title (str)`
- **반환값**: 갱신된 세션 row (dict)

## 메시지 관리

### `insert_message`
- **하는 일**: 메시지를 저장하고 순번(`turn_index`)을 자동 채번한다.
- **필수 인자**: `session_id (str)`, `user_query (str)`, `ai_response (str)`
- **반환값 예시**: `{"out_message_id": ..., "out_turn_index": ...}` 또는 `None`

### `get_recent_messages`
- **하는 일**: 세션 내 최근 N개 대화를, 오래된 순으로 정렬해서 반환한다.
- **필수 인자**: `session_id (str)`
- **선택 인자**: `limit_count (int, 기본 5)`
- **반환값**: `list[dict]`

## 사용자 인증

### `login`
- **하는 일**: 로그인 아이디+비밀번호를 검증한다. 일치하면 사용자 정보를 반환하고, 일치하지 않으면 `None`을 반환한다.
- **필수 인자**: `login_id (str)`, `password (str)`
- **반환값 예시**: `{"user_id": ..., "name": ..., "login_id": ..., "role": ...}` 또는 `None`

### `create_user_account`
- **하는 일**: 새 계정을 생성한다 (회원가입이 아니라 관리자가 미리 만들어두는 용도). 비밀번호는 DB 쪽에서 자동으로 암호화되어 저장된다.
- **필수 인자**: `name (str)`, `login_id (str)`, `password (str)`
- **선택 인자**: `role (str, 기본 "user", "admin" 또는 "user"만 허용)`
- **반환값 예시**: `{"user_id": ..., "name": ..., "login_id": ..., "role": ...}`

## 문서등록 관리

### `register_document`
- **하는 일**: 문서를 documents 테이블에 등록하고, 함께 넘어온 분류값(업무구분/수행업무/수행부서/보고서명)을 각각의 옵션 테이블에도 upsert한다 (이미 있으면 무시, 없으면 추가).
- **필수 인자**: `production_year (int)`, `work_category (str, None 가능)`, `p_task_name (str, None 가능)`, `department (str, None 가능)`, `report_type (str, None 가능)`, `file_path (str)`
- **선택 인자**: `registered_at (str, 기본 오늘 날짜)`
- **반환값 예시**: `{"id": ..., "filename": ...}`

### `get_document`
- **하는 일**: 문서를 id로 단건 조회한다.
- **필수 인자**: `id (int)`
- **반환값**: `dict` 또는 결과 없으면 `None`. 키: `id, filename, file_path, production_year, work_category, task_name, department, report_type, registered_at`

### `list_documents`
- **하는 일**: 최근 등록순으로 문서 목록을 페이지네이션해서 조회한다.
- **선택 인자**: `limit (int, 기본 50)`, `offset (int, 기본 0)`
- **반환값**: `list[dict]`, 각 dict 키는 `get_document`와 동일

### `search_documents_by_filename`
- **하는 일**: 파일명(파일 경로의 마지막 부분) 기준으로 부분일치 검색한다.
- **필수 인자**: `query (str)`
- **반환값**: `list[dict]`, 키: `id, filename, file_path, registered_at`

### `update_document`
- **하는 일**: 문서의 분류 필드(생산연도/업무구분/수행업무/수행부서/보고서명)를 수정한다. 존재하지 않는 id로 호출하면 예외가 발생한다.
- **필수 인자**: `id (int)`, `production_year (int)`, `work_category (str, None 가능)`, `p_task_name (str, None 가능)`, `department (str, None 가능)`, `report_type (str, None 가능)`
- **반환값**: 수정된 문서의 id (`int`)

### `delete_document`
- **하는 일**: 문서를 id로 삭제한다. 존재하지 않는 id로 호출하면 예외가 발생한다.
- **필수 인자**: `id (int)`
- **반환값**: 삭제된 문서의 id (`int`)

## 문서등록_ㄸ문서 옵션 관리

### `get_work_category_options`
- **하는 일**: 업무구분 드롭다운 후보 목록을 조회한다 (엑셀 원본 값으로 미리 시드되어 있고, `register_document` 호출 시 새 값이 자동으로 추가된다).
- **필수 인자**: 없음
- **반환값**: `list[str]` (정렬된 값 목록)

### `get_task_name_options`
- **하는 일**: 수행업무 드롭다운 후보 목록을 조회한다.
- **필수 인자**: 없음
- **반환값**: `list[str]`

### `get_department_options`
- **하는 일**: 수행부서 드롭다운 후보 목록을 조회한다.
- **필수 인자**: 없음
- **반환값**: `list[str]`

### `get_report_type_options`
- **하는 일**: 보고서명 드롭다운 후보 목록을 조회한다.
- **필수 인자**: 없음
- **반환값**: `list[str]`

## 공공데이터 관리

### `insert_api_data`
- **하는 일**: 새 공공데이터를 등록한다.
- **필수 인자**: `title (str)`, `url (str)`, `source (str)`, `key (str)`, `data (str)`, `data_type (str)`
- **반환값 예시**: `{"title": ..., "url": ..., "source": ..., "key": ..., "data": ..., "data_type": ..., "date": ...}`
- **호출 예시**:
  ```python
  result = manager.call(
      "insert_api_data",
      title="테스트",
      url="http://test.com",
      source="테스트소스",
      key="testkey",
      data="원본데이터",
      data_type="json",
  )
  ```

### `select_all_api_data`
- **하는 일**: 전체 공공데이터 목록을 최신순으로 반환한다.
- **필수 인자**: 없음
- **반환값**: `list[dict]`, 각 dict 키: `title, url, source, key, data, data_type, date`
- **호출 예시**:
  ```python
  result = manager.call("select_all_api_data")
  ```

### `update_api_data_date`
- **하는 일**: url로 찾아서 data(응답 원문)를 갱신한다. date도 자동으로 현재시각으로 갱신된다.
- **필수 인자**: `url (str)`, `data (str)`
- **반환값**: `{"title": ..., "success": True/False}` — 해당 url이 없으면
  `{"title": None, "success": False}`
- **호출 예시**:
  ```python
  result = manager.call("update_api_data_date", url="http://test.com", data="갱신된데이터")
  ```

### `delete_api_data`
- **하는 일**: url로 공공데이터를 삭제한다.
- **필수 인자**: `url (str)`
- **반환값**: 성공하면 True, 해당 url이 없으면 False
- **호출 예시**:
  ```python
  result = manager.call("delete_api_data", url="http://test.com")
  ```

## 단어사전 관리

### `search_word`
- **하는 일**: 단어를 정확히 일치하는 것만 검색한다 (부분일치 안 됨).
- **필수 인자**: `word (str)`
- **반환값**: `{"word": ..., "replacement": ...}` 또는 결과 없으면 None

### `list_all_words`
- **하는 일**: 등록된 단어/대체어 전체 목록을 조회한다.
- **필수 인자**: 없음
- **반환값**: list of dict

### `insert_word`
- **하는 일**: 새 단어/대체어 쌍을 등록한다.
- **필수 인자**: `word (str)`, `replacement (str)`
- **반환값**: 등록된 row (dict), 키: `word, replacement`

### `update_word`
- **하는 일**: 기존 단어(word)를 찾아서 그 대체어(replacement)만 수정한다.
- **필수 인자**: `word (str)`, `new_replacement (str)`
- **반환값**: 수정된 row (dict) 또는 해당 word가 없으면 None

## 주의사항

- `overall_summary`, `current_topic`을 실제로 언제 갱신할지는 이 모듈이 정하지 않는다 (호출하는 쪽에서 판단해서 `update_overall_summary`/`update_current_topic`을 부르면 됨).
- `manager.call()`에서 존재하지 않는 작업 이름을 넣으면 `ValueError`가 발생한다.
- DB 처리 중 에러가 나면 예외가 그대로 발생한다 (별도로 감싸서 처리하지 않음).
