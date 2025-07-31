Below is a **reference implementation blueprint** you can copy-paste into a repo and iterate.
Everything runs on a single Mac (Python 3.11, no GPU required) but can also call cloud LLMs when you want higher-grade judgments.

---

## 1 · System architecture

```
                 ┌──────────────────────┐
   raw HTML ───► │ 1. PRE-PROCESSOR     │
                 │ • read_html          │
                 │ • language_detect    │
                 │ • split_into_blocks  │
                 └─────────┬────────────┘
                           │
        ┌──────────────────▼──────────────────────┐
        │ 2. METRIC ENGINE                        │
        │ ┌───────────────┐  ┌──────────────────┐ │
        │ │ 2-A Classical │  │ 2-B Heuristics   │ │
        │ │  precision/rec│  │  link-density…   │ │
        │ └───────────────┘  └──────────────────┘ │
        │               ╲   ╱                    │
        │               ┌▼─▼┐                    │
        │               │Σ  │ weighted combine   │
        └───────────────┴┬─┬┴────────────────────┘
                          │
        ┌─────────────────▼────────────────────┐
        │ 3. LLM EVALUATOR (optional / tiered) │
        │ • direct scoring prompt              │
        │ • QA-recall sub-routine              │
        └───────────────┬──────────────────────┘
                        │
        ┌───────────────▼─────────────────┐
        │ 4. AGGREGATOR & MAPPER          │
        │   map [0,1] F1 → [-1,+1]        │
        └───────────────┬─────────────────┘
                        │
                 ┌──────▼──────┐
                 │  JSON SCORE │
                 └─────────────┘
```

*All boxes are pure-Python except the LLM evaluator, which can route to OpenAI GPT-3.5/4, GPT-4o-mini, or an on-device quantised LLaMA.*

---

## 2 · Input & output contracts

```json5
// input.json
{
  "url": "https://site.com/news/abc",
  "language": "auto",                // "auto" or an ISO code
  "html": "<html>...</html>",        // original markup
  "extracted": {
    "text": "The extracted article …",
    "blocks": ["para1 …", "para2 …", ...] // optional segmentation
  }
}
```

```json5
// score.json  (deterministic machine-readable)
{
  "score": 0.87,                     // final -1…+1
  "subscores": {
    "precision": 0.93,
    "recall": 0.94,
    "noise": 0.90,
    "structure": 0.88,
    "semantics": 0.91
  },
  "llm_explanation": "misses final caption, keeps a 'share' button"
}
```

---

## 3 · Algorithms

### 3-A  Classical precision & recall

```python
from difflib import SequenceMatcher
import nltk, re

def tokens(text):
    return re.findall(r"\w+", text.lower())

def align_metrics(gold, extracted):
    gold_t, ext_t = tokens(gold), tokens(extracted)
    # match ratio ≈ common subsequence length
    matcher = SequenceMatcher(None, gold_t, ext_t)
    matches = sum(tr.size for tr in matcher.get_matching_blocks())
    recall  = matches / len(gold_t) if gold_t else 0
    precision = matches / len(ext_t) if ext_t else 0
    return precision, recall
```

> **Gold reference**
> If you have a labelled corpus (e.g. CleanEval or Zyte benchmark) load their `gold.txt` (see §5). Otherwise run Mozilla Readability or Trafilatura once to get a *proxy* gold; imperfect but fast.

### 3-B  Heuristic cleanliness score

```python
def heuristic_noise_score(extracted, lang):
    words = tokens(extracted)
    link_count = extracted.count("http")
    short_blocks = sum(len(b.split()) < 5 for b in extracted.split("\n"))
    stopwords = nltk.corpus.stopwords.words(lang)
    stop_ratio = sum(w in stopwords for w in words) / len(words) if words else 0
    penalty  = 0.2*link_count + 0.3*short_blocks + (0.4 if stop_ratio < 0.2 else 0)
    return max(0, 1-penalty)   # 1 = perfectly clean
```

### 3-C  LLM direct evaluator  (cost-aware)

````python
import openai, json, textwrap

def ask_llm(original, extracted, model="gpt-3.5-turbo", temp=0):
    system = "You are a strict evaluator of news-article extraction."
    user = textwrap.dedent(f"""
      ORIGINAL:
      ```{original[:6000]}```    # clip to stay in context
      EXTRACTED:
      ```{extracted[:6000]}```
      ---
      Score the extraction:
      1. coverage (0-1)
      2. noise (0-1)
      3. structure (0-1)
      4. semantic (0-1)
      Return ONLY valid JSON: {{"coverage":..,"noise":..,"structure":..,"semantic":..,"explanation":""}}
    """)
    r = openai.ChatCompletion.create(
            model=model, messages=[{"role":"system", "content":system},
                                   {"role":"user","content":user}],
            temperature=temp)
    return json.loads(r.choices[0].message.content)
````

You can swap `model="gpt-4o-mini"` or a local llama.cpp endpoint to balance speed & price.

### 3-D  QA recall sub-routine (optional)

```python
def qa_recall(original, extracted, model="gpt-3.5-turbo"):
    q_prompt = f"Generate 3 factual Q&A pairs that a reader could answer after reading:\n{original[:3000]}"
    qa = openai.ChatCompletion.create(model=model, messages=[{"role":"user","content":q_prompt}])
    qa_pairs = json.loads(qa.choices[0].message.content)   # [{q,a}, …]
    correct = 0
    for pair in qa_pairs:
        ans = openai.ChatCompletion.create(
            model=model,
            messages=[{"role":"user", "content":f"Answer briefly: {pair['q']}\nTEXT:\n{extracted}"}])
        if pair['a'].lower() in ans.choices[0].message.content.lower():
            correct += 1
    return correct / len(qa_pairs)
```

