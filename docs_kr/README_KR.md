
# VectorWave: Seamless Auto-Vectorization Framework

[](https://www.google.com/search?q=LICENSE)

## 🌟 프로젝트 소개 (Overview)

**VectorWave**는 파이썬 함수/메서드의 출력을 **데코레이터**를 사용하여 자동으로 **벡터 데이터베이스(Vector DB)**에 저장하고 관리하는 혁신적인 프레임워크입니다. 개발자는 데이터 수집, 임베딩 생성, 벡터 DB 저장의 복잡한 과정을 신경 쓸 필요 없이, 단 한 줄의 코드(`@vectorize`)로 함수 출력을 지능적인 벡터 데이터로 변환할 수 있습니다.

---

## ✨ 주요 특징 (Features)

* **`@vectorize` 데코레이터:**
  1.  **정적 데이터 수집:** 스크립트 로드 시, 함수의 소스 코드, 독스트링, 메타데이터를 `VectorWaveFunctions` 컬렉션에 1회 저장합니다.
  2.  **동적 데이터 로깅:** 함수가 호출될 때마다 실행 시간, 성공/실패 상태, 에러 로그, 그리고 '동적 태그'를 `VectorWaveExecutions` 컬렉션에 기록합니다.
* **분산 추적 (Distributed Tracing):** `@vectorize`와 `@trace_span` 데코레이터를 결합하여 복잡한 다단계 워크플로우의 실행을 하나의 **`trace_id`**로 묶어 분석할 수 있습니다.
* **검색 인터페이스:** 저장된 벡터 데이터(함수 정의)와 로그(실행 기록)를 검색하는 `search_functions` 및 `search_executions` 함수를 제공하여 RAG 및 모니터링 시스템 구축을 용이하게 합니다.

---

## 🚀 사용법 (Usage)

VectorWave는 데코레이터를 통한 '저장'과 함수를 통한 '검색'으로 구성되며, 이제 **실행 흐름 추적** 기능이 포함됩니다.

### 1. (필수) 데이터베이스 초기화 및 설정

```python
import time
from vectorwave import (
    vectorize, 
    initialize_database, 
    search_functions, 
    search_executions
)
# [추가] 분산 추적을 위해 trace_span을 별도로 임포트합니다.
from vectorwave.monitoring.tracer import trace_span 

# 스크립트 시작 시 한 번만 호출하면 됩니다.
try:
    client = initialize_database()
    print("VectorWave DB 초기화 성공.")
except Exception as e:
    print(f"DB 초기화 실패: {e}")
    exit()
````

### 2\. [저장] `@vectorize`와 분산 추적 사용

`@vectorize`는 트레이싱의 **루트(Root)** 역할을 수행하며, 내부 함수에 `@trace_span`을 적용하여 워크플로우 실행을 \*\*하나의 `trace_id`\*\*로 묶습니다.

```python
# --- 하위 스팬 함수: 인자를 캡처합니다 ---
@trace_span(attributes_to_capture=['user_id', 'amount'])
def step_1_validate_payment(user_id: str, amount: int):
    """(스팬) 결제 유효성 검사. user_id와 amount를 로그에 기록합니다."""
    print(f"  [SPAN 1] Validating payment for {user_id}...")
    time.sleep(0.1)
    return True

@trace_span(attributes_to_capture=['user_id', 'receipt_id'])
def step_2_send_receipt(user_id: str, receipt_id: str):
    """(스팬) 영수증 발송."""
    print(f"  [SPAN 2] Sending receipt {receipt_id}...")
    time.sleep(0.2)


# --- 루트 함수 (@trace_root 역할) ---
@vectorize(
    search_description="사용자 결제를 처리하고 영수증을 반환합니다.",
    sequence_narrative="결제가 완료되면 이메일로 영수증이 발송됩니다.",
    team="billing",  # ⬅️ 커스텀 태그 (모든 실행 로그에 기록됨)
    priority=1       # ⬅️ 커스텀 태그 (실행 중요도)
)
def process_payment(user_id: str, amount: int):
    """(루트 스팬) 사용자 결제 워크플로우를 실행합니다."""
    print(f"  [ROOT EXEC] process_payment: Starting workflow for {user_id}...")
    
    # 하위 함수 호출 시, 동일한 trace_id가 ContextVar를 통해 자동으로 상속됩니다.
    step_1_validate_payment(user_id=user_id, amount=amount) 
    
    receipt_id = f"receipt_{user_id}_{amount}"
    step_2_send_receipt(user_id=user_id, receipt_id=receipt_id)

    print(f"  [ROOT DONE] process_payment")
    return {"status": "success", "receipt_id": receipt_id}

# --- 함수 실행 ---
print("Now calling 'process_payment'...")
# 이 하나의 호출은 DB에 총 3개의 실행 로그(스팬)를 기록하며,
# 세 로그는 하나의 'trace_id'로 묶입니다.
process_payment("user_789", 5000)
```

### 3\. [검색 ①] 함수 정의 검색 (RAG 용도)

```python
# '결제'와 관련된 함수를 자연어(벡터)로 검색합니다.
print("\n--- '결제' 관련 함수 검색 ---")
payment_funcs = search_functions(
    query="사용자 결제 처리 기능",
    limit=3
)
for func in payment_funcs:
    print(f"  - 함수명: {func['properties']['function_name']}")
    print(f"  - 설명: {func['properties']['search_description']}")
    print(f"  - 유사도(거리): {func['metadata'].distance:.4f}")
```

### 4\. [검색 ②] 실행 로그 검색 (모니터링 및 추적)

`search_executions` 함수는 이제 `trace_id`를 기준으로 관련된 모든 실행 로그(스팬)를 검색할 수 있습니다.

```python
# 1. 특정 워크플로우(process_payment)의 Trace ID를 찾습니다.
latest_payment_span = search_executions(
    limit=1, 
    filters={"function_name": "process_payment"},
    sort_by="timestamp_utc",
    sort_ascending=False
)
trace_id = latest_payment_span[0]["trace_id"] 

# 2. 해당 Trace ID에 속한 모든 스팬을 시간순으로 검색합니다.
print(f"\n--- Trace ID ({trace_id[:8]}...) 전체 추적 ---")
trace_spans = search_executions(
    limit=10,
    filters={"trace_id": trace_id},
    sort_by="timestamp_utc",
    sort_ascending=True # 워크플로우 흐름 분석을 위해 오름차순 정렬
)

for i, span in enumerate(trace_spans):
    print(f"  - [Span {i+1}] {span['function_name']} ({span['duration_ms']:.2f}ms)")
    # 하위 스팬의 캡처된 인자(user_id, amount 등)도 함께 표시됩니다.
    
# 예상 결과:
# - [Span 1] step_1_validate_payment (100.81ms)
# - [Span 2] step_2_send_receipt (202.06ms)
# - [Span 3] process_payment (333.18ms)
```

-----

알겠습니다. 기존 `README_KR.md` 파일의 `⚙️ 설정 (Configuration)` 섹션을 **새로운 벡터화 전략** 내용으로 업데이트하고, 요청하신 대로 각 전략별 `.env` 설정 예시 코드를 추가하겠습니다.

다음은 `vtm/docs_kr/README_KR.md` 파일의 **"-----"** 구분선 사이에 들어갈 업데이트된 **"설정"** 섹션의 전체 내용입니다.

-----

## ⚙️ 설정 (Configuration)

VectorWave는 Weaviate 데이터베이스 연결 정보와 **벡터화 전략**을 **환경 변수** 또는 `.env` 파일을 통해 자동으로 읽어옵니다.

라이브러리를 사용하는 당신의 프로젝트 루트 디렉터리(예: `test_ex/example.py`가 있는 곳)에 `.env` 파일을 생성하고 필요한 값들을 설정하세요.

### 벡터화 전략 설정 (VECTORIZER)

`test_ex/.env` 파일의 `VECTORIZER` 환경 변수 설정을 통해 텍스트 벡터화 방식을 선택할 수 있습니다.

| `VECTORIZER` 설정 | 설명 | 필요한 추가 설정 |
| :--- | :--- | :--- |
| **`huggingface`** | (기본 권장) 로컬 CPU에서 `sentence-transformers` 라이브러리를 사용해 벡터화합니다. API 키가 필요 없어 즉시 테스트 가능합니다. | `HF_MODEL_NAME` (예: "sentence-transformers/all-MiniLM-L6-v2") |
| **`openai_client`** | (고성능) OpenAI Python 클라이언트를 사용하여 `text-embedding-3-small` 같은 최신 모델로 벡터화합니다. | `OPENAI_API_KEY` (유효한 OpenAI API 키) |
| **`weaviate_module`** | (Docker 위임) 벡터화 작업을 Weaviate 도커 컨테이너의 내장 모듈 (예: `text2vec-openai`)에 위임합니다. | `WEAVIATE_VECTORIZER_MODULE`, `OPENAI_API_KEY` |
| **`none`** | 벡터화를 수행하지 않습니다. 데이터는 벡터 없이 저장됩니다. | 없음 |

-----

### .env 파일 적용 예시

사용하려는 전략에 맞춰 `.env` 파일의 내용을 구성하세요.

#### 예시 1: `huggingface` 사용 (로컬, API 키 불필요)

로컬 머신에서 `sentence-transformers` 모델을 사용합니다. API 키가 필요 없어 즉시 테스트에 용이합니다.

```ini
# .env (HuggingFace 사용 시)
# --- 기본 Weaviate 연결 설정 ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- [전략 1] HuggingFace 설정 ---
VECTORIZER="huggingface"
HF_MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"

# (이 모드에서는 OPENAI_API_KEY가 필요하지 않습니다)
OPENAI_API_KEY=sk-...

# --- [고급] 커스텀 속성 설정 ---
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties
RUN_ID=test-run-001
```

#### 예시 2: `openai_client` 사용 (Python 클라이언트, 고성능)

`openai` Python 라이브러리를 통해 직접 OpenAI API를 호출합니다.

```ini
# .env (OpenAI Python Client 사용 시)
# --- 기본 Weaviate 연결 설정 ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- [전략 2] OpenAI Client 설정 ---
VECTORIZER="openai_client"

# [필수] 유효한 OpenAI API 키를 입력해야 합니다.
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# (이 모드에서는 HF_MODEL_NAME이 사용되지 않습니다)
HF_MODEL_NAME=...

# --- [고급] 커스텀 속성 설정 ---
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties
RUN_ID=test-run-001
```

#### 예시 3: `weaviate_module` 사용 (Docker 위임)

벡터화 작업을 Python이 아닌 Weaviate 도커 컨테이너에 위임합니다. (`vw_docker.yml` 설정 참조)

```ini
# .env (Weaviate Module 위임 시)
# --- 기본 Weaviate 연결 설정 ---
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# --- [전략 3] Weaviate Module 설정 ---
VECTORIZER="weaviate_module"
WEAVIATE_VECTORIZER_MODULE=text2vec-openai
WEAVIATE_GENERATIVE_MODULE=generative-openai

# [필수] Weaviate 컨테이너가 이 API 키를 읽어 사용합니다.
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- [고급] 커스텀 속성 설정 ---
CUSTOM_PROPERTIES_FILE_PATH=.weaviate_properties
RUN_ID=test-run-001
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

