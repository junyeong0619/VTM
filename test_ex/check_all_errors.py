import sys
import os
from dotenv import load_dotenv

# --- 1. 경로 설정 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

try:
    # --- 2. 필요한 모듈 임포트 ---
    from vectorwave import initialize_database
    from vectorwave.database.db import get_cached_client
    # 'find_recent_errors' 대신 일반 검색 함수 임포트
    from vectorwave.search.execution_search import find_executions
except ImportError as e:
    print(f"모듈 임포트 실패: {e}")
    sys.exit(1)

def check_all_invalid_input_errors():
    """
    시간 제한 없이 'INVALID_INPUT' 상태의 모든 에러를 검색합니다.
    """
    try:
        # --- 3. DB 초기화 ---
        print("데이터베이스 연결 및 초기화...")
        client = initialize_database()
        if not client:
            print("DB 연결 실패.")
            return

        print("\n" + "="*50)
        print("--- [검증: 시간제한 없는 'INVALID_INPUT' 에러 검색] ---")
        print("="*50)

        # 'find_recent_errors' 대신 'find_executions' 사용
        filters = {
            "status": "ERROR",
            "error_code": "INVALID_INPUT"
        }

        # 시간순으로 정렬 (최신순)
        all_errors = find_executions(
            filters=filters,
            sort_by="timestamp_utc",
            sort_ascending=False,
            limit=50  # 최대 50개까지
        )

        if not all_errors:
            print("  -> DB에 'INVALID_INPUT' 에러 로그가 전혀 없습니다.")
            print("  -> example.py가 성공적으로 실행되었는지 다시 확인하세요.")
        else:
            print(f"  -> 총 {len(all_errors)}개의 'INVALID_INPUT' 에러를 찾았습니다 (시간 무관).")
            for log in all_errors:
                print(f"  - [Error] {log['function_name']} | {log.get('error_code')} | {log['timestamp_utc']}")

    except Exception as e:
        print(f"검증 중 치명적 에러 발생: {e}")
    finally:
        # --- 8. 연결 종료 ---
        client = get_cached_client()
        if client:
            client.close()
            print("\n데이터베이스 연결을 닫았습니다.")

if __name__ == "__main__":
    load_dotenv()
    check_all_invalid_input_errors()