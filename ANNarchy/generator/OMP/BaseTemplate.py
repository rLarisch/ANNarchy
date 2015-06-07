omp_header_template = """#ifndef __ANNARCHY_H__
#define __ANNARCHY_H__

#include <string>
#include <vector>
#include <algorithm>
#include <map>
#include <deque>
#include <iostream>
#include <sstream>
#include <fstream>
#include <cstdlib>
#include <stdlib.h>
#include <string.h>
#include <random>
%(include_omp)s

/*
 * Built-in functions
 *
 */
#define positive(x) (x>0.0? x : 0.0)
#define negative(x) (x<0.0? x : 0.0)
#define clip(x, a, b) (x<a? a : (x>b? b :x))

/*
 * Custom functions
 *
 */
%(custom_func)s

/*
 * Structures for the populations
 *
 */
%(pop_struct)s
/*
 * Structures for the projections
 *
 */
%(proj_struct)s


/*
 * Internal data
 *
*/
extern double dt;
extern long int t;
extern std::mt19937  rng;


/*
 * Declaration of the populations
 *
 */
%(pop_ptr)s

/*
 * Declaration of the projections
 *
 */
%(proj_ptr)s


/*
 * Recorders
 *
 */
class Monitor
{
public:
    Monitor(std::vector<int> ranks, int period, long int offset){
        this->ranks = ranks;
        this->period = period;
        this->offset = offset;
        if(this->ranks.size() ==1 && this->ranks[0]==-1) // All neurons should be recorded
            this->partial = false;
        else
            this->partial = true;
    };

    virtual void record() {std::cout << "recording" << std::endl;};

    // Attributes
    bool partial;
    std::vector<int> ranks;
    int period;
    long int offset;

};
%(record_classes)s

extern std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder);
void removeRecorder(Monitor* recorder);

/*
 * Simulation methods
 *
*/

void initialize(double _dt, long int seed) ;

void run(int nbSteps);

int run_until(int steps, std::vector<int> populations, bool or_and);

void step();


/*
 * Time export
 *
*/
long int getTime() ;
void setTime(long int t_) ;

double getDt() ;
void setDt(double dt_);

/*
 * Number of threads
 *
*/
void setNumberThreads(int threads);

#endif
"""

omp_body_template = """
#include "ANNarchy.h"
%(prof_include)s

/*
 * Internal data
 *
 */
double dt;
long int t;
std::mt19937  rng;

// Populations
%(pop_ptr)s

// Projections
%(proj_ptr)s

// Global operations
%(glops_def)s

// Recorders 
std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder){
    recorders.push_back(recorder);
}
void removeRecorder(Monitor* recorder){
    for(int i=0; i<recorders.size(); i++){
        if(recorders[i] == recorder){
            recorders.erase(recorders.begin()+i);
            break;
        }
    }
}

// Simulate the network for the given number of steps
void run(int nbSteps) {
%(prof_run_pre)s
    for(int i=0; i<nbSteps; i++) {
        step();
    }
%(prof_run_post)s

}

int run_until(int steps, std::vector<int> populations, bool or_and)
{

%(run_until)s

}

// Initialize the internal data and random numbers generators
void initialize(double _dt, long int seed) {
%(initialize)s
}

// Step method. Generated by ANNarchy.
void step()
{
%(prof_step_pre)s

    double sum;
    int rk_pre, rk_post, i, j, rk_j, nb_post;
    
    ////////////////////////////////
    // Presynaptic events
    ////////////////////////////////
%(reset_sums)s
%(compute_sums)s

    ////////////////////////////////
    // Update random distributions
    ////////////////////////////////
%(random_dist_update)s

    ////////////////////////////////
    // Update neural variables
    ////////////////////////////////
%(update_neuron)s

    ////////////////////////////////
    // Delay outputs
    ////////////////////////////////
%(delay_code)s

    ////////////////////////////////
    // Global operations (min/max/mean)
    ////////////////////////////////
%(update_globalops)s

    ////////////////////////////////
    // Update synaptic variables
    ////////////////////////////////
%(update_synapse)s    

    ////////////////////////////////
    // Postsynaptic events
    ////////////////////////////////
%(post_event)s

    ////////////////////////////////
    // Structural plasticity
    ////////////////////////////////
%(structural_plasticity)s

    ////////////////////////////////
    // Recording
    ////////////////////////////////
    for(int i=0; i < recorders.size(); i++){
        recorders[i]->record();
    }

    ////////////////////////////////
    // Increase internal time
    ////////////////////////////////
    t++;
}


/*
 * Access to time and dt
 *
*/
long int getTime() {return t;}
void setTime(long int t_) { t=t_;}
double getDt() { return dt;}
void setDt(double dt_) { dt=dt_;}

/*
 * Number of threads
 *
*/
void setNumberThreads(int threads)
{
    %(set_number_threads)s
}
"""

omp_run_until_template = {
    'default':
"""
    run(steps);
    return steps;
""",
    'body': 
"""
    bool stop = false;
    bool pop_stop = false;
    int nb = 0;
    for(int n = 0; n < steps; n++)
    {
        step();
        nb++;
        stop = or_and;
        for(int i=0; i<populations.size();i++)
        {
            // Check all populations
            switch(populations[i]){
%(run_until)s
            }

            // Accumulate the results
            if(or_and)
                stop = stop && pop_stop;
            else
                stop = stop || pop_stop;
        }
        if(stop)
            break;
    }
    return nb;

"""
}

omp_initialize_template = """
%(prof_init)s

    // Internal variables
    dt = _dt;
    t = (long int)(0);

    // Random number generators
    if(seed==-1){
        rng = std::mt19937(time(NULL));
    }
    else{
        rng = std::mt19937(seed);
    }

    // Populations
%(pop_init)s

    // Projections
%(proj_init)s
"""

cuda_header_template = """#ifndef __ANNARCHY_H__
#define __ANNARCHY_H__

#include <string>
#include <vector>
#include <algorithm>
#include <map>
#include <deque>
#include <iostream>
#include <sstream>
#include <fstream>
#include <cstdlib>
#include <stdlib.h>
#include <string.h>

#include <cuda_runtime_api.h>
#include <curand_kernel.h>

/*
 * Structures for the populations
 *
 */
%(pop_struct)s
/*
 * Structures for the projections
 *
 */
%(proj_struct)s

/*
 * Internal data
 *
*/
extern double dt;
extern long int t;

/*
 * Declaration of the populations
 *
 */
%(pop_ptr)s

/*
 * Declaration of the projections
 *
 */
%(proj_ptr)s

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

/*
 * Recorders
 *
 */
class Monitor
{
public:
    Monitor(std::vector<int> ranks, int period, long int offset){
        this->ranks = ranks;
        this->period = period;
        this->offset = offset;
        if(this->ranks.size() ==1 && this->ranks[0]==-1) // All neurons should be recorded
            this->partial = false;
        else
            this->partial = true;
    };

    virtual void record() {std::cout << "recording" << std::endl;};

    // Attributes
    bool partial;
    std::vector<int> ranks;
    int period;
    long int offset;

};
%(record_classes)s

extern std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder);
void removeRecorder(Monitor* recorder);

/*
 * Simulation methods
 *
*/

void initialize(double _dt, long seed) ;

void run(int nbSteps);

inline int run_until(int steps, std::vector<int> populations, bool or_and) {
    printf("NOT IMPLEMENTED ...");
}

void step();

inline void setNumberThreads(int) {
    // Dummy function
}

/*
 * Time export
 *
*/
long int getTime() ;
void setTime(long int t_) ;

double getDt() ;
void setDt(double dt_);

#endif
"""

