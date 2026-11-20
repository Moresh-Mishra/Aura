# Aura

**Aura is an experimental, modular computer-use agent for Windows.** Its
long-term goal is to understand a user's objective, perceive the desktop
environment, plan actions, interact with applications, verify outcomes,
and retain useful context.

Aura is being developed incrementally. The current project focuses on
building a reliable, deterministic desktop interaction foundation before
connecting autonomous planning and language models.

> **Project status:** Active development --- foundational perception,
> desktop interaction, application/window management, an action
> controller, and an initial action policy have been developed. The full
> autonomous agent orchestration and model integrations are planned, not
> yet complete.

## Vision

Aura is intended to bring together:

-   **Perception:** Capture the screen and extract visual/UI
    information.
-   **Reasoning:** Interpret user instructions and make decisions.
-   **Planning:** Break larger objectives into actionable steps.
-   **Execution:** Interact with desktop applications through reusable
    tools.
-   **Verification:** Check whether actions produced the intended
    result.
-   **Memory:** Retain relevant context across tasks.
-   **Safety:** Enforce permissions and operational boundaries.

The goal is not simply to automate clicks. It is to build an agent that
can complete multi-step computer tasks while remaining observable,
verifiable, and constrained.

## Current capabilities

The following capabilities have been developed and tested during the
current development cycle. Integration and coverage may vary by module.

### Perception

-   Screenshot capture using MSS.
-   OCR integration using Tesseract and `pytesseract`.
-   Text extraction, confidence filtering, and bounding-box information.
-   Text grouping/reconstruction and geometric analysis.
-   UI detection and work on spatial/accessibility relationships.

### Desktop interaction

-   Mouse movement and clicking.
-   Keyboard key presses, text entry, and hotkeys.
-   Vertical and horizontal scrolling.
-   Coordinate-based drag-and-drop.
-   Input validation for coordinates and action parameters.

### Application and window management

-   Installed-application discovery and launching.
-   Running-process identification.
-   Window enumeration and title-based lookup.
-   Window activation.
-   Minimize, maximize, and restore operations.
-   Reuse of an already-running application where possible.

### Action execution

-   A structured `ActionRequest` interface.
-   A central action dispatcher in `src/tools/controller.py`.
-   Integration of desktop tools through the controller.
-   Execution results returned to the caller.

### Initial safety policy

-   Action classification into automatically allowed,
    confirmation-required, and blocked categories.
-   Unknown actions fail closed.
-   Kernel-related action names are explicitly prohibited.
-   The initial policy is integrated with the controller.

**Security note:** The current safety policy is an early development
layer, not a complete security sandbox. The prototype approval mechanism
must be replaced with a trusted user-confirmation flow before autonomous
model-generated actions are enabled. Every action and parameter must be
validated at the execution boundary.

## Architecture

Aura is organized into separate subsystems so that perception, planning,
safety, execution, verification, and memory can evolve independently.

``` text
aura/
├── artifacts/
├── src/
│   ├── agent/          # Future task orchestration and execution loop
│   ├── aura/           # Core application/package components
│   ├── memory/         # Memory and context management
│   ├── perception/     # Screenshots, OCR, UI detection and context
│   ├── planner/        # Task decomposition and planning
│   ├── safety/         # Action policy and permission checks
│   ├── tools/          # Desktop tools and action controller
│   └── verification/   # Action requests and outcome verification
├── test/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

This is the intended high-level layout, not a guarantee that every
listed module is already implemented or populated. Keep desktop
utilities directly under `src/tools/`; Aura does not use a nested
`desktop/` directory.

### Responsibilities

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  `src/agent/`                        Coordinate complete user tasks
                                      (planned)

  `src/planner/`                      Break objectives into steps
                                      (developing/planned)

  `src/perception/`                   Observe and interpret the desktop

  `src/tools/`                        Perform individual desktop actions

  `src/tools/controller.py`           Validate and dispatch individual
                                      `ActionRequest` operations

  `src/safety/`                       Evaluate whether actions are
                                      allowed

  `src/verification/`                 Check action outcomes

  `src/memory/`                       Store and retrieve useful context
  -----------------------------------------------------------------------

### Controller vs. orchestrator

These are separate responsibilities:

-   **Controller:** Executes an individual action request by dispatching
    it to the appropriate tool.
-   **Orchestrator:** Coordinates an entire user goal, including
    planning, safety checks, execution, observation, verification,
    retries, and replanning.

The controller is not intended to become the application's full
orchestration layer. A dedicated orchestrator is planned under
`src/agent/`.

## Planned execution flow

The intended agent loop is:

``` text
User objective
      |
      v
