package qlsc.passthrough;

import java.io.IOException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.Driver;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

/**
 * The JDBC pass-through (plans/2026-09-28-jdbc-passthrough.md): Virtual Graph reads BigQuery as the
 * principal a query is for, not as its own single identity.
 *
 * A statement Virtual Graph prepares from a signed Cypher query carries the gateway's token as the
 * parameter labelled qlsc_principal. On execution the token is verified (Token), its predicate taken out
 * (Rewrite), and the statement run on a connection for that principal: the same URL with
 * ServiceAccountImpersonationEmail=<principal>, which the real driver honours from the application-default
 * credentials it already uses. Unsigned, forged or expired statements are refused; metadata calls (how
 * Virtual Graph checks its schema) go to the base connection.
 */
public final class Passthrough {
    private Passthrough() {}

    static final String REAL_JAR = env("QLSC_REAL_DRIVER", "/var/lib/neo4j/qlsc/google-cloud-bigquery-jdbc-1.0.0-all.jar");
    static final String KEY_FILE = env("QLSC_PASSTHROUGH_KEY_FILE", "/nvg_home/passthrough.key");
    static final String REAL_CLASS = "com.google.cloud.bigquery.jdbc.BigQueryDriver";

    private static Driver real;
    private static byte[] key;

    static String env(String name, String fallback) {
        String v = System.getenv(name);
        return v == null || v.isBlank() ? fallback : v;
    }

    static void log(String message) {
        System.err.println("qlsc-passthrough: " + message);
    }

    /** The real driver, from its own jar, in a loader that looks there first for its own package: this
     * jar holds a class of the same name (the stand-in Virtual Graph asks for). */
    static synchronized Driver real() throws SQLException {
        if (real == null) {
            try {
                URL jar = Path.of(REAL_JAR).toUri().toURL();
                ClassLoader loader = new ChildFirst(new URL[] {jar}, Passthrough.class.getClassLoader());
                real = (Driver) loader.loadClass(REAL_CLASS).getDeclaredConstructor().newInstance();
                log("the real driver from " + REAL_JAR + "; enforcing principal tokens");
            } catch (Exception e) {
                throw new SQLException("qlsc pass-through: can't load the real BigQuery driver from " + REAL_JAR, e);
            }
        }
        return real;
    }

    static synchronized byte[] key() throws SQLException {
        if (key == null) {
            try {
                key = HexFormat.of().parseHex(Files.readString(Path.of(KEY_FILE)).strip());
            } catch (IOException | IllegalArgumentException e) {
                throw new SQLException("qlsc pass-through: no key at " + KEY_FILE, e);
            }
        }
        return key;
    }

    public static Connection connect(String url, Properties info) throws SQLException {
        Connection base = real().connect(url, info);
        if (base == null) return base;
        return (Connection) Proxy.newProxyInstance(
                Passthrough.class.getClassLoader(), new Class<?>[] {Connection.class}, new Conn(url, info, base));
    }

    /** A connection whose signed statements run as their principal. Hikari lends it to one thread at a
     * time, so its per-principal connections need no locking. */
    static final class Conn implements InvocationHandler {
        final String url;
        final Properties info;
        final Connection base;
        final Map<String, Connection> as = new HashMap<>();

        Conn(String url, Properties info, Connection base) {
            this.url = url;
            this.info = info;
            this.base = base;
        }

        Connection forPrincipal(String principal) throws SQLException {
            if (principal.isEmpty()) return base; // the data source's own identity: the estate's own reads
            Connection c = as.get(principal);
            if (c == null || c.isClosed()) {
                c = real().connect(url + ";ServiceAccountImpersonationEmail=" + principal, info);
                as.put(principal, c);
            }
            return c;
        }

        @Override
        public Object invoke(Object proxy, Method m, Object[] args) throws Throwable {
            String name = m.getName();
            if (name.equals("prepareStatement") && args != null && args[0] instanceof String sql) {
                return Proxy.newProxyInstance(
                        Passthrough.class.getClassLoader(), new Class<?>[] {PreparedStatement.class}, new Stmt(this, m, args, sql));
            }
            if (name.equals("createStatement") || name.equals("prepareCall")) {
                Object inner = call(base, m, args);
                Class<?> type = name.equals("prepareCall") ? java.sql.CallableStatement.class : Statement.class;
                return Proxy.newProxyInstance(Passthrough.class.getClassLoader(), new Class<?>[] {type}, new Unsigned(inner));
            }
            if (name.equals("close")) {
                for (Connection c : as.values()) c.close();
                as.clear();
            }
            if (name.equals("unwrap") || name.equals("isWrapperFor")) return call(base, m, args);
            if (name.equals("getMetaData")) return (DatabaseMetaData) call(base, m, args); // names, not rows
            return call(base, m, args);
        }
    }

    /** A prepared statement held until it executes: the token is a parameter, bound after it is prepared. */
    static final class Stmt implements InvocationHandler {
        final Conn conn;
        final Method prepare;
        final Object[] prepareArgs;
        final String sql;
        final boolean signed;
        final List<Object[]> calls = new ArrayList<>(); // (Method, args) before it runs
        PreparedStatement inner;

        Stmt(Conn conn, Method prepare, Object[] prepareArgs, String sql) {
            this.conn = conn;
            this.prepare = prepare;
            this.prepareArgs = prepareArgs;
            this.sql = sql;
            this.signed = Rewrite.signed(sql);
        }

