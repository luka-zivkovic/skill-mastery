# Failure Analysis

Analyze failed trajectories. Identify the smallest skill changes that would likely prevent
each failure. Do not propose broad rewrites. Return concrete observations, affected skill
sections, and candidate patch ideas.

## First, ingest the rejected-edit buffer (close the loop)

Before proposing anything, run `summarize_skill_history.py <records>` and read the
**"Rejected edits to avoid re-proposing"** block. Do NOT re-propose an edit that is already
in that buffer this epoch — a rejected edit is mechanical negative feedback, not a fresh
idea. If a failure seems to call for a rejected edit again, find a *different* fix or
explain why the prior rejection no longer applies.

## Look for recurring patterns, not anecdotes

Work over a minibatch (~8 failures) and target the failure that repeats across cases.
Single-trajectory fixes produce anecdotal, over-specific edits. Prefer generalizable rules;
never hardcode task-specific values.
