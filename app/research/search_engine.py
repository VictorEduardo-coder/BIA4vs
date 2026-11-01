import json
import re
import urllib.parse
import urllib.request

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


class SearchEngine:
    TRIGGER_PATTERNS = [
        r"\bversão mais recente\b",
        r"\búltima versão\b",
        r"\bdocumentação oficial\b",
        r"\bpesquise\b",
        r"\bpesquisar\b",
        r"\bconsulte a documentação\b",
        r"\batualizado\b",
        r"\batualmente\b",
        r"\blançamento\b",
        r"\bcve-\d{4}-\d+\b"
    ]

    def needs_external_search(self, query):
        text = query.lower()
        for pattern in self.TRIGGER_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def search(self, query, max_results=4):
        if DDGS is not None:
            results = []
            try:
                with DDGS() as ddgs:
                    for row in ddgs.text(query, max_results=max_results):
                        results.append({
                            "title": row.get("title", "Sem título"),
                            "url": row.get("href", ""),
                            "snippet": row.get("body", "")
                        })
                if results:
                    return results
            except Exception:
                pass
        return self._fallback_search(query, max_results)

    def _fallback_search(self, query, max_results=4):
        results = []
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "BIA4vs/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "Resultado Principal"),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", "")
                })
            for topic in data.get("RelatedTopics", []):
                if len(results) >= max_results:
                    break
                if "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:60],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")
                    })
        except Exception as exc:
            return [{"title": "Erro na pesquisa externa", "url": "", "snippet": str(exc)}]
        return results

    def format_results_for_context(self, results):
        if not results:
            return "Nenhum resultado externo encontrado."
        lines = ["RESULTADOS DE PESQUISA EXTERNA:"]
        for idx, item in enumerate(results, 1):
            lines.append(f"{idx}. Fonte: {item['title']}")
            if item["url"]:
                lines.append(f"   Link: {item['url']}")
            lines.append(f"   Resumo: {item['snippet']}")
        return "\n".join(lines)