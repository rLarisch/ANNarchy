"""

    storage_formats.py

    This file is part of ANNarchy.

    Copyright (C) 2022 Alex Schwarz and Helge Uelo Dinkelbach
    <helge.dinkelbach@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ANNarchy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
# Defines the tested storage_formats. The tests are overloaded in __init__.py.
single_thread = {
    # File == Test case
    "test_RateTransmission":                ["lil", "csr", "ell"],
    "test_CustomConnectivity":              ["lil", "csr", "ell"],
    "test_Projection":                      ["lil", "csr"],
    "test_ContinuousUpdate":                ["lil", "csr"],
    # from test_Dendrite.py
    "test_DendriteDefaultSynapse":          ["lil", "csr", "ell"],
    "test_DendriteModifiedSynapse":         ["lil", "csr"],
    # from test_RateSynapse.py
    "test_Locality":                        ["lil", "csr"],
    "test_AccessPSP":                       ["lil", "csr"],
    "test_ModifiedPSP":                     ["lil", "csr"],
    # from test_RateDelays
    "test_NoDelay":                         ["lil", "csr", "ell"],
    "test_UniformDelay":                    ["lil", "csr"],
    "test_NonUniformDelay":                 ["lil", "csr"],
    "test_SynapseOperations":               ["lil"],
    "test_SynapticAccess":                  ["lil", "csr"],
    # from test_SpikingSynapse
    "test_PreSpike":                        ["lil", "csr"],
    "test_PostSpike":                       ["lil", "csr"],
    # from test_SpikingTransmission
    "test_SpikeTransmissionNoDelay":        ["lil", "csr"],
    "test_SpikeTransmissionUniformDelay":   ["lil", "csr"],
    "test_SpikeTransmissionNonUniformDelay":["lil"],
    # SpecificProjections
    # "test_Convolution":         ["lil", "csr", "ell"],
    # "test_Pooling":             ["lil", "csr", "ell"],
    # "test_CurrentInjection":    ["lil", "csr", ],
}

open_mp = {
    # File == Test case
    "test_RateTransmission":                ["lil", "csr", "ell"],
    "test_CustomConnectivity":              ["lil", "csr", "ell"],
    "test_Projection":                      ["lil", "csr"],
    "test_ContinuousUpdate":                ["lil", "csr"],
    # from test_Dendrite.py
    "test_DendriteDefaultSynapse":          ["lil", "csr", "ell"],
    "test_DendriteModifiedSynapse":         ["lil", "csr"],
    # from test_RateSynapse.py
    "test_Locality":                        ["lil", "csr"],
    "test_AccessPSP":                       ["lil", "csr"],
    "test_ModifiedPSP":                     ["lil", "csr"],
    # from test_RateDelays
    "test_NoDelay":                         ["lil", "csr", "ell"],
    "test_UniformDelay":                    ["lil", "csr"],
    "test_NonUniformDelay":                 ["lil", "csr"],
    "test_SynapseOperations":               ["lil"],
    "test_SynapticAccess":                  ["lil", "csr"],
    # from test_SpikingSynapse
    "test_PreSpike":                        ["lil", "csr"],
    "test_PostSpike":                       ["lil", "csr"],
    # from test_SpikingTransmission
    "test_SpikeTransmissionNoDelay":        ["lil", "csr"],
    "test_SpikeTransmissionUniformDelay":   ["lil", "csr"],
    "test_SpikeTransmissionNonUniformDelay":["lil"],
    # SpecificProjections
    # "test_Convolution":         ["lil", "csr", "ell"],
    # "test_Pooling":             ["lil", "csr", "ell"],
    # "test_CurrentInjection":    ["lil", "csr", ],
}

cuda = {
    "test_RateTransmission":    ["csr", "ellr"],
    "test_CustomConnectivity":  ["csr", "ellr"],
    "test_Dendrite":            ["csr", "ellr"],
    "test_Projection":          ["csr", "ellr"],
    "test_Locality":            ["csr", "ellr"],
    "test_AccessPSP":           ["csr", "ellr"],
    "test_ModifiedPSP":         ["csr", "ellr"],
    "test_NoDelay":             ["csr", "ellr"],
    "test_UniformDelay":        ["csr", "ellr"],
    "test_NonUniformDelay":     ["csr", ],
    "test_ContinuousUpdate":    ["csr", "ellr"],
    "test_SynapticAccess":      ["csr", "ellr"],
    "test_PreSpike":            ["csr", ],
    "test_PostSpike":           ["csr", ],
    "test_SpikeTransmission":   ["csr", ],
    "test_SynapseOperations":   ["csr", ],
}

# Defines which test classes should be run with pre_to_post and post_to_pre
#p2p = ["test_Dendrite", "test_Projection", "test_PreSpike", "test_PostSpike",
#       "test_CurrentInjection"]
p2p = []