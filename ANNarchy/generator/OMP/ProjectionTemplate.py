"""

    PopulationTemplate.py

    This file is part of ANNarchy.

    Copyright (C) 2013-2016  Julien Vitay <julien.vitay@gmail.com>,
    Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>

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
from ANNarchy.generator.OMP.PopulationTemplate import attribute_pyx_wrapper
header_struct = {
    'openmp': """#pragma once

#include "pop%(pre_id)s.hpp"
#include "pop%(post_id)s.hpp"

extern PopStruct%(pre_id)s pop%(pre_id)s;
extern PopStruct%(post_id)s pop%(post_id)s;

/////////////////////////////////////////
// proj%(id_proj)s: %(pre_name)s -> %(post_name)s with target %(target)s
/////////////////////////////////////////
struct ProjStruct%(id_proj)s{
    // number of dendrites
    int size;

    // Learning flag
    bool _learning;

    // Connectivity
    std::vector<int> post_rank ;
    std::vector< std::vector< int > > pre_rank ;

%(delay)s
%(exact)s
%(decl)s

    void init_projection() {
%(init)s
    }

    void compute_psp() {
%(psp_prefix)s

%(psp)s
    }
    
    void update_rng() {
%(update_rng)s
    }

    void update_synapse() {
        int rk_pre, rk_post;

%(update)s
    }

    // Accessors for c-wrapper
    int get_size() { return size; }
    void set_size(int new_size) { size = new_size; }
    std::vector<int> get_post_rank() { return post_rank; }
    void set_post_rank(std::vector<int> ranks) { post_rank = ranks; }
    std::vector< std::vector<int> > get_pre_rank() { return pre_rank; }
    void set_pre_rank(std::vector< std::vector<int> > ranks) { pre_rank = ranks; }
    int nb_synapses(int n) { return pre_rank[n].size(); }

%(accessor)s
};
""",
    'cuda': """#pragma once

#include "pop%(pre_id)s.hpp"
#include "pop%(post_id)s.hpp"

extern PopStruct%(pre_id)s pop%(pre_id)s;
extern PopStruct%(post_id)s pop%(post_id)s;

/////////////////////////////////////////
// proj%(id_proj)s: %(pre_name)s -> %(post_name)s with target %(target)s
/////////////////////////////////////////
struct ProjStruct%(id_proj)s{
    // number of dendrites
    int size;

    // Learning flag
    bool _learning;

    // Connectivity
    std::vector<int> post_rank ;
    int* gpu_post_rank;
    std::vector< std::vector< int > > pre_rank ;
    int* gpu_pre_rank;
    int* gpu_nb_synapses;
    int* gpu_off_synapses;

    // flat connectivity parameters
    int overallSynapses;
    std::vector<int> flat_idx;
    std::vector<int> flat_off;

    // stream
    cudaStream_t stream;

%(delay)s
%(exact)s
%(decl)s

    void init_projection() {
%(init)s
    }

    void compute_psp() {
%(psp_prefix)s

%(psp)s
    }

    void update_rng() {
%(update_rng)s
    }

    void update_synapse() {
        int rk_pre, rk_post;

%(update)s
    }

    // Accessors for c-wrapper
    int get_size() { return size; }
    void set_size(int new_size) { size = new_size; }
    std::vector<int> get_post_rank() { return post_rank; }
    void set_post_rank(std::vector<int> ranks) { post_rank = ranks; }
    std::vector< std::vector<int> > get_pre_rank() { return pre_rank; }
    void set_pre_rank(std::vector< std::vector<int> > ranks) { pre_rank = ranks; }
    int nb_synapses(int n) { return pre_rank[n].size(); }

%(accessor)s

    /*
     * (De-)Flattening of LIL structures
     */
    template<typename T>
    std::vector<int> flattenIdx(std::vector<std::vector<T> > in)
    {
        std::vector<T> flatIdx = std::vector<T>();
        typename std::vector<std::vector<T> >::iterator it;

        for ( it = in.begin(); it != in.end(); it++)
        {
            flatIdx.push_back(it->size());
        }

        return flatIdx;
    }

