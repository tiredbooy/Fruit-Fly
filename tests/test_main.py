import unittest

from main import build_parser


class MainCliTest(unittest.TestCase):
    def test_data_status_command_is_available(self) -> None:
        arguments = build_parser().parse_args(["data-status"])

        self.assertEqual("data-status", arguments.command)

    def test_animated_run_command_is_available(self) -> None:
        arguments = build_parser().parse_args(
            [
                "run",
                "--animate",
                "--steps",
                "2",
                "--fps",
                "20",
                "--memory-file",
                "/tmp/test-memory.json",
                "--reset-memory",
                "--seed",
                "1234",
            ]
        )

        self.assertEqual("run", arguments.command)
        self.assertTrue(arguments.animate)
        self.assertEqual(2, arguments.steps)
        self.assertEqual(20.0, arguments.fps)
        self.assertEqual("/tmp/test-memory.json", str(arguments.memory_file))
        self.assertTrue(arguments.reset_memory)
        self.assertEqual(1234, arguments.seed)


if __name__ == "__main__":
    unittest.main()