        @Override
        public Object invoke(Object proxy, Method m, Object[] args) throws Throwable {
            String name = m.getName();
            if (inner == null && (name.startsWith("set") || name.equals("clearParameters") || name.equals("addBatch"))) {
                calls.add(new Object[] {m, args});
                return null;
            }
            if (inner == null && (name.equals("close") || name.equals("isClosed"))) {
                return name.equals("isClosed") ? Boolean.FALSE : null;
            }
            if (inner == null && (name.equals("getMetaData") || name.equals("getParameterMetaData"))) {
                String text = signed ? Rewrite.of(sql).sql() : sql; // column types from the base connection: names, not rows
                try (PreparedStatement p = conn.base.prepareStatement(text)) {
                    return call(p, m, args);
                }
            }
            if (inner == null) inner = materialize();
            return call(inner, m, args);
        }

        /** Verify the token, take its predicate out, and prepare the statement as the principal. */
        PreparedStatement materialize() throws Throwable {
            if (!signed && keyCheck(sql)) { // Virtual Graph's key check: no rows, only a 1
                PreparedStatement p = (PreparedStatement) call(conn.base, prepare, prepareArgs);
                for (Object[] c : calls) call(p, (Method) c[0], (Object[]) c[1]);
                return p;
            }
            if (!signed) {
                log("refused an unsigned statement: " + brief(sql));
                throw new SQLException("qlsc pass-through: refused, the query carries no principal token (sign it through the qlsc gateway)");
            }
            Rewrite.Result r = Rewrite.of(sql);
            Object token = null;
            for (Object[] c : calls) {
                Object[] a = (Object[]) c[1];
                if (((Method) c[0]).getName().startsWith("set") && a != null && a.length >= 2
                        && a[0] instanceof Integer i && i == r.parameter()) token = a[1];
            }
            String principal;
            try {
                principal = Token.verify(key(), token == null ? null : token.toString(), System.currentTimeMillis() / 1000);
            } catch (Token.Invalid e) {
                log("refused a statement: " + e.getMessage());
                throw new SQLException("qlsc pass-through: refused, " + e.getMessage());
            }
            Connection target = conn.forPrincipal(principal);
            Object[] args = prepareArgs.clone();
            args[0] = r.sql();
            PreparedStatement p = (PreparedStatement) call(target, prepare, args);
            for (Object[] c : calls) {
                Method m = (Method) c[0];
                Object[] a = c[1] == null ? null : ((Object[]) c[1]).clone();
                if (m.getName().startsWith("set") && a != null && a.length >= 1 && a[0] instanceof Integer i
                        && m.getParameterTypes()[0] == int.class && isParameterSetter(m)) {
                    if (i == r.parameter()) continue; // the token: never sent on
                    if (i > r.parameter()) a[0] = i - 1;
                }
                call(p, m, a);
            }
            log("ran a statement as " + (principal.isEmpty() ? "the data source" : principal));
            return p;
        }
    }

    static String brief(String sql) {
        String one = sql.replaceAll("\\s+", " ").strip();
        return one.length() <= 160 ? one : one.substring(0, 160) + "...";
    }

    /** setString(int, ...), setObject(int, ...): a parameter; setFetchSize(int), setMaxRows(int): not. */
    static boolean isParameterSetter(Method m) {
        return m.getParameterCount() >= 2;
    }

    /** The one unsigned statement allowed: Virtual Graph's check, at startup, that a node key is unique. It
     * returns at most a constant 1, whether the key repeats, and no data. Matched whole, nothing looser. */
    static final java.util.regex.Pattern KEY_CHECK = java.util.regex.Pattern.compile(
            "SELECT 1 FROM `[\\w-]+`\\.`\\w+`\\.`\\w+` GROUP BY `\\w+` HAVING COUNT\\(\\*\\) > 1 LIMIT 1");

    static boolean keyCheck(String sql) {
        return KEY_CHECK.matcher(sql.replaceAll("\\s+", " ").strip()).matches();
    }

    /** A plain statement: no parameters, so no token. Refused when it executes; anything else passes. */
    static final class Unsigned implements InvocationHandler {
        final Object inner;

        Unsigned(Object inner) {
            this.inner = inner;
        }

        @Override
        public Object invoke(Object proxy, Method m, Object[] args) throws Throwable {
            if (m.getName().startsWith("execute") && args != null && args.length > 0 && args[0] instanceof String q
                    && keyCheck(q)) {
                return call(inner, m, args); // Virtual Graph's startup check that a node key is unique: no rows, only a 1
            }
            if (m.getName().startsWith("execute")) {
                log("refused an unsigned statement: " + (args != null && args.length > 0 && args[0] instanceof String q ? brief(q) : m.getName()));
                throw new SQLException("qlsc pass-through: refused, a plain statement carries no principal token");
            }
            return call(inner, m, args);
        }
    }

    static Object call(Object target, Method m, Object[] args) throws Throwable {
        try {
            return m.invoke(target, args);
        } catch (InvocationTargetException e) {
            throw e.getCause();
        }
    }

    /** Child-first for the real driver's own package (this jar has a class of that name); parent-first
     * otherwise, as when the real jar sat in lib/. */
    static final class ChildFirst extends URLClassLoader {
        ChildFirst(URL[] urls, ClassLoader parent) {
            super(urls, parent);
        }

        @Override
        protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
            synchronized (getClassLoadingLock(name)) {
                Class<?> c = findLoadedClass(name);
                if (c == null && name.startsWith("com.google.cloud.bigquery.jdbc.")) {
                    try {
                        c = findClass(name);
                    } catch (ClassNotFoundException e) {
                        c = null;
                    }
                }
                if (c == null) {
                    try {
                        c = getParent().loadClass(name);
                    } catch (ClassNotFoundException e) {
                        c = findClass(name);
                    }
                }
                if (resolve) resolveClass(c);
                return c;
            }
        }
    }
}