    template<typename T>
    std::vector<int> flattenOff(std::vector<std::vector<T> > in)
    {
        std::vector<T> flatOff = std::vector<T>();
        typename std::vector<std::vector<T> >::iterator it;

        int currOffset = 0;
        for ( it = in.begin(); it != in.end(); it++)
        {
            flatOff.push_back(currOffset);
            currOffset += it->size();
        }

        return flatOff;
    }

    template<typename T>
    std::vector<T> flattenArray(std::vector<std::vector<T> > in)
    {
        std::vector<T> flatVec = std::vector<T>();
        typename std::vector<std::vector<T> >::iterator it;

        for ( it = in.begin(); it != in.end(); it++)
        {
            flatVec.insert(flatVec.end(), it->begin(), it->end());
        }

        return flatVec;
    }

    template<typename T>
    std::vector<std::vector<T> > deFlattenArray(std::vector<T> in, std::vector<int> idx)
    {
        std::vector<std::vector<T> > deFlatVec = std::vector<std::vector<T> >();
        std::vector<int>::iterator it;

        int t=0;
        for ( it = idx.begin(); it != idx.end(); it++)
        {
            std::vector<T> tmp = std::vector<T>(in.begin()+t, in.begin()+t+*it);
            t += *it;

            deFlatVec.push_back(tmp);
        }

        return deFlatVec;
    }
};
"""
}

pyx_wrapper = """
cdef class proj%(id)s_wrapper :

    def __cinit__(self, synapses):

        cdef CSR syn = synapses
        cdef int size = syn.size
        cdef int nb_post = syn.post_rank.size()

        proj%(id)s.set_size( size )
        proj%(id)s.set_post_rank( syn.post_rank )
        proj%(id)s.set_pre_rank( syn.pre_rank )
        proj%(id)s.set_w(syn.w)
%(delay_init)s
%(exact_init)s

    property size:
        def __get__(self):
            return proj%(id)s.get_size()

    def nb_synapses(self, int n):
        return proj%(id)s.nb_synapses(n)

    def _set_learning(self, bool l):
        proj%(id)s._learning = l

    def post_rank(self):
        return proj%(id)s.get_post_rank()
    def pre_rank(self, int n):
        return proj%(id)s.get_pre_rank()[n]

%(delay_acc)s

%(accessor)s
%(structural_plasticity)s
"""

pyx_struct = """
    cdef struct ProjStruct%(id_proj)s :
        bool _learning

        int get_size()
        vector[int] get_post_rank()
        vector[vector[int]] get_pre_rank()
        int nb_synapses(int)
        void set_size(int)
        void set_post_rank(vector[int])
        void set_pre_rank(vector[vector[int]])

%(delay)s
%(exact)s
%(export)s
%(structural_plasticity)s
"""

# c like definition of synaptic attributes, whereas 'local' is used if values can vary across
# synapses, consequently 'global' is used if values are common to all synapses within a dendrite.
# Please note, that one projection represents a collection of dendrites.
#
# Parameters:
#
#    type: data type of the variable (double, float, int ...)
#    name: name of the variable
#    attr_type: either 'variable' or 'parameter'
attribute_decl = {
    'openmp': {
    'local':
"""
    // Local %(attr_type)s %(name)s
    std::vector< std::vector<%(type)s > > %(name)s;
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    std::vector< %(type)s >  %(name)s ;
"""
    },
    'cuda': {
    'local':
"""
    // Local %(attr_type)s %(name)s
    std::vector< std::vector<%(type)s > > %(name)s;
    %(type)s* gpu_%(name)s;
    bool %(name)s_dirty;
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    std::vector< %(type)s >  %(name)s ;
"""
    }
}

# c like definition of accessors for synaptic attributes, whereas 'local' is used if values can vary
# across synapses, consequently 'global' is used if values are common to all neurons.
#
# Parameters:
#
#    type: data type of the variable (double, float, int ...)
#    name: name of the variable
#    attr_type: either 'variable' or 'parameter'
attribute_acc = {
    'openmp': {
    'local':
"""
    // Local %(attr_type)s %(name)s
    std::vector<std::vector< %(type)s > > get_%(name)s() { return %(name)s; }
    std::vector<%(type)s> get_dendrite_%(name)s(int rk) { return %(name)s[rk]; }
    %(type)s get_synapse_%(name)s(int rk_post, int rk_pre) { return %(name)s[rk_post][rk_pre]; }
    void set_%(name)s(std::vector<std::vector< %(type)s > >value) { %(name)s = value; }
    void set_dendrite_%(name)s(int rk, std::vector<%(type)s> value) { %(name)s[rk] = value; }
    void set_synapse_%(name)s(int rk_post, int rk_pre, %(type)s value) { %(name)s[rk_post][rk_pre] = value; }
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    std::vector<%(type)s> get_%(name)s() { return %(name)s; }
    %(type)s get_dendrite_%(name)s(int rk) { return %(name)s[rk]; }
    void set_%(name)s(std::vector<%(type)s> value) { %(name)s = value; }
    void set_dendrite_%(name)s(int rk, %(type)s value) { %(name)s[rk] = value; }
