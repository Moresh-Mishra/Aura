
from dataclasses import dataclass, field, asdict
from typing import Optional, Any


@dataclass
class ExpectedOutcome:
    """
    Describes what Aura expects to happen after an action.
    """

    kind: str

    target_text: Optional[str] = None

    element_type: Optional[str] = None

    expected_value: Any = None

    options: dict = field(default_factory=dict)


@dataclass
class ActionRequest:
    """
    Standard representation of an action Aura wants to execute.
    """

    action: str

    target: Optional[dict] = None

    parameters: dict = field(default_factory=dict)

    expected_outcome: Optional[ExpectedOutcome] = None

    def __post_init__(self):

        if not isinstance(self.action, str) or not self.action.strip():
            raise ValueError("Action must be a non-empty string.")

        if self.target is not None and not isinstance(self.target, dict):
            raise TypeError("Target must be a dictionary.")

        if not isinstance(self.parameters, dict):
            raise TypeError("Parameters must be a dictionary.")

        if (
            self.expected_outcome is not None
            and not isinstance(self.expected_outcome, ExpectedOutcome)
        ):
            raise TypeError(
                "Expected outcome must be an ExpectedOutcome object."
            )

    def to_dict(self):
        return asdict(self)

if __name__ == "__main__":

    request = ActionRequest(
        action="click",

        target={
            "text": "Outline Section",
            "element_type": "button"
        },

        expected_outcome=ExpectedOutcome(
            kind="element_position_changed",
            target_text="Timeline Section",
            options={
                "minimum_delta": 20
            }
        )
    )

    print(request.to_dict())