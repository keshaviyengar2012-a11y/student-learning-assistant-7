import unittest

from assistant import curriculum


class Curriculum(unittest.TestCase):
    def test_cbse_grade_10_maths(self):
        names = [t["name"] for t in curriculum.topics("CBSE", 10, "math")]
        self.assertIn("Quadratic Equations", names)

    def test_igcse_has_additional_maths(self):
        self.assertIn("advmath", curriculum.subjects("Cambridge IGCSE", 10))

    def test_board_without_built_in_list(self):
        self.assertIsNone(curriculum.syllabus("ICSE", 10))
        self.assertIn("math", curriculum.subjects("ICSE", 10))


if __name__ == "__main__":
    unittest.main()