"""
    },
    'cuda': {
    'local':
"""
    // Local %(attr_type)s %(name)s
    std::vector<std::vector< %(type)s > > get_%(name)s() { return %(name)s; }
    std::vector<%(type)s> get_dendrite_%(name)s(int rk) { return %(name)s[rk]; }
    %(type)s get_synapse_%(name)s(int rk_post, int rk_pre) { return %(name)s[rk_post][rk_pre]; }
    void set_%(name)s(std::vector<std::vector< %(type)s > >value) { %(name)s = value; %(name)s_dirty = true; }
    void set_dendrite_%(name)s(int rk, std::vector<%(type)s> value) { %(name)s[rk] = value; %(name)s_dirty = true; }
    void set_synapse_%(name)s(int rk_post, int rk_pre, %(type)s value) { %(name)s[rk_post][rk_pre] = value; %(name)s_dirty = true; }
""",
    'global':
"""
    // Global %(attr_type)s %(name)s
    std::vector<%(type)s> get_%(name)s() { return %(name)s; }
    %(type)s get_dendrite_%(name)s(int rk) { return %(name)s[rk]; }
    void set_%(name)s(std::vector<%(type)s> value) { %(name)s = value; }
    void set_dendrite_%(name)s(int rk, %(type)s value) { %(name)s[rk] = value; }
"""
    }
}

# Initialization of parameters due to the init_projection method.
#
# Parameters:
#
#    name: name of the variable
#    init: initial value
attribute_cpp_init = {
    'openmp':
    {
    'local':
"""
        // Local %(attr_type)s %(name)s
        proj%(id)s.%(name)s = std::vector< std::vector<%(type)s> >(proj%(id)s.post_rank.size(), std::vector<%(type)s>());
""",
    'global':
"""
        // Global %(attr_type)s %(name)s
        proj%(id)s.%(name)s = std::vector<%(type)s>(proj%(id)s.post_rank.size(), %(init)s);
"""
    },
    'cuda':
    {
    'local':
"""
        // Local %(attr_type)s %(name)s
""",
    'global':
"""
        // Global %(attr_type)s %(name)s
"""
    }
}

# export of accessors for synaptic attributes towards python, whereas 'local' is used if values can vary
# across synapses within a dendrite, consequently 'global' is used if values are common to all synapses within
# a single dendrite.
#
# Parameters:
#
#    type: data type of the variable (double, float, int ...). One should check if cython can understand the
#          used types ( e. g. vector[bool] would not work properly... )
#    name: name of the variable
#    attr_type: either 'variable' or 'parameter'
attribute_cpp_export = {
    'local':
"""
        # Local %(attr_type)s %(name)s
        vector[vector[%(type)s]] get_%(name)s()
        vector[%(type)s] get_dendrite_%(name)s(int)
        %(type)s get_synapse_%(name)s(int, int)
        void set_%(name)s(vector[vector[%(type)s]])
        void set_dendrite_%(name)s(int, vector[%(type)s])
        void set_synapse_%(name)s(int, int, %(type)s)
""",
    'global':
"""
        # Global %(attr_type)s %(name)s
        vector[%(type)s] get_%(name)s()
        %(type)s get_dendrite_%(name)s(int)
        void set_%(name)s(vector[%(type)s])
        void set_dendrite_%(name)s(int, %(type)s)
