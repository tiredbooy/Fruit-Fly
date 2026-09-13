from contextlib import redirect_stdout
import io
import tempfile
from pathlib import Path
import unittest

from main import build_parser, main


class GymCommandTest(unittest.TestCase):
    def test_data_status_validates_the_gym_circuits_too(self):
        with redirect_stdout(io.StringIO()) as output:
            result = main(['data-status'])
        self.assertEqual(0, result, output.getvalue())
        self.assertIn('Validated gym runtime edges:', output.getvalue())

    def test_gym_commands_parse_population_and_learning_options(self):
        options = build_parser().parse_args(['gym', '--flies', '3', '--no-learning', '--steps', '10'])
        self.assertEqual(3, options.flies)
        self.assertTrue(options.no_learning)
        self.assertEqual(10, options.steps)
        self.assertEqual('gym-web', build_parser().parse_args(['gym-web']).command)

    def test_unsupported_full_and_nonfinite_rates_fail_before_loading(self):
        for arguments in [['--brain', 'full'], ['--fps', 'nan'], ['--fps', 'inf'], ['--flies', '11'], ['--steps', '0']]:
            with redirect_stdout(io.StringIO()) as output:
                result = main(['gym', *arguments])
            self.assertNotEqual(0, result)
            self.assertIn('Error:', output.getvalue())

    def test_finite_real_gym_command_saves_experiment_two_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(io.StringIO()) as output:
                result = main(['gym', '--steps', '3', '--seed', '7', '--memory-dir', directory])
            self.assertEqual(0, result, output.getvalue())
            self.assertIn('3 steps', output.getvalue())
            self.assertTrue((Path(directory) / 'fly-1/gym-memory.json').is_file())
