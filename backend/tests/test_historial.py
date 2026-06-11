import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from app.repositories import historial


class ConversationOwnershipTests(unittest.TestCase):
    def test_history_is_returned_in_chronological_order(self):
        query = MagicMock()
        query.table.return_value = query
        query.select.return_value = query
        query.eq.return_value = query
        query.order.return_value = query
        query.limit.return_value = query
        query.execute.return_value = SimpleNamespace(
            data=[
                {"rol": "bot", "texto": "Respuesta"},
                {"rol": "user", "texto": "Pregunta"},
            ]
        )

        with patch.object(historial, "supabase", query):
            mensajes = historial.obtener_historial(
                "conversation-1",
                limite=500,
            )

        self.assertEqual(
            mensajes,
            [
                {"role": "user", "content": "Pregunta"},
                {"role": "assistant", "content": "Respuesta"},
            ],
        )

    def test_rename_filters_by_owner(self):
        query = MagicMock()
        query.table.return_value = query
        query.update.return_value = query
        query.eq.return_value = query
        query.execute.return_value = SimpleNamespace(data=[])

        with patch.object(historial, "supabase", query):
            historial.renombrar_conversacion(
                "conversation-1",
                "user-1",
                "Nuevo titulo",
            )

        self.assertIn(call("id", "conversation-1"), query.eq.call_args_list)
        self.assertIn(call("user_id", "user-1"), query.eq.call_args_list)

    def test_delete_filters_by_owner(self):
        query = MagicMock()
        query.table.return_value = query
        query.delete.return_value = query
        query.eq.return_value = query
        query.execute.return_value = SimpleNamespace(data=[])

        with patch.object(historial, "supabase", query):
            historial.eliminar_conversacion(
                "conversation-1",
                "user-1",
            )

        self.assertIn(call("id", "conversation-1"), query.eq.call_args_list)
        self.assertIn(call("user_id", "user-1"), query.eq.call_args_list)
