package qlsc.passthrough;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * The gateway's signed statement of who a query is for: base64url("principal\nexpires") + "." +
 * base64url(HMAC-SHA256 of that payload), with the key only the gateway and this driver hold. The empty
 * principal is the data source itself (the estate's own reads). Mirrors qlsc/entitle.py's token().
 */
public final class Token {
    private Token() {}

    public static final class Invalid extends Exception {
        public Invalid(String why) {
            super(why);
        }
    }

    public static String sign(byte[] key, String principal, long expires) {
        String payload = principal + "\n" + expires;
        return b64(payload.getBytes(StandardCharsets.UTF_8)) + "." + b64(mac(key, payload));
    }

    /** The principal a token names, or Invalid: malformed, forged (another key), or expired. */
    public static String verify(byte[] key, String token, long now) throws Invalid {
        if (token == null) throw new Invalid("no principal token");
        int dot = token.indexOf('.');
        if (dot < 0) throw new Invalid("a malformed principal token");
        String payload;
        byte[] sig;
        try {
            payload = new String(Base64.getUrlDecoder().decode(token.substring(0, dot)), StandardCharsets.UTF_8);
            sig = Base64.getUrlDecoder().decode(token.substring(dot + 1));
        } catch (IllegalArgumentException e) {
            throw new Invalid("a malformed principal token");
        }
        if (!MessageDigest.isEqual(sig, mac(key, payload))) throw new Invalid("a principal token not signed by the gateway");
        int nl = payload.lastIndexOf('\n');
        if (nl < 0) throw new Invalid("a malformed principal token");
        long expires;
        try {
            expires = Long.parseLong(payload.substring(nl + 1));
        } catch (NumberFormatException e) {
            throw new Invalid("a malformed principal token");
        }
        if (now > expires) throw new Invalid("an expired principal token");
        return payload.substring(0, nl);
    }

    private static byte[] mac(byte[] key, String payload) {
        try {
            Mac m = Mac.getInstance("HmacSHA256");
            m.init(new SecretKeySpec(key, "HmacSHA256"));
            return m.doFinal(payload.getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private static String b64(byte[] b) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(b);
    }
}
