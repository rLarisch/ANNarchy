header_template = """#ifndef __ANNARCHY_H__
#define __ANNARCHY_H__

#include <string>
#include <vector>
#include <deque>
#include <iostream>
#include <sstream>
#include <fstream>
#include <omp.h>
#include <cstdlib>
#include <stdlib.h>
#include <string.h>
#include <random>

/*
 * Built-in functions
 *
 */
#define positive(x) (x>0.0? x : 0.0)
#define negative(x) (x<0.0? x : 0.0)
#define clip(x, a, b) (x<a? a : (x>b? b :x))

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
extern std::vector< std::mt19937 >  rng;


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
 * Simulation methods
 *
*/

void initialize(double _dt) ;

void run(int nbSteps);

void step();


/*
 * Time export
 *
*/
int getTime() ;
void setTime(int t_) ;

double getDt() ;
void setDt(double dt_);

/*
 * Number of threads
 *
*/
void setNumThreads(int threads);

#endif
"""