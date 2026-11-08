# Go Style Best Practices — Reference

Source: https://google.github.io/styleguide/go/best-practices

## Naming

### Function and method names

Omit at call site:
- Types of inputs/outputs (when no collision)
- Method receiver type
- Whether input/output is a pointer
- Package name (don't repeat in exported functions: `yamlconfig.Parse` not `yamlconfig.ParseYAMLConfig`)
- Parameter variable names (`Override(dest, source)` not `OverrideFirstWithSecond(dest, source)`)

Conventions:
- Noun names for functions that return something: `JobName(key)`
- Verb names for functions that do something: `WriteDetail(w)`
- Same logic, different types: type suffix: `ParseInt`, `ParseInt64`, `AppendInt`, `AppendInt64`

### Test double packages

Append `test` to the package name: `creditcardtest`. Name doubles by behavior when one type needs several: `AlwaysCharges`, `AlwaysDeclines`. Name by type when multiple types need doubles: `StubService`, `StubStoredValue`.

### Shadowing

Don't shadow a variable in a new scope unintentionally — it causes bugs where the outer variable is silently still in use after the block. Intentional stomping (`ctx, cancel := ...`) is fine when the original is no longer needed.

### Util packages

Don't name packages `util`, `helper`, `common`. The callsite should be self-documenting:
- `spannertest.NewDatabaseFromFile(...)` — clear.
- `test.NewDatabaseFromFile(...)` — unclear.

### Package size

One cohesive idea per package. Don't force one-file-per-type. Split when concepts are distinct; combine when the client needs both to interact.

## Documentation

### Conventions

- Document non-obvious or error-prone parameters and fields. Skip obvious ones.
- Don't restate what context cancellation implies.
- Document significant error sentinels and error types returned.
- Document cleanup requirements (e.g., "Caller should close resp.Body").

### Concurrency documentation

- Read-only ops: assumed safe. Omit concurrency comments.
- Mutating ops: assumed unsafe. Omit.
- Document when: unclear if read-only or mutating; the API provides synchronization; the API consumes user-implemented interfaces with concurrency requirements.

### Godoc formatting

- Blank line separates paragraphs.
- Indent by 2 extra spaces for verbatim text.
- Runnable examples appear in `*_test.go`.
- Use `pkgsite` to preview.

### Signal boosting

When code looks normal but isn't, boost the signal with a comment:
```go
if err := doSomething(); err == nil { // if NO error
```

## Variable declarations

### Initialization

Prefer `:=` over `var` for non-zero values:
```go
i := 42  // not var i = 42
```

### Zero values

Use `var` for zero-value declarations when the value is ready for later use (e.g., unmarshalling target). Don't use explicit zero composite literals.

### Composite literals

Use when you know the initial elements. Empty composites are noisy vs. zero-value `var`.

### Size hints

`make([]T, 0, n)` only with empirical evidence. Overallocation wastes memory.

### Channel direction

Specify `<-chan T` or `chan<- T` where possible. Prevents casual errors, conveys ownership.

## Function argument lists

Keep signatures short. When a function grows many parameters:

### Option structure

Collect optional arguments into a struct passed as the last argument:
```go
type ReplicationOptions struct {
    Config              *replicator.Config
    PrimaryRegions      []string
    ReadonlyRegions     []string
    // ...
}
func EnableReplication(ctx context.Context, opts ReplicationOptions)
```

Use when: most callers specify one or more options, options are shared between functions.

### Variadic options

```go
type Option func(*options)
func WithTimeout(d time.Duration) Option { ... }
func EnableReplication(ctx context.Context, config *Config, opts ...Option)
```

Use when: most callers pass no options, there are many options, options require arguments, options can fail.

## Tests

### Test functions vs. assertion helpers

- Test helpers: setup/cleanup; call `t.Helper()`.
- Assertion helpers: not idiomatic. Don't create them.
- Inline validation and failure in the `Test` function when possible.
- For shared validation, return a value (`error`) from a helper instead of taking `*testing.T`.

### Use real transports

Prefer connecting a real client to a test double server over hand-implementing a client. Tests more of the real code path.

### t.Error vs t.Fatal

- `t.Error`: keep going, report all failures.
- `t.Fatal`: only when the test cannot proceed (setup failure) or subsequent checks would be meaningless.
- In table-driven tests with subtests: `t.Fatal` within a subtest stops only that entry.
- `t.Fatal` is unsafe in goroutines other than the test goroutine.

### Error handling in test helpers

Setup failures → `t.Fatalf` in the helper. The failure is an environment problem, not a code-under-test problem.

### Acceptance testing

For validating user implementations of an interface:
1. Create a `Xtest` package (e.g., `chesstest`).
2. Export a function: `func ExercisePlayer(b *chess.Board, p chess.Player) error`.
3. The function returns nil on success or a structured error.

### Equality comparison

Prefer `cmp.Equal` / `cmp.Diff` for complex types. Use `protocmp.Transform` for protobuf messages. Don't use `reflect.DeepEqual` in new code. For error comparison, use `errors.Is` or `cmpopts.EquateErrors`.

### Print diffs

Include direction key in the failure message:
```go
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("Foo() returned unexpected difference (-want +got):\n%s", diff)
}
```

## Error handling

### Error structure

- Sentinel values for unparameterized global errors: `var ErrDuplicate = errors.New("duplicate")`.
- Structured error types for programmatic inspection: `*os.PathError`.
- Don't distinguish errors by parsing their string representation.

### Adding information to errors

- Don't duplicate info the underlying error already has.
- Don't add annotations whose only purpose is to signal failure ("failed: %v" → just return `err`).
- Use stop-word-free messages: "load certificate: %w" not "failed to load certificate: %w".

### %v vs %w

- `%v`: simple annotation, hiding internal details, system boundaries.
- `%w`: programmatic inspection, error chaining, documented contract.
- Place `%w` at end: `"action: %w"`.
- Exception: sentinel categorization errors place `%w` at the beginning: `"%w: invalid header"`.

### Error logging

- Don't both log and return an error; let the caller handle it.
- Use `log.Error` sparingly (expensive, causes flush).
- Avoid PII in logs.
- Use `log.V(n)` for verbose; guard expensive calls: `if log.V(2) { log.Info(sql.Explain()) }`.

### Program checks and panics

- Use `log.Fatal` for invariant violations where internal state is unrecoverable.
- Don't recover panics to avoid crashes (propagates corrupted state).
- `panic` acceptable: API misuse (like `reflect`), internal implementation with matching recover at the boundary, unreachable code after `log.Fatal`.

## Concurrency

### Goroutine lifetimes

- Make goroutine lifetimes explicit via `context.Context` and `sync.WaitGroup`.
- Leaked goroutines blocking on channels won't be GC'd.
- Synchronous functions keep concurrency localized and testable.

### Synchronous functions

Prefer synchronous functions. Callers can add a goroutine; removing concurrency from a callee is hard.

## Program initialization

- Propagate initialization errors to `main`.
- Use `log.Exit` (with actionable message) over `log.Fatal` (stack trace) for bad config.
- In `init` or `Must` functions, `panic` is acceptable instead of `log.Fatal`.
