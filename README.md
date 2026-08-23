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

`db_manager.py`의 `handlers` 딕셔너리에 등록된 14개 작업이다.

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

### `insert_message`
- **하는 일**: 메시지를 저장하고 순번(`turn_index`)을 자동 채번한다.
- **필수 인자**: `session_id (str)`, `user_query (str)`, `ai_response (str)`
- **반환값 예시**: `{"out_message_id": ..., "out_turn_index": ...}` 또는 `None`

### `get_recent_messages`
- **하는 일**: 세션 내 최근 N개 대화를, 오래된 순으로 정렬해서 반환한다.
- **필수 인자**: `session_id (str)`
- **선택 인자**: `limit_count (int, 기본 5)`
- **반환값**: `list[dict]`

### `get_session_context`
- **하는 일**: 세션의 전체 요약(`overall_summary`)과 현재 토픽(`current_topic`)을 한 번에 조회한다. LLM 프롬프트 조립 시 "장기 기억"으로 쓰기 위한 조회 전용 작업이다.
- **필수 인자**: `session_id (str)`
- **반환값 예시**: `{"overall_summary": ..., "current_topic": ...}` 또는 `None`

### `update_current_topic`
- **하는 일**: 지금 이 순간 얘기 중인 주제(`current_topic`)를 갱신한다. `overall_summary`(전체 누적 요약)와는 별개로 짧은 주제 라벨만 덮어쓴다.
- **필수 인자**: `session_id (str)`, `topic (str)`
- **반환값**: 갱신된 세션 row (dict), 키: `session_id, user_id, created_at, updated_at, overall_summary, current_topic`

### `get_api_data`
- **하는 일**: 공공데이터를 id로 단건 조회한다.
- **필수 인자**: `id (int)`
- **반환값**: `dict` 또는 `None`

### `list_api_data`
- **하는 일**: 전체 공공데이터 목록을 최신순으로 반환한다.
- **필수 인자**: 없음
- **반환값**: `list[dict]`

### `insert_api_data`
- **하는 일**: `data_pipeline`이 만든 `ApiEntity`(metadata, json)를 저장한다. `json`은 이미 직렬화된 JSON 문자열이므로 다시 직렬화하지 않고 그대로 넘겨야 한다.
- **필수 인자**: `metadata (str)`, `json (str)`
- **반환값**: 저장된 row (dict)

### `delete_api_data`
- **하는 일**: 공공데이터를 id로 삭제한다.
- **필수 인자**: `id (int)`
- **반환값**: 실제로 삭제됐으면 `True` (`bool`)

### `search_word`
- **하는 일**: 단어를 정확히 일치하는 것만 검색한다 (부분일치 안 됨).
- **필수 인자**: `word (str)`
- **반환값**: `{"id": ..., "word": ..., "replacement": ...}` 또는 결과 없으면 None

### `list_all_words`
- **하는 일**: 등록된 단어/대체어 전체 목록을 조회한다.
- **필수 인자**: 없음
- **반환값**: list of dict

### `insert_word`
- **하는 일**: 새 단어/대체어 쌍을 등록한다.
- **필수 인자**: `word (str)`, `replacement (str)`
- **반환값**: 등록된 row (dict)

## 주의사항

- `overall_summary`, `current_topic`을 실제로 언제 갱신할지는 이 모듈이 정하지 않는다 (호출하는 쪽에서 판단해서 `update_overall_summary`/`update_current_topic`을 부르면 됨).
- `manager.call()`에서 존재하지 않는 작업 이름을 넣으면 `ValueError`가 발생한다.
- DB 처리 중 에러가 나면 예외가 그대로 발생한다 (별도로 감싸서 처리하지 않음).
