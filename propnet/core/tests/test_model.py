import unittest

import math
import numpy as np

from propnet.core.models import EquationModel
from propnet.core.symbols import Symbol
from propnet.core.quantity import QuantityFactory
from propnet.core.registry import Registry

# TODO: test PyModule, PyModel
# TODO: separate these into specific tests of model functionality
#       and validation of default models


class ModelTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        non_builtin_syms = [k for k, v in Registry("symbols").items() if not v.is_builtin]
        for sym in non_builtin_syms:
            Registry("symbols").pop(sym)
            Registry("units").pop(sym)
        non_builtin_models = [k for k, v in Registry("models").items() if not v.is_builtin]
        for model in non_builtin_models:
            Registry("models").pop(model)

    def test_unit_handling(self):
        """
        Tests unit handling with a simple model that calculates the area of a rectangle as the
        product of two lengths.

        In this case the input lengths are provided in centimeters and meters.
        Tests whether the input units are properly coerced into canonical types.
        Tests whether the output units are properly set.
        Tests whether the model returns as predicted.
        Returns:
            None
        """
        L = Symbol('l', ['L'], ['L'], units=[1.0, [['centimeter', 1.0]]], shape=[1])
        A = Symbol('a', ['A'], ['A'], units=[1.0, [['centimeter', 2.0]]], shape=[1])

        for sym in (L, A):
            Registry("symbols")[sym] = sym
            Registry("units")[sym] = sym.units

        get_area_config = {
            'name': 'area',
            # 'connections': [{'inputs': ['l1', 'l2'], 'outputs': ['a']}],
            'equations': ['a = l1 * l2'],
            # 'unit_map': {'l1': "cm", "l2": "cm", 'a': "cm^2"}
            'symbol_property_map': {"a": A, "l1": L, "l2": L}
        }
        model = EquationModel(**get_area_config)
        out = model.evaluate({'l1': QuantityFactory.create_quantity(L, 1, 'meter'),
                              'l2': QuantityFactory.create_quantity(L, 2)}, allow_failure=False)

        self.assertTrue(math.isclose(out['a'].magnitude, 200.0))
        self.assertTrue(out['a'].units == A.units)

    def test_model_returns_nan(self):
        # This tests model failure with scalar nan.
        # Quantity class has other more thorough tests.

        A = Symbol('a', ['A'], ['A'], units='dimensionless', shape=1)
        B = Symbol('b', ['B'], ['B'], units='dimensionless', shape=1)
        for sym in (B, A):
            Registry("symbols")[sym] = sym
            Registry("units")[sym] = sym.units
        get_config = {
            'name': 'equality',
            # 'connections': [{'inputs': ['b'], 'outputs': ['a']}],
            'equations': ['a = b'],
            # 'unit_map': {'a': "dimensionless", 'a': "dimensionless"}
            'symbol_property_map': {"a": A, "b": B}
        }
        model = EquationModel(**get_config)
        out = model.evaluate({'b': QuantityFactory.create_quantity(B, float('nan'))},
                             allow_failure=True)
        self.assertFalse(out['successful'])
        self.assertEqual(out['message'], 'Evaluation returned invalid values (NaN)')

    def test_model_returns_complex(self):
        # This tests model failure with scalar complex.
        # Quantity class has other more thorough tests.

        A = Symbol('a', ['A'], ['A'], units='dimensionless', shape=1)
        B = Symbol('b', ['B'], ['B'], units='dimensionless', shape=1)
        for sym in (B, A):
            Registry("symbols")[sym] = sym
            Registry("units")[sym] = sym.units
        get_config = {
            'name': 'add_complex_value',
            # 'connections': [{'inputs': ['b'], 'outputs': ['a']}],
            'equations': ['a = b + 1j'],
            # 'unit_map': {'a': "dimensionless", 'a': "dimensionless"}
            'symbol_property_map': {"a": A, "b": B}
        }
        model = EquationModel(**get_config)
        out = model.evaluate({'b': QuantityFactory.create_quantity(B, 5)},
                             allow_failure=True)
        self.assertFalse(out['successful'])
        self.assertEqual(out['message'], 'Evaluation returned invalid values (complex)')

        out = model.evaluate({'b': QuantityFactory.create_quantity(B, 5j)},
                             allow_failure=True)
        self.assertTrue(out['successful'])
        self.assertTrue(np.isclose(out['a'].magnitude, 6j))

    def test_model_register_unregister(self):
        A = Symbol('a', ['A'], ['A'], units='dimensionless', shape=1)
        B = Symbol('b', ['B'], ['B'], units='dimensionless', shape=1)
        C = Symbol('c', ['C'], ['C'], units='dimensionless', shape=1)
        D = Symbol('d', ['D'], ['D'], units='dimensionless', shape=1)
        m = EquationModel('equation_model_to_remove', ['a = b * 3'], symbol_property_map={'a': A, 'b': B})
        self.assertIn(m.name, Registry("models"))
        self.assertTrue(m.registered)
        m.unregister()
        self.assertNotIn(m.name, Registry("models"))
        self.assertFalse(m.registered)
        m.register()
        self.assertTrue(m.registered)
        with self.assertRaises(KeyError):
            m.register(overwrite_registry=False)

        m.unregister()
        m = EquationModel('equation_model_to_remove', ['a = b * 3'], symbol_property_map={'a': A, 'b': B},
                          register=False)
        self.assertNotIn(m.name, Registry("models"))
        self.assertFalse(m.registered)

        m.register()
        with self.assertRaises(KeyError):
            _ = EquationModel('equation_model_to_remove', ['a = b * 3'],
                              symbol_property_map={'a': A, 'b': B},
                              register=True, overwrite_registry=False)

        m_replacement = EquationModel('equation_model_to_remove', ['c = d * 3'],
                                      symbol_property_map={'c': C, 'd': D})

        m_registered = Registry("models")['equation_model_to_remove']
        self.assertIs(m_registered, m_replacement)
        self.assertIsNot(m_registered, m)


if __name__ == "__main__":
    unittest.main()
