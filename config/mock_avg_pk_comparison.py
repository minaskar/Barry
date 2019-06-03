import sys
sys.path.append("..")

from barry.framework.samplers.ensemble import EnsembleSampler
from barry.setup import setup
from barry.framework.fitter import Fitter
from barry.framework.datasets.mock_power import MockPowerSpectrum
from barry.framework.models import PowerBeutler2017, PowerDing2018, PowerSeo2016

if __name__ == "__main__":
    pfn, dir_name, file = setup(__file__)

    models = [
        PowerBeutler2017(fit_omega_m=False, name="Beutler2017"),
        PowerDing2018(fit_omega_m=False, name="Ding2018", recon_smoothing_scale=21.21, recon=True),
        PowerSeo2016(fit_omega_m=False, name="Seo2016", recon_smoothing_scale=21.21, recon=True),
    ]

    datas = [MockPowerSpectrum(name="MockAvgPk 02-30 Recon", recon=True, min_k=0.02, max_k=0.30)]

    sampler = EnsembleSampler(num_steps=1500, num_burn=500, temp_dir=dir_name, save_interval=30)

    fitter = Fitter(dir_name)
    fitter.set_models(*models)
    fitter.set_data(*datas)
    fitter.set_sampler(sampler)
    fitter.set_num_walkers(50)
    fitter.fit(file, viewer=False)

    if fitter.is_laptop():
        from chainconsumer import ChainConsumer

        c = ChainConsumer()
        for posterior, weight, chain, model, data in fitter.load():
            name = f"{model.get_name()} {data.get_name()}"
            linestyle = "--" if "FitOm" in name else "-"
            c.add_chain(chain, weights=weight, parameters=model.get_labels(), name=name, linestyle=linestyle)
        c.configure(shade=True)
        c.plotter.plot(filename=pfn + "_contour.png", truth={"$\\Omega_m$": 0.3121, '$\\alpha$': 1.0})
        with open(pfn + "_params.txt", "w") as f:
            f.write(c.analysis.get_latex_table(transpose=True))


