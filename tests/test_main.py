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
                "--brain",
                "full",
            ]
        )

        self.assertEqual("run", arguments.command)
        self.assertTrue(arguments.animate)
        self.assertEqual(2, arguments.steps)
        self.assertEqual(20.0, arguments.fps)
        self.assertEqual("/tmp/test-memory.json", str(arguments.memory_file))
        self.assertTrue(arguments.reset_memory)
        self.assertEqual(1234, arguments.seed)
        self.assertEqual("full", arguments.brain)

    def test_full_brain_management_commands_are_available(self) -> None:
        build = build_parser().parse_args(["brain-build"])
        status = build_parser().parse_args(["brain-status"])
        benchmark = build_parser().parse_args(
            ["brain-benchmark", "--substeps", "12"]
        )

        self.assertEqual("brain-build", build.command)
        self.assertEqual("brain-status", status.command)
        self.assertEqual("brain-benchmark", benchmark.command)
        self.assertEqual(12, benchmark.substeps)

    def test_web_command_selects_backend_and_network_address(self) -> None:
        arguments = build_parser().parse_args(
            [
                "web",
                "--brain",
                "full",
                "--host",
                "0.0.0.0",
                "--port",
                "8123",
                "--fps",
                "12",
                "--seed",
                "7",
                "--memory-file",
                "/tmp/web-memory.json",
                "--reset-memory",
            ]
        )

        self.assertEqual("web", arguments.command)
        self.assertEqual("full", arguments.brain)
        self.assertEqual("0.0.0.0", arguments.host)
        self.assertEqual(8123, arguments.port)
        self.assertEqual(12.0, arguments.fps)
        self.assertEqual(7, arguments.seed)
        self.assertTrue(arguments.reset_memory)


if __name__ == "__main__":
    unittest.main()
