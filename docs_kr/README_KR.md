
# VectorWave: Seamless Auto-Vectorization Framework

[](https://www.google.com/search?q=LICENSE)

## 🌟 프로젝트 소개 (Overview)

**VectorWave**는 파이썬 함수/메서드의 출력을 **데코레이터**를 사용하여 자동으로 \*\*벡터 데이터베이스(Vector DB)\*\*에 저장하고 관리하는 혁신적인 프레임워크입니다. 개발자는 데이터 수집, 임베딩 생성, 벡터 DB 저장의 복잡한 과정을 신경 쓸 필요 없이, 단 한 줄의 코드(`@vectorize`)로 함수 출력을 지능적인 벡터 데이터로 변환할 수 있습니다.

## ✨ 주요 특징 (Features)

* **`@vectorize` 데코레이터:**
  1.  **정적 데이터 수집:** 스크립트 로드 시, 함수의 소스 코드, 독스트링, 메타데이터를 `VectorWaveFunctions` 컬렉션에 1회 저장합니다.
  2.  **동적 데이터 로깅:** 함수가 호출될 때마다 실행 시간, 성공/실패 상태, 에러 로그, 그리고 '동적 태그'를 `VectorWaveExecutions` 컬렉션에 기록합니다.
* **검색 인터페이스:** 저장된 벡터 데이터(함수 정의)와 로그(실행 기록)를 검색하는 `search_functions` 및 `search_executions` 함수를 제공하여 RAG 및 모니터링 시스템 구축을 용이하게 합니다.

## 🚀 사용법 (Usage)

VectorWave는 데코레이터를 통한 '저장'과 함수를 통한 '검색'으로 구성됩니다.

```python
import time
from vectorwave import (
    vectorize, 
    initialize_database, 
    search_functions, 
    search_executions
)

# 1. (필수) 데이터베이스 초기화
#    스크립트 시작 시 한 번만 호출하면 됩니다.
try:
    client = initialize_database()
    print("VectorWave DB 초기화 성공.")
except Exception as e:
    print(f"DB 초기화 실패: {e}")
    exit()

# 2. [저장] @vectorize 데코레이터 사용
#    스크립트 로드 시, 이 함수의 정의(소스코드, 설명 등)가 DB에 저장됩니다.
@vectorize(
    search_description="결제 시스템에서 사용자에게 요금을 청구합니다.",
    sequence_narrative="결제가 완료되면 영수증 ID를 반환합니다.",
    team="billing",  # 커스텀 태그
    priority=1       # 커스텀 태그
)
def process_payment(user_id: str, amount: int):
    """사용자 ID와 금액을 받아 결제를 처리하는 함수"""
    print(f"  [실행] {user_id}의 {amount}원 결제 처리 중...")
    time.sleep(0.5)
    # 함수가 호출되면, 이 실행 로그(성공, 0.5초 소요 등)가 DB에 저장됩니다.
    return {"status": "success", "receipt_id": f"receipt_{user_id}_{amount}"}

# --- 함수 실행 ---
process_payment("user_123", 10000)
process_payment("user_456", 500)

# 3. [검색 ①] 함수 정의 검색 (RAG 용도)
#    '결제'와 관련된 함수를 자연어(벡터)로 검색합니다.
print("\n--- '결제' 관련 함수 검색 ---")
payment_funcs = search_functions(
    query="사용자 결제 처리 기능",
    limit=3
)
for func in payment_funcs:
    print(f"  - 함수명: {func['properties']['function_name']}")
    print(f"  - 설명: {func['properties']['search_description']}")
    print(f"  - 유사도(거리): {func['metadata'].distance:.4f}")

# 4. [검색 ②] 함수 실행 로그 검색 (모니터링 용도)
#    'billing' 팀의 실행 기록을 검색합니다.
print("\n--- 'billing' 팀 실행 로그 검색 (최신순) ---")
billing_logs = search_executions(
    limit=5,
    filters={"team": "billing"},
    sort_by="timestamp_utc",
    sort_ascending=False
)
for log in billing_logs:
    print(f"  - {log['timestamp_utc']} / {log['status']} / {log['duration_ms']:.2f}ms")

# (스크립트 종료 시 client 자동 관리)

```

## ⚙️ 설정 (Configuration)

VectorWave는 Weaviate 데이터베이스 연결 정보를 **환경 변수** 또는 `.env` 파일을 통해 자동으로 읽어옵니다.

라이브러리를 사용하는 당신의 프로젝트 루트 디렉터리(예: `main.py`가 있는 곳)에 `.env` 파일을 생성하고 필요한 값들을 설정하세요.

### .env 파일 예시

```ini
# .env
# --- 기본 Weaviate 연결 설정 ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- Vectorizer 설정 (OpenAI 사용 시) ---
# text2vec-openai 모듈 등을 사용할 경우 OpenAI API 키가 필요합니다.
# OPENAI_API_KEY=sk-your-key-here

# --- [고급] 커스텀 속성 설정 ---
# 1. 스키마에 추가할 커스텀 속성을 정의한 JSON 파일의 경로입니다.
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties

# 2. '전역 동적 태깅'에 사용할 환경 변수입니다.
#    (.weaviate_properties 파일에 "run_id"가 정의되어 있어야 함)
RUN_ID=test-run-001
EXPERIMENT_ID=exp-abc
```

-----

### 커스텀 속성 및 동적 실행 태깅

VectorWave는 정적 데이터(함수 정의)와 동적 데이터(실행 로그) 외에 사용자가 정의한 추가 메타데이터를 저장할 수 있습니다. 이는 두 단계로 작동합니다.

#### 1단계: 커스텀 스키마 정의 (태그 "허용 목록")

`.env` 파일의 `CUSTOM_PROPERTIES_FILE_PATH`에 지정된 경로(기본값: `.weaviate_properties`)에 JSON 파일을 생성합니다.

이 파일은 Weaviate 컬렉션에 \*\*새로운 속성(열)\*\*을 추가하도록 VectorWave에 지시합니다. 이 파일은 모든 커스텀 태그의 **"허용 목록(allow-list)"** 역할을 합니다.

**`.weaviate_properties` 예시:**

```json
{
  "run_id": {
    "data_type": "TEXT",
    "description": "The ID of the specific test run"
  },
  "experiment_id": {
    "data_type": "TEXT",
    "description": "Identifier for the experiment"
  },
  "team": {
    "data_type": "TEXT",
    "description": "이 함수를 담당하는 팀"
  },
  "priority": {
    "data_type": "INT",
    "description": "실행 우선순위"
  }
}
```

* 위와 같이 정의하면 `VectorWaveFunctions`와 `VectorWaveExecutions` 컬렉션 모두에 `run_id`, `experiment_id`, `team`, `priority` 속성이 추가됩니다.

#### 2단계: 동적 실행 태깅 (값 추가하기)

함수가 실행될 때, VectorWave는 `VectorWaveExecutions` 로그에 태그를 추가합니다. 이 태그는 두 가지 방식으로 수집된 후 병합됩니다.

**1. 전역 태그 (환경 변수)**
VectorWave는 1단계에서 정의된 키의 **대문자 이름**(예: `RUN_ID`, `EXPERIMENT_ID`)과 일치하는 환경 변수를 찾습니다. 발견된 값은 `global_custom_values`로 로드되어 *모든* 실행 로그에 추가됩니다. 스크립트 실행 전반에 걸친 메타데이터에 이상적입니다.

**2. 함수별 태그 (데코레이터)**
`@vectorize` 데코레이터에 직접 키워드 인수(`**execution_tags`)로 태그를 전달할 수 있습니다. 이는 함수별 메타데이터에 이상적입니다.

```python
# --- .env 파일 ---
# RUN_ID=global-run-abc
# TEAM=default-team

@vectorize(
    search_description="결제 처리",
    sequence_narrative="...",
    team="billing",  # <-- 함수별 태그
    priority=1       # <-- 함수별 태그
)
def process_payment():
    pass

@vectorize(
    search_description="다른 함수",
    sequence_narrative="...",
    run_id="override-run-xyz" # <-- 전역 태그를 덮어씀
)
def other_function():
    pass
```

**태그 병합 및 유효성 검사 규칙**

1.  **유효성 검사 (중요):** 태그(전역 또는 함수별)는 **반드시** `.weaviate_properties` 파일(1단계)에 키(예: `run_id`, `team`, `priority`)가 먼저 정의된 경우에만 Weaviate에 저장됩니다. 스키마에 정의되지 않은 태그는 **무시**되며, 스크립트 시작 시 경고가 출력됩니다.

2.  **우선순위 (덮어쓰기):** 만약 태그 키가 두 곳 모두에 정의된 경우(예: `.env`의 전역 `RUN_ID`와 데코레이터의 `run_id="override-xyz"`), **데코레이터에 명시된 함수별 태그가 항상 이깁니다**.

**결과 로그:**

* `process_payment()` 실행 로그: `{"run_id": "global-run-abc", "team": "billing", "priority": 1}`
* `other_function()` 실행 로그: `{"run_id": "override-run-xyz", "team": "default-team"}`

-----

## 🤝 기여 (Contributing)

버그 보고, 기능 요청, 코드 기여 등 모든 형태의 기여를 환영합니다. 자세한 내용은 [CONTRIBUTING.md](https://www.google.com/search?q=httpsS://www.google.com/search%3Fq%3DCONTRIBUTING.md)를 참고해 주세요.

## 📜 라이선스 (License)

이 프로젝트는 MIT 라이선스에 따라 배포됩니다. 자세한 내용은 [LICENSE](https://www.google.com/search?q=LICENSE) 파일을 확인하세요.