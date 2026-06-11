import unittest

from app.repositories.cache import generar_clave_cache


class CacheKeyTests(unittest.TestCase):
    def test_key_is_isolated_by_user(self):
        key_a = generar_clave_cache("Pregunta", "user-a", [])
        key_b = generar_clave_cache("Pregunta", "user-b", [])

        self.assertNotEqual(key_a, key_b)

    def test_key_changes_with_conversation_context(self):
        history_a = [{"role": "user", "content": "Contrato laboral"}]
        history_b = [{"role": "user", "content": "Contrato civil"}]

        key_a = generar_clave_cache("Requisitos", "user-a", history_a)
        key_b = generar_clave_cache("Requisitos", "user-a", history_b)

        self.assertNotEqual(key_a, key_b)
