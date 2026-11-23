import tempfile
import unittest
from pathlib import Path
from app.code_analysis.analyzer import CodeAnalyzer
from app.core.context_manager import ContextManager
from app.storage.conversation_history import ConversationHistory
from config.settings import MAX_CONTEXT_MESSAGES, SYSTEM_PROMPT


class TestStorageAndContext(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_file = Path(self.tmp.name) / "test_history.db"
        self.history = ConversationHistory(db_path=self.db_file)
        self.analyzer = CodeAnalyzer()
        self.context = ContextManager(self.history, self.analyzer)

    def tearDown(self):
        self.tmp.cleanup()

    def test_conversation_crud_and_message_ordering(self):
        conv_id = self.history.create_conversation("Sessão Inicial")
        self.history.rename_conversation(conv_id, "  Análise SQL  ")

        convs = self.history.list_conversations()
        self.assertEqual(len(convs), 1)
        self.assertEqual(convs[0]["title"], "Análise SQL")

        self.history.add_message(conv_id, "user", "Primeira pergunta")
        self.history.add_message(conv_id, "assistant", "Primeira resposta")
        self.history.add_message(conv_id, "user", "Segunda pergunta")

        msgs = self.history.get_messages(conv_id, limit=2)
        self.assertEqual(len(msgs), 2)
        self.assertEqual([m["content"] for m in msgs], ["Primeira resposta", "Segunda pergunta"])

        self.history.delete_conversation(conv_id)
        self.assertEqual(self.history.list_conversations(), [])
        self.assertEqual(self.history.get_messages(conv_id), [])

    def test_context_manager_respects_window_and_injects_attachments(self):
        conv_id = self.history.create_conversation("Contexto")
        for idx in range(MAX_CONTEXT_MESSAGES + 4):
            self.history.add_message(conv_id, "user", f"msg-{idx}")

        attachment = {
            "name": "query.sql",
            "extension": ".sql",
            "content": "DELETE FROM logs;",
        }
        messages = self.context.build_messages(
            conv_id,
            user_prompt="Verifique riscos nesse SQL",
            attachments=[attachment],
            search_context="Doc oficial SQLite",
        )

        # 1 system + MAX_CONTEXT_MESSAGES history + 1 current enriched user prompt
        self.assertEqual(len(messages), MAX_CONTEXT_MESSAGES + 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], SYSTEM_PROMPT)

        final_prompt = messages[-1]["content"]
        self.assertIn("Doc oficial SQLite", final_prompt)
        self.assertIn("--- ANEXO: query.sql ---", final_prompt)
        self.assertIn("DELETE sem cláusula WHERE", final_prompt)
        self.assertIn("Verifique riscos nesse SQL", final_prompt)


if __name__ == "__main__":
    unittest.main()
