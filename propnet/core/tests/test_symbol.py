import unittest

from propnet.core.symbols import Symbol
from propnet.core.registry import Registry


class SymbolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_symbol = Registry("symbols").get("youngs_modulus")

    @classmethod
    def tearDownClass(cls):
        if cls.old_symbol is not None:
            Registry("symbol")['youngs_modulus'] = cls.old_symbol

    def test_property_construction(self):
        sample_symbol_type_dict = {
            'name': 'youngs_modulus',
            'units': [1.0, [["gigapascal", 1.0]]],
            'display_names': ["Young's modulus", "Elastic modulus"],
            'display_symbols': ["E"],
            'shape': 1,
            'comment': ""
        }

        sample_symbol_type = Symbol(
            name='youngs_modulus',  #
            units=[1.0, [["gigapascal", 1.0]]],  #ureg.parse_expression("GPa"),
            display_names=["Young's modulus", "Elastic modulus"],
            display_symbols=["E"],
            shape=1,
            comment="")

        self.assertEqual(sample_symbol_type,
                         Symbol.from_dict(sample_symbol_type_dict))


if __name__ == "__main__":
    unittest.main()
