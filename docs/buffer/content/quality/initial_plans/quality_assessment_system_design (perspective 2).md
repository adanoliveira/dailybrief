### Key Points
- The revised system uses a large language model (LLM) to evaluate news article extractions, scoring from -1 to 1, where 1 is perfect, 0 is no content, and -1 is all noise.
- It seems likely to provide accurate and semantic evaluations by leveraging LLMs to identify core content and assess completeness and purity.
- Research suggests LLMs can parse HTML effectively, but consistency and cost may pose challenges, requiring careful prompt design and resource management.
- The system is designed to be robust, deterministic, and scalable, with validation against benchmarks like CleanEval recommended for reliability.

### System Overview
The revised system evaluates the quality of news article extractions by using an LLM, such as GPT-4o-mini, to directly assess how well the extracted content matches the original article’s core content while excluding noise. It scores extractions from -1 (all noise) to 1 (perfect extraction), with 0 indicating no content extracted despite core content existing. The system is designed to run on a single Mac with Python 3.11, with optional cloud LLM calls for enhanced accuracy.

### How It Works
The system processes raw HTML and extracted content in JSON format, using an LLM to identify core content (title, author, date, main text) and evaluate the extraction’s completeness (how much core content is captured) and purity (how little noise is included). The final score is computed as `completeness - (1 - purity)`, ensuring a range from -1 to 1. This approach leverages the LLM’s ability to understand webpage structure and semantics, making it flexible and robust.

### Benefits
- **Semantic Accuracy**: LLMs can understand context, improving evaluation over traditional metrics.
- **No Manual Gold Standard**: Eliminates the need for labor-intensive annotations.
- **Flexibility**: Handles diverse webpage structures and languages.

