"""Shared estimators for the crime/weather pipeline.

Daily crime series are (a) non-negative counts whose variance grows with the
mean and (b) strongly serially correlated (residual lag-1 autocorrelation
~0.3).  We address both:

* ``poisson_hac`` — the PRIMARY model.  Poisson pseudo-maximum-likelihood with a
  log link: the coefficient point estimates are consistent for the conditional
  mean E[y|x] even when the data are over-dispersed (Gourieroux-Monfort-Trognon
  / Wooldridge QMLE result), and a Newey-West HAC sandwich on the score gives
  standard errors that are robust to BOTH the over-dispersion of counts and the
  serial correlation — so we never have to assume the Poisson variance.  A
  +d-unit change in a regressor multiplies the expected count by exp(d*beta);
  effects are reported as that percentage, ``(exp(d*beta) - 1) * 100``.

* ``ols`` — retained only for the deseasonalised "anomaly" check, where the
  series is a continuous day-of-year residual that can go negative and a count
  model does not apply; it carries the same Newey-West HAC errors.

Both HAC estimators assume rows are in time order AND contiguous (no date
gaps): the lag terms treat adjacent rows as one-day-apart neighbours.  For a
filtered / non-contiguous frame (e.g. hot-days-only sub-samples) pass
``hac=False`` to ``poisson_hac`` to fall back to White (heteroskedasticity-only)
errors, which drop the meaningless cross-day autocovariances.

``bh`` returns Benjamini-Hochberg FDR-adjusted q-values for a family of tests.
"""
import numpy as np
from scipy import stats


def ols(y, X):
    """Linear OLS with Newey-West (HAC) standard errors. Returns (beta, pvalues)."""
    X = np.column_stack([np.ones(len(y))] + X)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    u = X * resid[:, None]                      # n x k score contributions
    L = max(1, int(4 * (n / 100) ** (2 / 9)))   # Bartlett-kernel bandwidth (rule of thumb)
    S = u.T @ u
    for lag in range(1, L + 1):
        w = 1 - lag / (L + 1)                    # Bartlett weight
        G = u[lag:].T @ u[:-lag]
        S += w * (G + G.T)
    se = np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))
    p = 2 * (1 - stats.t.cdf(np.abs(beta / se), n - k))
    return beta, p


def poisson_hac(y, X, hac=True):
    """Poisson PML (log link) with a robust sandwich covariance.

    Parameters
    ----------
    y    : array of non-negative counts.
    X    : list of regressor column arrays (an intercept is added).
    hac  : if True (default) use a Newey-West HAC sandwich (rows must be a
           contiguous daily series); if False use a White/HC0 sandwich (for
           non-contiguous sub-samples where the autocovariance lags are
           meaningless).

    Returns (beta, pvalues) on the log scale.  Convert a coefficient ``b`` to a
    percentage effect with ``(np.exp(step * b) - 1) * 100`` and to an absolute
    incidents-per-day effect at the mean with ``ybar * (np.exp(step * b) - 1)``.
    """
    y = np.asarray(y, dtype=float)
    X = np.column_stack([np.ones(len(y))] + X)
    n, k = X.shape
    beta = np.zeros(k)
    beta[0] = np.log(y.mean() + 0.5)            # sensible intercept start
    for _ in range(100):                        # IRLS / Fisher scoring
        mu = np.exp(np.clip(X @ beta, -30, 30))
        XtWX = X.T @ (mu[:, None] * X) + 1e-10 * np.eye(k)
        step = np.linalg.solve(XtWX, X.T @ (y - mu))
        beta = beta + step
        if np.max(np.abs(step)) < 1e-9:
            break
    mu = np.exp(np.clip(X @ beta, -30, 30))
    bread = np.linalg.inv(X.T @ (mu[:, None] * X) + 1e-10 * np.eye(k))
    u = X * (y - mu)[:, None]                    # score contributions x_t (y_t - mu_t)
    S = u.T @ u                                  # White / HC0 meat
    if hac:
        L = max(1, int(4 * (n / 100) ** (2 / 9)))
        for lag in range(1, L + 1):
            w = 1 - lag / (L + 1)
            G = u[lag:].T @ u[:-lag]
            S += w * (G + G.T)
    se = np.sqrt(np.diag(bread @ S @ bread))
    p = 2 * (1 - stats.norm.cdf(np.abs(beta / se)))   # GLM asymptotic z-test
    return beta, p


def bh(pvals):
    """Benjamini-Hochberg FDR-adjusted q-values for a family of p-values."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]     # enforce monotonicity
    out = np.empty(n)
    out[order] = np.clip(q, 0, 1)
    return out
