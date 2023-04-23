import unittest
import util


class MyTestCase(unittest.TestCase):
    def test_readable_file_size(self):
        self.assertEqual(util.readable_file_size(0, suffix="B", justify_left=False), "    0.0 B")
        self.assertEqual(util.readable_file_size(1023, suffix="B", justify_left=False), " 1023.0 B")
        self.assertEqual(util.readable_file_size(1024, suffix="B", justify_left=False), "   1.0 KB")
        self.assertEqual(util.readable_file_size(1025, suffix="B", justify_left=False), "   1.0 KB")
        self.assertEqual(util.readable_file_size(2000, suffix="B", justify_left=False), "   2.0 KB")
        self.assertEqual(util.readable_file_size(1024 * 1024, suffix="B", justify_left=False), "   1.0 MB")
        self.assertEqual(util.readable_file_size(1024 * 1024 * 1024, suffix="B", justify_left=False), "   1.0 GB")


if __name__ == '__main__':
    unittest.main()