### Considerations
- **Cost**: Cloud LLM calls can be expensive; using cost-effective models like GPT-4o-mini helps.
- **Consistency**: Careful prompt design is needed to ensure reliable LLM outputs.
- **Validation**: Testing against benchmarks like [CleanEval](https://www.researchgate.net/publication/220746707_Cleaneval_A_Competition_for_Cleaning_Web_Pages) ensures accuracy.

---

### Revised System for Evaluating News Article Extraction Quality

To create a more refined system for evaluating the quality of news article extractions from web scraping, I propose a streamlined approach centered on large language models (LLMs) to assess completeness and purity, producing a quality score from -1 to 1. This system builds on the strengths of the provided design while addressing its weaknesses, such as reliance on proxy gold standards and empirical weights, by leveraging LLMs’ semantic understanding of HTML and content. The system is designed to be comprehensive, robust, deterministic, and reliable, suitable for running on a single Mac with Python 3.11, with optional cloud LLM integration for enhanced accuracy.

#### System Architecture

The system comprises three main components:

1. **Pre-processor**:
   - Reads raw HTML and extracted content in JSON format.
   - Detects the language using a library like langdetect to inform LLM processing.
   - Optionally simplifies HTML to manage large files, though raw HTML is typically sufficient for LLMs.

2. **LLM Evaluator**:
   - **Core Content Identification**: Uses a prompt to extract title, author, publication date, and main text from the HTML, leveraging LLMs’ ability to parse HTML, as demonstrated in research on [HTML understanding with LLMs](https://openreview.net/forum?id=GVMwL15UrZO).
   - **Completeness Assessment**: Compares the extracted content to the identified core content, rating the proportion of core content captured (0 to 1).
   - **Purity Assessment**: Evaluates the extracted content for noise (e.g., ads, navigation), rating the proportion of core content (0 to 1).
   - Uses a cost-effective LLM like GPT-4o-mini for efficiency, with prompts designed for consistency.

3. **Aggregator**:
   - Combines completeness and purity scores into a final quality score using the formula `completeness - (1 - purity)`.
   - Handles edge cases, such as empty extractions, by assigning a score of 0.

#### Input and Output Contracts

**Input**:
```json
{
  "url": "https://example.com/news/article",
  "language": "auto",
  "html": "<html>...</html>",
  "extracted": {
    "title": "Article Title",
    "author": "Author Name",
    "date": "2025-05-29",
    "content": "Main article text..."
  }
}
```

**Output**:
```json
{
  "score": 0.85,
  "subscores": {
    "completeness": 0.95,
    "purity": 0.90
  },
  "explanation": "The extraction captures the title, author, date, and most of the main text, but includes a minor advertisement."
}
```

#### Algorithms and Implementation

The system relies on Python 3.11 for preprocessing and LLM integration, with the following key algorithms:

**Pre-processing**:
- **Language Detection**: Uses langdetect to identify the language, ensuring the LLM applies appropriate linguistic rules. For robustness, a fallback to user-specified language can be implemented for short or mixed-language texts.
- **HTML Handling**: Reads raw HTML using libraries like BeautifulSoup for parsing if needed, though the LLM can process raw HTML directly, as supported by studies on [LLM HTML parsing](https://medium.com/@ignacio.cplatas/enhancing-web-scraping-with-large-language-models-a-modern-approach-6216d5bba8d5).

**LLM Evaluation**:
- **Core Content Identification**: A prompt instructs the LLM to extract core content from the HTML, focusing on semantic tags (e.g., `<article>`, `<h1>`) and common class names (e.g., "story-body"). The LLM’s ability to understand HTML structure, as shown in [HTML understanding with LLMs](https://openreview.net/forum?id=GVMwL15UrZO), ensures accurate identification.
- **Completeness Assessment**: The LLM compares the extracted JSON fields (title, author, date, content) to the identified core content, checking for presence and accuracy. For the main text, it samples five random sentences from the core content and checks their presence in the extracted content, averaging the results with binary checks for title, author, and date.
- **Purity Assessment**: The LLM scans the extracted content for noise indicators (e.g., "Sponsored", "Related Articles") and estimates the noise proportion, assigning a purity score as 1 minus the noise proportion.

**Prompt for Core Content Identification**:

Given the following HTML of a news article webpage, extract the core content:
- Title
- Author(s)
- Publication date
- Main article text (excluding ads, navigation, etc.)

HTML:
[insert HTML here]

Provide the extracted information in JSON format:
{
  "title": "...",
  "author": "...",
  "date": "...",
  "main_text": "..."
}


**Prompt for Completeness Assessment**:

Given the core content of a news article and the extracted content, assess how much of the core content is present in the extracted content.

Core Content:
{
  "title": "...",
  "author": "...",
  "date": "...",
  "main_text": "..."
}

Extracted Content:
{
  "title": "...",
  "author": "...",
  "date": "...",
  "content": "..."
}

Steps:
1. Check if the extracted title matches the core title (1 if match, 0 if not).
2. Check if the extracted author matches the core author (1 if match, 0 if not).
3. Check if the extracted date matches the core date (1 if match, 0 if not).
4. Select 5 random sentences from the core main text and check how many are present in the extracted content (proportion, e.g., 4/5 = 0.8).
5. Compute completeness as the average of these four scores.

Return:
{
  "completeness": 0.XX,
  "rationale": "Explanation of the assessment"
}


**Prompt for Purity Assessment**:

Given the extracted content from a news article, assess how much of it is noise (e.g., ads, navigation, unrelated text).

Extracted Content:
{
  "title": "...",
  "author": "...",
  "date": "...",
  "content": "..."
}

Steps:
1. Identify noise elements (e.g., text containing "Sponsored", "Advertisement", "Related Articles", navigation links).
2. Estimate the proportion of the content that is noise (e.g., 20% noise = 0.2).
3. Compute purity as 1 minus the noise proportion.

Return:
{
  "purity": 0.XX,
  "rationale": "Explanation of the assessment"
}


**Score Calculation**:
```python
def calculate_quality_score(completeness, purity):
    if completeness == 0 and purity == 0:  # Empty extraction
        return 0
    return completeness - (1 - purity)
```

#### Operating Modes

The system supports multiple operating modes to balance cost and accuracy:

| Mode             | Components Used        | Cost           | Throughput       |
|------------------|-----------------------|----------------|------------------|
| Local-only       | Pre-processor only    | Free           | 500 pages/sec    |
| Hybrid-cheap     | + GPT-4o-mini Eval    | ~$0.001/page   | 5–10 pages/sec   |
| Full             | + GPT-4 Eval          | ~$0.02/page    | 1 page/sec       |

- **Local-only**: Suitable for preprocessing and basic validation, but lacks semantic evaluation.
- **Hybrid-cheap**: Uses GPT-4o-mini for cost-effective LLM evaluation, ideal for most use cases.
- **Full**: Employs GPT-4 for maximum accuracy, suitable for critical evaluations.

#### Validation and Benchmarks

To ensure reliability, the system should be validated against established benchmarks:
- **CleanEval 2007**: 700 pages, English and Chinese, with human-cleaned gold standards ([CleanEval](https://www.researchgate.net/publication/220746707_Cleaneval_A_Competition_for_Cleaning_Web_Pages)).
- **Zyte Benchmark**: 500 pages, English, with JSON gold standards ([Zyte Benchmark](https://github.com/scrapinghub/article-extraction-benchmark)).
- **Trafilatura Evaluation Set**: 750 documents, multiple languages, with ROUGE-LSum metrics ([Trafilatura](https://trafilatura.readthedocs.io/en/latest/evaluation.html)).
- **Webis 2023**: Combines eight datasets for comprehensive testing ([Webis](https://downloads.webis.de/theses/papers/gupta_2022.pdf)).

Start with Zyte for JSON compatibility, then use CleanEval for multilingual validation. Compare LLM scores to human evaluations or benchmark metrics to tune prompt effectiveness.

#### Enhancements and Extensions

- **Multiple Extractors for Proxy Gold Standard**: Combine outputs from tools like Readability, Trafilatura, and Boilerpipe to create a more reliable proxy gold standard, as suggested by research on [web content extraction algorithms](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms). This can be used for validation or as a fallback if LLM evaluation is too costly.
- **Prompt Optimization**: Fine-tune prompts using a small validation set to ensure consistent LLM outputs, addressing potential variability noted in [LLM evaluation studies](https://www.sciencedirect.com/science/article/pii/S0010482524002737).
- **Rich Media Handling**: Extend evaluation to include images and captions by adding fields to the JSON input and prompts to check their relevance, enhancing completeness assessment.
- **Diagnostic Feedback**: Include detailed error analysis in the output (e.g., missing paragraphs, specific noise types) to guide pipeline improvements.
- **Streaming Pipeline**: For large-scale processing, parallelize preprocessing and batch LLM calls for low-confidence cases, as suggested in the original design.

#### Comparison with Original Design

The original design combined classical metrics (precision, recall), heuristics (noise score), and optional LLM evaluations (direct scoring, QA recall). While effective, it relied on proxy gold standards and empirical weights, which could introduce inaccuracies. The revised system:
- Centers on LLM evaluation for semantic accuracy, reducing dependence on potentially flawed proxy standards.
- Simplifies the scoring process by focusing on completeness and purity, making it more deterministic.
- Retains flexibility with operating modes but prioritizes LLM capabilities, supported by research on [LLM HTML understanding](https://openreview.net/forum?id=GVMwL15UrZO).
- Maintains compatibility with benchmarks like CleanEval and Zyte for validation.

#### Practical Considerations

- **Implementation**: Use Python 3.11 with libraries like langdetect, BeautifulSoup, and OpenAI’s API for LLM integration. Ensure the LLM context window (e.g., 128k tokens for GPT-4o-mini) can handle typical HTML sizes, truncating non-essential sections if needed.
- **Cost Management**: Use GPT-4o-mini for cost efficiency (~$0.001/page) and cache LLM responses for similar pages to reduce API calls.
- **Consistency**: Set LLM temperature to 0 for deterministic outputs and average multiple evaluations if variability persists.
- **Scalability**: Batch process inputs for large datasets, leveraging cloud LLMs for high-throughput modes.

#### Example Evaluation

Consider an article with a title, author, date, and 10 paragraphs in the HTML. The extracted JSON captures the correct title, author, date, and 8 paragraphs but includes an advertisement. The LLM:
- Identifies core content: title, author, date, and main text.
- Completeness: Title, author, date match (1 each); 4/5 sampled sentences present (0.8). Completeness = (1 + 1 + 1 + 0.8) / 4 = 0.95.
- Purity: Estimates 10% noise (advertisement). Purity = 1 - 0.1 = 0.9.
- Score: 0.95 - (1 - 0.9) = 0.85.

This score reflects a high-quality extraction with minor noise, aligning with the desired -1 to 1 range.

#### Research Insights

Research supports the use of LLMs for HTML parsing and content extraction:
- A study on [HTML understanding with LLMs](https://openreview.net/forum?id=GVMwL15UrZO) shows fine-tuned LLMs achieve 12% higher accuracy in semantic HTML tasks, suggesting their suitability for identifying core content.
- Articles on [web scraping with LLMs](https://medium.com/@ignacio.cplatas/enhancing-web-scraping-with-large-language-models-a-modern-approach-6216d5bba8d5) highlight LLMs’ ability to structure data from webpages, supporting their use in evaluation.
- Benchmarks like [CleanEval](https://www.researchgate.net/publication/220746707_Cleaneval_A_Competition_for_Cleaning_Web_Pages) and [Zyte](https://github.com/scrapinghub/article-extraction-benchmark) use precision, recall, and F1 scores, which the LLM can approximate semantically without manual annotations.

#### Limitations and Future Work

- **Cost**: Cloud LLM calls may be expensive for large datasets; local models like LLaMA could be explored for cost-free Oto.
- **HTML Complexity**: Some webpages with dynamic content may challenge LLM parsing; combining LLM evaluation with heuristic preprocessing could help.
- **Consistency**: LLM variability can be mitigated with prompt engineering and validation against benchmarks.
- **Future Enhancements**: Incorporate ensemble methods from multiple extractors for validation, as suggested by [web content extraction studies](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms), and explore fine-tuning LLMs on extraction evaluation datasets.

This revised system offers a robust, semantic, and scalable solution for evaluating news article extractions, leveraging LLMs’ advanced capabilities while maintaining compatibility with established benchmarks.

**Key Citations**:
- [CleanEval: A Competition for Cleaning Web Pages](https://www.researchgate.net/publication/220746707_Cleaneval_A_Competition_for_Cleaning_Web_Pages)
- [Zyte Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark)
- [Trafilatura Evaluation Set](https://trafilatura.readthedocs.io/en/latest/evaluation.html)
- [Webis Combined 2023 Dataset](https://downloads.webis.de/theses/papers/gupta_2022.pdf)
- [Understanding HTML with Large Language Models](https://openreview.net/forum?id=GVMwL15UrZO)
- [Enhancing Web Scraping with Large Language Models](https://medium.com/@ignacio.cplatas/enhancing-web-scraping-with-large-language-models-a-modern-approach-6216d5bba8d5)
- [Comprehensive Evaluation of LLMs on Biomedical Tasks](https://www.sciencedirect.com/science/article/pii/S0010482524002737)
- [Comparison of Web Content Extraction Algorithms](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms)