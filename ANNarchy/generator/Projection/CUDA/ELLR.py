#===============================================================================
#
#     ELLR.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2021  Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
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
init_launch_config = """
        // Generate the kernel launch configuration
        _threads_per_block = 32;
        auto tmp_blocks = static_cast<int>(ceil(static_cast<double>(nb_dendrites())/32.0));
        _nb_blocks = static_cast<unsigned short int>( std::min<unsigned int>(tmp_blocks, 65535) );

    #ifdef _DEBUG
        std::cout << "Kernel configuration: " << _nb_blocks << ", " << _threads_per_block << std::endl;
    #endif
"""

attribute_decl = {
    'local': """
    // Local %(attr_type)s %(name)s
    std::vector< %(type)s > %(name)s;
    %(type)s* gpu_%(name)s;
    bool %(name)s_dirty;
""",
    'semiglobal': """
    // Semiglobal %(attr_type)s %(name)s
    std::vector< %(type)s >  %(name)s ;
    %(type)s* gpu_%(name)s;
    bool %(name)s_dirty;
""",
    'global': """
    // Global %(attr_type)s %(name)s
    %(type)s %(name)s;
    %(type)s* gpu_%(name)s;
    bool %(name)s_dirty;
"""
}

attribute_cpp_init = {
    'local': """
        // Local %(attr_type)s %(name)s
        %(name)s = init_matrix_variable<%(type)s>(%(init)s);
        gpu_%(name)s = init_matrix_variable_gpu<%(type)s>(%(name)s);
        %(name)s_dirty = true;
""",
    'semiglobal': """
        // Semiglobal %(attr_type)s %(name)s
        %(name)s = init_vector_variable<%(type)s>(%(init)s);
        gpu_%(name)s = init_vector_variable_gpu<%(type)s>(%(name)s);
        %(name)s_dirty = true;
""",
    'global': """
        // Global %(attr_type)s %(name)s
        %(name)s = static_cast<%(type)s>(%(init)s);
        cudaMalloc((void**)&gpu_%(name)s, sizeof(%(type)s));
        %(name)s_dirty = true;
"""
}

attribute_cpp_size = {
    'local': """
        // Local %(attr_type)s %(name)s
        size_in_bytes += sizeof(bool);
        size_in_bytes += sizeof(%(ctype)s*);
        size_in_bytes += sizeof(std::vector<%(ctype)s>);
        size_in_bytes += sizeof(%(ctype)s) * %(name)s.capacity();       
""",
    'semiglobal': """
        // Semiglobal %(attr_type)s %(name)s
        size_in_bytes += sizeof(bool);
        size_in_bytes += sizeof(%(ctype)s*);
        size_in_bytes += sizeof(std::vector<%(ctype)s>);
        size_in_bytes += sizeof(%(ctype)s) * %(name)s.capacity();
""",
    'global': """
        // Global
        size_in_bytes += sizeof(bool);
        size_in_bytes += sizeof(%(ctype)s*);
        size_in_bytes += sizeof(%(ctype)s);
"""
}

attribute_host_to_device = {
    'local': """
        // %(name)s: local
        if ( %(name)s_dirty )
        {
        #ifdef _DEBUG
            std::cout << "HtoD: %(name)s ( proj%(id)s )" << std::endl;
        #endif
            cudaMemcpy( gpu_%(name)s, %(name)s.data(), %(name)s.size() * sizeof( %(type)s ), cudaMemcpyHostToDevice);
            %(name)s_dirty = false;
        #ifdef _DEBUG
            cudaError_t err = cudaGetLastError();
            if ( err!= cudaSuccess )
                std::cout << "  error: " << cudaGetErrorString(err) << std::endl;
        #endif
        }
""",
    'semiglobal': """
        // %(name)s: semiglobal
        if ( %(name)s_dirty )
        {
        #ifdef _DEBUG
            std::cout << "HtoD: %(name)s ( proj%(id)s )" << std::endl;
        #endif
            cudaMemcpy( gpu_%(name)s, %(name)s.data(), %(name)s.size() * sizeof( %(type)s ), cudaMemcpyHostToDevice);
            %(name)s_dirty = false;
        #ifdef _DEBUG
            cudaError_t err = cudaGetLastError();
            if ( err!= cudaSuccess )
                std::cout << "  error: " << cudaGetErrorString(err) << std::endl;
        #endif
        }
""",
    'global': """
        // %(name)s: global
        if ( %(name)s_dirty )
        {
        #ifdef _DEBUG
            std::cout << "HtoD: %(name)s ( proj%(id)s )" << std::endl;
        #endif
            cudaMemcpy( gpu_%(name)s, &%(name)s, sizeof( %(type)s ), cudaMemcpyHostToDevice);
            %(name)s_dirty = false;
        #ifdef _DEBUG
            cudaError_t err = cudaGetLastError();
            if ( err!= cudaSuccess )
                std::cout << "  error: " << cudaGetErrorString(err) << std::endl;
        #endif
        }
"""
}

