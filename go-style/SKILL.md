---
name: go-style
description: Apply Google's Go Style Guide when writing, reviewing, or refactoring Go code, and structure Go projects following the official module layout guidance. Use when writing Go source, tests, or benchmarks; deciding on naming conventions, error handling patterns, receiver choices, import ordering, doc comment rules, interface design, concurrency patterns, test structure conventions, project directory layout, or which standard library features to prefer over older patterns.
---

# Go Style

This skill distills the Google Go Style Guide (canonical guide + style decisions + best practices) into actionable rules for writing idiomatic Go. Every rule below carries the guide's authority; the disclosed references carry the reasoning.

- `references/decisions.md` — style decisions with rationale and examples for naming, imports, errors, formatting, testing, and language features.
- `references/package-choices.md` — setup patterns, version pinning, and style-guide caveats for each standard package.
- `references/best-practices.md` — best practices for documentation, concurrency, function arguments, tests, and error handling.
- `references/modern-go.md` — modern stdlib APIs to prefer over older patterns, organised by Go version (1.18–1.27).

## Style principles (in priority order)

1. **Clarity** — purpose and rationale are clear to the reader (not the author). Names, comments, and code organization serve the reader. Explain *why*, not *what*.
2. **Simplicity** — simplest approach that works. No unnecessary abstraction. Complexity only when justified, and then documented.
3. **Concision** — high signal-to-noise. Repetition and extraneous syntax obscure the relevant details.
4. **Maintainability** — easy for a future programmer to modify correctly. APIs that grow gracefully. Minimal coupling.
5. **Consistency** — match the broader codebase; break ties in favor of consistency, but never override the principles above.

## Formatting

- Run `gofmt` on all source. Generated code should be formatted too.
- `MixedCaps` (camelCase/PascalCase), never snake_case, for all Go identifiers. Constants are `MaxLength` / `maxLength`, not `MAX_LENGTH`.
- No fixed line length. Refactor long lines instead of splitting. Never split before an indentation change or to break a long string literal.

## Naming

Read `references/decisions.md#naming` for full guidance. Key rules:

- **Package names**: lowercase, no underscores, concise. Avoid `util`, `common`, `helper`, `model`. The callsite must read clearly: `bytes.Buffer`, `ring.New`.
- **Receiver names**: short (1-2 letters), abbreviation of the type, consistent across every method on that type. `func (s *Server)` not `func (self *Scanner)`.
- **Constants**: MixedCaps, named by role not value. No `k` prefix, no SCREAMING_SNAKE.
- **Initialisms**: same case within an initialism (`URL` or `url`, never `Url`). In multi-initialism names, each initialism keeps its own case: `XMLAPI`.
- **Getters**: no `Get` prefix. Use `Counts()` not `GetCounts()`. `Compute`/`Fetch` for expensive calls.
- **Variable names**: length proportional to scope, inversely proportional to usage count. Omit type-like words: `users` not `numUsers`, `userSlice`. Reflect contents and use, not origin.
- **Single-letter names**: only for receivers, loop indices, and familiar short-scoped types (`r` for `io.Reader`, `w` for `io.Writer`).
- **Repetition**: eliminate redundant context. `widget.NewWidget` → `widget.New`. Don't repeat the package name, receiver type, or parameter names in function names.

## Error handling

- `error` is the last result parameter. Return the `error` interface, not a concrete type.
- Error strings: lowercase first letter, no trailing punctuation.
- Handle errors before proceeding — indent the error flow, not the success path:
  ```go
  if err != nil {
      return err
  }
  // normal code
  ```
- Never ignore errors silently. Handle, return, or (rarely) `log.Fatal`. If discarding is safe, add a comment explaining why.
- Avoid in-band errors (returning -1 or ""). Return an additional value (`ok bool` or `error`).
- Wrap errors with context: `fmt.Errorf("load config: %w", err)`. Don't add redundant info the underlying error already provides. Avoid stop words like "failed to".
- Use `%w` when callers should inspect the error chain via `errors.Is`/`errors.As`. Use `%v` for simple annotation or at system boundaries. Place `%w` at the end of the message string.
- Don't `panic` for normal errors. Use `panic` only for impossible invariants or API misuse, and never let it escape a package boundary.
- `Must` functions (e.g. `regexp.MustCompile`) only at startup, never on user input.

## Commentary and documentation

- All exported names need doc comments: full sentences beginning with the name.
- An article ("a", "an", "the") may precede the name.
- Comments explain *why*, not *what*. Let self-describing names carry the "what".
- Package comments go immediately above the package clause, one per package. For `main` packages, use the binary name.
- Runnable examples go in `_test.go` files, not production source.
- Use `doc.go` for long package documentation.
- Don't restate what's implied (e.g., that context cancellation interrupts the function).

## Imports

