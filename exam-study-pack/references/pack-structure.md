# Study Pack Structure

## Folder Contract

Use this shape unless the existing project already has a close equivalent:

```text
exam-prep/
├── PLAN.md
├── stages/
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
├── .vitepress/
│   └── config.mts
├── .gitignore
├── package.json
└── dist/
    └── <vitepress build output>
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

## Formula Formatting

Write all mathematical formulas in TeX syntax wrapped in MathJax delimiters:

- Inline formulas: `$G(s) = \frac{1}{s + 2}$`
- Displayed equations:

```markdown
$$
K_p = \lim_{s \to 0} G(s)
$$
```

Use dollar-sign delimiters in stage notes, method templates, drills, and solutions. Do not leave formulas as bare text such as `G(s) = 1/(s + 2)` unless the expression is intentionally plain code or a filename.

Use `\lvert` and `\rvert` instead of raw `|` for absolute values, determinants, magnitudes, and vertical bars. This is required inside markdown tables because unescaped `|` characters are interpreted as column separators. For example, write `$\lvert G(j\omega) \rvert$`, not `$|G(j\omega)|$`.

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

## VitePress Site Rules

When building HTML output:

- install VitePress with `npm add -D vitepress@next`
- install the VitePress math plugin dependency with `npm add -D markdown-it-mathjax3`
- create `.vitepress/config.mts`
- write `.gitignore` for `node_modules/`, VitePress cache, and `dist/`
- add `docs:dev`, `docs:build`, and `docs:preview` package scripts with `npm pkg set`
- configure nav/sidebar entries for `PLAN.md`, `stages/`, and `solutions/`
- enable VitePress markdown math support with `markdown: { math: true }` so `$...$` and `$$...$$` formulas render
- keep local images as relative markdown image links
- escape literal angle brackets in source text so inequalities do not become HTML tags
- make print styles avoid breaking images, tables, code blocks, and displayed math across pages