"""
}

attribute_pyx_wrapper = {
    'local':
"""
    # Local %(attr_type)s %(name)s
    def get_%(name)s(self):
        return proj%(id)s.get_%(name)s()
    def set_%(name)s(self, value):
        proj%(id)s.set_%(name)s( value )
    def get_dendrite_%(name)s(self, int rank):
        return proj%(id)s.get_dendrite_%(name)s(rank)
    def set_dendrite_%(name)s(self, int rank, vector[%(type)s] value):
        proj%(id)s.set_dendrite_%(name)s(rank, value)
    def get_synapse_%(name)s(self, int rank_post, int rank_pre):
        return proj%(id)s.get_synapse_%(name)s(rank_post, rank_pre)
    def set_synapse_%(name)s(self, int rank_post, int rank_pre, %(type)s value):
        proj%(id)s.set_synapse_%(name)s(rank_post, rank_pre, value)
""",
    'global':
"""
    # Global %(attr_type)s %(name)s
    def get_%(name)s(self):
        return proj%(id)s.get_%(name)s()
    def set_%(name)s(self, value):
        proj%(id)s.set_%(name)s(value)
    def get_dendrite_%(name)s(self, int rank):
        return proj%(id)s.get_dendrite_%(name)s(rank)
    def set_dendrite_%(name)s(self, int rank, %(type)s value):
        proj%(id)s.set_dendrite_%(name)s(rank, value)
"""
}

# Code templates for recorder class.
#
#    struct: base template
#    local: codes for struct member, init and recording for local variables
#    global: codes for struct member, init and recording for global variables
record = {
    'struct': """
class ProjRecorder%(id)s : public Monitor
{
public:
    ProjRecorder%(id)s(std::vector<int> ranks, int period, long int offset)
        : Monitor(ranks, period, offset)
    {
%(init_code)s
    };
    virtual void record() {
%(recording_code)s
    };
%(struct_code)s
};
""",
    'local': {
        'struct': """
    // Local variable %(name)s
    std::vector< std::vector< %(type)s > > %(name)s ;
    bool record_%(name)s ;
""",
        'init' : """
        this->%(name)s = std::vector< std::vector< %(type)s > >();
        this->record_%(name)s = false;
""",
        'recording': """
        if(this->record_%(name)s && ( (t - this->offset) %% this->period == 0 )){
            this->%(name)s.push_back(proj%(id)s.%(name)s[this->ranks[0]]);
        }
"""
    },
    'global': {
        'struct': """
    // Global variable %(name)s
    std::vector< %(type)s > %(name)s ;
    bool record_%(name)s ;
""",
        'init' : """
        this->%(name)s = std::vector< %(type)s >();
        this->record_%(name)s = false;
""",
        'recording': """
        if(this->record_%(name)s && ( (t - this->offset) %% this->period == 0 )){
            this->%(name)s.push_back(proj%(id)s.%(name)s[this->ranks[0]]);
        }
"""
    }
}

delay = {
    'header_struct': """
    std::vector< std::vector< int > > delay ;
""",
    'decl':
"""
        vector[vector[int]] delay
""",
    'cinit':
"""
        proj%(id)s.delay = syn.delay
""",
    'pyx_wrapper_acc':
"""
    # Access to delay
    def get_delay(self):
        return proj%(id)s.delay
    def get_dendrite_delay(self, idx):
        return proj%(id)s.delay[idx]
    def set_delay(self, value):
        proj%(id)s.delay = value
"""
}

exact_integ = {
    'header_struct': """
    std::vector<std::vector<long> > _last_event;
""",
    'decl': """
        vector[vector[long]] _last_event
""",
    'cinit':
"""
        proj%(id)s._last_event = vector[vector[long]](nb_post, vector[long]())
        for n in range(nb_post):
            proj%(id)s._last_event[n] = vector[long](proj%(id)s.nb_synapses(n), -10000)
