# Standard Package Choices — Reference

These are the project-standard third-party packages. Each entry covers the import path, setup pattern, and any tension with the Google Go Style Guide that applies.

---

## Database: sqlc + pgx

**Generate type-safe Go from SQL queries.**

```
go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest
```

`sqlc.yaml` at module root:
```yaml
version: "2"
sql:
  - engine: "postgresql"
    queries: "./internal/store/queries/"
    schema: "./internal/store/migrations/"
    gen:
      go:
        package: "store"
        out: "./internal/store"
        sql_driver: "pgx/v5"
```

- sqlc generates `Querier` interface + `Queries` struct. The generated code uses `pgx/v5` as the driver.
- Put query files in `internal/store/queries/`, schema/migrations in `internal/store/migrations/` or a top-level `migrations/`.
- Generated files are committed (not gitignored). Run `sqlc generate` after changing `.sql` files.
- sqlc enforces that queries compile against the schema. Mismatch = build failure.

Pinned deps to add:
```
github.com/jackc/pgx/v5 vX.Y.Z
github.com/sqlc-dev/sqlc vX.Y.Z  (tool, not a runtime dep)
```

---

## Migrations: golang-migrate

**Versioned SQL migration files, CLI and library.**

Install CLI:
```
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest
```

Runtime library:
```
github.com/golang-migrate/migrate/v4 vX.Y.Z
```

Migration file naming: `000001_create_users.up.sql` / `000001_create_users.down.sql`.

Library usage in `main` or an init package:
```go
m, err := migrate.New("file://migrations", os.Getenv("DATABASE_URL"))
if err != nil { ... }
if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) { ... }
```

- Don't embed migrations in the binary unless there is a specific operational reason to do so. File-based is simpler.
- Keep migration files in a top-level `migrations/` directory when using `cmd/` layout.

---

## HTTP Router: chi

**Stdlib-compatible, minimal, middleware-first.**

```
github.com/go-chi/chi/v5 vX.Y.Z
```

Pattern:
```go
r := chi.NewRouter()
r.Use(middleware.Logger)
r.Use(middleware.Recoverer)

r.Get("/health", handleHealth)
r.Route("/api/v1", func(r chi.Router) {
    r.Get("/users/{id}", handleGetUser)
    r.Post("/users", handleCreateUser)
})

http.ListenAndServe(":8080", r)
```

- `chi.URLParam(r, "id")` extracts path params; stay consistent with this over query-string hacks.
- Handler signature is `func(w http.ResponseWriter, r *http.Request)` — plain stdlib. No framework lock-in.
- Group related routes under a `r.Route(...)` block; each block can get its own middleware stack.
- Keep chi in `cmd/<name>/main.go` or the top-level wire-up file. Route logic lives in `internal/<domain>/handler.go` with plain `http.HandlerFunc`-compatible functions.

**Style note:** Chi's `context.WithValue` for request-scoped values (e.g., authenticated user) follows chi conventions, but stay within `context.Context` — no custom context types.

---

## Logging: slog (stdlib)

**Go 1.21+. Structured, levelled, zero deps.**

```go
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))
slog.SetDefault(logger)
```

Patterns:
```go
slog.Info("user created", "userID", id, "email", email)
slog.Error("db query failed", "err", err, "query", q)
slog.With("requestID", rid).Info("handling request")
```

- Use `slog.With(...)` to build a child logger carrying per-request or per-component fields.
- Key names: lowercase, no spaces: `"userID"`, `"requestID"`, `"err"`.
- Don't log and return the same error. Log at the boundary where you absorb the error; return it where you propagate it.
- `slog.Error` is for errors the service cannot recover from automatically. For recoverable errors that affect a request, log at `slog.Warn` or `slog.Info`.

No external logger dep needed. zerolog/zap remain an option only if benchmarks prove slog is the bottleneck.

---

## Config: viper

**Env vars + config files + flags, in priority order.**

```
github.com/spf13/viper vX.Y.Z
```

Usage pattern — load in `main`, pass values down as parameters:
```go
viper.SetEnvPrefix("APP")
viper.AutomaticEnv()
viper.SetDefault("server.port", 8080)
viper.SetConfigName("config")
viper.AddConfigPath(".")
_ = viper.ReadInConfig() // file is optional

cfg := Config{
    Port:        viper.GetInt("server.port"),
    DatabaseURL: viper.GetString("database.url"),
}
```

- **Load viper in `main` only** (or a dedicated `config` package). Don't call `viper.Get*` in library packages — this is what the style guide warns against with flags.
- Pass config values as parameters or a struct, never as globals from `viper` directly.
- Use `viper.GetString("database.url")` not `os.Getenv("DATABASE_URL")` once viper is wired, so the file override path works.
- Keep config keys in `snake.case`. Viper maps `APP_SERVER_PORT` → `server.port` automatically with `SetEnvPrefix`.

