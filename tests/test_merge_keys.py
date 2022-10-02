from io import StringIO
from unittest import TestCase, main

from src.merge_keys import read_src, write_dst

ORIGINAL = f"""
t_type1 k_key1
# t_type2 k_key2
t_type3 k_key3
""".strip()


class TestMergeKeys(TestCase):
    def setUp(self) -> None:
        self.dst = StringIO(ORIGINAL)

    def assertContents(self, expected: str):
        self.dst.seek(0)
        contents = self.dst.read()
        self.assertEqual(expected, contents)

    def read_and_write(self, src):
        add, rem = read_src(src)
        write_dst(self.dst, add, rem)

    def test_blank_src(self):
        self.read_and_write(StringIO(""))
        self.assertContents(ORIGINAL)

    def test_empty_src(self):
        self.read_and_write(StringIO(f"\n  \n  # t_type1k_key1  \n\n \n"))
        self.assertContents(ORIGINAL)

    def test_invalid_line_ignored(self):
        self.read_and_write(
            StringIO(
                f"""
t_type1k_key1
t_type4 k_key4
"""
            )
        )
        self.assertContents(ORIGINAL + f"\nt_type4 k_key4")

    def test_remove_commented_out_src_keys(self):
        self.read_and_write(
            StringIO(
                f"""
# t_type2 k_key2
# t_type3 k_key3
# t_type1 k_key2
# t_type1 k_key3
# t_type1 k_key4
"""
            )
        )
        self.assertContents(f"""t_type1 k_key1""")

    def test_add_new_src_keys(self):
        self.read_and_write(
            StringIO(
                f"""
t_type1 k_key2
t_type2 k_key1
"""
            )
        )
        self.assertContents(ORIGINAL + f"\nt_type1 k_key2\nt_type2 k_key1")

    def test_existing_src_keys(self):
        self.read_and_write(
            StringIO(
                f"""
t_type3 k_key3
t_type1 k_key1
t_type2 k_key1
"""
            )
        )
        self.assertContents(ORIGINAL + f"\nt_type2 k_key1")

    def test_src_key_is_commented_out_in_dst(self):
        self.read_and_write(
            StringIO(
                f"""
t_type2 k_key2
t_type1 k_key1
t_type2 k_key1
"""
            )
        )
        self.assertContents(
            f"""t_type1 k_key1
t_type2 k_key2
t_type3 k_key3
t_type2 k_key1"""
        )


if __name__ == "__main__":
    main()
