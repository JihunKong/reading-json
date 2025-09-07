#!/usr/bin/env python3
import os, argparse, json, csv, math, re, glob, statistics
from collections import Counter

def tokenize(s):
    s = s.lower()
    s = re.sub(r"[^0-9a-z가-힣\s]", " ", s)
    toks = [t for t in s.split() if t]
    return toks

def cosine_sim(a, b):
    ca, cb = Counter(a), Counter(b)
    dot = sum(ca[t]*cb[t] for t in set(ca) & set(cb))
    na = math.sqrt(sum(v*v for v in ca.values()))
    nb = math.sqrt(sum(v*v for v in cb.values()))
    return (dot / (na*nb)) if na>0 and nb>0 else 0.0

def load_items(items_dir):
    index = {}
    for fp in glob.glob(os.path.join(items_dir, "*.json")):
        try:
            with open(fp,"r",encoding="utf-8") as f:
                obj = json.load(f)
                index[obj["id"]] = obj
        except Exception as e:
            print(f"[WARN] skip {fp}: {e}")
    return index

def evaluate_free_topic(user_text, target_text, ignore_words=None):
    ignore = set((ignore_words or []) + ["매우","정말","진짜","완전"])
    utoks = [t for t in tokenize(user_text) if t not in ignore]
    ttoks = [t for t in tokenize(target_text) if t not in ignore]
    sim = cosine_sim(utoks, ttoks)
    # naive "pos" requirement -> require at least one Korean verb-like ending and one noun-like token (heuristic)
    has_verb = any(t.endswith(("다","했다","한다","된다","향상","개선")) for t in utoks)
    has_noun = any(len(t)>=2 for t in utoks)
    return sim, has_noun and has_verb

def grade_row(row, items, sim_th=0.68, require_pos=True):
    task_id = row["task_id"]
    item = items.get(task_id)
    result = {"submission_id":row["submission_id"], "task_id":task_id, "user_id":row["user_id"], "is_correct": None, "similarity": None, "feedback": ""}
    if not item:
        result["feedback"] = "문항을 찾을 수 없습니다."
        return result

    # MCQ grading when provided
    if row.get("choice_index","").strip() != "":
        try:
            ci = int(row["choice_index"])
            if item["task_type"]=="paragraph":
                ans = item["q_keywords_mcq"]["answer_index"]
            else:
                ans = item["q_keywords_mcq"]["answer_index"]
            result["is_correct"] = (ci == ans)
            if not result["is_correct"]:
                result["feedback"] = "핵심어 선택을 다시 검토하세요. 본문에서 가장 일반화된 개념을 찾는 것이 요령입니다."
        except Exception:
            result["feedback"] = "객관식 채점 실패(입력 형식 확인)."

    # Free-topic grading
    if row.get("free_topic","").strip():
        user_topic = row["free_topic"]
        target = item["q_topic_free"]["target_topic"]
        ignore = item["q_topic_free"].get("evaluation",{}).get("ignore_words",[])
        min_sim = item["q_topic_free"].get("evaluation",{}).get("min_similarity", sim_th)
        sim, ok_pos = evaluate_free_topic(user_topic, target, ignore_words=ignore)
        passed = (sim >= min_sim) and ((not require_pos) or ok_pos)
        result["similarity"] = round(sim,2)
        result["is_correct"] = (result["is_correct"] if result["is_correct"] is not None else True) and passed
        fb = []
        if sim < min_sim:
            fb.append("핵심 개념어를 더 포함해 요약해 보세요.")
        if require_pos and not ok_pos:
            fb.append("명사·동사 중심의 정보 문장 형태로 쓰세요(예: '~한다', '~이다').")
        # suggest missing keywords (simple difference on top frequent tokens)
        ttoks = tokenize(target)
        utoks = tokenize(user_topic)
        missing = [t for t in ttoks if t not in utoks][:2]
        if missing:
            fb.append("예: " + ", ".join(missing))
        result["feedback"] = " ".join(fb) if fb else "좋습니다."
    return result

def main():
    ap = argparse.ArgumentParser(description="Grader CLI")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("grade")
    s.add_argument("--items-dir", default="/data/items")
    s.add_argument("--submissions", required=True)
    s.add_argument("--similarity-threshold", type=float, default=0.68)
    s.add_argument("--require-pos", default="NOUN,VERB")

    ss = sub.add_parser("grade-sample")
    ss.add_argument("--input", default="grader/samples/submissions.csv")

    args = ap.parse_args()

    if args.cmd=="grade":
        items = load_items(args.items_dir)
        out_rows = []
        with open(args.submissions,"r",encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                r = grade_row(row, items, sim_th=args.similarity_threshold, require_pos=bool(args.require_pos))
                out_rows.append(r)
        os.makedirs("reports", exist_ok=True)
        out_csv = "reports/grades.csv"
        with open(out_csv,"w",encoding="utf-8",newline="") as f:
            w = csv.DictWriter(f, fieldnames=["submission_id","task_id","user_id","is_correct","similarity","feedback"])
            w.writeheader()
            for r in out_rows:
                w.writerow(r)
        print(f"Wrote {out_csv}")

    elif args.cmd=="grade-sample":
        items = load_items("/data/items")
        out_rows = []
        with open(args.input,"r",encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                r = grade_row(row, items)
                out_rows.append(r)
        os.makedirs("reports", exist_ok=True)
        out_csv = "reports/grades.csv"
        with open(out_csv,"w",encoding="utf-8",newline="") as f:
            w = csv.DictWriter(f, fieldnames=["submission_id","task_id","user_id","is_correct","similarity","feedback"])
            w.writeheader()
            for r in out_rows:
                w.writerow(r)
        print(f"Wrote {out_csv}")
    else:
        ap.print_help()

if __name__=="__main__":
    main()
