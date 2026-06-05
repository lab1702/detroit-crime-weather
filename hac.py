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

``deseasonalize`` removes a smooth seasonal cycle (harmonic/Fourier regression
on the day-of-year) and returns anomalies; it is leap-year safe and far more
stable than a raw per-calendar-day mean estimated from only ~9 observations
per day.

These are thin wrappers over statsmodels; they only fix the Newey-West
bandwidth and unpack ``(params, pvalues)`` in the shape the pipeline expects.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests


def _newey_west_lags(n):
    """Bartlett-kernel bandwidth (Newey-West rule of thumb)."""
    return max(1, int(4 * (n / 100) ** (2 / 9)))


def ols(y, X):
    """Linear OLS with Newey-West (HAC) standard errors. Returns (beta, pvalues)."""
    Xc = sm.add_constant(np.column_stack(X))
    res = sm.OLS(np.asarray(y, dtype=float), Xc).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": _newey_west_lags(len(y)), "use_correction": False},
        use_t=True,
    )
    return res.params, res.pvalues


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
    Xc = sm.add_constant(np.column_stack(X))
    if hac:
        cov_kwds = {"cov_type": "HAC", "cov_kwds": {"maxlags": _newey_west_lags(len(y))}}
    else:
        cov_kwds = {"cov_type": "HC0"}
    res = sm.GLM(np.asarray(y, dtype=float), Xc, family=sm.families.Poisson()).fit(**cov_kwds)
    return res.params, res.pvalues


def bh(pvals):
    """Benjamini-Hochberg FDR-adjusted q-values for a family of p-values."""
    return multipletests(np.asarray(pvals, dtype=float), method="fdr_bh")[1]


def deseasonalize(s, n_harmonics=3):
    """Seasonal anomalies of a daily Series via harmonic (Fourier) regression.

    Fits ``y ~ 1 + sum_k [sin(k*phi) + cos(k*phi)]`` where the phase ``phi`` is
    the fraction of the year elapsed, using each year's actual length (365 or
    366). This is leap-year safe — Feb-29 and every post-February date in a leap
    year get the correct calendar phase, unlike grouping on ``dayofyear`` — and,
    being a smooth low-order fit, gives a far more stable "normal" than a raw
    per-calendar-day mean built from only ~9 observations per day. The original
    index is preserved so callers can keep aligning by position.
    """
    idx = s.index
    doy = idx.dayofyear.to_numpy(dtype=float)
    year_len = np.where(idx.is_leap_year, 366.0, 365.0)
    phi = 2.0 * np.pi * doy / year_len
    cols = [np.ones_like(phi)]
    for k in range(1, n_harmonics + 1):
        cols.append(np.sin(k * phi))
        cols.append(np.cos(k * phi))
    X = np.column_stack(cols)
    y = np.asarray(s, dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return pd.Series(y - X @ beta, index=idx)
