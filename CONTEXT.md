# Agent Video Workstation

This context defines the language for a lightweight browser workspace where a human marks short video ranges, collapses them into representative visual moments, and hands structured intent to AI agents for replacement-render work.

## Language

**Source Video**:
The original full video uploaded for review, from which Target Windows are selected and into which Replacement Renders are later merged.
_Avoid_: original video, arsenal video, input video

**Source Scope**:
The v1 constraint that one project contains exactly one Source Video, while allowing many Stations to be created from it.
_Avoid_: multi-source project, asset library, source collection

**Target Window**:
A short selected span of source video that becomes the unit of review and replacement work, usually around 10 to 20 seconds.
_Avoid_: clip, segment, range

**Target Window Duration Guardrail**:
The v1 experimental boundary that Target Windows are commonly 10 to 20 seconds and may extend up to about 50 seconds while replacement quality is evaluated across models and approaches.
_Avoid_: fixed max duration, arbitrary limit

**Station**:
A saved agent-facing work unit on the timeline, tied to exactly one continuous Target Window and suitable for assignment to one AI coding or editing session.
_Avoid_: task, bookmark, marker

**Non-Overlapping Station Rule**:
The v1 implementation rule that Station Target Windows must not overlap in source time; future versions may revisit overlapping work after prototyping.
_Avoid_: overlap merge, nested station, layered station

**Visual Canvas**:
The browser workspace where a human reviews Representative Frames, adds Visual Markup, writes notes, and prepares Station Folders without performing final video edits or orchestrating agents directly.
_Avoid_: editor, harness, agent runner

**Station Context**:
The non-visual project context bundled with a Station, including storyline, script, transcript, design rules, brand guidance, and constraints needed to keep an Agent Action aligned with the full video.
_Avoid_: background, extra context, global prompt

**Partial Station Context**:
The v1 allowance that a Station may be handed off with missing context only when README.md and station.json explicitly declare what is missing and instruct the agent not to invent it.
_Avoid_: silent missing context, assumed context

**Transcript Scope**:
The v1 rule that each Station includes both the full Source Video transcript for story context and a Target Window transcript for exact Station timing.
_Avoid_: transcript only, local transcript, global transcript

**Frame Collapse**:
The process of reducing many frames inside a Target Window into a much smaller set of visually distinct representative frames.
_Avoid_: dedupe, compression, summarization

**Temporal Frame Deduplication**:
The v1 Frame Collapse technique that uses mathematical visual similarity, such as perceptual hashes and Hamming distance, to remove near-duplicate frames before selecting Representative Frames.
_Avoid_: t-duplication, vision model reduction, semantic frame selection

**Perceptual Hash Contract**:
The v1 rule that frame similarity is defined through perceptual-hash distance, while the exact hash algorithm can remain an implementation detail.
_Avoid_: dHash-only contract, model embedding similarity

**Frame Sampling Rate**:
The v1 baseline rate for extracting candidate frames before Temporal Frame Deduplication, set to two frames per second for initial experiments.
_Avoid_: all-frame extraction, arbitrary sampling

**Manual Representative Frame**:
A frame explicitly added by the human to a Station when the automatic Frame Sampling Rate or Temporal Frame Deduplication misses a visually important moment.
_Avoid_: manual override, pinned frame, extra screenshot

**Visual State Bucket**:
A group of near-duplicate frames treated as the same visual state during Temporal Frame Deduplication.
_Avoid_: cluster, scene, duplicate group

**Representative Candidate Selection**:
The v1 rule that chooses Representative Frames by ranking sampled frames with cheap visual quality signals before removing near-duplicates by perceptual-hash distance.
_Avoid_: middle-frame selection, random frame selection

**Frame Collapse Report**:
The Station evidence file that records sampling rate, perceptual-hash method, thresholds, candidate counts, kept frames, rejected near-duplicates, and selection reasons.
_Avoid_: debug log, dedupe output, reduction notes

**Representative Frame**:
A frame selected by Frame Collapse to stand for one visually stable moment or scene state inside the Target Window.
_Avoid_: keyframe, screenshot, thumbnail

**Temporal Strip**:
A left-to-right visual layout of Representative Frames where each frame is tagged with the span of Target Window time it covers.
_Avoid_: contact sheet, storyboard, frame grid