"""
}

# All code templates needed for structural plasticity.
structural_plasticity = {
    'header_struct': {
        'header': """
    // Structural plasticity
    int dendrite_index(int post, int pre){
        int idx = 0;
        for(int i=0; i<pre_rank[post].size(); i++){
            if(pre_rank[post][i] == pre){
                idx = i;
                break;
            }
        }
        return idx;
    }
    void addSynapse(int post, int pre, double weight, int _delay=0%(extra_args)s){
        // Find where to put the synapse
        int idx = pre_rank[post].size();
        for(int i=0; i<pre_rank[post].size(); i++){
            if(pre_rank[post][i] > pre){
                idx = i;
                break;
            }
        }
        pre_rank[post].insert(pre_rank[post].begin() + idx, pre);
        w[post].insert(w[post].begin() + idx, weight);
        %(delay_code)s
%(add_code)s
%(spike_add)s
%(rd_add)s
    };
    void removeSynapse(int post, int idx){
        pre_rank[post].erase(pre_rank[post].begin() + idx);
        w[post].erase(w[post].begin() + idx);
%(remove_code)s
%(spike_remove)s
%(rd_remove)s
    };
""",
        'pruning': """
    // Pruning
    bool _pruning;
    int _pruning_period;
    long int _pruning_offset;
""",
        'creating': """
    // Creating
    bool _creating;
    int _creating_period;
    long int _creating_offset;
""",
        'spiking_addcode': """
        // Add the corresponding pair in inv_rank
        int idx_post = 0;
        for(int i=0; i<post_rank.size(); i++){
            if(post_rank[i] == post){
                idx_post = i;
                break;
            }
        }
        inv_rank[pre].push_back(std::pair<int, int>(idx_post, idx));
""",
        'spiking_removecode': """
        // Remove the corresponding pair in inv_rank
        int pre = pre_rank[post][idx];
        for(int i=0; i<inv_rank[pre].size(); i++){
            if(inv_rank[pre][i].second == idx){
                inv_rank[pre].erase(inv_rank[pre].begin() + i);
                break;
            }
        }
"""
},
    'pyx_struct': {
        'pruning':
"""
        # Pruning
        bool _pruning
        int _pruning_period
        long _pruning_offset
""",
        'creating':
"""
        # Creating
        bool _creating
        int _creating_period
        long _creating_offset
""",
        'func':
"""
        # Structural plasticity
        int dendrite_index(int post, int pre)
        void addSynapse(int post, int pre, double weight, int _delay%(extra_args)s)
        void removeSynapse(int post, int pre)
"""
    },
    'pyx_wrapper': {
        'pruning':
"""
    # Pruning
    def start_pruning(self, int period, long offset):
        proj%(id)s._pruning = True
        proj%(id)s._pruning_period = period
        proj%(id)s._pruning_offset = offset
    def stop_pruning(self):
        proj%(id)s._pruning = False
""",
        'creating':
"""
    # Creating
    def start_creating(self, int period, long offset):
        proj%(id)s._creating = True
        proj%(id)s._creating_period = period
        proj%(id)s._creating_offset = offset
    def stop_creating(self):
        proj%(id)s._creating = False
""",
        'func':
"""
    # Structural plasticity
    def add_synapse(self, int post_rank, int pre_rank, double weight, int delay%(extra_args)s):
        proj%(id)s.addSynapse(post_rank, pre_rank, weight, delay%(extra_values)s)
    def remove_synapse(self, int post_rank, int pre_rank):
        proj%(id)s.removeSynapse(post_rank, proj%(id)s.dendrite_index(post_rank, pre_rank))
