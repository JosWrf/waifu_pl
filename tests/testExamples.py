import subprocess
import os
from pathlib import Path
import re
from typing import List
from termcolor import colored, cprint


class Patterns:
    expected_ouput = re.compile("# expect: (.*)")
    expected_error = re.compile("")


class TestResult:
    """Stores the results obtained by validating the generated output against
    the expected output."""

    def __init__(self) -> None:
        self.failed = 0
        self.passed = 0
        self.messages = []

    def add_failed(self, test_name: str, message: str):
        self.failed += 1
        failed = colored((" " if test_name else "") + "FAILED", "red", attrs=["bold"])
        message = colored(message, "red")
        message = test_name + failed + " " + message
        self.messages.append(message)

    def add_passed(self, message: str):
        self.passed += 1
        passed = colored("PASSED", "green", attrs=["bold"])
        message = message + " " + passed
        self.messages.append(message)


class Test:
    """Each file in a subdirectory corresponds to a test."""

    def __init__(self, name: str, abs_path: str) -> None:
        self.name = name
        self.abs_path = abs_path
        self.expected_output = []
        self.expected_errors = []
        self.results = TestResult()
        self.load()

    def load(self) -> None:
        text = self.read()
        self.parse(text)

    def parse(self, text: str) -> None:
        for index, line in enumerate(text):
            matched = Patterns.expected_ouput.search(line.rstrip("\n"))
            if matched:
                # Group 0 is the entire regex
                self.expected_output.append(ExpectedOutput(index + 1, matched.group(1)))

    def read(self) -> List[str]:
        # Trailing newlines do not seem to be an issue
        lines = None
        with open(self.abs_path, "r") as handle:
            lines = handle.readlines()

        return lines

    def run(self) -> TestResult:
        # Akward way to get to the waifu file.
        interpreter = os.path.join(Path(__file__).parent.parent, "waifu.py")

        generated_output = subprocess.run(
            args=["python", interpreter, self.abs_path],
            capture_output=True,
            encoding="utf-8",
        )
        output = generated_output.stdout.rstrip("\n").split("\n")

        self.compare_expected_output(output)

        return self.results

    def compare_expected_output(self, generated_ouput: List[str]) -> None:

        num_expected = 0
        for index, line in enumerate(generated_ouput):
            if index < len(self.expected_output):
                expected = self.expected_output[index]
                if expected.output != line:
                    self.results.add_failed(
                        f"[expected{num_expected}] ",
                        f"At line {expected.line}: Expected {expected.output} but got {line}.",
                    )
                else:
                    self.results.add_passed(f"[expected{num_expected}]")
            else:
                self.results.add_failed(
                    "", f"Superflous output {line} where None was expected."
                )
            num_expected += 1

        while num_expected < len(self.expected_output):
            expected = self.expected_output[num_expected]
            self.results.add_failed(
                f"[expected{num_expected}] ",
                f"At line {expected.line}: Expected {expected.output} but got None.",
            )
            num_expected += 1


class ExpectedOutput:
    """Stores the line number from parsed test case, which is later used
    for error reporting."""

    def __init__(self, line: int, output: str) -> None:
        self.line = line
        self.output = output


class Suite:
    """Created for each subdirectory under examples.
    Groups tests and stores their evaluation details."""

    def __init__(self, name: str, abs_path: str) -> None:
        self.name = name
        self.abs_path = abs_path
        self.tests = []
        self.report_messages = []
        self.passed = 0
        self.failed = 0

    def load_tests(self, file_path: str) -> None:
        for name in os.listdir(file_path):
            abs_path = os.path.join(file_path, name)
            test = Test(name, abs_path)
            self.tests.append(test)

    def run_tests(self) -> None:
        for test in self.tests:
            result = test.run()
            self.create_test_summary(result, test)
        self.report_suite_summary()

    def create_test_summary(self, result: TestResult, test: Test) -> None:
        self.failed += result.failed
        self.passed += result.passed
        for i in range(len(result.messages)):
            result.messages[i] = self.name + "::" + test.name + result.messages[i]
            self.report_messages.append(result.messages[i])

    def report_suite_summary(self) -> None:
        cprint(f"Result from running {self.abs_path}", "magenta")
        for message in self.report_messages:
            print(message)
        cprint(f"PASSED {self.passed} / {self.passed + self.failed}\n", "yellow")


class TestHarness:
    """Groups the test suites together in one place."""

    def __init__(self) -> None:
        self.suites = []

    def load_suite(self, name: str, path: str) -> None:
        suite = Suite(name, path)
        suite.load_tests(path)
        self.suites.append(suite)

    def run_test_cases(self) -> None:
        for suite in self.suites:
            suite.run_tests()


def define_test_cases(path: str) -> TestHarness:
    suites = TestHarness()

    for name in os.listdir(path):
        abs_path = os.path.join(path, name)
        suites.load_suite(name, abs_path)

    return suites


if __name__ == "__main__":
    # navigate from where test script is run to examples folder
    test_path = os.path.join(Path(__file__).parent.parent, "examples")
    harness = define_test_cases(test_path)
    harness.run_test_cases()
