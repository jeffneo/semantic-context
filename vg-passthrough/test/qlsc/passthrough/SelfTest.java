package qlsc.passthrough;

import java.nio.charset.StandardCharsets;

/** The token and the rewrite, checked without a warehouse (build.sh runs it before packaging). */
public final class SelfTest {
    static int failed = 0;

    static void check(boolean ok, String what) {
        System.out.println((ok ? "ok    " : "FAIL  ") + what);
        if (!ok) failed++;
    }

    static String invalid(byte[] key, String token, long now) {
        try {
            return "valid: " + Token.verify(key, token, now);
        } catch (Token.Invalid e) {
            return e.getMessage();
        }
    }

    public static void main(String[] args) throws Exception {
        byte[] key = "0123456789abcdef0123456789abcdef".getBytes(StandardCharsets.UTF_8);
        byte[] other = "fedcba9876543210fedcba9876543210".getBytes(StandardCharsets.UTF_8);
        String t = Token.sign(key, "qlsc-risk@p.iam.gserviceaccount.com", 1000);
        check(Token.verify(key, t, 999).equals("qlsc-risk@p.iam.gserviceaccount.com"), "a token names its principal");
        check(Token.verify(key, Token.sign(key, "", 1000), 5).isEmpty(), "the data source's own token names no one");
        check(invalid(key, t, 1001).contains("expired"), "an expired token is refused");
        check(invalid(other, t, 999).contains("not signed"), "a token signed with another key is refused");
        String forged = t.substring(0, t.indexOf('.')).replace('A', 'B') + t.substring(t.indexOf('.'));
        check(!invalid(key, forged, 999).startsWith("valid"), "a token whose principal was changed is refused");
        check(invalid(key, "nonsense", 999).contains("malformed"), "a malformed token is refused");
        check(invalid(key, null, 999).contains("no principal"), "no token is refused");

        String sql = "SELECT `c`.`state_code` AS `st`, count(*) AS `n` FROM `p`.`g`.`dim_customer` AS `c` "
                + "WHERE (`c`.`segment` = ? /*autostring0*/) AND (? /*qlsc_principal*/ IS NOT NULL) GROUP BY `st` LIMIT ? /*param_1*/";
        Rewrite.Result r = Rewrite.of(sql);
        check(r.parameter() == 2, "the token's parameter is found by its label: " + r.parameter());
        check(!r.sql().contains("qlsc_principal") && r.sql().contains("AND (TRUE)"), "its predicate is taken out: " + r.sql());
        check(r.sql().chars().filter(c -> c == '?').count() == 2, "the other parameters stay");
        Rewrite.Result q = Rewrite.of("SELECT '?' AS a, `x?` FROM t WHERE (? /*qlsc_principal*/ IS NOT NULL)");
        check(q.parameter() == 1, "a question mark in a literal or a name is not a parameter");
        check(!Rewrite.signed("SELECT 1"), "an unsigned statement is seen as unsigned");
        String keyCheck = "SELECT 1 FROM `jeffdavis-bq-testproj`.`fnb_graph`.`dim_customer` GROUP BY `customer_key` HAVING COUNT(*) > 1 LIMIT 1";
        check(Passthrough.keyCheck(keyCheck), "Virtual Graph's key check is allowed unsigned");
        check(Passthrough.keyCheck(keyCheck.replace(" GROUP", "\n  GROUP")), "however its lines are broken");
        check(!Passthrough.KEY_CHECK.matcher(keyCheck.replace("SELECT 1", "SELECT cif_number")).matches(), "a query reading a column in its shape is not");
        check(!Passthrough.KEY_CHECK.matcher(keyCheck + " UNION ALL SELECT 1").matches(), "nor one with more after it");
        if (failed > 0) {
            System.out.println(failed + " failed");
            System.exit(1);
        }
        System.out.println("all passed");
    }
}
