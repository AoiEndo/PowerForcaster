"""Bayesian model stub using PyMC (pymc)."""
import pymc as pm
import arviz as az
import numpy as np

def bayesian_regression(X, y):
    with pm.Model() as model:
        intercept = pm.Normal("intercept", mu=0, sigma=10)
        coefs = pm.Normal("coefs", mu=0, sigma=10, shape=X.shape[1])
        mu = intercept + pm.math.dot(X, coefs)
        sigma = pm.HalfNormal("sigma", sigma=1)
        obs = pm.Normal("obs", mu=mu, sigma=sigma, observed=y)
        trace = pm.sample(return_inferencedata=True)
    return model, trace
