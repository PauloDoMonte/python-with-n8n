import unittest
from app import extrair_regiao, classificar_pergunta

class TestAppFunctions(unittest.TestCase):

    def test_extrair_regiao(self):
        # Teste com diferentes variações de input para a função extrair_regiao
        self.assertEqual(extrair_regiao("Qual é a disponibilidade na região da Bahia?"), "Bahia")
        self.assertEqual(extrair_regiao("Estou interessado na região de São Paulo"), "São Paulo")
        self.assertEqual(extrair_regiao("Há imóveis na região do Rio de Janeiro?"), "Rio de Janeiro")
        self.assertIsNone(extrair_regiao("Qual é a disponibilidade?"))  # Caso em que a região não é mencionada

    def test_classificar_pergunta(self):
        # Teste com diferentes tipos de perguntas
        self.assertEqual(classificar_pergunta("Qual é a disponibilidade na região da Bahia?"), "disponibilidade")
        self.assertEqual(classificar_pergunta("Estou interessado na venda de imóveis"), "venda")
        self.assertEqual(classificar_pergunta("Gostaria de saber sobre o aluguel de apartamentos"), "aluguel")
        self.assertEqual(classificar_pergunta("Qual é o preço?"), "indefinido")  # Caso em que a pergunta não é categorizada

if __name__ == '__main__':
    unittest.main()