**Style-guide tension:** Viper is heavy (many transitive deps) and tempts flag-in-library patterns. Mitigate by keeping all viper calls in one file (`internal/config/config.go` or `main.go`) and returning a plain struct.

---

## CLI: cobra

**Subcommands, help generation, shell completions.**

```
github.com/spf13/cobra vX.Y.Z
```

Standard structure:
```go
var rootCmd = &cobra.Command{Use: "myapp", Short: "..."}

func Execute() error { return rootCmd.Execute() }

func init() {
    rootCmd.AddCommand(serveCmd)
    rootCmd.AddCommand(migrateCmd)
}
```

Each subcommand in its own file under `cmd/<binary>/`. Keep cobra wiring in `cmd/`; logic in `internal/`.

- Get context from `cmd.Context()`, not `context.Background()`. The style guide flags this specifically for cobra.
- Use `cobra.Command.RunE` (returns error) not `Run` (ignores error).
- Don't define business logic in cobra command functions. They call `internal/` functions and handle the error.

**When cobra is overkill:** A tool with one mode and a few flags is better served by stdlib `flag`. Cobra's startup cost (reflection, help generation) is non-zero.

---

## Testing: go-cmp + testify

**go-cmp for value comparison; testify for suite convenience.**

```
github.com/google/go-cmp vX.Y.Z
github.com/stretchr/testify vX.Y.Z
```

**go-cmp** is style-guide recommended and the default for comparing structs and complex values:
```go
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("Foo() mismatch (-want +got):\n%s", diff)
}
```

**testify** is permitted for convenience; use sparingly:
```go
// OK: quick nil/bool checks
require.NoError(t, err)
assert.Equal(t, want, got)
```

Avoid:
- `assert.Contains`, `assert.Eventually` — write the check explicitly.
- `testify/mock` — prefer real implementations or hand-written fakes.
- testify suites — unnecessary complexity.

**Style-guide tension:** The Google style guide says don't create assertion libraries and explicitly prefers inline `t.Errorf`. Testify is a convenience exception at the project level. When in doubt, go with `go-cmp` + `t.Errorf`.

---

## gRPC + Protobuf

**Only for gRPC services.**

```
google.golang.org/grpc vX.Y.Z
google.golang.org/protobuf vX.Y.Z
```

- Generated packages renamed with `pb` suffix at import: `foopb "path/to/foo_go_proto"`.
- Use `grpc` suffix for generated gRPC client/server code.
- Generated code is exempt from MixedCaps and initialism rules (style guide explicit exception).
- Context comes from the stream, not `context.Background()`. Handle cancellation at the server boundary.

---

## SQLite: modernc.org/sqlite

**Pure Go, no CGo, cross-compiles to any GOARCH/GOOS.**

```
modernc.org/sqlite vX.Y.Z
```

Use through the standard `database/sql` interface:
```go
import (
    "database/sql"
    _ "modernc.org/sqlite"
)

db, err := sql.Open("sqlite", "file:app.db?_journal_mode=WAL&_foreign_keys=on")
```

- Always enable WAL mode (`_journal_mode=WAL`) and foreign keys (`_foreign_keys=on`) in the DSN.
- sqlc supports SQLite: set `engine: "sqlite"` in `sqlc.yaml`.
- golang-migrate supports SQLite: use `sqlite` as the driver name.
- SQLite is one writer at a time. Use a single `*sql.DB` with `db.SetMaxOpenConns(1)` for writes, or separate read/write pools.
- File path for tests: `file::memory:?cache=shared` for in-memory, or `t.TempDir()` + a file path for isolation.

---

## Redis: go-redis/v9

**Full-featured Redis client.**

```
github.com/redis/go-redis/v9 vX.Y.Z
```

Basic setup:
```go
rdb := redis.NewClient(&redis.Options{
    Addr:     os.Getenv("REDIS_ADDR"), // "localhost:6379"
    Password: os.Getenv("REDIS_PASSWORD"),
    DB:       0,
})
// Verify connection
if err := rdb.Ping(ctx).Err(); err != nil { ... }
```

- Pass `*redis.Client` as a dependency, not a global.
- Use `redis.NewUniversalClient` when the project may move between standalone, Sentinel, or Cluster.
- Key naming: `<service>:<entity>:<id>` — e.g., `auth:session:abc123`. Document the schema.
- Use `EXPIRE` / `TTL` on every key that shouldn't live forever.
- Prefer pipelines for bulk writes: `rdb.Pipelined(ctx, func(pipe redis.Pipeliner) error { ... })`.
- For distributed locks, use Redlock only if you need it; a simple `SET NX EX` suffices for most cases.