cuda_body_template = """
#ifdef __CUDA_ARCH__
/***********************************************************************************/
/*                                                                                 */
/*                                                                                 */
/*          DEVICE - code                                                          */
/*                                                                                 */
/*                                                                                 */
/***********************************************************************************/
#include <curand_kernel.h>
#include <float.h>

// global time step
__constant__ long int t;

/****************************************
 * init random states                   *
 ****************************************/
__global__ void rng_setup_kernel( int N, curandState* states, unsigned long seed )
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;

    if( tid < N )
    {
        curand_init( seed, tid, 0, &states[ tid ] );
    }
}

/****************************************
 * inline functions                     *
 ****************************************/
__device__ __forceinline__ double positive( double x ) { return (x>0) ? x : 0; }
__device__ __forceinline__ double negative( double x ) { return x<0.0? x : 0.0; }
__device__ __forceinline__ double clip(double x, double a, double b) { return x<a? a : (x>b? b :x); }

/****************************************
 * custom functions                     *
 ****************************************/
%(custom_func)s

/****************************************
 * updating neural variables            *
 ****************************************/
%(pop_kernel)s
 
/****************************************
 * weighted sum kernels                 *
 ****************************************/
%(psp_kernel)s

/****************************************
 * update synapses kernel               *
 ****************************************/
%(syn_kernel)s

/****************************************
 * global operations kernel             *
 ****************************************/
%(glob_ops_kernel)s

#else
#include "ANNarchy.h"
#include <math.h>

// cuda specific header
#include <cuda_runtime_api.h>
#include <curand.h>
#include <float.h>

/***********************************************************************************/
/*                                                                                 */
/*                                                                                 */
/*          HOST - code                                                            */
/*                                                                                 */
/*                                                                                 */
/***********************************************************************************/
// kernel config
%(kernel_config)s

// RNG
__global__ void rng_setup_kernel( int N, curandState* states, unsigned long seed );

void init_curand_states( int N, curandState* states, unsigned long seed ) {
    int numThreads = 64;
    int numBlocks = ceil (double(N) / double(numThreads));

    rng_setup_kernel<<< numBlocks, numThreads >>>( N, states, seed);
}

/*
 * Internal data
 *
 */
double dt;
long int t;

// Recorders 
std::vector<Monitor*> recorders;
void addRecorder(Monitor* recorder){
    recorders.push_back(recorder);
}
void removeRecorder(Monitor* recorder){
    for(int i=0; i<recorders.size(); i++){
        if(recorders[i] == recorder){
            recorders.erase(recorders.begin()+i);
            break;
        }
    }
}

// Populations
%(pop_ptr)s

// Projections
%(proj_ptr)s

// Stream configuration (available for CC > 3.x devices)
// NOTE: if the CC is lower then 3.x modification of stream
//       parameter (4th arg) is automatically ignored by CUDA
%(stream_setup)s

// Helper function, to show progress
void progress(int i, int nbSteps) {
    double tInMs = nbSteps * dt;
    if ( tInMs > 1000.0 )
        std::cout << "\\rSimulate " << (int)(tInMs/1000.0) << " s: " << (int)( (double)(i+1)/double(nbSteps) * 100.0 )<< " finished.";
    else
        std::cout << "\\rSimulate " << tInMs << " ms: " << (int)( (double)(i+1)/double(nbSteps) * 100.0 )<< " finished.";
    std::flush(std::cout);
}

/**
 *  Implementation remark (27.02.2015, HD) to: run(int), step() and single_step()
 *
 *  we have two functions in ANNarchy to run simulation code: run(int) and step(). The latter one to
 *  run several steps at once, the other one just a single step. On CUDA I face the problem, that I
 *  propably need to update variables before step() and definitly changed variables after step().
 *  run(int) calls step() normally, if I add transfer codes in step(), run(N) would end up in N
 *  back transfers from GPUs, whereas we only need the last one.
 *  As solution I renamed step() to single_step(), the interface behaves as OMP side and I only
 *  transfer at begin and at end, as planned.
 */
void single_step(); // function prototype

// Simulate the network for the given number of steps
void run(int nbSteps) {
%(host_device_transfer)s

    stream_assign();

    // simulation loop
    for(int i=0; i<nbSteps; i++) {
        single_step();
        //progress(i, nbSteps);
    }
    
    //std::cout << std::endl;
%(device_host_transfer)s
}

void step() {
%(host_device_transfer)s
    single_step();
%(device_host_transfer)s
}

// Initialize the internal data and random numbers generators
void initialize(double _dt, long seed) {

    dt = _dt;
    t = (long int)(0);
    cudaMemcpyToSymbol(t, &t, sizeof(long int));

%(device_init)s

%(projection_init)s

    // create streams
    stream_setup();
}

%(kernel_def)s

// Step method. Generated by ANNarchy. (analog to step() in OMP)
void single_step()
{

    ////////////////////////////////
    // Presynaptic events
    ////////////////////////////////
%(compute_sums)s
    cudaDeviceSynchronize();

    ////////////////////////////////
    // Reset spikes
    ////////////////////////////////

    ////////////////////////////////
    // Update neural variables
    ////////////////////////////////
%(update_neuron)s    

    ////////////////////////////////
    // Delay outputs
    ////////////////////////////////
%(delay_code)s

    ////////////////////////////////
    // Global operations (min/max/mean)
    ////////////////////////////////
%(update_globalops)s

    cudaDeviceSynchronize();

    ////////////////////////////////
    // Update synaptic variables
    ////////////////////////////////
%(update_synapse)s    

    ////////////////////////////////
    // Postsynaptic events
    ////////////////////////////////

    ////////////////////////////////
    // Recording
    ////////////////////////////////
    for(int i=0; i < recorders.size(); i++){
        recorders[i]->record();
    }
    
    ////////////////////////////////
    // Increase internal time
    ////////////////////////////////
    t++;    // host side
    // note: the first parameter is the name of the device variable
    //       for earlier releases before CUDA4.1 this was a const char*
    cudaMemcpyToSymbol(t, &t, sizeof(long int));    // device side
}


/*
 * Access to time and dt
 *
*/
long int getTime() {return t;}
void setTime(long int t_) { t=t_;}
double getDt() { return dt;}
void setDt(double dt_) { dt=dt_;}
#endif
"""

cuda_stream_setup=\
"""
cudaStream_t streams[%(nbStreams)s];

void stream_setup()
{
    for ( int i = 0; i < %(nbStreams)s; i ++ )
    {
        cudaStreamCreate( &streams[i] );
    }
}

void stream_assign()
{
%(pop_assign)s

%(proj_assign)s
}

void stream_destroy()
{
    for ( int i = 0; i < %(nbStreams)s; i ++ )
    {
        // all work finished
        cudaStreamSynchronize( streams[i] );

        // destroy
        cudaStreamDestroy( streams[i] );
    }
}
"""
