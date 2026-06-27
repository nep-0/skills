# Study Pack Structure

## Folder Contract

Use this shape unless the existing project already has a close equivalent:

```text
<course>-exam-prep/
├── PLAN.md
├── steps/
│   ├── 00-start-here.md
│   ├── 01-<foundation>.md
│   ├── 02-<topic>.md
│   └── NN-past-paper-mocks.md
├── solutions/
│   ├── README.md
│   └── <year>-solutions.md
├── assets/
│   ├── question-crops/
│   ├── source-pages/
│   └── <reference-diagrams>.png
├── scripts/
│   └── build_study_pack_html.py
└── dist/
    └── <generated>.html
```

## PLAN.md

Write `PLAN.md` as the navigation layer:

- one-paragraph basis for the plan
- repeated exam pattern by question/topic
- ordered study stages
- solution links
- recommended order
- target competence checklist

## Stage Files

Use this template:

```markdown
# Stage N: Topic Name

Goal: one sentence.

## Beginner Explanation

Short conceptual bridge for students who missed the lectures.

## Source Materials

- [Lecture or tutorial](relative/path.pdf)

## Extracted Reference

![Useful diagram](../assets/example.png)

## Past-Paper Questions To Drill

- [2025 Q1](../../past papers/2025.pdf): short description.

## Printable Exam Questions

![2025 Q1](../assets/question-crops/2025-q1.png)

## Method Template

1. First repeatable step.
2. Second repeatable step.

## Drills

- Concrete practice task.

## Completion Test

This stage is complete when...
```

Omit sections that do not apply, but keep `Goal`, `Method Template` or equivalent checklist, `Drills`, and `Completion Test`.

## Solution Files

Use one file per paper. Start with the paper/year title. Preserve original question labels.

Prefer this style:

- `Question 1(a)`: concept answer or method.
- `Question 1(b)`: derivation with checkpoints.
- `Question 1(c)`: final range/result if exact inputs are readable.

Add an ambiguity note when a result depends on OCR, a diagram, a cropped image, or unreadable notation.

## Image Handling

Render PDF pages or crop question images when:

- the question includes diagrams
- OCR drops exponents, fractions, signs, or labels
- printable practice sheets are useful

Store original rendered pages in `assets/source-pages/<paper>/` and question crops in `assets/question-crops/`. Use descriptive filenames such as `2025-q1-start.png` and `2025-q1-cont.png`.

## HTML Build Rules

When building one-file HTML:

- embed local images as data URIs
- rewrite markdown links between included files to anchors
- protect display math before Markdown conversion
- escape literal angle brackets in source text so inequalities do not become HTML tags
- use MathJax for math rendering
- make print styles avoid breaking images, tables, code blocks, and displayed math across pages