---

## Background jobs: river

**Postgres-backed, transactional enqueueing.**

```
github.com/riverqueue/river vX.Y.Z
github.com/riverqueue/river/riverdriver/riverpgxv5 vX.Y.Z
```

Key concepts:
- Jobs are enqueued inside a transaction alongside the data they act on — no dual-write problem.
- Workers run in the same binary (or a separate `cmd/worker` binary).
- Job types are Go structs with an `Args()` method; workers implement `river.Worker[T]`.

Minimal pattern:
```go
// Define a job
type SendEmailArgs struct {
    To      string
    Subject string
}
func (SendEmailArgs) Kind() string { return "send_email" }

// Implement the worker
type SendEmailWorker struct{ river.WorkerDefaults[SendEmailArgs] }
func (w *SendEmailWorker) Work(ctx context.Context, job *river.Job[SendEmailArgs]) error {
    return sendEmail(ctx, job.Args.To, job.Args.Subject)
}

// Enqueue inside a transaction
_, err = riverClient.InsertTx(ctx, tx, SendEmailArgs{To: "x@y.com", Subject: "Hello"}, nil)
```

- Run migrations once: `river migrate-up --database-url $DATABASE_URL`.
- Keep worker implementations in `internal/<domain>/worker.go`; wiring in `cmd/worker/main.go`.
- Workers must be idempotent — river retries on failure.

---

## Concurrency: golang.org/x/sync

**Go-team maintained. Three tools worth knowing:**

```
golang.org/x/sync vX.Y.Z
```

**errgroup** — fan out N goroutines, collect the first error, cancel all on failure:
```go
g, ctx := errgroup.WithContext(ctx)
for _, item := range items {
    item := item
    g.Go(func() error { return process(ctx, item) })
}
if err := g.Wait(); err != nil { ... }
```

**semaphore** — bound concurrency:
```go
sem := semaphore.NewWeighted(10) // max 10 concurrent
if err := sem.Acquire(ctx, 1); err != nil { ... }
go func() { defer sem.Release(1); doWork() }()
```

**singleflight** — deduplicate concurrent identical calls (cache stampede prevention):
```go
var g singleflight.Group
v, err, _ := g.Do(cacheKey, func() (any, error) { return fetchFromDB(ctx, id) })
```

- Prefer `errgroup` over bare `sync.WaitGroup` whenever goroutines can fail.
- `singleflight` is for hot read paths; don't apply it to writes.

---

## Observability: OpenTelemetry

**Vendor-neutral traces and metrics. Pick an exporter per project.**

Core deps (always):
```
go.opentelemetry.io/otel vX.Y.Z
go.opentelemetry.io/otel/trace vX.Y.Z
go.opentelemetry.io/otel/metric vX.Y.Z
```

Common exporters (pick one per project):
```
go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp  # OTLP → Jaeger/Tempo/Honeycomb
go.opentelemetry.io/otel/exporters/prometheus                      # Prometheus scrape endpoint
```

Bootstrap in `main` before any handlers start:
```go
tp, err := newTracerProvider(ctx)  // configure exporter, resource, sampler
if err != nil { ... }
defer tp.Shutdown(ctx)
otel.SetTracerProvider(tp)
otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
    propagation.TraceContext{},
    propagation.Baggage{},
))
```

In library/handler code:
```go
tracer := otel.Tracer("myapp/store")
ctx, span := tracer.Start(ctx, "GetUser")
defer span.End()
```

- Initialize in `main` only. Library code uses `otel.Tracer(...)` / `otel.Meter(...)` from the global — no SDK dep in library packages.
- Instrument HTTP with `go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp`.
- Instrument database calls at the `internal/store` layer, not in generated sqlc code.
- Span names: `"<package>/<operation>"` — e.g., `"store/GetUser"`.

---

## UUIDs: stdlib `uuid` package (Go 1.27+)

**Zero deps. v4 and v7 built in.**

```go
import "uuid"

id := uuid.New()      // v4, random — equivalent to uuid.NewV4()
id := uuid.NewV7()    // v7, time-ordered — better for DB index locality

s := id.String()      // "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"

parsed, err := uuid.Parse(s)
known := uuid.MustParse("f81d4fae-7dec-11d0-a765-00a0c91e6bf6") // panics on bad input
```

`UUID` is a comparable `[16]byte` — usable as a map key, comparable with `==`.

