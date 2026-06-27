---
name: exam-study-pack
description: Build exam-prep study packs from course materials, lecture notes, tutorials, and past papers. Use when Codex needs to analyze repeated exam structure, create staged revision notes, extract or reference paper questions, write cautious check-your-work solutions, build printable/HTML study packs, or turn a one-off course prep folder into a repeatable workflow.
---

# Exam Study Pack

## Workflow

Use this skill to turn raw course materials into a structured exam-prep pack that another student can work through without redoing the discovery work.

Read `references/pack-structure.md` before creating or revising a pack. It defines the expected folders, files, and quality gates.

### 1. Inventory The Materials

Locate the course inputs:

- Past papers and mock papers
- Lecture slides, notes, tutorials, and answer sheets
- Formula sheets, appendices, diagrams, datasheets, or worked examples
- Existing prep notes, generated images, scripts, or solution files

List what exists and what is missing. Prefer `rg --files` for the inventory. If the pack depends on PDF content, inspect both extracted text and rendered pages because equations, diagrams, and superscripts are often image-only.

### 2. Infer The Exam Pattern

Compare past papers by year and question number. Identify:

- recurring question types
- repeated command words
- mark weighting and timing
- topic order
- fragile OCR/image-only questions
- source lectures or tutorials that map to each recurring question type

Write the pattern as a short plan before drafting detailed notes. Do not overfit to one paper when several years disagree.

### 3. Create The Pack Structure

Create a course-specific output folder, normally `<course>-exam-prep/`, with:

- `PLAN.md`
- `steps/00-start-here.md`
- `steps/01-...md` through the topic stages
- `steps/<final>-past-paper-mocks.md`
- `solutions/README.md`
- `solutions/<year>-solutions.md`
- `assets/` for crops, extracted diagrams, and source-page images when useful
- `scripts/` for repeatable build or extraction utilities
- `dist/` for generated output only

Keep generated artifacts in `dist/`. Keep source markdown and scripts editable and reviewable.

### 4. Draft Staged Method Notes

Each stage file should be a working checklist, not a lecture transcript.

Include:

- beginner explanation when the topic assumes missed lectures
- source material links
- extracted visual references when they materially help
- past-paper questions to drill
- printable question images when available
- method template
- drills
- completion test

Use the course's own terminology. For problem-solving exams, prioritize "what is the next step when I see this question?" over broad theory.

### 5. Add Solutions Carefully

Write solutions as check-your-work material, not as a substitute for attempts.

For each paper:

- preserve the question numbering used in the paper
- show method checkpoints before final answers
- state assumptions when diagrams or formulas are image-only
- avoid pretending uncertain OCR is exact
- collect known ambiguity in `solutions/README.md`

When algebra depends on an unreadable diagram, give the correct method and verification points instead of inventing a final expression.

### 6. Build A Portable Output

If the user wants a single printable file, use or adapt `scripts/build_study_pack_html.py`.

The script expects:

```bash
python3 scripts/build_study_pack_html.py \
  --root <pack-dir> \
  --title "Course Exam Prep" \
  --output <pack-dir>/dist/course-exam-prep.html \
  <ordered markdown files...>
```

Run the builder after editing markdown. Open or inspect the generated HTML enough to catch broken links, missing images, escaped math problems, and print layout issues.

## Quality Gates

Before finishing:

- Verify every linked local source file exists.
- Verify each stage has a concrete completion test.
- Verify solution notes separate certainty from OCR/image ambiguity.
- Keep course-specific facts in the generated pack, not in this skill.

## Resource Notes

- `references/pack-structure.md`: artifact pattern and authoring rules.
- `scripts/build_study_pack_html.py`: reusable Markdown-to-HTML pack builder with image embedding, local markdown link rewriting, and MathJax support.
