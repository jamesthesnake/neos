# AUTOGENERATED! DO NOT EDIT! File to edit: 06_cls.ipynb (unless otherwise specified).

__all__ = ['cls_maker']

# Cell
import jax
from jax import config
import pyhf

# avoid those precision errors!
config.update("jax_enable_x64", True)

pyhf.set_backend(pyhf.tensor.jax_backend())

from .fit import get_solvers
#from fullstream.models import nn_model_maker
from .transforms import *

# Cell
def cls_maker(nn_model_maker, solver_kwargs):
    def cls_jax(nn_params, test_mu):
        g_fitter, c_fitter = get_solvers(nn_model_maker, **solver_kwargs)

        m, bonlypars = nn_model_maker(nn_params)
        exp_data = m.expected_data(bonlypars)
        print(f'exp_data: {exp_data}')
        bounds = m.config.suggested_bounds()

        # map these
        initval = jax.numpy.asarray([test_mu, 1.0])
        transforms = solver_kwargs.get("pdf_transform", False)
        if transforms:
            initval = to_inf_vec(initval, bounds)

        # the constrained fit

        #print('fitting constrained with init val %s setup %s', initval,[test_mu, nn_params])

        numerator = (
            to_bounded_vec(c_fitter(initval, [test_mu, nn_params]), bounds)
            if transforms
            else c_fitter(initval, [test_mu, nn_params])
        )

        denominator = bonlypars  # to_bounded_vec(g_fitter(initval, [test_mu, nn_params]), bounds) if transforms else g_fitter(initval, [test_mu, nn_params])

        # print(f"constrained fit: {numerator}")
        # print(f"global fit: {denominator}")

        # compute test statistic (lambda(µ))
        profile_likelihood = -2 * (
            m.logpdf(numerator, exp_data)[0] - m.logpdf(denominator, exp_data)[0]
        )

        # in exclusion fit zero out test stat if best fit µ^ is larger than test µ
        muhat = denominator[0]
        sqrtqmu = jax.numpy.sqrt(
            jax.numpy.where(muhat < test_mu, profile_likelihood, 0.0)
        )
        # print(f"sqrt(q(mu)): {sqrtqmu}")
        # compute CLs
        nullval = sqrtqmu
        altval = 0
        CLsb = 1 - pyhf.tensorlib.normal_cdf(nullval)
        CLb = 1 - pyhf.tensorlib.normal_cdf(altval)
        CLs = CLsb / CLb
        return CLs

    return cls_jax