Agent orchestrator
      |
      v
Planner creates next step
      |
      v
Perception / gather context
      |
      v
Safety policy and trusted approval
      |
      v
Action controller
      |
      v
Desktop tool executes action
      |
      v
Verification checks outcome
      |
      +---- success ----> Continue / finish
      |
      +---- failure ----> Recover / replan
```

The complete loop is a roadmap item; it should not be interpreted as
fully implemented today.

## Development roadmap

1.  **Harden the safety system**
    -   Replace prototype approval with trusted user confirmation.
    -   Validate action names, parameters, targets, and application
        paths.
    -   Keep unknown actions blocked.
    -   Enforce least privilege and the user-mode-only boundary.
2.  **Strengthen verification**
    -   Verify application launches and window state changes.
    -   Verify UI element presence, disappearance, and text changes.
    -   Standardize success, failure, timeout, and retry outcomes.
3.  **Standardize tool contracts**
    -   Establish consistent input/output schemas.
    -   Add tool registration and capability descriptions.
    -   Improve error handling and logging.
4.  **Build a deterministic execution loop**
    -   Observe → Plan → Check safety → Execute → Verify → Continue or
        replan.
5.  **Build the agent orchestrator**
    -   Add task lifecycle management and coordination in `src/agent/`.
6.  **Integrate intelligence**
    -   Add the planned JEV SystemOne and reasoning-LLM components
        behind modular interfaces.
    -   Add natural-language and voice interfaces (STT/TTS) when the
        core loop is reliable.
7.  **Expand memory and autonomy**
    -   Add task context, useful long-term preferences, and robust
        multi-step workflows.

## Security principles

Aura is designed around the following constraints:

1.  **User-mode only:** Aura must not implement, load, or execute
    kernel-mode code or drivers, access kernel memory, or use
    kernel-level automation techniques.
2.  **Least privilege:** Run Aura as a normal user. Do not request
    administrator privileges by default.
3.  **Fail closed:** Unknown or unregistered actions must not execute.
4.  **Trusted approval:** Consequential actions must require approval
    from the user through a trusted interface. A language model must
    never approve its own action.
5.  **Validate at the boundary:** The controller must validate action
    parameters and targets even if an upstream planner has already
    checked them.
6.  **Verify outcomes:** A tool returning without an exception does not
    prove that the user's intended result occurred.

Windows user-mode APIs may internally call operating-system services
that execute in the kernel. That normal OS behaviour is distinct from
Aura itself executing kernel-mode code.

## Development environment

The project is developed on Windows. The current codebase uses Python
and Windows desktop automation APIs.

Known technologies used in the project include:

-   Python
-   MSS
-   Tesseract OCR / `pytesseract`
-   PyAutoGUI
-   `pywin32` (`win32gui`, `win32process`)
-   `psutil`

The exact dependency list and supported Python versions should be taken
from `pyproject.toml`. This README intentionally does not prescribe an
installation command that may diverge from the project's current
dependency configuration.

### Getting started

1.  Clone the repository.
2.  Open the project directory.
3.  Create and activate a Python virtual environment.
4.  Install the project using the dependency configuration in
    `pyproject.toml`.
5.  Configure local environment variables using `.env.example`, if
    required.
6.  Run the relevant module or tests using the commands documented in
    the project configuration and module entry points.

Example virtual-environment setup in Windows PowerShell:

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation due to its execution policy, use Command
Prompt instead:

``` cmd
.venv\Scripts\activate.bat
```

Do not commit `.env`, credentials, API keys, local machine paths, or
other secrets.

## Development conventions

-   Keep modules focused on one responsibility.
-   Keep desktop utility modules directly inside `src/tools/`.
-   Route desktop actions through the controller rather than duplicating
    dispatch logic.
-   Keep planning, orchestration, execution, perception, verification,
    and safety separate.
-   Add tests for new actions and safety rules.
-   Treat the safety policy as a mandatory execution boundary, not an
    optional planner feature.
-   Document whether a feature is implemented, integrated, or only
    planned.

## Project status

Aura is an active research and development project. APIs, module
boundaries, and capabilities may change as the architecture matures. Not
every item in the roadmap is implemented.

## License

No license has been specified yet. Until a license is added to this
repository, do not assume that the code is available for unrestricted
reuse or redistribution.
