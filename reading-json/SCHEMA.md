# 공통 JSON 스키마 요약

## paragraph task
- task_type: "paragraph"
- paragraph.text: 3~5문장
- q_keywords_mcq: 4지
- q_center_sentence_mcq: 5지(마지막 옵션은 "중심문장이 겉으로 드러나지 않음.")
- q_topic_free: 타깃 주제문 + 평가 파라미터(min_similarity 등)

## article task
- task_type: "article"
- article.paragraphs: 3~4문단
- q_keywords_mcq: 4지
- q_center_paragraph_mcq: 문단 번호 기반
- q_topic_free: 전체 주제 및 평가 파라미터