---

## 4 · Score aggregator

```python
def final_score(p, r, noise_h, llm=None, qa=None):
    # base F1
    f1 = 2*p*r/(p+r) if p+r else 0
    # combine
    w_llm, w_qa = 0.2, 0.1 if llm else 0, 0
    if qa is not None:
        w_qa = 0.1
    technical = 0.5*f1 + 0.3*noise_h + w_qa*qa
    blended = (1-w_llm)*technical + w_llm*(llm["coverage"]*0.6 + llm["noise"]*0.4)
    # map [0,1] → [-1,+1]
    return 2*blended - 1
```

Weights are empirical; tune on a validation set.

---

## 5 · Ready-to-use evaluation corpora

| Corpus (link)                       | Size              | Langs            | Notes                                                                        |
| ----------------------------------- | ----------------- | ---------------- | ---------------------------------------------------------------------------- |
| CleanEval 2007                      | 700 pages         | EN, ZH           | Classic boilerplate benchmark; gold ≈ human-cleaned text ([ResearchGate][1]) |
| Zyte *article-extraction-benchmark* | 500 pages         | EN               | HTML + JSON gold, scripts included ([GitHub][2])                             |
| Trafilatura evaluation set          | 750 docs          | EN, DE, FR, PL … | Public stats & ROUGE-LSum F1 leaderboard ([trafilatura.readthedocs.io][3])   |
| Webis combined 2023                 | 8 merged datasets | multi            | Largest modern benchmark; request from authors ([downloads.webis.de][4])     |

Start with Zyte (easy JSON) to validate code, then CleanEval for multilingual stress-test.

---

## 6 · Putting it together (driver script)

```python
import json, langdetect
from readability import Document

def evaluate_file(path_html, path_extr):
    html = open(path_html).read()
    extracted = open(path_extr).read()

    # 1. language
    lang = langdetect.detect(extracted)[:2]

    # 2. proxy gold via Readability if no gold file
    gold = Document(html).summary()
    gold_text = BeautifulSoup(gold, "lxml").get_text(" ", strip=True)

    # 3. classical
    p, r = align_metrics(gold_text, extracted)
    noise_h = heuristic_noise_score(extracted, lang)

    # 4. (optional) LLM
    llm = ask_llm(gold_text, extracted)         # skip if cost-sensitive
    qa  = qa_recall(gold_text, extracted)       # skip for speed

    # 5. final
    score = final_score(p, r, noise_h, llm, qa)
    result = {
        "score": round(score, 3),
        "subscores": {
            "precision": round(p,3), "recall": round(r,3),
            "noise": round(noise_h,3),
            "structure": llm["structure"],
            "semantics": llm["coverage"],
        },
        "llm_explanation": llm["explanation"]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

Run:

```bash
python evaluate.py page.html extracted.txt > score.json
```

---

## 7 · Operating modes

| Mode             | Components used        | Cost           | Throughput       |
| ---------------- | ---------------------- | -------------- | ---------------- |
| **Local-only**   | Classical + heuristics | free           | 200 pages / sec  |
| **Hybrid-cheap** | + GPT-3.5 direct eval  | \$0.001 / page | 5–10 pages / sec |
| **Full**         | + QA + GPT-4           | \$0.02 / page  | 1 page / sec     |

Switch modes via CLI flags (e.g. `--no-llm`, `--llm=cheap`, `--llm=full`).

---

## 8 · Extending / tuning

* **Weights:** optimise with grid-search on a held-out slice of CleanEval or Zyte.
* **Language packs:** plug in extra stopword lists, or use spaCy models for pt, es.
* **Streaming pipeline:** if you process millions of URLs, parallelise pre-processor & metric engine; send only low-confidence cases to the LLM tier.
* **Ensembling extractors:** run two extractors (Trafilatura + Readability) and pick the output with the higher evaluation score – Bevendorff et al. showed this outperforms any single extractor ([downloads.webis.de][5]).

---

### Bottom line

The architecture above gives you **deterministic, fast, reference-based scoring** plus an **LLM “sense check”** for semantic fidelity.
Mapping everything onto the simple -1…+1 scale makes regression tests trivial: every code change to your scraper should *never* decrease the mean score on a small canary set.

[1]: https://www.researchgate.net/publication/220746707_Cleaneval_A_Competition_for_Cleaning_Web_Pages?utm_source=chatgpt.com "(PDF) Cleaneval: A Competition for Cleaning Web Pages"
[2]: https://github.com/scrapinghub/article-extraction-benchmark?utm_source=chatgpt.com "Article extraction benchmark: dataset and evaluation scripts - GitHub"
[3]: https://trafilatura.readthedocs.io/en/latest/evaluation.html?utm_source=chatgpt.com "Evaluation — Trafilatura 2.0.0 documentation"
[4]: https://downloads.webis.de/theses/papers/gupta_2022.pdf?utm_source=chatgpt.com "[PDF] Advancing and Benchmarking Large-Scale Content Extraction from ..."
[5]: https://downloads.webis.de/publications/slides/bevendorff_2023b.pdf?utm_source=chatgpt.com "[PDF] An Empirical Comparison of Web Content Extraction Algorithms"
