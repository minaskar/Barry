import sys


sys.path.append("..")
from barry.config import setup
from barry.models import PowerNoda2019
from barry.datasets import PowerSpectrum_SDSS_DR12_Z061_NGC
from barry.postprocessing import BAOExtractor
from barry.cosmology.camb_generator import CambGenerator
from barry.samplers import DynestySampler
from barry.fitter import Fitter

if __name__ == "__main__":
    pfn, dir_name, file = setup(__file__)

    c = CambGenerator()
    r_s = c.get_data()[0]
    fitter = Fitter(dir_name)

    ps = [
        BAOExtractor(r_s, extra_ks=(0.095, 0.13)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.14)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.15)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.16)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.17)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.18)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.19)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.20)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.21)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.22)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.23)),
        BAOExtractor(r_s, extra_ks=(0.095, 0.24)),
    ]

    recon = True
    for p in ps:
        n = f"$k = {p.extra_ks[1]:0.2f}\, h / {{\\rm Mpc}}$"
        model = PowerNoda2019(postprocess=p, recon=recon)
        data = PowerSpectrum_SDSS_DR12_Z061_NGC(min_k=0.02, max_k=0.30, postprocess=p, recon=recon, realisation=0)
        fitter.add_model_and_dataset(model, data, name=n)

    sampler = DynestySampler(temp_dir=dir_name, nlive=1000)

    fitter.set_sampler(sampler)
    fitter.set_num_walkers(10)
    fitter.fit(file)

    if fitter.should_plot():
        from chainconsumer import ChainConsumer

        c = ChainConsumer()
        for posterior, weight, chain, evidence, model, data, extra in fitter.load():
            print(extra["name"])
            c.add_chain(chain, weights=weight, parameters=model.get_labels(), **extra)
        c.configure(shade=True, bins=25, legend_artists=True, cmap="plasma", sigmas=[0, 1, 2])
        extents = None  # {"$\\alpha$": (0.88, 1.18), "$A$": (0, 10), "$b$": (1.5, 1.8), r"$\gamma_{rec}$": (1, 8)}
        params = ["$\\alpha$", "$A$", "$b$"]
        truth = {"$\\Omega_m$": 0.31, "$\\alpha$": 0.9982}
        c.analysis.get_latex_table(filename=pfn + "_params.txt")
        c.plotter.plot_summary(filename=[pfn + "_summary.png", pfn + "_summary.pdf"], errorbar=True, truth=truth, extents=extents, parameters=params)
        c.plotter.plot(filename=[pfn + "_contour.png", pfn + "_contour.pdf"], truth=truth, extents=extents, parameters=params, figsize="COLUMN")
        # c.plotter.plot_walks(filename=pfn + "_walks.png", truth={"$\\Omega_m$": 0.3121, '$\\alpha$': 1.0},
        #                      extents=extents)

    # FINDINGS
    # Well, looks like where you transition from alternating indices to only using the extractor
    # has a strong impact on not only where you fit alpha, b, gamma and A, but also on their uncertainties.
    # It also impracts the degeneracy direction between alpha and A.