attribute_device_to_host = {
    'local': """
            // %(name)s: local
        #ifdef _DEBUG
            std::cout << "DtoH: %(name)s ( proj%(id)s )" << std::endl;
        #endif
            cudaMemcpy( %(name)s.data(), gpu_%(name)s, %(name)s.size() * sizeof( %(type)s ), cudaMemcpyDeviceToHost);
        #ifdef _DEBUG
            cudaError_t err_%(name)s = cudaGetLastError();
            if ( err_%(name)s != cudaSuccess )
                std::cout << "  error: " << cudaGetErrorString(err_%(name)s) << std::endl;
        #endif
""",
    'semiglobal': "",
    'global': ""
}

#
#   Synaptic delays
#
delay = {
    'uniform': {
        'declare': """
    // Uniform delay
    int delay ;""",
        'pyx_struct': """
        # Non-uniform delay
        int delay""",
        'init': "delay = delays[0][0];",
        'pyx_wrapper_init': """
        proj%(id_proj)s.delay = syn.uniform_delay""",
        'pyx_wrapper_accessor': """
    # Access to non-uniform delay
    def get_delay(self):
        return proj%(id_proj)s.delay
    def get_dendrite_delay(self, idx):
        return proj%(id_proj)s.delay
    def set_delay(self, value):
        proj%(id_proj)s.delay = value
"""
    }
}

#
# Implement the continuous transmission for rate-code synapses.
#
rate_psp_kernel = {
    'body': {
        'sum':"""
__global__ void cu_proj%(id_proj)s_psp_ell_r( int post_size, %(conn_args)s%(add_args)s, %(float_prec)s* %(target_arg)s ) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    while( i < post_size ) {
        
        %(float_prec)s localSum = %(thread_init)s;

        for(int j =0; j < rl[i]; j++)
            localSum += %(psp)s

        %(target_arg)s%(post_index)s += localSum;

        i += gridDim.x * blockDim.x;
    }
}
"""        
    },
    'header': """__global__ void cu_proj%(id)s_psp_ell_r( int post_size, %(conn_args)s%(add_args)s, %(float_prec)s* %(target_arg)s );
""",
    'call': """
    // proj%(id_proj)s: pop%(id_pre)s -> pop%(id_post)s
    if ( pop%(id_post)s._active && proj%(id_proj)s._transmission ) {

        cu_proj%(id_proj)s_psp_ell_r<<< proj%(id_proj)s._nb_blocks, proj%(id_proj)s._threads_per_block >>>(
                       proj%(id_proj)s.nb_dendrites(),
                       /* ranks and offsets */
                       %(conn_args)s
                       /* computation data */
                       %(add_args)s
                       /* result */
                       %(target_arg)s );

    #ifdef _DEBUG
        auto err = cudaGetLastError();
        if ( err != cudaSuccess ) {
            std::cout << "cu_proj%(id_proj)s_psp: " << cudaGetErrorString(err) << std::endl;
        }
    #endif
    }
""",
    'thread_init': {
        'float': {
            'sum': "0.0f",
            'min': "FLT_MAX",
            'max': "FLT_MIN",
            'mean': "0.0f"
        },
        'double': {
            'sum': "0.0",
            'min': "DBL_MAX",
            'max': "DBL_MIN",
            'mean': "0.0"
        }
    }    
}