- Groups in order: stdlib, other (project + vendored), protobuf imports (`pb` suffix), blank imports (`_`).
- Don't rename imports unless colliding or the name is uninformative. Rename project-local imports over stdlib.
- Proto imports: rename to remove underscores, suffix with `pb` or `grpc`.
- No `import .` (dot imports).
- Blank imports only in `main` or tests. Document library packages that need side-effect imports.

## Interfaces

- Define interfaces at the point of consumption, not production. Accept interfaces, return concrete types.
- Keep interfaces small. Don't create interfaces until a real need exists.
- Don't wrap RPC clients in manual interfaces just for testing. Use real transports with test doubles.
- Don't export test-double implementations solely for testing. Test via the public API.
- Keep interfaces unexported if only used internally.

## Concurrency

- Make goroutine lifetimes explicit. Know when and how every goroutine stops.
- Prefer synchronous functions. Callers can add concurrency; removing it from the caller side is hard.
- Never start a goroutine without knowing how it will stop. Use `context.Context` and `sync.WaitGroup` to bound lifetimes.
- Specify channel direction (`<-chan int`) where possible.
- Document concurrency safety: omit it for read-only operations (assumed safe) and mutating operations (assumed unsafe); document only when unclear or when the API provides synchronization.

## Receivers

- If the method mutates the receiver → pointer receiver.
- If the struct contains uncopyable fields (`sync.Mutex`, `bytes.Buffer`) → pointer receiver.
- For large structs or uncertain growth → pointer receiver.
- For maps, functions, channels, or basic types → value receiver.
- For small plain-data structs with no mutable fields → value receiver.
- When in doubt → pointer receiver.
- All methods on a type should use the same receiver type.

## Variables and literals

- Prefer `:=` for non-zero initialization. Use `var` for zero-value declarations ready for later use.
- Prefer `nil` slices over `[]T{}`. Don't make callers distinguish nil from empty.
- Use field names in struct literals for types from other packages. Optional for local types.
- Use size hints (`make([]T, 0, n)`) only with empirical evidence that it matters.
- Don't pass pointers to small values just to save bytes. Protobuf messages should be pointers.
- Use `any` over `interface{}` in new code.

## Testing

- Use the `testing` package only. No third-party frameworks or assertion libraries.
- Table-driven tests when many cases share logic. Use subtests (`t.Run`) with descriptive names.
- Keep going after failures: prefer `t.Error` over `t.Fatal` within test cases. Reserve `t.Fatal` for setup failures or when further checks would be meaningless.
- Useful failure messages: identify the function, the input, got before want. `YourFunc(%v) = %v, want %v`.
- Use `cmp.Diff` for comparing complex values. Include a diff direction key: `(-want +got)`.
- Mark test helpers with `t.Helper()`. Helpers do setup/cleanup, not assertions.
- Don't compare on error string text; use `errors.Is` or `cmpopts.EquateErrors`.
- Don't create change-detector tests. Compare on stable semantic results, not serialization output.
- `t.Fatal` is unsafe in goroutines other than the test goroutine; use `t.Error` + channel instead.

## Context

- `context.Context` is always the first parameter: `func F(ctx context.Context, ...)`.
- Don't store context in struct fields. Pass it as a parameter to methods that need it.
- Don't create custom context types.
- Use `context.Background()` only in entrypoints (`main`, `init`). In tests, use `t.Context()`.
- Contexts are immutable; safe to pass the same context to multiple calls.

## Project layout

Start flat. Add directories only when the code demands them. A directory is a package: every file in it shares the package name, and the import path's last element is the name. This progression matches the official ["Organizing a Go module"](https://go.dev/doc/modules/layout) guide.

| Project shape | Layout | When to add |
|---|---|---|
| Small tool, one binary | Flat: `main.go` + logic files in module root | Default. Ship as-is. |
| One binary, private internals | Add `internal/` for packages outside importers can't reach | When you need to hide code from other modules. |
| Two or more binaries | Add `cmd/<name>/` per binary, thin `main.go` in each | When the repo builds more than one binary. |
| Multi-service repo | `cmd/` + `internal/` split by domain | When several services share code. |

- Don't use `src/`. Go code lives at the module root.
- Don't use `pkg/` unless you're deliberately publishing a public API from the module root. Most projects don't need it.
- Don't create empty folders (`api/`, `build/`, `deployments/`). Add a directory the day you have code for it.
- Don't name packages by role (`utils`, `common`, `helpers`). Name them by what they provide (`store`, `auth`, `retry`).
- Put real logic in `internal/`; keep `cmd/<name>/main.go` thin — it wires packages together, nothing more.
- Keep tests next to the code they cover (`foo_test.go` beside `foo.go`).

## Standard package set

