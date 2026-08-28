"""
test_documents.py
==================

documents 관련 기능(register_document / get_document / list_documents /
search_documents_by_filename / update_document / delete_document / 드롭다운 옵션
조회)이 실제 DB에 대해 정상 동작하는지 확인하는 통합 테스트 스크립트.

실행 방법: 저장소 루트에서 `python test_documents.py`

참고: db_manager.py의 handlers 딕셔너리를 직접 확인한 결과, "get_dropdown_options"라는
이름의 단일 handler는 등록돼 있지 않다. 대신 업무구분/수행업무/수행부서/보고서명별로
분리된 4개의 handler(get_work_category_options / get_task_name_options /
get_department_options / get_report_type_options)가 각각 파라미터 없이 자기 카테고리의
list[str]만 반환하는 형태로 등록돼 있다. 아래 테스트는 이 실제 이름/형태 기준으로 작성됨.
"""

from db_manager import DBManager

TEST_FILE_PATH = "/uploads/2026/99/__integration_test__.pdf"
TEST_FILENAME = "__integration_test__.pdf"


def main():
    manager = DBManager()
    manager.init()

    failed = False
    document_id = None
    deleted = False

    try:
        # ============================================================
        # 1. 드롭다운 옵션 4종 조회 (파라미터 없이)
        # ============================================================
        try:
            work_category_options = manager.call("get_work_category_options")
            task_name_options = manager.call("get_task_name_options")
            department_options = manager.call("get_department_options")
            report_type_options = manager.call("get_report_type_options")

            assert isinstance(work_category_options, list)
            assert isinstance(task_name_options, list)
            assert isinstance(department_options, list)
            assert isinstance(report_type_options, list)
            assert len(work_category_options) >= 5, f"work_category 시드 데이터 부족: {len(work_category_options)}건"
            assert len(department_options) >= 89, f"department 시드 데이터 부족: {len(department_options)}건"

            print(
                "[OK] 1. 드롭다운 옵션 4종 조회: "
                f"work_category={len(work_category_options)}건, "
                f"task_name={len(task_name_options)}건, "
                f"department={len(department_options)}건, "
                f"report_type={len(report_type_options)}건"
            )
        except Exception as e:
            print("[FAIL] 1. 드롭다운 옵션 4종 조회:", repr(e))
            failed = True

        # ============================================================
        # 2. work_category만 다시 조회해서 1번 결과와 개수 일치 확인
        # ============================================================
        try:
            work_category_options_again = manager.call("get_work_category_options")
            assert len(work_category_options_again) == len(work_category_options)
            print(f"[OK] 2. get_work_category_options 재호출 개수 일치: {len(work_category_options_again)}건")
        except Exception as e:
            print("[FAIL] 2. get_work_category_options 재호출 개수 일치:", repr(e))
            failed = True

        # ============================================================
        # 3. register_document (분류값에 앞뒤 공백 섞어서 등록)
        # ============================================================
        try:
            register_result = manager.call(
                "register_document",
                production_year=2026,
                work_category="  재정지원사업  ",
                p_task_name="  SW 중심대학사업  ",
                department="  기획처  ",
                report_type="  실적보고서  ",
                file_path=TEST_FILE_PATH,
            )
            document_id = register_result["id"]
            assert register_result["filename"] == TEST_FILENAME, (
                f"filename이 file_path에서 정확히 추출되지 않음: {register_result['filename']!r}"
            )
            print(f"[OK] 3. register_document: id={document_id}, filename={register_result['filename']!r}")
        except Exception as e:
            print("[FAIL] 3. register_document:", repr(e))
            failed = True

        # ============================================================
        # 4. get_document로 방금 등록한 문서 조회 (트림 확인)
        # ============================================================
        if document_id is not None:
            try:
                doc = manager.call("get_document", id=document_id)
                assert doc is not None, "방금 등록한 문서가 조회되지 않음"
                assert doc["work_category"] == "재정지원사업", (
                    f"work_category가 트림되지 않음: {doc['work_category']!r}"
                )
                print(f"[OK] 4. get_document (트림 확인): {doc}")
            except Exception as e:
                print("[FAIL] 4. get_document (트림 확인):", repr(e))
                failed = True
        else:
            print("[FAIL] 4. get_document (트림 확인): 3번에서 document_id를 얻지 못해 건너뜀")
            failed = True

        # ============================================================
        # 5. list_documents로 목록 조회 (방금 등록한 문서 포함 여부)
        # ============================================================
        if document_id is not None:
            try:
                documents = manager.call("list_documents")
                ids = [d["id"] for d in documents]
                assert document_id in ids, f"list_documents 결과에 id={document_id}가 없음"
                print(f"[OK] 5. list_documents: {len(documents)}건 중 id={document_id} 포함 확인")
            except Exception as e:
                print("[FAIL] 5. list_documents:", repr(e))
                failed = True
        else:
            print("[FAIL] 5. list_documents: document_id가 없어 건너뜀")
            failed = True

        # ============================================================
        # 6. search_documents_by_filename으로 파일명 검색
        # ============================================================
        if document_id is not None:
            try:
                search_results = manager.call("search_documents_by_filename", query="__integration_test__")
                ids = [d["id"] for d in search_results]
                assert document_id in ids, f"search_documents_by_filename 결과에 id={document_id}가 없음"
                print(f"[OK] 6. search_documents_by_filename: {len(search_results)}건 중 id={document_id} 포함 확인")
            except Exception as e:
                print("[FAIL] 6. search_documents_by_filename:", repr(e))
                failed = True
        else:
            print("[FAIL] 6. search_documents_by_filename: document_id가 없어 건너뜀")
            failed = True

        # ============================================================
        # 7. update_document로 수정 (공백 섞어서) 후 다시 조회해서 트림 확인
        # ============================================================
        if document_id is not None:
            try:
                updated_id = manager.call(
                    "update_document",
                    id=document_id,
                    production_year=2027,
                    work_category="  수정된분류  ",
                    p_task_name="  수정된업무  ",
                    department="  수정된부서  ",
                    report_type="  수정된보고서  ",
                )
                assert updated_id == document_id, f"update_document 반환 id 불일치: {updated_id}"

                doc_after_update = manager.call("get_document", id=document_id)
                assert doc_after_update["work_category"] == "수정된분류", (
                    f"수정 후 work_category가 트림되지 않음: {doc_after_update['work_category']!r}"
                )
                assert doc_after_update["production_year"] == 2027
                print(f"[OK] 7. update_document + 재조회 (트림 확인): {doc_after_update}")
            except Exception as e:
                print("[FAIL] 7. update_document + 재조회 (트림 확인):", repr(e))
                failed = True
        else:
            print("[FAIL] 7. update_document + 재조회: document_id가 없어 건너뜀")
            failed = True

        # ============================================================
        # 8. 존재하지 않는 id로 update_document 호출 → 예외 발생 확인
        # ============================================================
        try:
            manager.call(
                "update_document",
                id=999999999,
                production_year=2026,
                work_category=None,
                p_task_name=None,
                department=None,
                report_type=None,
            )
            print("[FAIL] 8. 존재하지 않는 id로 update_document: 예외가 발생하지 않음")
            failed = True
        except Exception as e:
            print(f"[OK] 8. 존재하지 않는 id로 update_document: 예상대로 예외 발생 ({e!r})")

        # ============================================================
        # 9. delete_document로 삭제 후 get_document로 재조회 (None 확인)
        # ============================================================
        if document_id is not None:
            try:
                deleted_id = manager.call("delete_document", id=document_id)
                assert deleted_id == document_id, f"delete_document 반환 id 불일치: {deleted_id}"
                deleted = True

                doc_after_delete = manager.call("get_document", id=document_id)
                assert doc_after_delete is None, f"삭제 후에도 문서가 조회됨: {doc_after_delete}"
                print(f"[OK] 9. delete_document + 재조회(None 확인): deleted_id={deleted_id}")
            except Exception as e:
                print("[FAIL] 9. delete_document + 재조회(None 확인):", repr(e))
                failed = True
        else:
            print("[FAIL] 9. delete_document: document_id가 없어 건너뜀")
            failed = True

    finally:
        # ============================================================
        # 10. 정리 — 테스트용 문서가 DB에 남지 않도록 보장
        # ============================================================
        if document_id is not None and not deleted:
            try:
                manager.call("delete_document", id=document_id)
                print(f"[OK] 10. cleanup: 잔여 테스트 문서 삭제 완료 (id={document_id})")
            except Exception as e:
                print(f"[FAIL] 10. cleanup: 잔여 테스트 문서(id={document_id}) 삭제 실패:", repr(e))
                failed = True
        else:
            print("[OK] 10. cleanup: 정리할 잔여 테스트 문서 없음")

        manager.close()

    print()
    if failed:
        print("결과: 하나 이상의 단계에서 실패했습니다. 위 [FAIL] 항목을 확인하세요.")
    else:
        print("결과: 모든 단계 통과.")


if __name__ == "__main__":
    main()
