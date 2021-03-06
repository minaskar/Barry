import numpy as np

from barry.models.bao_power import PowerSpectrumFit


class PowerBeutler2017(PowerSpectrumFit):
    """ P(k) model inspired from Beutler 2017.

    See https://ui.adsabs.harvard.edu/abs/2017MNRAS.464.3409B for details.

    """

    def __init__(self, name="Pk Beutler 2017", fix_params=("om"), smooth_type="hinton2017", recon=False, postprocess=None, smooth=False, correction=None):
        super().__init__(name=name, fix_params=fix_params, smooth_type=smooth_type, postprocess=postprocess, smooth=smooth, correction=correction)

        self.recon = recon

    def declare_parameters(self):
        super().declare_parameters()
        self.add_param("sigma_nl", r"$\Sigma_{nl}$", 0.01, 20.0, 10.0)  # BAO damping
        self.add_param("sigma_s", r"$\Sigma_s$", 0.01, 20.0, 10.0)  # Fingers-of-god damping
        self.add_param("a1", r"$a_1$", -10000.0, 30000.0, 0)  # Polynomial marginalisation 1
        self.add_param("a2", r"$a_2$", -20000.0, 10000.0, 0)  # Polynomial marginalisation 2
        self.add_param("a3", r"$a_3$", -1000.0, 5000.0, 0)  # Polynomial marginalisation 3
        self.add_param("a4", r"$a_4$", -200.0, 200.0, 0)  # Polynomial marginalisation 4
        self.add_param("a5", r"$a_5$", -3.0, 3.0, 0)  # Polynomial marginalisation 5

    def compute_power_spectrum(self, p, smooth=False, shape=True):
        """ Computes the power spectrum for the Beutler et. al., 2017 model at k/alpha
        
        Parameters
        ----------
        p : dict
            dictionary of parameter names to their values
        smooth : bool, optional
            Whether to return a smooth model or not. Defaults to False
            
        Returns
        -------
        array
            pk_final - The power spectrum at the dilated k-values
        
        """

        # Get the basic power spectrum components
        ks = self.camb.ks
        pk_smooth_lin, pk_ratio = self.compute_basic_power_spectrum(p["om"])

        # Compute the smooth model
        fog = 1.0 / (1.0 + ks ** 2 * p["sigma_s"] ** 2 / 2.0) ** 2
        pk_smooth = p["b"] ** 2 * pk_smooth_lin * fog

        # Polynomial shape
        if shape:
            if self.recon:
                shape = p["a1"] * ks ** 2 + p["a2"] + p["a3"] / ks + p["a4"] / (ks * ks) + p["a5"] / (ks ** 3)
            else:
                shape = p["a1"] * ks + p["a2"] + p["a3"] / ks + p["a4"] / (ks * ks) + p["a5"] / (ks ** 3)
        else:
            shape = 0

        if smooth:
            pk1d = pk_smooth + shape
        else:
            # Compute the propagator
            C = np.exp(-0.5 * ks ** 2 * p["sigma_nl"] ** 2)
            pk1d = (pk_smooth + shape) * (1.0 + pk_ratio * C)

        return ks, pk1d


if __name__ == "__main__":
    import sys

    sys.path.append("../..")
    from barry.datasets.dataset_power_spectrum import PowerSpectrum_SDSS_DR12_Z061_NGC
    from barry.config import setup_logging

    setup_logging()

    print("Checking pre-recon")
    dataset = PowerSpectrum_SDSS_DR12_Z061_NGC(recon=False)
    model_pre = PowerBeutler2017(recon=False)
    model_pre.sanity_check(dataset)

    print("Checking post-recon")
    dataset = PowerSpectrum_SDSS_DR12_Z061_NGC(recon=True)
    model_post = PowerBeutler2017(recon=True)
    model_post.sanity_check(dataset)
