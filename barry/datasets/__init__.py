"""
======
Models
======

.. currentmodule:: barry.datasets

Generic
=======

.. autosummary::
   :toctree: generated/

   Dataset -- Generic dataset
   MultiDataset -- Multiple datasets combined

Concrete
========

.. autosummary::
   :toctree: generated/

   PowerSpectrum_SDSS_DR12_Z061_NGC
   PowerSpectrum_SDSS_DR12_Z051_NGC
   PowerSpectrum_SDSS_DR12_Z051_SGC
   PowerSpectrum_SDSS_DR12_Z051
   PowerSpectrum_SDSS_DR7_Z015
   DummyCorrelationFunction_SDSS_DR12_Z061_NGC
   DummyPowerSpectrum_SDSS_DR12_Z061_NGC
   CorrelationFunction_SDSS_DR7_Z015_MGS
   CorrelationFunction_SDSS_DR12_Z061_NGC

"""

from barry.datasets.dataset import Dataset, MultiDataset
from barry.datasets.dataset_correlation_function import CorrelationFunction_SDSS_DR12_Z061_NGC
from barry.datasets.dataset_power_spectrum import (
    PowerSpectrum_SDSS_DR12_Z061_NGC,
    PowerSpectrum_SDSS_DR12_Z051_NGC,
    PowerSpectrum_SDSS_DR12_Z051_SGC,
    PowerSpectrum_SDSS_DR12_Z051,
)
from barry.datasets.dummy import DummyPowerSpectrum_SDSS_DR12_Z061_NGC, DummyCorrelationFunction_SDSS_DR12_Z061_NGC

__all__ = [
    "PowerSpectrum_SDSS_DR12_Z061_NGC",
    "PowerSpectrum_SDSS_DR12_Z051_NGC",
    "PowerSpectrum_SDSS_DR12_Z051_SGC",
    "PowerSpectrum_SDSS_DR12_Z051",
    "CorrelationFunction_SDSS_DR12_Z061_NGC",
    "DummyPowerSpectrum_SDSS_DR12_Z061_NGC",
    "DummyCorrelationFunction_SDSS_DR12_Z061_NGC",
]
