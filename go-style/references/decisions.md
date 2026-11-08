# Go Style Decisions — Reference

Source: https://google.github.io/styleguide/go/decisions

## Naming

### Underscores

No underscores in Go names except: (1) package names imported only by generated code, (2) test/benchmark/example functions in `*_test.go`, (3) low-level cgo interop. Filenames are not Go identifiers and may contain underscores.

### Package names

Lowercase, no underscores, no abbreviations that lose meaning. Single-word or run together: `tabwriter`, not `tab_writer`. Avoid names shadowed by common local variables (prefer `usercount` over `count`). Rename imported packages with underscores at import time. Don't use `util`, `helper`, `common`, `model`, `testhelper`.

Import renaming: use same local name wherever that package is imported in the same or nearby packages. Suffix `pkg` when a package name collides with a desired local variable name (e.g., `urlpkg`).

### Receiver names

Short, abbreviation of the type, consistent across all methods. Not `self` or `this`.

| Avoid               | Prefer              |
|---------------------|---------------------|
| `func (tray Tray)`  | `func (t Tray)`     |
| `func (this *ReportWriter)` | `func (w *ReportWriter)` |

### Constant names

MixedCaps. Based on role, not value. No `K` prefix, no `MAX_UPPER_CASE`.

```go
const MaxPacketSize = 512
const (
    ExecuteBit = 1 << iota
    WriteBit
    ReadBit
)
```

### Initialisms

Keep initialism letters same case within each initialism:

| Usage   | Exported | Unexported |
|---------|----------|------------|
| URL     | `URL`    | `url`      |
| XML API | `XMLAPI` | `xmlAPI`   |
| iOS     | `IOS`    | `iOS`      |
| gRPC    | `GRPC`   | `gRPC`     |
| ID      | `ID`     | `id`       |

### Getters

No `Get`/`get` prefix. Start with the noun: `Counts()` not `GetCounts()`. Use `Compute`/`Fetch` when the operation is expensive or can block.

### Variable names

Length ∝ scope size, ∝ 1/usage frequency. Omit type qualifiers: `users` not `userSlice`, `count` not `numUsers`. Omit context-clear words in implementation of `UserCount`: just `count` or `c`. Single-letter names OK for receivers, loop indices, and familiar idioms (`r io.Reader`, `w io.Writer`).

### Repetition

Remove redundant information:

- Package vs. exported symbol: `widget.NewWidget` → `widget.New`
- Variable vs. type: `var primaryProject *Project` → `var primary *Project`
- External context vs. name: in package `sqldb`, `DBConnection` → `Connection`

## Commentary

### Doc comments

Full sentences starting with the name of the thing:
```go
// A Request represents a request to run a command.
type Request struct { ... }

// Encode writes the JSON encoding of req to w.
func Encode(w io.Writer, req *Request) { ... }
```

Apply to the following symbol or group of struct fields. Unexported code benefits from the same format; easy to export later.

### Sentences

Complete sentences: capitalized, punctuated. Fragment end-of-line struct field comments are fine without punctuation.

### Named result parameters

Name when clarifying two same-type returns or when the caller must act on a specific return:
```go
func WithTimeout(parent Context, d time.Duration) (ctx Context, cancel func())
```

Don't name solely to enable naked returns. Naked returns only in small functions.

## Imports

### Import grouping (in order)

1. Standard library
2. Other (project + vendored)
3. Protocol Buffer imports (`foopb "path/to/foo_go_proto"`)
4. Blank imports (`_ "path/to/package"`)

### Blank imports

Only in `main` packages or tests. Library packages must not blank-import side-effect packages.

### Dot imports

Never use `import .` in production code.

## Errors

### Returning errors

- `error` last in return list.
- Return `error` interface, not `*os.PathError` or other concrete types (nil concrete pointer wrapped in interface ≠ nil).
- If function takes `context.Context`, it should return `error`.

### Error strings

