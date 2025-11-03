# Git 커밋 메시지 작성 가이드

## 커밋 메시지 형식

```
<type>(<scope>): <subject>
```

- **type**: 커밋 타입 (필수)
- **scope**: 변경 범위 (선택)
- **subject**: 간단한 설명 (필수)

## 커밋 타입

### feat: 새로운 기능 추가
```bash
feat: Add new feature
feat(auth): Add user signup API endpoint
```

### fix: 버그 수정
```bash
fix: Fix bug
fix(parser): Fix null pointer exception
```

### docs: 문서 수정
```bash
docs: Update documentation
docs(readme): Update installation guidelines
```

### style: 코드 스타일 변경 (기능 변경 없음)
```bash
style: Change code formatting
style(api): Apply Prettier formatting
```

### refactor: 코드 리팩토링 (기능 변경 없음)
```bash
refactor: Improve code structure
refactor(user): Simplify UserService logic
```

### test: 테스트 코드 추가/수정
```bash
test: Add or modify tests
test(auth): Add test cases for login failures
```

### chore: 빌드, 설정 등 기타 작업
```bash
chore: Update build configuration
chore: Add *.log to .gitignore
```

### perf: 성능 개선
```bash
perf: Improve performance
perf(api): Optimize database query
```

### ci: CI/CD 설정 변경
```bash
ci: Update CI pipeline
ci: Add GitHub Actions workflow
```

### build: 빌드 시스템 변경
```bash
build: Update dependencies
build: Update webpack configuration
```

### revert: 이전 커밋 되돌리기
```bash
revert: Revert "feat: Add new feature"
```

## 작성 규칙

### 1. 명령형 현재형 사용
✅ 좋은 예:
```bash
feat(auth): Add user login functionality
fix(api): Resolve CORS issue
docs: Update API documentation
```

❌ 나쁜 예:
```bash
feat(auth): Added user login functionality
fix(api): Resolved CORS issue
docs: Updated API documentation
```

### 2. 제목은 50자 이내로 작성
```bash
✅ feat(auth): Add OAuth2 authentication
❌ feat(auth): Add OAuth2 authentication with Google, Facebook, and Twitter providers
```

### 3. 제목 첫 글자는 대문자로
```bash
✅ feat: Add new feature
❌ feat: add new feature
```

### 4. 제목 끝에 마침표 사용 금지
```bash
✅ feat: Add user authentication
❌ feat: Add user authentication.
```

### 5. scope를 사용하여 변경 범위 명시
```bash
feat(auth): Add login endpoint
feat(user): Add profile page
feat(api): Add rate limiting
fix(database): Fix connection pool leak
```

## 고급 사용법

### Breaking Changes (주요 변경사항)
```bash
feat(api)!: Change authentication method to OAuth2

BREAKING CHANGE: JWT authentication is replaced with OAuth2.
Users need to update their authentication flow.
```

### 여러 단락 사용
```bash
feat(auth): Add two-factor authentication

Implement TOTP-based 2FA using Google Authenticator.
Users can enable 2FA in their account settings.

Closes #123
```

### 이슈 연결
```bash
fix(parser): Fix null pointer exception

Fixes #456
Closes #789
Related to #234
```

### 커밋 되돌리기
```bash
revert: Revert "feat(auth): Add OAuth2 support"

This reverts commit a1b2c3d4e5f6.
Reason: OAuth2 implementation caused performance issues.
```

## 완전한 예시

### 예시 1: 새로운 기능
```bash
feat(auth): Add user signup API endpoint
```

### 예시 2: 버그 수정
```bash
fix(parser): Fix null pointer exception in data parsing
```

### 예시 3: 문서 수정
```bash
docs(readme): Update installation guidelines
```

### 예시 4: 스타일 변경
```bash
style(api): Apply Prettier formatting
```

### 예시 5: 리팩토링
```bash
refactor(user): Simplify UserService logic
```

### 예시 6: 테스트
```bash
test(auth): Add test cases for login failures
```

### 예시 7: 기타 작업
```bash
chore: Add *.log to .gitignore
```

### 예시 8: 성능 개선
```bash
perf(database): Add index to user_id column
```

### 예시 9: CI/CD
```bash
ci: Add automated testing workflow
```

### 예시 10: Breaking Change
```bash
feat(api)!: Change response format to REST standard

BREAKING CHANGE: API responses now follow REST conventions.
Update client code to handle new response structure.
```

## 빠른 참조

| 타입 | 목적 | 예시 |
|------|------|------|
| `feat` | 새로운 기능 | `feat(auth): Add login` |
| `fix` | 버그 수정 | `fix(api): Fix CORS` |
| `docs` | 문서 | `docs: Update README` |
| `style` | 포맷팅 | `style: Apply linter` |
| `refactor` | 리팩토링 | `refactor: Clean up code` |
| `test` | 테스트 | `test: Add unit tests` |
| `chore` | 유지보수 | `chore: Update deps` |
| `perf` | 성능 | `perf: Optimize query` |
| `ci` | CI/CD | `ci: Add workflow` |
| `build` | 빌드 시스템 | `build: Update config` |
| `revert` | 되돌리기 | `revert: Revert commit` |

## 팁

1. **구체적으로 작성**: 가능하면 scope 포함
2. **간결하게 작성**: 제목은 짧고 명확하게
3. **일관성 유지**: 팀 컨벤션 따르기
4. **설명적으로 작성**: 무엇을 왜 했는지 설명 (어떻게가 아님)
5. **본문 활용**: 복잡한 변경사항은 본문에 상세히 작성

## 자주 사용하는 Scope

- `auth`: 인증/인가
- `api`: API 엔드포인트
- `ui`: 사용자 인터페이스
- `database`: 데이터베이스 변경
- `config`: 설정
- `deps`: 의존성
- `security`: 보안 관련
- `i18n`: 국제화
- `a11y`: 접근성
- `seo`: SEO 관련