- Use `uuid.NewV7()` for IDs stored in Postgres/SQLite indexes. Monotonically increasing within a millisecond keeps index pages hot and reduces page splits.
- Use `uuid.New()` (v4) when ordering doesn't matter or when IDs must be opaque/unpredictable.
- `NewV7` holds a package-level mutex to guarantee monotonicity; safe for concurrent use.
- Postgres columns: `UUID` type with `DEFAULT gen_random_uuid()` at the DB level; Go generates IDs application-side when the ID must be known before the insert (e.g., to enqueue a job in the same transaction).
- Requires Go 1.27+. Confirm `go` directive in `go.mod` is `1.27` or later before use.

---

## JSON: encoding/json/v2 (stdlib, Go 1.27+)

**Use for all new JSON code. Stricter, more interoperable defaults than v1.**

```go
import "encoding/json/v2"

// New code: v2 defaults
body, err := json.Marshal(v)
err = json.Unmarshal(body, &v)

// Marshal to an io.Writer
err = json.MarshalWrite(w, v)
```

v2 behavior changes from v1:
- Invalid UTF-8 in strings → error (v1 silently replaces with U+FFFD).
- Duplicate JSON object names → error (v1 permits).
- `nil` slice → `[]`, `nil` map → `{}` (v1 marshals both as `null`).
- Invalid struct tags → runtime error (v1 silently ignores).

**Existing code:** leave `encoding/json` (v1) code unchanged unless migration is explicitly requested. v1 is covered by the Go 1 compatibility promise and will not go away. v1 and v2 are compatible: v2 custom marshalers work through v1 `json.Marshal` and vice versa.

**Migrating existing code to v2:**
- Start with `jsonv1.DefaultOptionsV1()` to preserve v1 wire behavior, then remove options one at a time after verifying consumers.
```go
import (
    jsonv1 "encoding/json"
    json "encoding/json/v2"
)

body, err := json.Marshal(v, jsonv1.DefaultOptionsV1())
```
- For production services: use [`jsonsplit`](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit) in `CallBothButReturnV1` mode to detect v1/v2 differences without changing output, then switch to v2 once differences stop.
- Never do a blind import swap on existing code — even a compiling change can alter wire behavior (`null` → `[]`, new errors on previously-tolerated input).

**New struct tags (Go 1.27+, work with both v1 and v2):**
- Use `omitzero` for bool, numeric, struct, and `time.Time` fields whose zero value means "absent".
- Keep `omitempty` for strings, slices, and maps where JSON empty-value semantics apply.
```go
type CacheEntry struct {
    Name      string    `json:"name,omitempty"`
    Warm      bool      `json:"warm,omitzero"`
    Hits      int64     `json:"hits,omitzero"`
    ExpiresAt time.Time `json:"expiresAt,omitzero"`
}
```

- `json.Marshalers` overrides marshal behavior for specific types you don't control.
- `json.MatchCaseInsensitiveNames` controls case-insensitive field matching.

---

## Auth tokens: golang-jwt/jwt v5

**Thin JWT library. HS256, RS256, ES256.**

```
github.com/golang-jwt/jwt/v5 vX.Y.Z
```

Sign (HS256):
```go
token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
    "sub": userID,
    "exp": time.Now().Add(24 * time.Hour).Unix(),
    "iat": time.Now().Unix(),
})
signed, err := token.SignedString([]byte(os.Getenv("JWT_SECRET")))
```

Verify:
```go
token, err := jwt.Parse(signed, func(t *jwt.Token) (any, error) {
    if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
        return nil, fmt.Errorf("unexpected signing method: %v", t.Header["alg"])
    }
    return []byte(os.Getenv("JWT_SECRET")), nil
})
claims, ok := token.Claims.(jwt.MapClaims)
```

- Always validate the signing method in the key function — never accept `alg: none`.
- Prefer typed claims (`jwt.RegisteredClaims` embedded in a custom struct) over `jwt.MapClaims` in production code.
- Keep the signing secret in env / secrets manager; never in source or config files.
- Short expiry + refresh tokens is out of scope for this library entry; design that at the service level.

---

## Test doubles: hand-written fakes

**No mock generator. Write minimal fakes by hand.**

The style guide's position: test via the public API of the real implementation; use real transports with test double *servers*, not mock *clients*. When a fake is genuinely needed, a hand-written struct is more legible than generated mock wiring.

Pattern — implement the interface minimally:
```go
// In the test file or a _test package
type fakeMailer struct {
    sent []mail.Message
}

func (f *fakeMailer) Send(_ context.Context, m mail.Message) error {
    f.sent = append(f.sent, m)
    return nil
}
```

- Name fakes by their behavior when multiple variants exist (`alwaysFailMailer`).
- Keep fakes in `_test.go` files or a `<pkg>test` package; never in production code.
- testify's `mock` package is available but not preferred. Use it only when the interface is large and hand-writing is disproportionate.
