# Generator (생성기)

문단/글 + 문항 JSON을 **대량 생성**하고, 스키마 검증 및 기본 품질 필터를 거친 후 `out/`에 저장합니다.

## 실행 예시
```bash
# 문단 중심 5세트 생성
python cli.py generate --count 5 --mode paragraph

# 글 중심 3세트 생성
python cli.py generate --count 3 --mode article

# 난이도/태그 지정
python cli.py generate --count 2 --mode paragraph --difficulty medium --tags 사실적읽기,요약
```
