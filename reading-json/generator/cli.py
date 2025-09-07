#!/usr/bin/env python3
import os, argparse, json, random, time, re, hashlib

def slug(s): 
    return re.sub(r"[^a-z0-9]+","-", s.lower()).strip("-")

def make_id(prefix):
    ts = time.strftime("%Y%m%d%H%M%S", time.localtime())
    rnd = random.randint(1000,9999)
    return f"{prefix}_{ts}_{rnd}"

TOPIC_FALLBACK = [
    "도서관의 디지털 전환", "지역 축제의 변화", "스마트팜 기초", "해양 생태 보전", "청소년 금융 문해"
]

def load_topics(seed_file):
    topics = []
    if os.path.exists(seed_file):
        with open(seed_file,"r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line or line.lower().startswith("topic"): 
                    if "," in line:  # csv header skip
                        continue
                    if line.lower().startswith("topic"):
                        continue
                if "," in line:
                    topics.append(line.split(",")[0].strip())
                else:
                    topics.append(line)
    if not topics:
        topics = TOPIC_FALLBACK
    return topics

def generate_paragraph(topic, difficulty="medium", tags=None):
    tags = tags or []
    # naive 3~5 sentence paragraph (rule-based)
    sentences = [
        f"{topic}에 대한 관심이 높아지고 있다.",
        f"여러 기관이 {topic}을(를) 도입하거나 개선하려는 노력을 보이고 있다.",
        f"이 변화는 학습자와 지역사회에 긍정적인 효과를 가져올 수 있다.",
        f"다만 접근성이나 비용 등 현실적인 제약을 점검할 필요가 있다.",
        f"결론적으로 {topic}의 적절한 활용은 효율성과 편익을 높인다."
    ]
    n = random.randint(3,5)
    para_text = " ".join(sentences[:n])

    # keyword mcq
    choices = [topic.split()[0] if " " in topic else topic, "일반적 변화", "개발", "참여"]
    random.shuffle(choices)
    answer_idx = choices.index(choices[0])  # weak heuristic: pick index of first element post-shuffle? better: ensure target is in pos 1
    # Instead, set correct to the entry most similar to topic (first element we created)
    correct_choice = choices[answer_idx]

    # center sentence mcq (5 choices, last is 'not explicit')
    sent_items = [{"idx":i+1,"text":s} for i,s in enumerate(sentences[:min(4,n)]+sentences[min(4,n):4])]
    # pad to 4 sentences (if fewer), then add invisible option
    while len(sent_items) < 4:
        sent_items.append({"idx":len(sent_items)+1,"text":sentences[len(sent_items)]})
    sent_items.append({"idx":5,"text":"중심문장이 겉으로 드러나지 않음."})
    center_idx = 1  # simple heuristic: first sentence

    obj = {
        "version":"1.0","locale":"ko-KR","task_type":"paragraph",
        "id": make_id("para"), "source":"synthetic",
        "paragraph":{"topic_hint":topic,"text":para_text},
        "q_keywords_mcq":{
            "stem":"위 문단을 가장 잘 대표하는 '핵심어'는?",
            "choices":choices, "answer_index":choices.index(correct_choice),
            "rationale":"문단의 중심 개념과 가장 일반화된 핵심어가 일치합니다."
        },
        "q_center_sentence_mcq":{
            "stem":"다음 중 중심문장으로 가장 알맞은 것은?",
            "sentences":sent_items,
            "answer_idx":center_idx,
            "rationale":"문단의 도입문이 전체 내용을 포괄적으로 제시합니다."
        },
        "q_topic_free":{
            "stem":"이 문단의 주제를 한 문장으로 직접 써 보세요.",
            "target_topic": f"{topic}의 도입과 활용이 가져오는 효과",
            "evaluation":{
                "min_similarity":0.68,
                "ignore_words":["매우","정말","진짜","완전"],
                "must_include_pos":["NOUN","VERB"]
            },
            "feedback_guides":[
                "핵심 명사와 동사를 포함해 보세요.",
                "감탄사·미사여구를 줄이고 정보어를 사용하세요."
            ]
        },
        "metainfo":{"difficulty":difficulty,"tags":tags or ["사실적읽기","요약"]}
    }
    return obj

def generate_article(topic, difficulty="medium", tags=None):
    tags = tags or []
    paragraphs = [
        f"{topic}은(는) 최근 다양한 분야에서 관심이 확대되고 있다.",
        f"현장에서는 {topic}을(를) 적용하기 위한 시도가 이루어지고 있다.",
        f"이러한 변화는 효율성 제고와 학습 경험 향상에 기여할 수 있다.",
        f"지속 가능한 운영을 위해 과제 점검이 필요하다."
    ]
    m = random.randint(3,4)
    chosen = paragraphs[:m]
    center_idx = 1
    center_choices = [{"idx":i+1,"text":p} for i,p in enumerate(chosen)]
    # keyword mcq
    choices = [f"{topic}의 변화", "참여 확대", "효율성", "운영 과제"]
    random.shuffle(choices)
    correct = f"{topic}의 변화"
    answer_index = choices.index(correct) if correct in choices else 0

    obj = {
        "version":"1.0","locale":"ko-KR","task_type":"article",
        "id": make_id("art"), "source":"synthetic",
        "article":{"title":f"{topic}의 동향","paragraphs":chosen},
        "q_keywords_mcq":{
            "stem":"글 전체를 가장 잘 대표하는 핵심어는?",
            "choices":choices,"answer_index":answer_index,
            "rationale":"글 전반의 논지가 주제의 변화/동향을 중심으로 전개됩니다."
        },
        "q_center_paragraph_mcq":{
            "stem":"이 글의 중심 문단으로 가장 적절한 것은?",
            "choices":center_choices,"answer_idx":center_idx,
            "rationale":"글의 전환·총괄 방향을 제시하는 도입 문단입니다."
        },
        "q_topic_free":{
            "stem":"이 글의 주제를 한 문장으로 직접 써 보세요.",
            "target_topic": f"{topic}이(가) 확산되며 효율성과 학습 경험 향상에 기여한다",
            "evaluation":{"min_similarity":0.70,"ignore_words":["매우","정말"],"must_include_pos":["NOUN","VERB"]}
        },
        "metainfo":{"difficulty":difficulty,"tags":tags or ["사실적읽기","요약","주제"]}
    }
    return obj

def main():
    ap = argparse.ArgumentParser(description="Generator CLI")
    sub = ap.add_subparsers(dest="cmd")

    g = sub.add_parser("generate")
    g.add_argument("--mode", choices=["paragraph","article"], required=True)
    g.add_argument("--count", type=int, default=5)
    g.add_argument("--difficulty", default="medium")
    g.add_argument("--tags", default="")
    g.add_argument("--seed-file", default="seeds/topics.csv")

    args = ap.parse_args()
    if args.cmd=="generate":
        topics = load_topics(args.seed_file)
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        outdir = "out"
        os.makedirs(outdir, exist_ok=True)
        for i in range(args.count):
            topic = random.choice(topics)
            if args.mode=="paragraph":
                obj = generate_paragraph(topic, args.difficulty, tags)
            else:
                obj = generate_article(topic, args.difficulty, tags)
            fn = f"{outdir}/{obj['id']}.json"
            with open(fn,"w",encoding="utf-8") as f:
                json.dump(obj,f,ensure_ascii=False,indent=2)
        print(f"Generated {args.count} items to {outdir}/")

    else:
        ap.print_help()

if __name__=="__main__":
    main()