synapse_update = {
    # Update of global synaptic equations, consist of body (annarchyDevice.cu),
    # header and call semantic (take place in ANNarchyHost.cu)
    'global': {
        'body': """
// gpu device kernel for projection %(id)s
__global__ void cuProj%(id)s_global_step( /* default params */
                              %(float_prec)s dt
                              /* additional params */
                              %(kernel_args)s,
                              /* plasticity enabled */
                              bool plasticity )
{
%(pre_loop)s
%(global_eqs)s
}
""",
        'header': """__global__ void cuProj%(id)s_global_step( %(float_prec)s dt %(kernel_args)s, bool plasticity);
""",
        'call': """
        // global update
        cuProj%(id_proj)s_global_step<<< 1, 1, 0, proj%(id_proj)s.stream>>>(
            proj%(id_proj)s.nb_dendrites(),
            /* default args*/
            _dt
            /* kernel args */
            %(kernel_args_call)s
            /* synaptic plasticity */
            , proj%(id_proj)s._plasticity
        );

    #ifdef _DEBUG
        cudaDeviceSynchronize();
        err = cudaGetLastError();
        if ( global_step != cudaSuccess) {
            std::cout << "proj%(id_proj)s_step: " << cudaGetErrorString( err ) << std::endl;
        }
    #endif
"""
    },

    # Update of semiglobal synaptic equations, consist of body (annarchyDevice.cu),
    # header and call semantic (take place in ANNarchyHost.cu)
    'semiglobal': {
        'body': """
// gpu device kernel for projection %(id)s
__global__ void cuProj%(id)s_semiglobal_step( /* default params */
                              int post_size, int *post_rank, int *row_ptr, int* pre_rank, %(float_prec)s dt
                              /* additional params */
                              %(kernel_args)s,
                              /* plasticity enabled */
                              bool plasticity )
{
    int i = threadIdx.x + blockIdx.x*blockDim.x;
    

%(pre_loop)s
    while ( i < post_size ) {
%(semiglobal_eqs)s

        i += gridDim.x * blockDim.x;
    }
}
""",
        'header': """__global__ void cuProj%(id)s_semiglobal_step( int post_size, int *post_rank, int *row_ptr, int* pre_rank, %(float_prec)s dt %(kernel_args)s, bool plasticity);
""",
        'call': """
        // semiglobal update
        cuProj%(id_proj)s_semiglobal_step<<< proj%(id_proj)s._nb_blocks, proj%(id_proj)s._threads_per_block, 0, proj%(id_proj)s.stream >>>(
            proj%(id_proj)s.nb_dendrites(),
            /* default args*/
            proj%(id_proj)s.gpu_post_rank, proj%(id_proj)s.gpu_row_ptr, proj%(id_proj)s.gpu_pre_rank, _dt
            /* kernel args */
            %(kernel_args_call)s
            /* synaptic plasticity */
            , proj%(id_proj)s._plasticity
        );

    #ifdef _DEBUG
        cudaDeviceSynchronize();
        err = cudaGetLastError();
        if ( err != cudaSuccess) {
            std::cout << "proj%(id_proj)s_semiglobal_step: " << cudaGetErrorString( err ) << std::endl;
        }
    #endif
"""
    },

    # Update of local synaptic equations, consist of body (annarchyDevice.cu),
    # header and call semantic (take place in ANNarchyHost.cu)
    'local': {
        'body': """
// gpu device kernel for projection %(id)s
__global__ void cuProj%(id)s_local_step( /* default params */
                              int post_size, int *post_rank, int *pre_rank, int* rl, %(float_prec)s dt
                              /* additional params */
                              %(kernel_args)s,
                              /* plasticity enabled */
                              bool plasticity )
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
%(pre_loop)s

    // Updating local variables of projection %(id)s
    while ( i < post_size )
    {
        for ( int j = 0; j < rl[i]; j++ ) {
%(local_eqs)s
        }

        i += blockDim.x * gridDim.x;
    }
}
""",
        'header': """__global__ void cuProj%(id)s_local_step( int post_size, int *post_rank, int *pre_rank, int* rl, %(float_prec)s dt %(kernel_args)s, bool plasticity);
""",
        'call': """
        // local update
        cuProj%(id_proj)s_local_step<<< 1, 32, 0, proj%(id_proj)s.stream >>>(
            /* default args*/
            proj%(id_proj)s.nb_dendrites(), proj%(id_proj)s.gpu_post_ranks_, proj%(id_proj)s.gpu_col_idx_, proj%(id_proj)s.gpu_rl_, _dt
            /* kernel args */
            %(kernel_args_call)s
            /* synaptic plasticity */
            , proj%(id_proj)s._plasticity
        );

    #ifdef _DEBUG
        cudaDeviceSynchronize();
        err = cudaGetLastError();
        if ( err != cudaSuccess) {
            std::cout << "proj%(id_proj)s_step: " << cudaGetErrorString( err ) << std::endl;
        }
    #endif
""",
    },

    # call semantic for global, semiglobal and local kernel
    'call': """
    // proj%(id_proj)s: pop%(pre)s -> pop%(post)s
    if ( proj%(id_proj)s._transmission && proj%(id_proj)s._update && proj%(id_proj)s._plasticity && ( (t - proj%(id_proj)s._update_offset)%%proj%(id_proj)s._update_period == 0L)) {
        %(float_prec)s _dt = dt * proj%(id_proj)s._update_period;
#ifdef _DEBUG
    cudaError_t err;
#endif
%(global_call)s
int nb_blocks;
%(semiglobal_call)s
%(local_call)s
    }
"""
}

conn_templates = {
    # launch config
    'launch_config': init_launch_config,

    # accessors
    'attribute_decl': attribute_decl,
    'attribute_cpp_init': attribute_cpp_init,
    'attribute_cpp_size': attribute_cpp_size,
    'host_to_device': attribute_host_to_device,
    'device_to_host': attribute_device_to_host,
    'delay': delay,

    # operations
    'rate_psp': rate_psp_kernel,
    'synapse_update': synapse_update
}