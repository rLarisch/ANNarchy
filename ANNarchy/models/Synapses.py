from ANNarchy.core.Synapse import Synapse
from ANNarchy.core.Global import _error

##################
### STP
##################
class STP(Synapse):
    """ 
    Synapse exhibiting short-term facilitation and depression, implemented using the model of Tsodyks, Markram et al.:

        Tsodyks, Uziel and Markram (2000) Synchrony Generation in Recurrent Networks with Frequency-Dependent Synapses. Journal of Neuroscience 20:RC50

    Note that the time constant of the post-synaptic current is set in the neuron model, not here.

    *Parameters*:

    * tau_rec = 100.0 : depression time constant (ms).
    * tau_facil = 0.01 : facilitation time constant (ms).
    * U = 0.5 : use parameter.

    *Variables*:

    * x : recovery variable.

        dx/dt = (1 - x)/tau_rec 

    * u : facilitation variable.

        du/dt = (U - u)/tau_facil 

    Both variables are integrated exactly. 

    *Pre-spike events*:

        g_target += w * u * x
        x *= (1 - u)
        u += U * (1 - u)
    """

    def __init__(self, tau_rec=100.0, tau_facil=0.01, U=0.5):

        if tau_facil<= 0.0:
            _error('tau_facil must be positive. Choose a very small value if you have to, or derive a new synapse.')
            exit(0)

        parameters = """
    tau_rec = %(tau_rec)s
    tau_facil = %(tau_facil)s
    U = %(U)s
    """ % {'tau_rec': tau_rec, 'tau_facil': tau_facil, 'U': U}
        equations = """
    }
    dx/dt = (1 - x)/tau_rec : init = 1.0, exact
    du/dt = (U - u)/tau_facil : init = %(U)s, exact   
    """ % {'tau_rec': tau_rec, 'tau_facil': tau_facil, 'U': U}
        pre_spike="""
    g_target += w * u * x
    x *= (1 - u)
    u += U * (1 - u)
    """

        Synapse.__init__(self, parameters=parameters, equations=equations, pre_spike=pre_spike)


##################
### STDP
##################
class STDP(Synapse):
    """ 
    Spike-timing dependent plasticity.

    This is the online version of the STDP rule.

        Song, S., and Abbott, L.F. (2001). Cortical development and remapping through spike timing-dependent plasticity. Neuron 32, 339-350. 

    **Parameters**:

    * tau_plus = 20.0 : time constant of the pre-synaptic trace (ms)
    * tau_minus = 20.0 : time constant of the pre-synaptic trace (ms)
    * A_plus = 0.01 : increase of the pre-synaptic trace after a spike.
    * A_minus = 0.01 : decrease of the post.synaptic trace after a spike. 
    * w_min = 0.0 : minimal value of the weight w.
    * w_max = 1.0 : maimal value of the weight w.

    **Variables**:

    * x : pre-synaptic trace.

        tau_plus  * dx/dt = -x

    * y: post-synaptic trace.

        tau_minus * dy/dt = -y

    Both variables are evaluated exactly.

    **Pre-spike events**:

        g_target += w

        x += A_plus * w_max

        w = clip(w + y, w_min , w_max)

    **Post-spike events**:

        y -= A_minus * w_max
        
        w = clip(w + x, w_min , w_max)
    """

    def __init__(self, tau_plus=20.0, tau_minus=20.0, A_plus=0.01, A_minus=0.01, w_min=0.0, w_max=1.0):

        parameters="""
            tau_plus = %(tau_plus)s : postsynaptic
            tau_minus = %(tau_minus)s : postsynaptic
            A_plus = %(A_plus)s : postsynaptic
            A_minus = %(A_minus)s : postsynaptic
            w_min = %(w_min)s : postsynaptic
            w_max = %(w_max)s : postsynaptic
        """ % {'tau_plus': tau_plus, 'tau_minus':tau_minus, 'A_plus':A_plus, 'A_minus': A_minus, 'w_min': w_min, 'w_max': w_max}

        equations = """
            tau_plus  * dx/dt = -x : exact
            tau_minus * dy/dt = -y : exact
        """
        pre_spike="""
            g_target += w
            x += A_plus * w_max
            w = clip(w + y, w_min , w_max)
        """          
        post_spike="""
            y -= A_minus * w_max
            w = clip(w + x, w_min , w_max)
        """

        Synapse.__init__(self, parameters=parameters, equations=equations, pre_spike=pre_spike, post_spike=post_spike)