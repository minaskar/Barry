import sys

sys.path.append("..")
from barry.config import setup
from barry.models import PowerNoda2019
from barry.datasets import PowerSpectrum_SDSS_DR12_Z061_NGC
from barry.postprocessing import BAOExtractor
from barry.cosmology.camb_generator import getCambGenerator
from barry.samplers import DynestySampler
from barry.fitter import Fitter

if __name__ == "__main__":
    pfn, dir_name, file = setup(__file__)

    c = getCambGenerator()
    r_s = c.get_data()[0]

    postprocess = BAOExtractor(r_s)

    sampler = DynestySampler(temp_dir=dir_name)
    fitter = Fitter(dir_name)

    for r in [True, False]:
        rt = "Recon" if r else "Prerecon"
        data = PowerSpectrum_SDSS_DR12_Z061_NGC(recon=r, postprocess=postprocess)
        n = PowerNoda2019(postprocess=postprocess, recon=r, fix_params=["om", "f", "gamma", "b"])
        # n2 = PowerNoda2019(postprocess=postprocess, recon=r, fix_params=["om", "f", "gamma", "b"])
        n.param_dict["b"].default = 1.992 if r else 1.996
        fitter.add_model_and_dataset(
            n, data, name=f"N19 {rt} fixed $f$, $\\gamma_{{rec}}$, $b$", linestyle="-" if r else "--", color="o", shade_alpha=0.7, zorder=10
        )
        # fitter.add_model_and_dataset(n2, data, name=f"N19 {rt} fixed $f$, $\\gamma$, $b$ (N19 values)", linestyle=":", color="g", shade_alpha=0.0, zorder=10)
        fitter.add_model_and_dataset(
            PowerNoda2019(postprocess=postprocess, recon=r, fix_params=["om", "f", "gamma"]),
            data,
            name=f"N19 {rt} fixed $f$, $\\gamma_{{rec}}$",
            linestyle="-" if r else "--",
            color="r",
            shade_alpha=0.2,
        )
        fitter.add_model_and_dataset(
            PowerNoda2019(postprocess=postprocess, recon=r, fix_params=["om", "f"]),
            data,
            name=f"N19 {rt} fixed $f$",
            linestyle="-" if r else "--",
            color="#333333",
            shade_alpha=0.0,
        )
        fitter.add_model_and_dataset(
            PowerNoda2019(postprocess=postprocess, recon=r, fix_params=["om"]),
            data,
            name=f"N19 {rt}",
            linestyle="-" if r else "--",
            color="lb",
            shade_alpha=0.1,
        )

    fitter.set_sampler(sampler)
    fitter.set_num_walkers(20)
    fitter.fit(file)

    if fitter.should_plot():
        from chainconsumer import ChainConsumer

        c = ChainConsumer()
        names2 = []
        for posterior, weight, chain, evidence, model, data, extra in fitter.load():
            # print(model.get_names())
            # print(chain.mean(axis=0))
            name = extra["name"]
            if "fixed $f$" in name:
                names2.append(name)
            i = posterior.argmax()

            # If using the old chains without evidence
            import numpy as np

            chain = np.hstack((np.atleast_2d(evidence).T, chain))

            print(name, model.get_names(), chain[i, :])
            c.add_chain(chain, weights=weight, parameters=model.get_labels(), **extra)
        c.configure(shade=True, bins=20, legend_artists=True, max_ticks=4)
        # extents = {"$\\alpha$": (0.963, 1.06)}
        extents = None
        c.plotter.plot_summary(filename=[pfn + "_summary.png", pfn + "_summary.pdf"], errorbar=True, truth={"$\\Omega_m$": 0.3121, "$\\alpha$": 0.9982})
        c.plotter.plot(filename=[pfn + "_contour.png", pfn + "_contour.pdf"], truth={"$\\Omega_m$": 0.3121, "$\\alpha$": 0.9982})
        c.plotter.plot(
            filename=[pfn + "_contour2.png", pfn + "_contour2.pdf"],
            parameters=3,
            chains=names2,
            truth={"$\\Omega_m$": 0.3121, "$\\alpha$": 0.9982},
            figsize="COLUMN",
            extents=extents,
        )
        c.plotter.plot_walks(filename=pfn + "_walks.png", truth={"$\\Omega_m$": 0.3121, "$\\alpha$": 0.9982})
        c.analysis.get_latex_table(filename=pfn + "_params.txt")
        with open(pfn + "_corr.txt", "w") as f:
            f.write(c.analysis.get_correlation_table(chain="N19 Recon fixed $f$, $\\gamma_{rec}$"))

    # FINDINGS
    # So turns out that fixing all these parameters really helps get good constraints.
    # Both the choice of b and gamma entirely determine where alpha will fit.
    # Really fixing b is what is driving down uncertainty.