**Embedded Timing Label**:
Text drawn directly into the Temporal Strip that identifies a Coverage Span, its source time range, and its station-local duration.
_Avoid_: caption, overlay text, metadata label

**Coverage Span**:
The portion of a Target Window represented by one Representative Frame or one segment of a Temporal Strip.
_Avoid_: timestamp, duration, section

**Visual Markup**:
Human-authored visual evidence attached to a Target Window or Representative Frame, preserved as drawn pixels or an overlay snapshot rather than reduced to semantic types.
_Avoid_: annotation type, circle, arrow, drawing schema

**No Visual Markup Status**:
The explicit Station state where a Marked Frame exists but intentionally contains no human-drawn markup beyond the clean Representative Frame.
_Avoid_: missing markup, blank annotation, unmarked frame

**Station-Level Note**:
The required human note that states the intended change for a Station as a whole; Visual Markup alone is not enough for agent handoff.
_Avoid_: optional note, markup-only instruction

**Multi-Change Station**:
A Station that contains multiple requested visual changes within the same Target Window.
_Avoid_: one-change-only station, overlapping task split

**Before Frame**:
The source visual state an agent should compare against when interpreting requested change for a Representative Frame.
_Avoid_: original frame, input screenshot

**After Frame**:
The intended visual state or reference target an agent should compare toward when planning a Replacement Render.
_Avoid_: output frame, final screenshot

**Agent Work Packet**:
The exported bundle an AI agent reads, containing the source Target Window, Representative Frames, Visual Markup, before and after references, transcripts, and task notes.
_Avoid_: prompt, export, project

**Station Folder**:
The filesystem directory created for one Station, containing the Agent Work Packet and intended to be opened directly in Codex, Plot Code, Claude Code, or a similar agent workspace.
_Avoid_: workspace, repo, branch

**Station Handoff Validation**:
The v1 gate that keeps a Station in draft until required files exist, Station timing is valid, Station overlap rules pass, and station.json references resolve.
_Avoid_: partial handoff, best-effort export, unchecked station

**Agent Action**:
One AI session assigned to inspect and perform the work for a Station.
_Avoid_: subtask, code session, worker

**Station Lock**:
A v1 rule that prevents edits to a Station's notes, Visual Markup, settings, and packet contents while an Agent Action is active for that Station.
_Avoid_: versioning, live edit, concurrent edit

**Read Boundary**:
The v1 constraint that an Agent Action should inspect only the Station Folder and its included files unless the human explicitly provides more context.
_Avoid_: sandbox, permission model, repo access

**Replacement Render**:
The new generated video span that is intended to replace the original Target Window.
_Avoid_: final edit, output video, animation

**Merged Output**:
The video produced after one Replacement Render has been inserted into the Source Video for its Target Window.
_Avoid_: final video, stitched video, exported video

**Original Audio Preservation**:
The v1 merge rule that keeps the source video's audio for the Target Window while replacing only its visuals.
_Avoid_: replacement audio, silent patch, audio edit

**Media Properties**:
The measured width, height, frame rate, duration, codec, and audio presence for a source video, Target Window, Replacement Render, or merged output.
_Avoid_: metadata, specs, video info

**Normalization Report**:
The merge evidence that records whether ffmpeg changed a Replacement Render's resolution, frame rate, pixel format, codec, or duration handling before insertion.
_Avoid_: conversion log, ffmpeg notes

**Normalizing Merge**:
The v1 merge rule that ffmpeg may convert a Replacement Render to the Source Video's resolution, frame rate, and compatible encoding before insertion, while recording all changes in the Normalization Report.
_Avoid_: strict reject, agent-side matching, silent conversion

**Agent Render Notes**:
Notes written by the Agent Action after producing a Replacement Render, including assumptions, known issues, media properties, and compatibility concerns.
_Avoid_: agent comments, output notes

**Human Review Notes**:
Timestamped notes written by a human after reviewing a Replacement Render or merged playback, including FPS concerns, visual issues, and requested corrections.
_Avoid_: feedback, comments, review annotations

**Review Timecode**:
The v1 rule that Human Review Notes use station-local time as the primary timestamp while also recording the matching Source Video time.
_Avoid_: source-only note time, ambiguous timestamp
