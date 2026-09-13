# Project Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the approved Python package and directory scaffold while preserving `brain/data.py`.

**Architecture:** Keep brain simulation concerns in the `brain` package and world simulation concerns in the `world` package. Reserve tracked directories for future datasets and frontend work without introducing runtime behavior or coupling.

**Tech Stack:** Python 3, Git

**Spec:** `docs/superpowers/specs/2026-09-12-project-scaffold-design.md`

## Global Constraints

- Do not add dependencies or runtime behavior.
- Preserve the existing `brain/data.py` exactly.
- Make `brain` and `world` explicit Python packages.

---

### Task 1: Create and verify the scaffold

**Files:**
- Create: `brain/__init__.py`
- Preserve: `brain/data.py`
- Create: `brain/neuron.py`
- Create: `brain/network.py`
- Create: `brain/sensory.py`
- Create: `world/__init__.py`
- Create: `world/fly.py`
- Create: `world/environment.py`
- Create: `world/motor.py`
- Create: `frontend/.gitkeep`
- Create: `data/.gitkeep`
- Create: `main.py`

**Interfaces:**
- Consumes: no application interfaces; only the existing repository layout.
- Produces: importable `brain` and `world` packages and the requested tracked paths.

- [x] **Step 1: Record and run a failing structural check**

Run:

```bash
.venv/bin/python -c "from pathlib import Path; paths = ['brain/__init__.py', 'brain/neuron.py', 'brain/network.py', 'brain/sensory.py', 'world/__init__.py', 'world/fly.py', 'world/environment.py', 'world/motor.py', 'frontend/.gitkeep', 'data/.gitkeep', 'main.py']; missing = [path for path in paths if not Path(path).is_file()]; assert not missing, f'Missing: {missing}'"
```

Expected: FAIL listing the missing scaffold files.

- [x] **Step 2: Create the minimal scaffold**

Create each listed file as an empty file. Do not modify `brain/data.py`.

- [x] **Step 3: Verify structure and imports**

Run:

```bash
.venv/bin/python -c "import brain, brain.data, brain.network, brain.neuron, brain.sensory, world, world.environment, world.fly, world.motor"
```

Expected: exit code 0 with no output.

Run the structural check from Step 1 again.

Expected: exit code 0 with no output.

- [x] **Step 4: Review the resulting diff**

Run:

```bash
git status --short
git diff --check
```

Expected: every requested path is present, `brain/data.py` has no diff, and `git diff --check` exits successfully.
