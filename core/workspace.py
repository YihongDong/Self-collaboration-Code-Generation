from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TestResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class TestReport:
    result: TestResult = TestResult.PENDING
    error_message: str = ""
    test_code: str = ""

    @property
    def passed(self) -> bool:
        return self.result == TestResult.PASSED

    def __str__(self) -> str:
        if self.passed:
            return "Code Test Passed."
        if self.result == TestResult.TIMEOUT:
            return "timed out"
        return self.error_message or self.result.value


@dataclass
class Workspace:
    requirement: str = ""
    before_func: str = ""
    plan: str = ""
    code: str = ""
    method_name: str = ""
    test_report: Optional[TestReport] = None
    rounds: int = 0

    def to_session_history(self) -> dict:
        history = {}
        if self.plan:
            history["plan"] = self.plan
        history[f"Round_{self.rounds}"] = {"code": self.code}
        if self.test_report and not self.test_report.passed:
            history[f"Round_{self.rounds}"]["report"] = str(self.test_report)
        return history
