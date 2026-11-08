# Modern Go stdlib — Reference

Source: [JetBrains go-modern-guidelines](https://github.com/JetBrains/go-modern-guidelines) and the [Go stdlib docs](https://pkg.go.dev/std).

Use modern stdlib APIs over older patterns when targeting a Go version that supports them. Each entry shows the before → after pattern. Apply these when writing new code or reviewing PRs.

---

## Go 1.27+

### `encoding/json/v2`

Use `encoding/json/v2` for all new JSON code. Leave existing `encoding/json` code unchanged unless migration is explicitly requested. See `package-choices.md` for full migration guidance.

```go
// Before
import "encoding/json"
body, err := json.Marshal(v)

// After
import "encoding/json/v2"
body, err := json.Marshal(v)  // stricter defaults: nil slice → [], invalid UTF-8 → error
```

### Generic methods

Use generic methods instead of package-level generic helpers when the operation belongs to the type.

```go
// Before
func Map[T comparable, U any](s Set[T], f func(T) U) []U { ... }
names := Map(users, func(u User) string { return u.Name })

// After
func (s Set[T]) Map[U any](f func(T) U) []U { ... }
names := users.Map(func(u User) string { return u.Name })
```

### Promoted field literals

Set embedded struct fields directly with promoted field names in struct literals.

```go
// Before
doc := Document{
    AuditInfo: AuditInfo{CreatedBy: "alice", UpdatedBy: "alice"},
    Name: "report.pdf",
}

// After
doc := Document{
    CreatedBy: "alice",
    UpdatedBy: "alice",
    Name:      "report.pdf",
}
```

### `strings.CutLast` / `bytes.CutLast`

Use `CutLast` instead of `LastIndex` + manual slicing.

```go
// Before
i := strings.LastIndex(path, "/")
if i < 0 { return "", path, false }
dir, file := path[:i], path[i+1:]

// After
dir, file, found := strings.CutLast(path, "/")
```

### stdlib `uuid` package

Use `uuid` package instead of third-party libraries. See `package-choices.md` for details.

```go
// Before
import googleuuid "github.com/google/uuid"
id := googleuuid.New()

// After
import "uuid"
id := uuid.New()
```

### `url.Clone` / `url.Values.Clone`

Deep-copy URLs and values instead of manual field copying.

```go
// Before
copy := new(url.URL)
*copy = *base

// After
copy := base.Clone()
```

---

## Go 1.26+

### `new(value)` for pointer fields

Use `new(value)` instead of pointer helper functions or temp variables.

```go
// Before
cfg := Config{Timeout: Pointer(30 * time.Second)}

// After
cfg := Config{Timeout: new(30 * time.Second)}
```

`new` uses the default type of an untyped constant, so `new(30)` yields `*int`; write `new(30 * time.Second)` or `new(int32(30))` for specific types.

### `errors.AsType[T]`

Use `errors.AsType[T](err)` instead of `errors.As` with a temp var.

```go
// Before
var pathErr *os.PathError
if errors.As(err, &pathErr) { handle(pathErr) }

// After
if pathErr, ok := errors.AsType[*os.PathError](err); ok { handle(pathErr) }
```

---

## Go 1.25+

### `wg.Go`

Use `WaitGroup.Go` instead of `wg.Add` + `go func` + `defer wg.Done`.

```go
// Before
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func() { defer wg.Done(); process(item) }()
}
wg.Wait()

// After
var wg sync.WaitGroup
for _, item := range items {
    wg.Go(func() { process(item) })
}
wg.Wait()
```

---

## Go 1.24+

### `t.Context()`

Use `t.Context()` instead of `context.WithCancel(context.Background())` in tests.

```go
// Before
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// After
ctx := t.Context()
```

The context is canceled before `t.Cleanup` functions run. Cleanup needing a live context must create its own `context.Background()`.

### `b.Loop()`

Use `b.Loop()` instead of `for i := 0; i < b.N; i++` in benchmarks. `b.N` is only valid after `b.Loop()` returns, so restructure fixtures sized from `b.N`.

```go
// Before
func BenchmarkFoo(b *testing.B) {
    for i := 0; i < b.N; i++ { doWork() }
}

// After
func BenchmarkFoo(b *testing.B) {
    for b.Loop() { doWork() }
}
```

### `omitzero` JSON tag

Use `omitzero` for bool, numeric, struct, and `time.Time` fields whose zero value means absent. Keep `omitempty` for empty strings, slices, maps.

```go
type CacheEntry struct {
    Name      string    `json:"name,omitempty"`
    Warm      bool      `json:"warm,omitzero"`
    Hits      int64     `json:"hits,omitzero"`
    ExpiresAt time.Time `json:"expiresAt,omitzero"`
}
```

### `strings.SplitSeq` / `bytes.SplitSeq`

Use `SplitSeq` / `FieldsSeq` when iterating over split results. Streams substrings instead of allocating a slice.

```go
// Before
for _, part := range strings.Split(s, ",") { process(part) }

// After
for part := range strings.SplitSeq(s, ",") { process(part) }
```

### `http.ServeMux` method patterns

Use method-aware patterns and `r.PathValue`.

```go
// Before
mux.HandleFunc("/api/", func(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet { http.Error(w, "method not allowed", 405); return }
    id := strings.TrimPrefix(r.URL.Path, "/api/")
    handleID(w, r, id)
})

// After
mux.HandleFunc("GET /api/{id}", func(w http.ResponseWriter, r *http.Request) {
    handleID(w, r, r.PathValue("id"))
})
```

---

## Go 1.23+

### `maps.Keys` / `maps.Values` as iterators

Range over `maps.Keys` / `maps.Values` directly when a slice isn't needed.

```go
// Before
for k := range m { process(k) }

// After
for k := range maps.Keys(m) { process(k) }
```

### `slices.Collect`

Materialize an iterator into a slice.

```go
// Before
keys := make([]string, 0, len(m))
for k := range m { keys = append(keys, k) }

// After
keys := slices.Collect(maps.Keys(m))
```

### `slices.Sorted`

Collect and sort iterator values in one step.

```go
// Before
keys := make([]string, 0, len(m))
for k := range m { keys = append(keys, k) }
slices.Sort(keys)

// After
keys := slices.Sorted(maps.Keys(m))
```

### `time.Tick` GC

Go 1.23 can GC unreferenced tickers. Use `time.Tick` for simple forever loops, `time.NewTicker` when you need `Stop` / `Reset`.

```go
// Before
ticker := time.NewTicker(time.Second)
defer ticker.Stop()
for range ticker.C { poll() }

// After
for range time.Tick(time.Second) { poll() }
```

---

## Go 1.22+

### `range over int`

```go
// Before
for i := 0; i < len(items); i++ { process(items[i]) }

// After
for i := range len(items) { process(items[i]) }
```

### No redundant loop-variable copies

Go 1.22 gives each iteration its own variables. Drop `v := v` before closures, goroutines, or `&v`.

```go
// Before
for _, item := range items {
    item := item
    go func() { process(item) }()
}

// After
for _, item := range items {
    go func() { process(item) }()
}
```

If you need a pointer to the original slice element (not the per-iteration copy), use `&slice[i]`.

### `cmp.Or`

Pick the first non-zero value from a fallback chain. All args are evaluated before the call, so don't use for expensive or side-effecting alternatives, or when `false`/`0` is a valid result.

```go
// Before
name := os.Getenv("NAME")
if name == "" { name = "default" }

// After
name := cmp.Or(os.Getenv("NAME"), "default")
```

### `reflect.TypeFor[T]`

```go
// Before
typ := reflect.TypeOf((*T)(nil)).Elem()

// After
typ := reflect.TypeFor[T]()
```

---

## Go 1.21+

### Built-in `min` / `max`

```go
// Before
if b > a { a = b }

// After
a = max(a, b)
```

### `clear`

Delete all map entries or zero slice elements in place.

```go
// Before
for k := range m { delete(m, k) }

// After
clear(m)
```

### `slices` package

| Function | Replaces |
|---|---|
| `slices.Contains` | manual search loop |
| `slices.Index` | manual index loop |
| `slices.IndexFunc` | predicate-based manual loop |
| `slices.Sort` | `sort.Ints`, type-specific sort |
| `slices.SortFunc` | `sort.Slice` |
| `slices.SortStableFunc` | `sort.SliceStable` |
| `slices.Max` / `slices.Min` | manual scan loop |
| `slices.Reverse` | manual swap loop |
| `slices.Compact` | consecutive-duplicate removal |
| `slices.Clip` | `s[:len(s):len(s)]` |
| `slices.Clone` | `append([]T(nil), s...)` |

### `maps` package

| Function | Replaces |
|---|---|
| `maps.Clone` | manual map iteration copy |
| `maps.Copy` | `for k, v := range src { dst[k] = v }` |
| `maps.DeleteFunc` | manual delete loop with predicate |

### `sync.OnceFunc` / `sync.OnceValue`

```go
// Before
var once sync.Once
var value T
getter := func() T {
    once.Do(func() { value = computeValue() })
    return value
}

// After
getter := sync.OnceValue(func() T { return computeValue() })
```

### Typed atomics

Use `atomic.Bool`, `atomic.Int64`, `atomic.Pointer[T]` instead of untyped `atomic.StoreInt32` / `unsafe.Pointer`.

```go
// Before
var enabled int32
atomic.StoreInt32(&enabled, 1)

// After
var enabled atomic.Bool
enabled.Store(true)
```

```go
// Before
var ptr unsafe.Pointer
atomic.StorePointer(&ptr, unsafe.Pointer(cfg))

// After
var ptr atomic.Pointer[Config]
ptr.Store(cfg)
```

### `context.AfterFunc`

Run cleanup on context cancellation without a goroutine.

```go
// Before
go func() { <-ctx.Done(); cleanup() }()

// After
stop := context.AfterFunc(ctx, cleanup)
defer stop()
```

### `context.WithTimeoutCause` / `context.WithCancelCause`

When callers need to inspect the cancellation reason.

```go
// Before
ctx, cancel := context.WithCancel(parent)

// After
ctx, cancel := context.WithCancelCause(parent)
cancel(err)
cause := context.Cause(ctx)
```

### `log/slog`

Structured logging, zero deps. See `package-choices.md`.

---

## Go 1.20+

### `errors.Join`

Combine multiple errors while preserving `errors.Is` / `errors.As` matching.

```go
// Before
if err1 != nil && err2 != nil {
    return fmt.Errorf("%v; %w", err1, err2)
}

// After
return errors.Join(err1, err2)
```

### `strings.CutPrefix` / `strings.CutSuffix`

```go
// Before
if strings.HasPrefix(s, "pre:") { rest := strings.TrimPrefix(s, "pre:"); use(rest) }

// After
if rest, ok := strings.CutPrefix(s, "pre:"); ok { use(rest) }
```

### `bytes.Clone`

```go
// Before
copied := append([]byte(nil), b...)

// After
copied := bytes.Clone(b)
```

---

## Go 1.19+

### `fmt.Appendf`

Append formatted text to a byte slice without intermediate `Sprintf`.

```go
// Before
buf = append(buf, []byte(fmt.Sprintf("x=%d", x))...)

// After
buf = fmt.Appendf(buf, "x=%d", x)
```

### Typed atomics (Go 1.19+)

`atomic.Bool`, `atomic.Int64`, `atomic.Pointer[T]` introduced. See Go 1.21 section.

---

## Go 1.18+

### `any` over `interface{}`

```go
// Before
func Decode(v interface{}) error

// After
func Decode(v any) error
```

### `strings.Cut` / `bytes.Cut`

```go
// Before
i := strings.Index(s, ":")
if i < 0 { return "", "", false }
key, value := s[:i], s[i+1:]

// After
key, value, found := strings.Cut(s, ":")
```

### `strings.Clone`

Copy a string without retaining shared backing memory.

```go
// Before
copied := string([]byte(s))

// After
copied := strings.Clone(s)
```

---

## Go 1.13+

### `errors.Is`

Use `errors.Is(err, target)` instead of `err == target` so wrapped errors are handled correctly.

```go
// Before
if err == os.ErrNotExist { return nil }

// After
if errors.Is(err, os.ErrNotExist) { return nil }
```

---

## Go 1.8+

### `time.Until` / `time.Since`

```go
// Before
remaining := deadline.Sub(time.Now())
elapsed := time.Now().Sub(start)

// After
remaining := time.Until(deadline)
elapsed := time.Since(start)
```