Lowercase first letter, no trailing punctuation. Full messages (logs, UI) follow normal sentence capitalization.

### Handle errors

Don't discard with `_`. Choose: handle now, return to caller, or `log.Fatal`. If discarding, explain why in a comment.

### In-band errors

Don't return -1, `""`, or `nil` for errors. Return an `(value, ok bool)` or `(value, error)` pair.

### Indent error flow

```go
// Good: error handled first, success falls through
if err != nil {
    return err
}
// normal code
```

Not:
```go
// Bad: success path indented inside else
if err != nil {
    ...
} else {
    // normal code, indented unnecessarily
}
```

## Language

### Literal formatting

- Struct literals from other packages must use field names.
- Zero-value fields may be omitted when clarity is not lost.
- Closing brace on its own line for multi-line literals, followed by a comma on the last element.

### Don't panic

No `panic` for normal error handling. `log.Fatal` / `log.Exit` in `main` for bad configuration. Panics that signal API misuse are acceptable in library code only if they cannot escape the package (recover at the public API boundary).

### Must functions

Name `MustXYZ`. Only call at program startup or in package-level `var` initialization, never on user input.

### Goroutine lifetimes

Make goroutine end conditions obvious. Scope synchronization to a function. Document when goroutines outlive their creator.

### Interfaces

Accept interfaces; return concrete types. Define at the point of consumption. Consumer package defines the interface (unless it's a common protocol). Prefer real transports over hand-mocked clients in tests.

### Generics

Allowed when they fulfill real requirements. Don't use generics for algorithm polymorphism that works fine with a concrete type today. Don't use generics to build DSLs or custom assertion frameworks.

### Receiver type

- Mutates receiver → pointer
- Uncopyable fields (`sync.Mutex`) → pointer
- Large struct → pointer
- Map/func/channel receiver → value
- Small pure data → value
- Doubt → pointer
- All methods on a type should use the same receiver kind.

### switch and break

Don't add `break` at the end of `switch` clauses; it's redundant in Go. To break out of an enclosing `for` from inside `switch`, use a labelled `break`.

### Synchronous functions

Prefer synchronous over asynchronous. Callers can easily add a goroutine; removing concurrency from a callee is hard.

### crypto/rand

Use `crypto/rand` for keys, never `math/rand`.

## Useful test failures

Pattern: `YourFunc(%v) = %v, want %v`. Include: function name, inputs (short), got, want.

- Identify function in message even when test name already suggests it.
- Use `%q` when string content matters or could be empty.
- Print diffs (`cmp.Diff`) for large values. Include direction key: `(-want +got)`.
- Test semantics, not error strings. Use `errors.Is`, `cmpopts.EquateErrors`, or a boolean `wantErr`.

## Test structure

### Table-driven tests

Use when many cases share logic. Name rows; don't use `i` as the identifier. Print inputs in failure messages.

### Subtests

Use `t.Run`. No slash characters in subtest names. Names identify the input, not describe the test in prose.

### Test helpers

Mark with `t.Helper()`. Pass `*testing.T` as first non-context argument. Setup failures → `t.Fatal`. Test helpers do setup/cleanup, not assertions.

### Test package

- Same package (`package foo` in `foo_test.go`) for white-box tests.
- `package foo_test` for black-box or integration tests.
- `package foocardtest` naming convention for test double packages.

## Context

- First parameter, always.
- `ctx context.Context` in test helpers too.
- Use `t.Context()` in tests (not `context.Background()`). During cleanup, use `context.Background()` or `context.WithoutCancel`.
- No custom context types.
- No context in struct fields.

## Common libraries

### Flags

Define only in `package main`. Flag names in `snake_case`; the bound variable in `mixedCaps`. Prefer dependency injection over global flags in library code.

### Logging

`log.V(n).Infof(...)` for verbose. Don't log and return an error; let the caller decide. Avoid ERROR level; it's expensive and should be actionable.
