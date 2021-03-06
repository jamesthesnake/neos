# AUTOGENERATED! DO NOT EDIT! File to edit: 01_makers.ipynb (unless otherwise specified).

__all__ = ['hists_from_nn_three_blobs', 'nn_hepdata_like']

# Cell
import jax
import numpy as np

from neos import models

# Cell
def hists_from_nn_three_blobs(predict, NMC = 500, sig_mean = [-1, 1], b1_mean=[2, 2], b2_mean=[-1, -1], LUMI=10, sig_scale = 2, bkg_scale = 10):

    def get_hists(network, s, b1, b2):
        NMC = len(s)
        sh, bh1, bh2 = (
            predict(network, s).sum(axis=0) * sig_scale / NMC * LUMI,
            predict(network, b1).sum(axis=0) * bkg_scale / NMC * LUMI,
            predict(network, b2).sum(axis=0) * bkg_scale / NMC * LUMI,
        )
        b_mean = jax.numpy.mean(jax.numpy.asarray([bh1, bh2]), axis=0)
        b_unc = jax.numpy.std(jax.numpy.asarray([bh1, bh2]), axis=0)
        results = sh, b_mean, b_unc
        return results


    def hist_maker():
        bkg1 = np.random.multivariate_normal(b1_mean, [[1, 0], [0, 1]], size=(NMC,))
        bkg2 = np.random.multivariate_normal(b2_mean, [[1, 0], [0, 1]], size=(NMC,))
        sig = np.random.multivariate_normal(sig_mean, [[1, 0], [0, 1]], size=(NMC,))

        def make(network):
            return get_hists(network, sig, bkg1, bkg2)

        make.bkg1 = bkg1
        make.bkg2 = bkg2
        make.sig = sig
        return make

    return hist_maker

# Cell
def nn_hepdata_like(histogram_maker):
    hm = histogram_maker()

    def nn_model_maker(network):
        s, b, db = hm(network)
        m = models.hepdata_like(s, b, db)
        nompars = m.config.suggested_init
        bonlypars = jax.numpy.asarray([x for x in nompars])
        bonlypars = jax.ops.index_update(bonlypars, m.config.poi_index, 0.0)
        return m, bonlypars

    nn_model_maker.hm = hm
    return nn_model_maker