Use these packages by default so every project shares the same dependencies. Pick only the categories a project needs; a library should pull none of these. Read `references/package-choices.md` for setup notes, version pinning, and style-guide caveats.

| Category | Package | Notes |
|---|---|---|
| Postgres access | `github.com/sqlc-dev/sqlc` | Generates type-safe Go from SQL. Uses `pgx/v5` driver under the hood. |
| DB migrations | `github.com/golang-migrate/migrate/v4` | CLI + library. Versioned SQL files. |
| SQLite | `modernc.org/sqlite` | Pure Go, no CGo. Cross-compiles cleanly. |
| Redis | `github.com/redis/go-redis/v9` | Full-featured: pipelines, pub/sub, Cluster/Sentinel. |
| Background jobs | `github.com/riverqueue/river` | Postgres-backed, transactional enqueue. Use only if Postgres is already in the stack. |
| HTTP router | `github.com/go-chi/chi/v5` | Stdlib-compatible, middleware-friendly. |
| Logging | `log/slog` (stdlib) | Go 1.21+. Zero deps. |
| Config | `github.com/spf13/viper` | Env + file + flags. Use in `main` or a config package only. |
| CLI framework | `github.com/spf13/cobra` | Subcommands, help, completions. For simple tools, prefer stdlib `flag`. |
| Concurrency | `golang.org/x/sync` | `errgroup`, `semaphore`, `singleflight`. Go-team maintained. |
| Observability | `go.opentelemetry.io/otel` | Traces + metrics API; pick an exporter per project. |
| UUIDs | `uuid` (stdlib, Go 1.27+) | `uuid.New()` (v4), `uuid.NewV7()` (time-ordered). Zero deps. |
| JSON | `encoding/json/v2` (stdlib, Go 1.27+) | Use for all new JSON code. Stricter defaults; see `references/package-choices.md`. |
| Auth tokens | `github.com/golang-jwt/jwt/v5` | JWT: HS256, RS256, ES256. |
| Testing — comparison | `github.com/google/go-cmp` | Style-guide recommended. |
| Testing — assertions | `github.com/stretchr/testify` | Project-level convenience. Prefer `go-cmp` + `t.Errorf` where the check is trivial. |
| Validation | stdlib (manual) | No validation library. Validate in handlers. |
| Test doubles | hand-written fakes | No mock generator. Prefer real implementations or minimal hand-written fakes. |
| DI / wiring | manual in `main` | No DI framework. Wire dependencies by hand in `cmd/<name>/main.go`. |
| gRPC | `google.golang.org/grpc` | For gRPC services only. |
| Protobuf runtime | `google.golang.org/protobuf` | Generated code uses `pb`/`grpc` import suffix. Exempt from naming rules. |

Rules:
- Pin exact versions in `go.mod`. No open ranges.
- Prefer stdlib. These packages are the fallback when stdlib falls short.
- A package not on this list: propose adding it to the set rather than introducing a one-off dep.
- Libraries pull none of these; they belong in service/CLI projects only.

## Modern Go stdlib

Use modern stdlib APIs over older patterns when targeting a Go version that supports them. Read `references/modern-go.md` for the full list organized by Go version (1.18–1.27). Key rules:

- `encoding/json/v2` for all new JSON code (Go 1.27+). Leave existing `encoding/json` code unchanged unless migration is explicitly requested.
- `range over int` (`for i := range n`) instead of `for i := 0; i < n; i++` (Go 1.22+).
- No redundant loop-variable copies before closures or `&v` (Go 1.22+).
- `slices` and `maps` packages over hand-written loops: `slices.Contains`, `slices.Sort`, `slices.Clone`, `maps.Clone`, `maps.Copy`, etc. (Go 1.21+).
- Built-in `min`, `max`, `clear` over manual implementations (Go 1.21+).
- `cmp.Or` for fallback chains (Go 1.22+).
- `strings.Cut`, `strings.CutPrefix`, `strings.CutSuffix`, `strings.SplitSeq` over `Index` + manual slicing (Go 1.18+/1.20+/1.24+).
- `sync.OnceFunc`, `sync.OnceValue`, typed atomics (`atomic.Bool`, `atomic.Int64`, `atomic.Pointer[T]`) (Go 1.19+/1.21+).
- `context.AfterFunc` over goroutines waiting on `ctx.Done()` (Go 1.21+).
- `errors.Join` to combine errors, `errors.Is` for sentinel checks (Go 1.13+/1.20+).
- `t.Context()` in tests, `b.Loop()` in benchmarks (Go 1.24+).
- `wg.Go` on `sync.WaitGroup` instead of `wg.Add` + `go func` + `defer wg.Done` (Go 1.25+).
- `new(value)` for pointer fields instead of helper functions (Go 1.26+).
- `errors.AsType[T](err)` instead of `errors.As` + temp var (Go 1.26+).
