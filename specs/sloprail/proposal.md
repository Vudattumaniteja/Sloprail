# Sloprail

## TL;DR

Build Sloprail V1 as a lightweight Visual Canvas that creates Station Folders for AI agents. A Station compresses one Source Video Target Window into representative visual evidence, timing, notes, and context, then external agents produce Replacement Renders. ffmpeg automation merges one completed Replacement Render back into the Source Video while preserving original audio.

## Problem

Human video-change intent is often visual and timestamped, but agents receive vague prompts or too much raw video. This causes missed intent, wasted context, and unreliable replacement work.

## Opportunity

Modern coding agents can inspect folders, images, Markdown, and JSON well. HyperFrames-style render workflows can create replacement visuals, but they need precise evidence packets. Sloprail sits at the missing handoff layer between human visual intent and agent-render work.

## Audience

- **Primary:** A solo creator/operator who uses Codex, Plot Code, Claude Code, or similar agents to edit visual segments of explanatory videos.
- **Secondary:** Agent workflow builders who need a repeatable Station Folder contract for visual replacement tasks.

## Outcome

A human can create a validated Station Folder for a selected Target Window, hand it to an external agent, receive a Replacement Render, and merge it into the Source Video with evidence of media-property changes.

## Stakes

Without this layer, agents either inspect too much video or receive under-specified prompts. The result is inconsistent visual edits, weak review evidence, and repeated manual explanation.

## Approach

Start with a docs-first v1 that defines the Station Folder, frame collapse, agent output, and ffmpeg merge contracts. Implement the smallest Visual Canvas and automation around those contracts, while keeping model-quality questions experimental.

## Risks Summary

| Risk | Severity |
|---|---|
| Replacement Render quality varies across models and HyperFrames approaches | high |
| Normalizing Merge can cause visible fps or scaling artifacts | med |
| Frame Sampling Rate can miss fast visual events | med |
| Station Context can be incomplete and lead agents to invent rules | med |
| Scope can drift into a full agent harness or full video editor | high |

## Dependencies

- ffmpeg and ffprobe availability.
- A browser-based canvas implementation.
- External agent workspaces such as Codex, Plot Code, or Claude Code.
- Optional HyperFrames or equivalent render workflow.

## Next

See: `specs/`, `design.md`, `tasks.md`, `personas.md`, `journeys.md`, `metrics.md`, `out-of-scope.md`, `open-questions.md`.
