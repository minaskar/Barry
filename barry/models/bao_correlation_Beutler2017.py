import logging

from barry.models import PowerBeutler2017
from barry.models.bao_correlation import CorrelationFunctionFit
import numpy as np


class CorrBeutler2017(CorrelationFunctionFit):
    """  xi(s) model inspired from Beutler 2017 and Ross 2015.
    """

    def __init__(self, name="Corr Beutler 2017", smooth_type="hinton2017", fix_params=("om"), smooth=False, correction=None):
        super().__init__(name, smooth_type, fix_params, smooth, correction=correction)
        self.parent = PowerBeutler2017(fix_params=fix_params, smooth_type=smooth_type, recon=True, smooth=smooth, correction=correction)
        # Recon doesnt matter above as it only changes the unused shape terms for Beutler

    def set_data(self, data):
        super().set_data(data)
        self.parent.set_data(data)

    def declare_parameters(self):
        super().declare_parameters()
        self.add_param("sigma_nl", r"$\Sigma_{NL}$", 1.0, 20.0, 1.0)  # dampening
        self.add_param("a1", r"$a_1$", -100, 100, 0)  # Polynomial marginalisation 1
        self.add_param("a2", r"$a_2$", -2, 2, 0)  # Polynomial marginalisation 2
        self.add_param("a3", r"$a_3$", -0.2, 0.2, 0)  # Polynomial marginalisation 3

    def compute_correlation_function(self, d, p, smooth=False):
        # Get base linear power spectrum from camb
        ks = self.camb.ks
        pk_smooth, pk_ratio_dewiggled = self.compute_basic_power_spectrum(p["om"])

        # Blend the two
        if smooth:
            pk1d = pk_smooth
        else:
            pk_linear_weight = np.exp(-0.5 * (ks * p["sigma_nl"]) ** 2)
            pk1d = (pk_linear_weight * (1 + pk_ratio_dewiggled) + (1 - pk_linear_weight)) * pk_smooth

        # Convert to correlation function and take alpha into account
        xi = self.pk2xi(ks, pk1d, d * p["alpha"])

        # Polynomial shape
        shape = p["a1"] / (d ** 2) + p["a2"] / d + p["a3"]

        # Add poly shape to xi model, include bias correction
        model = xi * p["b"] + shape
        return model


if __name__ == "__main__":
    import sys

    sys.path.append("../..")
    from barry.datasets.dataset_correlation_function import CorrelationFunction_SDSS_DR12_Z061_NGC
    from barry.config import setup_logging

    setup_logging()

    print("Checking pre-recon")
    dataset = CorrelationFunction_SDSS_DR12_Z061_NGC(recon=False)
    model_pre = CorrBeutler2017()
    model_pre.sanity_check(dataset)

    print("Checking post-recon")
    dataset = CorrelationFunction_SDSS_DR12_Z061_NGC(recon=True)
    model_post = CorrBeutler2017()
    model_post.sanity_check(dataset)