"""
    }
}

# Comment to if (tid < 32) block:
#
# now that we are using warp-synchronous programming (below)
# we need to declare our shared memory volatile so that the compiler
# doesn't reorder stores to it and induce incorrect behavior.
cuda_psp_kernel=\
"""
__global__ void cuPop%(pre)s_Pop%(post)s_%(target)s_psp( int* rank_pre, int *nb_synapses, int* offsets, double *pre_r, double* w, double *sum_%(target)s ) {
    unsigned int tid = threadIdx.x;
    unsigned int j = tid+offsets[blockIdx.x];

    extern double __shared__ sdata[];
    double localSum = 0.0;

    while(j < nb_synapses[blockIdx.x]+offsets[blockIdx.x])
    {
        localSum += %(psp)s

        j+= blockDim.x;
    }

    sdata[tid] = localSum;
    __syncthreads();

    // do reduction in shared mem
    if (blockDim.x >= 512) { if (tid < 256) { sdata[tid] = localSum = localSum + sdata[tid + 256]; } __syncthreads(); }
    if (blockDim.x >= 256) { if (tid < 128) { sdata[tid] = localSum = localSum + sdata[tid + 128]; } __syncthreads(); }
    if (blockDim.x >= 128) { if (tid <  64) { sdata[tid] = localSum = localSum + sdata[tid +  64]; } __syncthreads(); }

    if (tid < 32)
    {
        volatile double* smem = sdata;

        if (blockDim.x >=  64) { smem[tid] = localSum = localSum + smem[tid + 32]; }
        if (blockDim.x >=  32) { smem[tid] = localSum = localSum + smem[tid + 16]; }
        if (blockDim.x >=  16) { smem[tid] = localSum = localSum + smem[tid +  8]; }
        if (blockDim.x >=   8) { smem[tid] = localSum = localSum + smem[tid +  4]; }
        if (blockDim.x >=   4) { smem[tid] = localSum = localSum + smem[tid +  2]; }
        if (blockDim.x >=   2) { smem[tid] = localSum = localSum + smem[tid +  1]; }

    }

    // write result for this block to global mem
    if (tid == 0)
    {
        sum_%(target)s[blockIdx.x] = sdata[0];
    }

}
"""

cuda_psp_kernel_call =\
"""
    // proj%(id)s: pop%(pre)s -> pop%(post)s
    if ( pop%(post)s._active ) {
        int sharedMemSize = __pop%(pre)s_pop%(post)s_%(target)s__ * 64;

        cuPop%(pre)s_Pop%(post)s_%(target)s_psp<<<pop%(post)s.size, __pop%(pre)s_pop%(post)s_%(target)s__, sharedMemSize>>>(
                       /* ranks and offsets */
                       proj%(id)s.gpu_pre_rank, proj%(id)s.gpu_nb_synapses, proj%(id)s.gpu_off_synapses,
                       /* computation data */
                       pop%(pre)s.gpu_r, proj%(id)s.gpu_w,
                       /* result */
                       pop%(post)s.gpu_sum_%(target)s );
    }
"""

cuda_proj_base_data =\
"""
    // Initialize device memory for proj%(id)s

    // post_rank
    cudaMalloc((void**)&proj%(id)s.gpu_post_rank, proj%(id)s.post_rank.size() * sizeof(int));
    cudaMemcpy(proj%(id)s.gpu_post_rank, proj%(id)s.post_rank.data(), proj%(id)s.post_rank.size() * sizeof(int), cudaMemcpyHostToDevice);

    // nb_synapses
    proj%(id)s.flat_idx = flattenIdx<int>(proj%(id)s.pre_rank);
    cudaMalloc((void**)&proj%(id)s.gpu_nb_synapses, proj%(id)s.flat_idx.size() * sizeof(int));
    cudaMemcpy(proj%(id)s.gpu_nb_synapses, proj%(id)s.flat_idx.data(), proj%(id)s.flat_idx.size() * sizeof(int), cudaMemcpyHostToDevice);
    proj%(id)s.overallSynapses = 0;
    std::vector<int>::iterator it%(id)s;
    for ( it%(id)s = proj%(id)s.flat_idx.begin(); it%(id)s != proj%(id)s.flat_idx.end(); it%(id)s++)
        proj%(id)s.overallSynapses += *it%(id)s;

    // off_synapses
    proj%(id)s.flat_off = flattenOff<int>(proj%(id)s.pre_rank);
    cudaMalloc((void**)&proj%(id)s.gpu_off_synapses, proj%(id)s.flat_off.size() * sizeof(int));
    cudaMemcpy(proj%(id)s.gpu_off_synapses, proj%(id)s.flat_off.data(), proj%(id)s.flat_off.size() * sizeof(int), cudaMemcpyHostToDevice);

    // pre_rank
    std::vector<int> flat_proj%(id)s_pre_rank = flattenArray<int>(proj%(id)s.pre_rank);
    cudaMalloc((void**)&proj%(id)s.gpu_pre_rank, flat_proj%(id)s_pre_rank.size() * sizeof(int));
    cudaMemcpy(proj%(id)s.gpu_pre_rank, flat_proj%(id)s_pre_rank.data(), flat_proj%(id)s_pre_rank.size() * sizeof(int), cudaMemcpyHostToDevice);
    flat_proj%(id)s_pre_rank.clear();

    // weights
    cudaMalloc((void**)&gpu_w, overallSynapses * sizeof(double));
    w_dirty = true; // enforce update
"""