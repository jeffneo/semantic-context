package com.google.cloud.bigquery.jdbc;

import java.sql.Connection;
import java.sql.Driver;
import java.sql.DriverManager;
import java.sql.DriverPropertyInfo;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.util.Properties;
import java.util.logging.Logger;
import qlsc.passthrough.Passthrough;

/**
 * The stand-in Virtual Graph finds: it requires a driver of this name, and connects through whichever is
 * registered for jdbc:bigquery:. The real driver, of the same name, is loaded from its own jar by
 * qlsc.passthrough.Passthrough, which decides as whom each statement runs.
 */
public final class BigQueryDriver implements Driver {
    static {
        try {
            DriverManager.registerDriver(new BigQueryDriver());
        } catch (SQLException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    @Override
    public Connection connect(String url, Properties info) throws SQLException {
        return acceptsURL(url) ? Passthrough.connect(url, info) : null;
    }

    @Override
    public boolean acceptsURL(String url) {
        return url != null && url.startsWith("jdbc:bigquery:");
    }

    @Override
    public DriverPropertyInfo[] getPropertyInfo(String url, Properties info) {
        return new DriverPropertyInfo[0];
    }

    @Override
    public int getMajorVersion() {
        return 1;
    }

    @Override
    public int getMinorVersion() {
        return 0;
    }

    @Override
    public boolean jdbcCompliant() {
        return false;
    }

    @Override
    public Logger getParentLogger() throws SQLFeatureNotSupportedException {
        throw new SQLFeatureNotSupportedException();
    }
}
