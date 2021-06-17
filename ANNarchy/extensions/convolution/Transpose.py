# =============================================================================
#
#     CopyProjection.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2020  Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>,
#     Julien Vitay <julien.vitay@gmail.com>,
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchy is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =============================================================================
from ANNarchy.core import Global
from ANNarchy.core.Projection import Projection
from ANNarchy.models.Synapses import DefaultRateCodedSynapse

class Transpose(Projection):
    """
    Creates a transposed projection reusing the weights of an already-defined rate-coded projection. Even though the
    original projection can be learnable, this one can not. The computed post-synaptic potential is the default case
    for rate-coded projections: w * pre.r

    The proposed *target* can differ from the target of the forward projection.

    Example:

        proj_ff = Projection( input, output, target="exc" )
        proj_ff.connect_all_to_all(weights=Uniform(0,1)

        proj_fb = Transpose(proj_ff, target="inh")
        proj_fb.connect()
    """
    def __init__(self, proj, target):
        """
        :param proj: original projection
        :param target: type of the connection (can differ from the original one)
        """
        Projection.__init__(
            self,
            pre = proj.post,
            post = proj.pre,
            target = target,
            synapse = DefaultRateCodedSynapse
        )

        # in the code generation we directly access properties of the
        # forward projection. Therefore we store the link here to have access in
        # self._generate()
        self.fwd_proj = proj

        # Some sanity checks
        if proj.pre.neuron_type == "spike" or proj.post.neuron_type == "spike":
            Global._error('TransposeProjection are only applicable on rate-coded projections yet ...')

        if (proj._connection_delay > 0.0):
            Global._error('TransposeProjection can not be applied on delayed projections yet ...')

        # simply copy from the forward view
        self.delays = proj._connection_delay
        self.max_delay = proj.max_delay
        self.uniform_delay = proj.uniform_delay

    def _copy(self):
        raise NotImplementedError

    def _create(self):
        pass

    def connect(self):
        # create fake LIL object to have the forward view in C++
        try:
            from ANNarchy.core.cython_ext.Connector import LILConnectivity
        except Exception as e:
            Global._print(e)
            Global._error('ANNarchy was not successfully installed.')

        lil = LILConnectivity()
        lil.max_delay = self.max_delay
        lil.uniform_delay = self.uniform_delay
        self.connector_name = "Transpose"
        self.connector_description = "Transpose"

    def _connect(self, module):
        proj = getattr(module, 'proj'+str(self.id)+'_wrapper')
        self.cyInstance = proj()

    def _generate(self):
        """
        Overrides default code generation. This function is called during the code generation procedure.
        """
        #
        # C++ definition and PYX wrapper
        self._specific_template['struct_additional'] = """
extern ProjStruct%(fwd_id_proj)s proj%(fwd_id_proj)s;    // Forward projection
""" % { 'fwd_id_proj': self.fwd_proj.id }

        self._specific_template['declare_connectivity_matrix'] = """
    // LIL connectivity (inverse of proj%(id)s)
    std::vector< int > inv_post_rank ;
    std::vector< std::vector< std::pair< int, int > > > inv_pre_rank ;

    void init_from_lil(std::vector<int>, std::vector<std::vector<int>>, std::vector<std::vector<%(float_prec)s>>, std::vector<std::vector<int>>) {

    }
""" % {'float_prec': Global.config['precision'], 'id': self.fwd_proj.id}

        # TODO: error message on setter?
        self._specific_template['access_connectivity_matrix'] = """
    // Accessor to connectivity data
    std::vector<int> get_post_rank() { return inv_post_rank; }
    int nb_synapses(int n) { return 0; }
"""
        self._specific_template['init_additional'] = """
        // Inverse connectivity to Proj%(fwd_id_proj)s
        auto inv_conn =  std::map< int, std::vector< std::pair<int, int> > > ();

        for (int i = 0; i < proj%(fwd_id_proj)s.pre_rank.size(); i++) {
            int post_rk = proj%(fwd_id_proj)s.post_rank[i];

            for (int j = 0; j < proj%(fwd_id_proj)s.pre_rank[i].size(); j++ ) {
                int pre_rk = proj%(fwd_id_proj)s.pre_rank[i][j];

                inv_conn[pre_rk].push_back(std::pair<int, int>(i, j));
            }
        }

        // keys are automatically sorted
        for (auto it = inv_conn.begin(); it != inv_conn.end(); it++ ) {
            inv_post_rank.push_back(it->first);
            inv_pre_rank.push_back(it->second);
        }

        // sanity check
        size_t inv_size = 0;
        for (int i = 0; i < inv_post_rank.size(); i++) {
            inv_size += inv_pre_rank[i].size();
        }

        assert( (proj%(fwd_id_proj)s.nb_synapses() == inv_size) );
""" % { 'fwd_id_proj': self.fwd_proj.id }

        self._specific_template['wrapper_init_connectivity'] = """
        pass
"""
        self._specific_template['wrapper_access_connectivity'] = """
    # read only connectivity
    def post_rank(self):
        return proj%(id_proj)s.get_post_rank()
""" % { 'id_proj': self.id }

        # memory management
        self._specific_template['determine_size_in_bytes'] = ""
        self._specific_template['clear_container'] = ""

        #
        # suppress monitor
        self._specific_template['monitor_export'] = ""
        self._specific_template['monitor_wrapper'] = ""
        self._specific_template['monitor_class'] = ""
        self._specific_template['pyx_wrapper'] = ""

        # The weight index depends on the
        # weight of the forward projection
        if self.fwd_proj._has_single_weight():
            weight_index = ""
        else:
            weight_index = "[post_idx][pre_idx]"

        #
        # PSP code
        self._specific_template['psp_code'] = """
        if (pop%(id_post)s._active && _transmission) {
            for (int i = 0; i < inv_post_rank.size(); i++) {
                %(float_prec)s sum = 0.0;

                for (auto it = inv_pre_rank[i].begin(); it != inv_pre_rank[i].end(); it++) {
                    auto post_idx = it->first;
                    auto pre_idx = it->second;

                    sum += pop%(id_pre)s.r[proj%(fwd_id_proj)s.post_rank[post_idx]] * proj%(fwd_id_proj)s.w%(index)s;
                }
                pop%(id_post)s._sum_%(target)s[inv_post_rank[i]] += sum;
            }
        }
""" % { 'float_prec': Global.config['precision'],
        'target': self.target,
        'id_pre': self.pre.id,
        'id_post': self.post.id,
        'fwd_id_proj': self.fwd_proj.id,
        'index': weight_index
}

    ##############################
    ## Override useless methods
    ##############################
    def _data(self):
        "Disable saving."
        desc = {}
        desc['post_ranks'] = self.post_ranks
        desc['attributes'] = self.attributes
        desc['parameters'] = self.parameters
        desc['variables'] = self.variables

        desc['dendrites'] = []
        desc['number_of_synapses'] = 0
        return desc

    def save_connectivity(self, filename):
        "Not available."
        Global._warning('Transposed projections can not be saved.')
    def save(self, filename):
        "Not available."
        Global._warning('Transposed projections can not be saved.')
    def load(self, filename):
        "Not available."
        Global._warning('Transposed projections can not be loaded.')

    # TODO: maybe this functions would be helpful for debugging. Even though
    #       they will be time consuming as the matrix need to be constructed.
    #       (HD, 9th July 2020)
    def receptive_fields(self, variable = 'w', in_post_geometry = True):
        "Not available."
        Global._warning('Transposed projections can not display receptive fields.')
    def connectivity_matrix(self, fill=0.0):
        "Not available."
        Global._warning('Transposed projections can not display connectivity matrices.')
