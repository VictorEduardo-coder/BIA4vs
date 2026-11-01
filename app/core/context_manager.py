from config.settings import MAX_CONTEXT_MESSAGES, SYSTEM_PROMPT


class ContextManager:
    def __init__(self, history_store, code_analyzer):
        self.history_store = history_store
        self.code_analyzer = code_analyzer

    def build_messages(self, conversation_id, user_prompt, attachments=None, search_context=None):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        past_messages = self.history_store.get_messages(
            conversation_id, limit=MAX_CONTEXT_MESSAGES
        )
        for msg in past_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})

        enriched_parts = []
        if search_context:
            enriched_parts.append(search_context)

        if attachments:
            for item in attachments:
                diag = self.code_analyzer.analyze_attachment(item)
                enriched_parts.append(
                    f"--- ANEXO: {item['name']} ---\n"
                    f"Diagnóstico Preliminar:\n{diag}\n\n"
                    f"Conteúdo:\n{item['content']}\n"
                    f"--- FIM DO ANEXO {item['name']} ---"
                )

        enriched_parts.append(user_prompt)
        messages.append({"role": "user", "content": "\n\n".join(enriched_parts)})
        return messages