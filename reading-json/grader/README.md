# Grader (채점기)

학생 응답(객관식/주관식)을 받아 채점하고, 피드백/리포트를 생성합니다.
수업 맥락별로 `.env` 또는 CLI 옵션으로 커스터마이즈하십시오.

## 실행 예시
```bash
# 샘플 채점
python cli.py grade-sample --input grader/samples/submissions.csv

# 디렉토리 일괄 채점(JSON+CSV)
python cli.py grade --items-dir /data/items --submissions grader/samples/submissions.csv   --similarity-threshold 0.68 --require-pos NOUN,VERB
```
