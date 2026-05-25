---
title: Git Branch Guideline
description: Naming and usage rules for project Git branches.
version: 1.0.0
language: en
status: active
last_updated: 2026-05-25
---

# Git Branch Guideline

## Predefined Variables

- `{DATE}`: Maps to the current date in `YYYY-MM-DD` format.
- `{DATETIME}`: Maps to the current date and time in `YYYY-MM-DD_HH24:mm:SS` format.
  - For branch names, prefer `YYYY-MM-DD_HH-mm-SS` if cross-platform compatibility is required, because `:` can cause issues on some filesystems and tools.
- `{UUID}`: A short UUID, using the first 8 characters of a UUIDv7 value.
- `{UUIDv7}`: A full UUID v7 value.
- `{NAME}`: A descriptive name that represents the purpose or content of the branch.

## Branch Naming

### `main`

`main`: The branch for the final production-ready state.

- Do not merge into this branch arbitrarily.
- Do not commit directly to this branch.
- Unless there is a specific reason otherwise, this branch is the base branch for other branches.

### `staging`

`staging`: The validation branch used for final testing before production release.

- Do not merge into this branch arbitrarily.
- Do not commit directly to this branch.

### `dev`

`dev/{NAME}`: A branch used for development-server testing.

- Do not merge into this branch arbitrarily.
- Direct commits are allowed only in limited cases.

### `feature`

`feature/{NAME}-{UUID}`: A branch for feature development.

- Branch from `main`.
- Add a short UUID to avoid duplicate feature branch names.

### `fix`

`fix/{DATE}/{NAME}-{UUID}`: A branch for bug fixes or related corrections.

- Usually branch from `main`.

### `temp`

`temp/{UUIDv7}`: A temporary branch.

- Usually branch from `main`.
- Create this branch temporarily before starting work.
- Before the final push, rename it to an appropriate `feature` or `fix` branch, or merge it into one.

### `merge`

`merge/{NAME}-{UUID}`: A branch for merge testing or merge execution.

- Use this branch temporarily to test merges.
- Use this branch when pulling `main` and preparing or executing a merge into `main`.
