# Technical specification: Virtual Graph reading as the person asking

**Audience:** engineers who know Virtual Graph (VG) and want to know exactly how a query's row-level security gets from the warehouse to the graph result, what it relies on, and where it would break.
**Status:** built and checked (local 2026-09-28; hosted, and through a composite database, 2026-10-09). A reference implementation, not a product feature. VG is in public preview, and everything here was learned from outside it: we read VG's behaviour, not its source.
**See also:** [README.md](README.md) (how to build and run it), [plans/2026-09-28-jdbc-passthrough.md](../plans/2026-09-28-jdbc-passthrough.md) (the decision and its reasons), [results/entitlements.md](../examples/fennmoor-bank/results/entitlements.md) (the evaluation).

## 1. The method in one paragraph

VG turns a Cypher query into SQL and sends it to the warehouse over JDBC, always as one identity (the data source's). We leave VG alone and change what is on the other end of that JDBC call. A small driver that takes the place of the warehouse's real JDBC driver (a) receives every SQL statement VG sends, (b) finds in it a **signed token, naming the person the query is for, that the gateway smuggled in as an ordinary Cypher parameter**, (c) verifies the token, (d) strips it out of the SQL so it never reaches the warehouse, and (e) runs the statement on a connection that **impersonates that person**. The warehouse then applies its own tables, columns, row policies and masking, because from its side the person is the one asking. A statement with no valid token is refused, never run as the data source. Nothing in VG changes, and no access rule is re-implemented anywhere: the warehouse remains the only rulebook.

```
 agent / user
     │  "as risk"
     ▼
 gateway (qlsc ask, the demo server)          trusted: holds the signing key, decides who the caller is
     │  Cypher + WHERE $qlsc_principal IS NOT NULL,  parameter qlsc_principal = token(risk, expires)
     ▼
 Virtual Graph (Neo4j)  ── plans ──▶  SQL: ... WHERE (? /*qlsc_principal*/ IS NOT NULL) ...   (token bound to the ?)
     │  JDBC
     ▼
 stand-in driver  (this repo, inside VG's JVM)
     │  verify token ─ remove the predicate and the parameter ─ pick the connection for "risk"
     ▼
 real BigQuery driver, ServiceAccountImpersonationEmail=<risk>        (the warehouse's own driver, unchanged)
     ▼
 BigQuery: runs as risk; row access policies, column tags and masking apply
```

## 2. The problem

VG reads the warehouse through one data source with one credential. Three things follow:

- **Row-level security is lost.** A row access policy filters by who runs the query. VG's reads all run as the data source, so every graph user sees what the data source sees. In the example, the data source sees 24,300 customers, and the risk team's policy allows 4,016.
- **VG applies no graph privileges to what it reads.** A Neo4j user with access to the database can read the whole virtual graph (finding 2 of the entitlements plan). Neo4j's own privileges cannot express "this user's rows" for a virtual graph.
- **Refusing is not a fix.** The first approach (option A in the plan) refused any Cypher query that touched a table with a row policy. That was safe and over-restrictive: 9 of 60 test questions were refused, including a table the principal could read entirely, because the graph's hub node sits on a table with a policy.

So the identity has to change at the one place that sees every statement VG sends: its JDBC driver.

## 3. Goals, threat model, non-goals

**Goals**
1. A graph query's rows, columns, aggregates and masking are exactly what the warehouse would return to the person asking, with no copy of the policy anywhere else.
2. **Fail closed.** Any statement that cannot show whom it is for is refused. There is no path where an error or a missing token turns into a read as the data source.
3. No change to VG, and no new service on the query path. The mechanism runs inside VG's JVM.
4. Provable from outside: the warehouse's own job log says who ran each job.

**Trust boundary.** Trusted: the gateway (it decides who the caller is and holds the signing key), the stand-in driver and the code in VG's JVM, the warehouse and its identity permissions. Not trusted: any Neo4j client that can open a bolt connection to VG, including one that never goes through the gateway.

**What an attacker with a bolt connection to VG can and cannot do**

| Attempt | Result |
|---|---|
| Send Cypher with no `$qlsc_principal` | the SQL VG generates has no marker: refused ([§5.5](#55-the-gate-materialize)) |
| Send a token they made up, or one for another principal with a changed name | HMAC does not match: refused |
| Send an expired token | refused |
| Send a valid token for principal P, obtained from the gateway | runs as **P**, which is the point: P's permissions bound what they can read. See the bearer-token limit in [§9](#9-limits-and-open-questions) |
| Read VG's schema (labels, property names) | allowed: names, not rows ([§8](#8-where-else-information-can-leak)) |

**Non-goals:** authenticating people (the gateway decides who a caller is; here, service accounts stand in for people), protecting the signing key from whoever holds it, hiding the existence of a table from someone who talks to VG directly, writes (the demo server is read-only; the driver does not distinguish).

## 4. Components

| Piece | Where | Role |
|---|---|---|
| Gateway | [src/qlsc/entitle.py](../src/qlsc/entitle.py) | signs each query for a principal: adds the predicate, makes the token, checks the driver is enforcing |
| `BigQueryDriver` (stand-in) | [src/com/google/cloud/bigquery/jdbc/BigQueryDriver.java](src/com/google/cloud/bigquery/jdbc/BigQueryDriver.java) | the class VG looks for; registers for `jdbc:bigquery:` and hands connections to `Passthrough` |
| `Passthrough` | [src/qlsc/passthrough/Passthrough.java](src/qlsc/passthrough/Passthrough.java) | wraps connections and statements; the gate; per-principal connections |
| `Token` | [src/qlsc/passthrough/Token.java](src/qlsc/passthrough/Token.java) | sign and verify; mirrors `entitle.token` |
| `Rewrite` | [src/qlsc/passthrough/Rewrite.java](src/qlsc/passthrough/Rewrite.java) | finds the token's `?` in the SQL and removes the predicate |
| The real driver | `google-cloud-bigquery-jdbc-1.0.0-all.jar` | unchanged; mounted outside Neo4j's `lib/` and loaded by `Passthrough` |
| The warehouse | BigQuery | impersonation, and all policy enforcement |

The driver is about 450 lines of Java 21 with no dependencies but the JDK.

## 5. How it works

### 5.1 Taking the real driver's place

VG requires a driver named `com.google.cloud.bigquery.jdbc.BigQueryDriver` and connects through `DriverManager`. The jar here contains a class of that exact name:

```java
// BigQueryDriver.java:19  (the stand-in VG finds; abridged)
static { DriverManager.registerDriver(new BigQueryDriver()); }
public Connection connect(String url, Properties info) throws SQLException {
    return acceptsURL(url) ? Passthrough.connect(url, info) : null;
}
```

and `build.sh` adds `META-INF/services/java.sql.Driver` naming it. The jar is mounted over the real jar's file name in Neo4j's `lib/`, so VG finds "the driver it needs". The real driver is mounted elsewhere and loaded on demand by `Passthrough`, in a class loader that looks in the real jar *first* for its own package, because two classes of one name would otherwise collide:

```java
// Passthrough.java:268  (abridged)
static final class ChildFirst extends URLClassLoader {
    protected Class<?> loadClass(String name, boolean resolve) {
        ...
        if (c == null && name.startsWith("com.google.cloud.bigquery.jdbc.")) { c = findClass(name); }  // its own package: ours, from the real jar
        if (c == null) { c = getParent().loadClass(name); }                                              // everything else: as usual
```

`Passthrough.real()` (line 57) loads it once, and every later `connect` goes through `real().connect(url, info)`. Nothing is copied or patched in the real driver.

### 5.2 The token

The gateway signs "who this query is for", with a key only it and the driver hold:

```
token = base64url(principal + "\n" + expires)  "."  base64url(HMAC-SHA256(key, principal + "\n" + expires))
```

```python
# entitle.py:214  (abridged)
def token(s, principal, now=None):
    expires = int((now or time.time()) + s["entitlements"]["token_seconds"])   # 300 s by default
    payload = f"{principal}\n{expires}".encode()
    return b64(payload) + "." + b64(hmac.new(key(s), payload, hashlib.sha256).digest())
```

```java
// Token.java:29  (abridged)
public static String verify(byte[] key, String token, long now) throws Invalid {
    ...
    if (!MessageDigest.isEqual(sig, mac(key, payload))) throw new Invalid("a principal token not signed by the gateway");  // constant time
    ...
    if (now > expires) throw new Invalid("an expired principal token");
    return payload.substring(0, nl);     // the principal
}
```

The principal is the identity to impersonate (for BigQuery, a service account email). **The empty principal means "the data source itself"**, used for the estate's own reads (building the graph, memory's reads with no principal named). The signature is checked with a constant-time compare. Any change to the principal invalidates the signature, which `SelfTest` checks (a token with a changed name is refused).

### 5.3 Getting the token into the SQL

This is the part that makes the design possible without touching VG. VG does carry Cypher *parameters* into the SQL it sends, as JDBC bind parameters, and it labels each one with a comment. From the SQL VG sends (shape taken from the self-test, which copies what VG emits):

```sql
SELECT `c`.`state_code` AS `st`, count(*) AS `n`
FROM `p`.`g`.`dim_customer` AS `c`
WHERE (`c`.`segment` = ? /*autostring0*/) AND (? /*qlsc_principal*/ IS NOT NULL)
GROUP BY `st` LIMIT ? /*param_1*/
```

`/*autostring0*/` is a literal VG lifted out of the Cypher; `/*param_1*/` is one it generated; **`/*qlsc_principal*/` is the name of a Cypher parameter we supplied**. So a Cypher predicate that mentions a parameter,

```cypher
MATCH (c:Customer) WHERE $qlsc_principal IS NOT NULL RETURN ...
```

arrives in every SQL statement VG writes for that query as `(? /*qlsc_principal*/ IS NOT NULL)`, with the token as the bound value. The predicate is always true when a token is present, so it changes no result; it exists only to make VG carry the token to the driver.

The gateway adds the predicate itself ([entitle.py:226](../src/qlsc/entitle.py), `signed()`): into the `WHERE` of the query's first `MATCH`, or as a new `WHERE` there, bracketing the user's own conditions so the predicate holds over all of them:

```python
return f"{cypher[:where[1]]} $qlsc_principal IS NOT NULL AND ({body})\n{cypher[end:]}"
```

**Observed, not guaranteed:** the predicate reached every statement in one-hop, multi-hop, two-step and truncating plans. That is an empirical fact about VG at the version tested, and the design does not depend on it for *safety* (§5.5: a statement without the marker is refused), only for the query working.

### 5.4 Deferring the statement

The token is a bound *parameter*, set after the statement is prepared, but the connection a statement must run on depends on the token. So the driver cannot prepare the statement on a connection at `prepareStatement` time. `Conn` and `Stmt` are `java.lang.reflect.Proxy` objects that hold the statement back:

```java
// Passthrough.java:154  (Stmt.invoke, abridged)
if (inner == null && (name.startsWith("set") || name.equals("clearParameters") || name.equals("addBatch"))) {
    calls.add(new Object[] {m, args});   // remembered, not applied
    return null;
}
...
if (inner == null) inner = materialize();   // anything that runs the statement: now, on the right connection
return call(inner, m, args);
```

Parameter setters are recorded as `(Method, args)`. The first call that needs the statement for real (`executeQuery`, etc.) triggers `materialize()`. Two calls are answered earlier without materializing: `close`/`isClosed`, and `getMetaData`/`getParameterMetaData`, which return column types computed on the **base** connection from the rewritten SQL (line 163). That is how VG checks its schema at startup, and it reads names and types, not rows.

### 5.5 The gate: `materialize`

All enforcement is in one method, [Passthrough.java:174](src/qlsc/passthrough/Passthrough.java) (abridged here; the comments in the excerpt are descriptions, not the file's):

```java
PreparedStatement materialize() throws Throwable {
    if (!signed && keyCheck(sql)) { ... run on base ... }          // the one unsigned statement allowed
    if (!signed) {
        throw new SQLException("qlsc pass-through: refused, the query carries no principal token ...");
    }
    Rewrite.Result r = Rewrite.of(sql);                            // which ? is the token, and the SQL without the predicate
    Object token = <the value bound to parameter r.parameter()>;
    String principal = Token.verify(key(), token == null ? null : token.toString(), now);   // throws: refused
    Connection target = conn.forPrincipal(principal);              // base, or the principal's own
    args[0] = r.sql();                                             // the SQL without the predicate
    PreparedStatement p = call(target, prepare, args);
    for (each recorded setter) {
        if (i == r.parameter()) continue;                          // the token: never sent on
        if (i > r.parameter()) a[0] = i - 1;                       // the ones after it move up one
        call(p, m, a);
    }
    log("ran a statement as " + principal);
    return p;
}
```

Reading it as a decision table, for a statement VG sends:

| The SQL | Then |
|---|---|
| has no `/*qlsc_principal*/` marker | refused (unless it is VG's key check, §5.7) |
| has the marker, no value bound to that parameter | `Token.verify(null)` → "no principal token": refused |
| has the marker, a forged, malformed or expired token | refused, with the reason |
| has the marker and a valid token | runs as the token's principal |
| the marker is present but not as a `? /*…*/ IS NOT NULL` predicate | `Rewrite.of` throws: the statement does not run |

**This is the invariant the design rests on: a statement runs only on a connection chosen by a verified token, and every other outcome is an exception.** There is no default branch that runs it as the data source. That is why §5.3's "observed, not guaranteed" does not matter for safety: if a future VG plan produced a statement without the marker, the cost is a refused query, not a read as the data source.

`Rewrite.of` ([Rewrite.java:20](src/qlsc/passthrough/Rewrite.java)) walks the SQL character by character, skipping quoted strings and backtick names (so a `?` inside a literal is not a parameter), counts `?` placeholders to find the **1-based index of the one followed by the marker**, and replaces `? /*qlsc_principal*/ IS NOT NULL` with `TRUE`, leaving the SQL valid and the other parameters in place:

```sql
... WHERE (`c`.`segment` = ? /*autostring0*/) AND (TRUE) GROUP BY `st` LIMIT ? /*param_1*/
```

The token is therefore never sent to the warehouse, so it does not appear in job history or any warehouse-side log.

### 5.6 One connection per principal

```java
// Passthrough.java:103
Connection forPrincipal(String principal) throws SQLException {
    if (principal.isEmpty()) return base;                         // the data source's own identity
    Connection c = as.get(principal);
    if (c == null || c.isClosed()) {
        c = real().connect(url + ";ServiceAccountImpersonationEmail=" + principal, info);
        as.put(principal, c);
    }
    return c;
}
```

The real BigQuery driver already supports impersonation per connection through the `ServiceAccountImpersonationEmail` URL property, using whatever application-default credentials it already has (on a workstation, a credentials file for the data source's account; on a Google Cloud machine, the machine's own account through the metadata server). So **no token broker is needed**: the data source's account needs permission to impersonate each principal, and the driver just opens a connection with the property set.

`Conn` holds a map from principal to connection. A pooled connection (VG uses Hikari) is lent to one thread at a time, so the map needs no locking; its principal connections close when it does. The cost is a new warehouse connection the first time a principal is seen on a given pooled connection, not per statement.

### 5.7 What passes without a token

Exactly two things, both returning no data:

| | Why | How it is held to that |
|---|---|---|
| VG's startup check that a node key is unique: `SELECT 1 FROM `p`.`d`.`t` GROUP BY `k` HAVING COUNT(*) > 1 LIMIT 1` | without it, VG will not start (found the hard way: the first deployment refused it) | matched whole by one regex ([Passthrough.java:229](src/qlsc/passthrough/Passthrough.java)); anything more or different, such as a different `SELECT` list or a trailing `UNION`, is refused (the self-test checks both) |
| Metadata: `DatabaseMetaData`, and a prepared statement's column types | VG checks its schema this way | answered on the base connection: names and types, not rows |

A plain (unprepared) statement, `createStatement().execute(sql)`, goes through `Unsigned` (line 237), which refuses everything except the key check.

### 5.8 The gateway fails closed too

The driver being absent is a way to lose the guarantee silently: if the real driver were mounted in its place (a configuration slip), VG would read as the data source for everyone and the gateway would not know. So before the gateway reads on anyone's behalf it checks, once per VG instance, that VG **refuses an unsigned query**:

```python
# entitle.py:248  (abridged)
UNSIGNED = "MATCH (n:`{label}`) RETURN count(n) AS n"
def enforced(s, V):
    try:
        V.rows(UNSIGNED.format(label=label)); _ENFORCED[uri] = False       # it ran: no pass-through
    except Neo4jError as e:
        if "pass-through: refused" not in (e.message or ""): raise
        _ENFORCED[uri] = True
```

If it runs, `signing()` raises `Unenforced` and the read is refused.

## 6. A query end to end

As **risk**, "customers in each state":

1. **Gateway.** `signing()` verifies the pass-through is enforcing, then sends
   `MATCH (c:Customer) WHERE $qlsc_principal IS NOT NULL RETURN c.state_code AS state, count(DISTINCT c.customer_key) AS customers ORDER BY customers DESC`
   with parameter `qlsc_principal = token("qlsc-risk@<project>…", now + 300)`.
2. **VG** plans it and sends one SQL statement to the driver (abridged):
   ``SELECT `c`.`state_code` AS `state`, count(distinct `c`.`customer_key`) AS `customers` FROM `<project>`.`<dataset>`.`dim_customer` AS `c` WHERE (? /*qlsc_principal*/ IS NOT NULL) GROUP BY … ORDER BY …``
   and binds the token to the `?`.
3. **Driver.** `prepareStatement` returns a held proxy. On execute: the marker is there; the token verifies for `qlsc-risk@…`; the predicate becomes `(TRUE)`; a connection with `;ServiceAccountImpersonationEmail=qlsc-risk@…` is opened (or reused); the SQL is prepared and run on it.
4. **BigQuery** runs the job as `qlsc-risk@…`. The dataset's row access policy on `dim_customer` leaves two states. The job log's `user_email` is `qlsc-risk@…`.
5. **VG** builds the graph result from rows it was given: 2 states, 4,016 customers. The administrator, the same question, gets 8 and 24,300; the contact center's job is refused by BigQuery.

## 7. Evidence

| Check | How | Result |
|---|---|---|
| Unit | `SelfTest` (the build runs it): sign/verify, expired, forged, another key, changed principal, malformed, none; the rewrite (parameter found by label, predicate removed, others stay, `?` in a literal left alone); the key check's pattern | all pass |
| Oracle | `eval/entitlements.py`: three principals, 20 questions, both routes. Every Cypher answer is checked against **BigQuery's job log**: each job VG ran for it carries the principal's identity (`INFORMATION_SCHEMA.JOBS`, by the `app=neo4j-virtual-graph` label) | 0 schema leaks, 0 row incidents, every answer ran as its principal ([results/entitlements.md](../examples/fennmoor-bank/results/entitlements.md)) |
| Direct access | a query to VG with no token, a forged token (one principal's name, another's signature), an expired token | all refused by the driver |
| Negative controls | four ways of breaking the gateway on purpose, five tries (e.g. one that signs every query as the data source, not the principal; one that runs SQL as the estate) | all caught: two by the rows check (the job log for Cypher), three by the schema check |
| Hosted | the same question through the deployed service as three principals, and unsigned | 8 states / 2 states / refused / refused; job log: the data source's account, then `qlsc-risk`, and no job for the refusals |
| Composite | `USE fennmoor.rows MATCH …` with the token as a parameter, hosted and local | same results; the signed parameter survives the composite's remote alias |

The property under test is *who ran the job*, read from the warehouse's own log, not whether the numbers look right. The numbers (24,300 → 4,016) are the sanity check; the job log is the proof.

## 8. Where else information can leak

The question this design should be judged on is not only "are the rows right" but which other channels carry information about data a person may not read. For each, what this design does and what it leaves:

| Channel | Status | How |
|---|---|---|
| **Row contents** | closed | the warehouse filters as the principal |
| **Columns, masking** | closed | the warehouse's column tags and masking apply to the principal's job |
| **Aggregates** (`count`, `sum`, group-bys) | closed | computed by the warehouse over what the principal may see (8 states become 2, 24,300 becomes 4,016); no post-filtering is done by VG or the gateway |
| **A table the principal may not read** | closed for rows; the existence leaks in an error to a direct bolt user | BigQuery's error names the table (we saw `Access Denied: Table <project>:…`). The demo server rewrites it to "the data it needs either does not exist or is not available to you"; a raw bolt client gets BigQuery's text |
| **VG's schema** (labels, property names) | open, by design | VG applies no graph privileges, so anyone with database access sees the model. The gateway filters the model for its own navigation (`entitle.model()`: only labels over readable tables, without hidden properties), but that does not bind a client that goes straight to bolt |
| **Metadata calls** | open, names only | answered on the base connection, so they reveal names and types of the graph's tables, not rows |
| **Key check** | open, one bit | VG's startup check returns "is this column's key unique" as the data source, matched by an exact pattern; VG, not a client, sends it |
| **Caches** | closed, as far as seen | the driver caches nothing; VG has no result cache we have seen. **If one existed it would have to key by principal**; nothing here would stop it from leaking across principals |
| **Connection pool** | closed | a pooled connection keeps a separate connection per principal; one principal's statements never run on another's |
| **Warehouse job history** | closed for the token | the token is removed from the SQL, so it is never in the warehouse's logs; jobs carry a label (`app=neo4j-virtual-graph`) so they can be audited |
| **VG logs** | open, small | the driver logs `ran a statement as <principal>` and, for a refusal, the first 160 characters of the SQL (no data) |
| **Agent memory** (promoted results) | outside this mechanism | a remembered context is a *copy* of rows, read when the principal asked. It leaves the warehouse's policies; the answer there is retention (six hours, swept) and a separate evaluation (`eval/memory_entitlements.py`) |
| **Prompts and navigation (LLM)** | outside this mechanism | the gateway's allowlist keeps unreadable tables, hidden columns and their filter values out of what a model is shown; checked by canary strings in `eval/entitlements.py` ("schema" leaks: 0) |
| **Timing, row counts, errors that differ by data** | not addressed | an answer's latency or an error that differs between "empty" and "denied" could signal; not measured |
| **Writes** | not addressed | the demo server opens read-only sessions; the driver does not distinguish a read from a write |

The method generalises to any of the channels the **warehouse** already controls (rows, columns, masking, aggregates), because the warehouse is the one making the decision and the driver only changes who it thinks is asking. It does not extend, by itself, to channels the warehouse does not see: the graph's own schema, caches inside VG, copies taken out of the warehouse (memory), or what is shown to a model. Those need their own rule, and most of them are kept closed here by the gateway, not by the driver.

## 9. Limits and open questions

Honest list, roughly in the order a reviewer would raise them.

1. **The token is a bearer token, and not bound to a query.** Whoever holds a valid token for principal P can run any Cypher as P until it expires (300 s by default). That is bounded by P's permissions, but it is not nothing: a token captured in transit could be replayed. Binding the token to a hash of the query, or to the Bolt session, would close it; we did not.
2. **The key is a shared secret.** Whoever holds it can sign for any principal the data source may impersonate, **including the data source itself** (the empty principal), which is the estate's full access. Locally it is a file on the host; hosted, a secret readable by the two service accounts that need it. A deployment should rotate it (the driver reads it once, at first use, so rotating means restarting VG).
3. **Service accounts stand in for people.** The data source's account must be allowed to impersonate each principal, so its own permissions are the ceiling of what any principal can read. There is no OIDC or workforce identity.
4. **The trust boundary is VG's JVM.** The proxies guard the path VG uses. Code inside the same JVM can reach around them: `unwrap`/`isWrapperFor` and `getMetaData()` are passed straight to the base connection ([Passthrough.java:129](src/qlsc/passthrough/Passthrough.java)), so they hand back objects of the real driver (and a metadata object's `getConnection()` is the base connection), which would run as the data source. Nothing reachable from Cypher does this, as far as we know; a Neo4j procedure or plugin loaded into the same server could.
5. **A prepared statement is assumed to be bound once and run once.** The held parameters are replayed, with the token skipped and later indexes shifted, at the first execution. After that (`inner != null`), calls go through unchanged, so a statement *re-bound* afterwards would use unshifted indexes. VG as tested prepares a statement per execution; we have not checked that it never reuses one.
6. **`signed()` is textual, not a parser.** It inserts the predicate with a small regex over Cypher's clause keywords. Shapes it does not handle well (e.g. a `UNION` whose second branch has its own `MATCH`) may produce SQL statements with no marker. Per §5.5 that yields a refused query, not a wrong read, but it is a functionality limit.
7. **It matches one driver's behaviour.** The class name, the `ServiceAccountImpersonationEmail` property, and the shape of VG's SQL (`? /*name*/`) are all outside our control. They hold at `google-cloud-bigquery-jdbc-1.0.0` and the VG in `neo4j:2026.09.0-enterprise`; either changing is a thing to re-check with the self-test and the oracle.
8. **Not measured:** the added latency of the first statement per principal per pooled connection (a new warehouse connection), how many principals a pool can hold, and the effect of driver-level metadata calls at scale.
9. **BigQuery only.** The mechanism (identity per connection) exists in other warehouses' drivers (a session role, an `EXECUTE AS`, an assumed role), but only BigQuery was built and tested.

## 10. What would make this unnecessary: a proposal, not a finding

The shim exists because VG has no way to say "this query is for someone else". Four additions to VG would make the method a supported feature instead of a driver substitute. These are suggestions, offered for the VG team to weigh, not things we know to be easy:

1. **Per-query context to the data-source provider.** Pass a declared, query-scoped value (a Bolt transaction metadata entry, or a named parameter) to the provider as a connection property or a call on a connection factory, so the identity can switch without a parameter smuggled through the SQL.
2. **A connection-provider hook** that VG calls per query (or per transaction) with that context and that returns the connection to use. Impersonation, a session role or a per-user token would live there.
3. **Stable, documented parameter labels** (`/*name*/`) if the comment route stays; this method depends on them today.
4. **Graph privileges on virtual graphs**, so a database-level rule can say which labels and properties a user's graph may show; today the schema is visible to anyone with access ([§8](#8-where-else-information-can-leak)).

## 11. Porting to another warehouse or source

What the method needs from the source, and what the driver would have to do:

1. A JDBC driver VG loads by name, so a stand-in can take its place (and a way to load the real one beside it).
2. A way to run a statement **as someone else** on a connection: impersonation, a session-level role, a delegated token, an assumed role.
3. The source must enforce its own rules for that identity (row policies, column rules, masking), or this adds nothing.
4. The same smuggled-parameter trick must reach the SQL: VG must carry a Cypher parameter into every statement with a recognisable marker. If it does not, the driver has nothing to verify.
5. A job log or audit trail that names the identity, to prove it from outside.

## 12. Files

| | |
|---|---|
| [src/qlsc/passthrough/Passthrough.java](src/qlsc/passthrough/Passthrough.java) | the connection and statement proxies, the gate, per-principal connections, the real driver's loader |
| [src/qlsc/passthrough/Token.java](src/qlsc/passthrough/Token.java) | token sign and verify |
| [src/qlsc/passthrough/Rewrite.java](src/qlsc/passthrough/Rewrite.java) | the token's parameter, the predicate's removal |
| [src/com/google/cloud/bigquery/jdbc/BigQueryDriver.java](src/com/google/cloud/bigquery/jdbc/BigQueryDriver.java) | the stand-in VG finds |
| [test/qlsc/passthrough/SelfTest.java](test/qlsc/passthrough/SelfTest.java) | the self-test `build.sh` runs |
| [../src/qlsc/entitle.py](../src/qlsc/entitle.py) | the gateway: `token`, `signed`, `signing`, `enforced`, the allowlist |
| [../examples/fennmoor-bank/eval/entitlements.py](../examples/fennmoor-bank/eval/entitlements.py) | the oracle, the direct probes, the negative controls |
