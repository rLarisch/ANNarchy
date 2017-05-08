#===============================================================================
#
#     MonitorGenerator.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2013-2016  Julien Vitay <julien.vitay@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
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
#===============================================================================
from ANNarchy.core import Global
from ANNarchy.generator.Template import MonitorTemplate as RecTemplate

class MonitorGenerator(object):
    """
    Creates the required codes for recording population
    and projection data
    """
    def __init__(self, annarchy_dir, populations, projections, net_id):
        """
        Constructor, stores all required data for later
        following code generation step

        Parameters:

            * *annarchy_dir*: unique target directory for the generated code
              files; they are stored in 'generate' sub-folder
            * *populations*: list of populations
            * *populations*: list of projections
            * *net_id*: unique id for the current network

        """
        self._annarchy_dir = annarchy_dir
        self._populations = populations
        self._projections = projections
        self._net_id = net_id

    def generate(self):
        """
        Generate one file "Recorder.h" comprising of Monitor base class and inherited
        classes for each Population/Projection.

        Templates:

            record_base_class
        """
        record_class = ""
        for pop in self._populations:
            record_class += self._pop_recorder_class(pop)

        for proj in self._projections:
            record_class += self._proj_recorder_class(proj)

        code = RecTemplate.record_base_class % {'record_classes': record_class}

        # Generate header code for the analysed pops and projs
        with open(self._annarchy_dir+'/generate/net'+str(self._net_id)+'/Recorder.h', 'w') as ofile:
            ofile.write(code)

    def _pop_recorder_class(self, pop):
        """
        Creates population recording class code.

        Returns:

            * complete code as string

        Templates:

            omp_population, cuda_population
        """
        if Global.config['paradigm'] == "openmp":
            template = RecTemplate.omp_population
        elif Global.config['paradigm'] == "cuda":
            template = RecTemplate.cuda_population
        else:
            raise NotImplementedError

        tpl_code = template['template']

        init_code = ""
        recording_code = ""
        recording_target_code = ""
        struct_code = ""

        # The post-synaptic potential for rate-code (weighted sum) as well
        # as the conductance variables are handled seperatly.
        target_list = []
        targets = []
        for t in pop.neuron_type.description['targets']:
            if isinstance(t, list):
                for t2 in t:
                    targets.append(t2)
            else:
                targets.append(t)
        for t in pop.targets:
            if isinstance(t, list):
                for t2 in t:
                    targets.append(t2)
            else:
                targets.append(t)
        targets = sorted(list(set(targets)))
        
        if pop.neuron_type.type == 'rate':
            for target in targets:
                struct_code += template['local']['struct'] % {'type' : 'double', 'name': '_sum_'+target}
                init_code += template['local']['init'] % {'type' : 'double', 'name': '_sum_'+target}
                recording_target_code += template['local']['recording'] % {'id': pop.id, 'type' : 'double', 'name': '_sum_'+target}
        else:
            for target in targets:
                struct_code += template['local']['struct'] % {'type' : 'double', 'name': 'g_'+target}
                init_code += template['local']['init'] % {'type' : 'double', 'name': 'g_'+target}
                recording_target_code += template['local']['recording'] % {'id': pop.id, 'type' : 'double', 'name': 'g_'+target}

                # to skip this entry in the following loop
                target_list.append('g_'+target)

        # Record global and local attributes
        attributes = []
        for var in pop.neuron_type.description['parameters'] + pop.neuron_type.description['variables']:
            # Skip targets
            if var['name'] in target_list:
                continue
            # Avoid doublons
            if var['name'] in attributes:
                continue
            attributes.append(var['name'])

            struct_code += template[var['locality']]['struct'] % {'type' : var['ctype'], 'name': var['name']}
            init_code += template[var['locality']]['init'] % {'type' : var['ctype'], 'name': var['name']}
            recording_code += template[var['locality']]['recording'] % {'id': pop.id, 'type' : var['ctype'], 'name': var['name']}

        # Spike events
        if pop.neuron_type.type == 'spike':
            struct_code += """
    // Local variable %(name)s
    std::map<int, std::vector< %(type)s > > %(name)s ;
    bool record_%(name)s ;
    void clear_spike() {
        for ( auto it = spike.begin(); it != spike.end(); it++ ) {
            it->second.clear();
        }
    }
""" % {'type' : 'long int', 'name': 'spike'}

            init_code += """
        this->%(name)s = std::map<int,  std::vector< %(type)s > >();
        if(!this->partial){
            for(int i=0; i<pop%(id)s.size; i++) {
                this->%(name)s[i]=std::vector<%(type)s>();
            }
        }
        else{
            for(int i=0; i<this->ranks.size(); i++) {
                this->%(name)s[this->ranks[i]]=std::vector<%(type)s>();
            }
        }
        this->record_%(name)s = false; """ % {'id': pop.id, 'type' : 'long int', 'name': 'spike'}

            recording_code += RecTemplate.recording_spike_tpl[Global.config['paradigm']] % {'id': pop.id, 'type' : 'int', 'name': 'spike'}

        ids = {
            'id': pop.id,
            'init_code': init_code,
            'struct_code': struct_code,
            'recording_code': recording_code,
            'recording_target_code': recording_target_code
        }
        return tpl_code % ids

    def _proj_recorder_class(self, proj):
        """
        Generate the code for the recorder object.

        Returns:

            * complete code as string

        Templates:

            record
        """
        if Global.config['paradigm'] == "openmp":
            template = RecTemplate.omp_projection
        elif Global.config['paradigm'] == "cuda":
            template = RecTemplate.cuda_projection
        else:
            raise NotImplementedError

        # Specific template
        if 'monitor_class' in proj._specific_template.keys():
            return proj._specific_template['monitor_class']

        init_code = ""
        recording_code = ""
        struct_code = ""

        attributes = []
        for var in proj.synapse_type.description['parameters'] + proj.synapse_type.description['variables']:
            # Avoid doublons
            if var['name'] in attributes:
                continue
            attributes.append(var['name'])

            # Get the locality
            locality = var['locality']
            
            # Special case for single weights
            if var['name'] == "w" and proj._has_single_weight():
                locality = 'global'
                
            # Get the template for the structure declaration
            struct_code += template[locality]['struct'] % {'type' : var['ctype'], 'name': var['name']}
            
            # Get the initialization code
            init_code += template[locality]['init'] % {'type' : var['ctype'], 'name': var['name']}
            
            # Get the recording code
            if proj._storage_format == "lil":
                recording_code += template[locality]['recording'] % {'id': proj.id, 'type' : var['ctype'], 'name': var['name']}
            else:
                Global._warning("Monitor: variable "+ var['name'] + " cannot be recorded for a projection using the csr format...")

        return template['struct'] % {'id': proj.id, 'init_code': init_code, 'recording_code': recording_code, 'struct_code': struct_code}