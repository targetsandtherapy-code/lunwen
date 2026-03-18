"""相关性排序模块 — 使用 LLM 对候选文献与段落内容打分"""
import json
from openai import OpenAI
from modules.searcher.base import Paper
from config import QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL


class RelevanceRanker:
    def __init__(self, api_key: str = QWEN_API_KEY, base_url: str = QWEN_BASE_URL, model: str = QWEN_MODEL):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def rank(self, context: str, claim: str, candidates: list[Paper], top_k: int = 3) -> list[Paper]:
        if not candidates:
            return []

        if len(candidates) <= top_k:
            return candidates

        candidates_text = ""
        for i, p in enumerate(candidates):
            abstract_preview = (p.abstract or "无摘要")[:150]
            candidates_text += f"\n{i+1}. 标题: {p.title}\n   摘要: {abstract_preview}\n   期刊: {p.journal or 'N/A'} | 年份: {p.year} | 被引: {p.citation_count or 0}\n"

        prompt = f"""你是学术论文引用匹配专家。请评估以下候选文献与论文段落的相关性。

论文段落上下文：
{context}

该引用需要支撑的论点：
{claim}

候选文献：
{candidates_text}

请对每篇候选文献打分(1-10分)，评分标准：
- 10分: 论文直接论述该论点，是最佳引用
- 7-9分: 高度相关，涵盖核心主题
- 4-6分: 部分相关，涉及相关领域
- 1-3分: 弱相关或不相关

请严格按以下 JSON 格式返回（不要添加其他文字）：
{{
  "rankings": [
    {{"index": 1, "score": 9, "reason": "简短理由"}},
    {{"index": 2, "score": 5, "reason": "简短理由"}}
  ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是学术论文引用匹配专家，擅长评估文献与论文段落的相关性。只返回 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
            )

            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            rankings = data.get("rankings", [])

            score_map = {}
            for r in rankings:
                idx = r.get("index", 0)
                score = r.get("score", 0)
                if 1 <= idx <= len(candidates):
                    score_map[idx - 1] = score

            scored = []
            for i, p in enumerate(candidates):
                scored.append((score_map.get(i, 0), p))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [p for _, p in scored[:top_k]]

        except Exception as e:
            print(f"[RelevanceRanker] 排序失败，返回原始顺序: {e}")
            return candidates[:top_k]
