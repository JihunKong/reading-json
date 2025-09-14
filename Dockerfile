# 한국어 학습 시스템 - 프로덕션 Docker 이미지
FROM python:3.11-slim

# 한국어 언어 설정
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    locales \
    default-jdk \
    fonts-nanum \
    fonts-nanum-extra \
    && locale-gen ko_KR.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치를 위한 requirements.txt 생성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# KoNLPy 한국어 처리를 위한 추가 설정
RUN python -c "import nltk; nltk.download('punkt')" || echo "NLTK download completed"

# 애플리케이션 파일 복사
COPY app/ ./app/
COPY core/ ./core/
COPY data/ ./data/

# 포트 설정
EXPOSE 8080

# 실행 권한 설정
RUN chmod +x app/main.py

# 한국어 학습 시스템 실행
CMD ["python", "app/main.py"]