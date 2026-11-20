
# Actions that can execute without an additional confirmation
AUTO_ALLOWED_ACTIONS = {
    "scroll",
    "open_application",
    "launch_application",
    "activate_window",
    "set_window_state",
}

# Actions requiring explicit user approval
CONFIRMATION_REQUIRED_ACTIONS = {
    "click",
    "type_text",
    "press_key",
    "hotkey",
    "drag",
}

# Permanently prohibited operation types
PROHIBITED_ACTIONS = {
    "kernel_operation",
    "execute_kernel_code",
    "load_kernel_driver",
    "install_kernel_driver",
    "kernel_memory_access",
}


def evaluate_action(action):
    """
    Evaluate whether an action is allowed, requires approval,
    or is prohibited.
    """

    if not isinstance(action, str) or not action.strip():
        return {
            "decision": "blocked",
            "reason": "Invalid action name."
        }

    action = action.strip().casefold()

    # 1. Permanent restrictions
    if (
        action in PROHIBITED_ACTIONS
        or "kernel" in action
    ):
        return {
            "decision": "blocked",
            "reason": "Kernel-level operations are prohibited."
        }

    # 2. Actions requiring user confirmation
    if action in CONFIRMATION_REQUIRED_ACTIONS:
        return {
            "decision": "confirmation_required",
            "reason": "This action requires explicit user approval.",
            "action": action
        }

    # 3. Automatically permitted actions
    if action in AUTO_ALLOWED_ACTIONS:
        return {
            "decision": "allowed",
            "reason": "Action is permitted by the current policy.",
            "action": action
        }

    # 4. Fail closed for unknown actions
    return {
        "decision": "blocked",
        "reason": "Action is not registered in the safety policy.",
        "action": action
    }


if __name__ == "__main__":

    test_actions = [
        "scroll",
        "click",
        "type_text",
        "hotkey",
        "open_application",
        "load_kernel_driver",
        "unknown_action"
    ]

    for action in test_actions:

        print(
            action,
            "->",
            evaluate_action(action)
        )
