
# VectorWave: Seamless Auto-Vectorization Framework

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🌟 프로젝트 소개 (Overview)

**VectorWave**는 파이썬 함수/메서드의 출력을 **데코레이터**를 사용하여 자동으로 **벡터 데이터베이스(Vector DB)**에 저장하고 관리하는 혁신적인 프레임워크입니다. 개발자는 데이터 수집, 임베딩 생성, 벡터 DB 저장의 복잡한 과정을 신경 쓸 필요 없이, 단 한 줄의 코드(`@vectorize`)로 함수 출력을 지능적인 벡터 데이터로 변환할 수 있습니다.

## ✨ 주요 특징 (Features)

* **`@vectorize` 데코레이터:**
    1.  **정적 데이터 수집:** 스크립트 로드 시, 함수의 소스 코드, 독스트링, 메타데이터를 `VectorWaveFunctions` 컬렉션에 1회 저장합니다.
    2.  **동적 데이터 로깅:** 함수가 호출될 때마다 실행 시간, 성공/실패 상태, 에러 로그, 그리고 '동적 태그'를 `VectorWaveExecutions` 컬렉션에 기록합니다.
* **간결한 검색 인터페이스:** (향후 제공 예정) 저장된 벡터 데이터에 대한 유의미한 검색(Similarity Search) 기능을 제공하여 RAG(Retrieval-Augmented Generation) 시스템 구축을 용이하게 합니다.

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
````

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

버그 보고, 기능 요청, 코드 기여 등 모든 형태의 기여를 환영합니다. 자세한 내용은 [CONTRIBUTING.md](httpsS://www.google.com/search?q=CONTRIBUTING.md)를 참고해 주세요.

## 📜 라이선스 (License)

이 프로젝트는 MIT 라이선스에 따라 배포됩니다. 자세한 내용은 [LICENSE](https://www.google.com/search?q=LICENSE) 파일을 확인하세요.

