from dataclasses import dataclass, field


class BudgetExceeded(Exception):
    def __init__(self, resource: str, spent: int, limit: int) -> None:
        self.resource = resource
        self.spent = spent
        self.limit = limit
        super().__init__(f"{resource} budget exceeded: {spent} > {limit}")


@dataclass
class RunBudget:
    """Tracks spend against a run-level ceiling. Agents decrement it as they call out."""

    max_tokens: int
    max_calls: int
    tokens_spent: int = field(default=0, init=False)
    calls_spent: int = field(default=0, init=False)

    def charge(self, tokens: int) -> None:
        self.calls_spent += 1
        if self.calls_spent > self.max_calls:
            raise BudgetExceeded("calls", self.calls_spent, self.max_calls)

        self.tokens_spent += tokens
        if self.tokens_spent > self.max_tokens:
            raise BudgetExceeded("tokens", self.tokens_spent, self.max_tokens)

    @property
    def tokens_remaining(self) -> int:
        return max(self.max_tokens - self.tokens_spent, 0)

    @property
    def calls_remaining(self) -> int:
        return max(self.max_calls - self.calls_spent, 0)
