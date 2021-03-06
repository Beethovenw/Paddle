import unittest

import paddle.v2.framework.core as core
from paddle.v2.framework.framework import Program
from paddle.v2.framework.framework import g_program


class TestProgram(unittest.TestCase):
    def test_program(self):
        b = g_program.current_block()
        self.assertEqual(-1, b.parent_idx)
        self.assertEqual(0, b.idx)

        b = g_program.create_block()
        self.assertEqual(1, b.idx)
        self.assertEqual(0, b.parent_idx)

        b = g_program.create_block()
        self.assertEqual(2, b.idx)
        self.assertEqual(1, b.parent_idx)

        g_program.rollback()

        b = g_program.current_block()
        self.assertEqual(1, b.idx)
        self.assertEqual(0, b.parent_idx)

        b = g_program.create_block()
        self.assertEqual(3, b.idx)
        self.assertEqual(1, b.parent_idx)

        g_program.rollback()
        b = g_program.current_block()
        self.assertEqual(1, b.idx)
        self.assertEqual(0, b.parent_idx)

    def test_append_backward(self):
        prog = Program.instance()
        block = prog.global_block()

        mul_x = block.create_var(
            dtype="float32", shape=[5, 10], lod_level=0, name="mul.x")
        mul_y = block.create_var(
            dtype="float32", shape=[10, 8], lod_level=0, name="mul.y")
        mul_out = block.create_var(
            dtype="float32", shape=[5, 8], lod_level=0, name="mul.out")
        mul_op = block.append_op(
            type="mul",
            inputs={"X": [mul_x],
                    "Y": mul_y},
            outputs={"Out": [mul_out]},
            attrs={"x_num_col_dims": 1})

        add_y = block.create_var(
            dtype="float32", shape=[5, 8], lod_level=0, name="add.y")
        add_out = block.create_var(
            dtype="float32", shape=[5, 8], lod_level=0, name="add.out")
        add_op = block.append_op(
            type="elementwise_add",
            inputs={"X": mul_out,
                    "Y": add_y},
            outputs={"Out": add_out},
            attrs={"x_num_col_dims": 1})

        param_to_grad = prog.append_backward(add_out, set())

        def grad_name(name):
            return name + "@GRAD"

        for var_name in ("mul.x", "mul.y", "mul.out", "add.y", "add.out"):
            self.assertEqual(param_to_grad[var_name][0], grad_name(var_name))
            self.assertEqual(param_to_grad[var_name][1], 0)

        expect_ops = [
            "mul", "elementwise_add", "fill_constant", "elementwise_add_grad",
            "mul_grad"
        ]
        actual_ops = []
        for op in block.ops:
            actual_ops.append(op.type)
        self.assertEqual(actual_ops, expect_ops)


if __name__ == '__main__':
    unittest.main()
