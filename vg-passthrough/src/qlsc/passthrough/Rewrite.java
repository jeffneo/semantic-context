package qlsc.passthrough;

/**
 * Virtual Graph's SQL for a signed query holds the gateway's predicate, `(? /*qlsc_principal*&#47; IS NOT
 * NULL)`: the Cypher's `$qlsc_principal IS NOT NULL`, its parameter labelled by name. This finds which
 * parameter it is and takes the predicate out, so the token never reaches the warehouse.
 */
public final class Rewrite {
    private Rewrite() {}

    public static final String MARK = "/*qlsc_principal*/";

    /** The SQL without the predicate, and the 1-based index of the token's parameter in the original. */
    public record Result(String sql, int parameter) {}

    public static boolean signed(String sql) {
        return sql != null && sql.contains(MARK);
    }

    public static Result of(String sql) {
        int index = 0;
        char quote = 0;
        for (int i = 0; i < sql.length(); i++) {
            char c = sql.charAt(i);
            if (quote != 0) {
                if (c == '\\') i++;
                else if (c == quote) quote = 0;
                continue;
            }
            if (c == '\'' || c == '"' || c == '`') {
                quote = c;
            } else if (c == '?') {
                index++;
                int after = skipSpace(sql, i + 1);
                if (sql.startsWith(MARK, after)) {
                    return new Result(removePredicate(sql, i, after + MARK.length()), index);
                }
            }
        }
        throw new IllegalArgumentException("no " + MARK + " parameter in the SQL");
    }

    /** `(? /*qlsc_principal*&#47; IS NOT NULL)` -> `(TRUE)`: the same shape, the same meaning, no parameter. */
    private static String removePredicate(String sql, int q, int markEnd) {
        int end = skipSpace(sql, markEnd);
        String rest = sql.substring(end);
        String isNotNull = "IS NOT NULL";
        if (rest.regionMatches(true, 0, isNotNull, 0, isNotNull.length())) {
            return sql.substring(0, q) + "TRUE" + sql.substring(end + isNotNull.length());
        }
        throw new IllegalArgumentException("the " + MARK + " parameter is not in an IS NOT NULL predicate");
    }

    private static int skipSpace(String s, int i) {
        while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++;
        return i;
    }
}
