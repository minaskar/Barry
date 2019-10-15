import logging
from functools import lru_cache

import numpy as np
from scipy import integrate
from barry.models.bao_correlation import CorrelationFunctionFit
from barry.cosmology.camb_generator import Omega_m_z


class CorrSeo2016(CorrelationFunctionFit):
    """ xi(s) model inspired from Seo 2016.

    See https://ui.adsabs.harvard.edu/abs/2016MNRAS.460.2453S for details.
    """

    def __init__(self, name="Corr Seo 2016", recon=False, smooth_type="hinton2017", fix_params=("om", "f"), smooth=False, correction=None):
        self.recon = recon
        self.recon_smoothing_scale = None
        super().__init__(name=name, fix_params=fix_params, smooth_type=smooth_type, smooth=smooth, correction=correction)
        self.nmu = 100
        self.mu = np.linspace(0.0, 1.0, self.nmu)
        self.smoothing_kernel = None

    @lru_cache(maxsize=32)
    def get_pt_data(self, om):
        return self.PT.get_data(om=om)

    @lru_cache(maxsize=8192)
    def get_damping_dd(self, growth, om):
        return np.exp(-np.outer(1.0 + (2.0 + growth) * growth * self.mu ** 2, self.camb.ks ** 2) * self.get_pt_data(om)["sigma_dd"] / 2.0)

    @lru_cache(maxsize=32)
    def get_damping_ss(self, om):
        return np.exp(-np.tile(self.camb.ks ** 2, (self.nmu, 1)) * self.get_pt_data(om)["sigma_ss"] / 2.0)

    @lru_cache(maxsize=8192)
    def get_damping(self, growth, om):
        return np.exp(-np.outer(1.0 + (2.0 + growth) * growth * self.mu ** 2, self.camb.ks ** 2) * self.get_pt_data(om)["sigma"] / 2.0)

    def set_data(self, data):
        super().set_data(data)
        # Compute the smoothing kernel (assumes a Gaussian smoothing kernel)
        if self.recon:
            self.smoothing_kernel = np.exp(-self.camb.ks ** 2 * self.recon_smoothing_scale ** 2 / 2.0)

    def declare_parameters(self):
        # Define parameters
        super().declare_parameters()
        self.add_param("f", r"$f$", 0.01, 1.0, 0.5)  # Growth rate of structure
        self.add_param("sigma_s", r"$\Sigma_s$", 0.01, 10.0, 5.0)  # Fingers-of-god damping
        self.add_param("a1", r"$a_1$", -100, 100, 0)  # Polynomial marginalisation 1
        self.add_param("a2", r"$a_2$", -2, 2, 0)  # Polynomial marginalisation 2
        self.add_param("a3", r"$a_3$", -0.2, 0.2, 0)  # Polynomial marginalisation 3

    def compute_correlation_function(self, d, p, smooth=False):
        """ Computes the correlation function model using the LPT based propagators from Seo et. al., 2016 at d*alpha

        Parameters
        ----------
        d : np.ndarray
            Array of separations to compute
        p : dict
            dictionary of parameter names to their values

        Returns
        -------
        array
            xi_final - The correlation function at the dilated d-values

        """

        # Get the basic power spectrum components
        ks = self.camb.ks
        pk_smooth_lin, pk_ratio = self.compute_basic_power_spectrum(p["om"])

        # Compute the growth rate depending on what we have left as free parameters
        growth = p["f"]

        # Lets round some things for the sake of numerical speed
        om = np.round(p["om"], decimals=5)
        growth = np.round(growth, decimals=5)

        # Compute the propagator
        if self.recon:
            damping_dd = self.get_damping_dd(growth, om)
            damping_ss = self.get_damping_ss(om)

            smooth_prefac = np.tile(self.smoothing_kernel / p["b"], (self.nmu, 1))
            kaiser_prefac = 1.0 + np.outer(growth / p["b"] * self.mu ** 2, 1.0 - self.smoothing_kernel)
            propagator = (kaiser_prefac * damping_dd + smooth_prefac * (damping_ss - damping_dd)) ** 2
        else:
            damping = self.get_damping(growth, om)

            prefac_k = 1.0 + np.tile(3.0 / 7.0 * (self.get_pt_data(om)["R1"] * (1.0 - 4.0 / (9.0 * p["b"])) + self.get_pt_data(om)["R2"]), (self.nmu, 1))
            prefac_mu = np.outer(
                self.mu ** 2,
                growth / p["b"]
                + 3.0 / 7.0 * growth * self.get_pt_data(om)["R1"] * (2.0 - 1.0 / (3.0 * p["b"]))
                + 6.0 / 7.0 * growth * self.get_pt_data(om)["R2"],
            )
            propagator = ((prefac_k + prefac_mu) * damping) ** 2

        # Compute the smooth model
        fog = 1.0 / (1.0 + np.outer(self.mu ** 2, ks ** 2 * p["sigma_s"] ** 2 / 2.0)) ** 2
        pk_smooth = p["b"] ** 2 * pk_smooth_lin * fog

        # Integrate over mu
        if smooth:
            pk1d = integrate.simps(pk_smooth * (1.0 + 0.0 * pk_ratio * propagator), self.mu, axis=0)
        else:
            pk1d = integrate.simps(pk_smooth * (1.0 + pk_ratio * propagator), self.mu, axis=0)

        # Convert to correlation function and take alpha into account
        xi = self.pk2xi(ks, pk1d, d * p["alpha"])

        # Polynomial shape
        shape = p["a1"] / (d ** 2) + p["a2"] / d + p["a3"]

        # Add poly shape to xi model, include bias correction
        model = xi + shape
        return model


if __name__ == "__main__":
    import sys
    import timeit
    from barry.datasets.dataset_correlation_function import CorrelationFunction_SDSS_DR12_Z061_NGC

    sys.path.append("../..")
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)7s |%(funcName)20s]   %(message)s")
    logging.getLogger("matplotlib").setLevel(logging.ERROR)

    dataset = CorrelationFunction_SDSS_DR12_Z061_NGC(recon=False)
    data = dataset.get_data()
    model_pre = CorrSeo2016(recon=False)
    model_pre.set_data(data)

    dataset = CorrelationFunction_SDSS_DR12_Z061_NGC(recon=True)
    data = dataset.get_data()
    model_post = CorrSeo2016(recon=True)
    model_post.set_data(data)

    p = {"om": 0.3, "alpha": 1.0, "sigma_s": 10.0, "b": 1.6, "a1": 0, "a2": 0, "a3": 0, "a4": 0, "a5": 0}

    n = 200

    def test_pre():
        model_pre.get_likelihood(p, data[0])

    def test_post():
        model_post.get_likelihood(p, data[0])

    print("Pre-reconstruction likelihood takes on average, %.2f milliseconds" % (timeit.timeit(test_pre, number=n) * 1000 / n))
    print("Post-reconstruction likelihood takes on average, %.2f milliseconds" % (timeit.timeit(test_post, number=n) * 1000 / n))

    if True:
        p, minv = model_pre.optimize()
        print("Pre reconstruction optimisation:")
        print(p)
        print(minv)
        model_pre.plot(p)

        print("Post reconstruction optimisation:")
        p, minv = model_post.optimize()
        print(p)
        print(minv)
        model_post.plot(p)
