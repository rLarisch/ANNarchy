#   BOLD monitoring example
#
#   More details can be found in the recent article: TODO
#
#   author: Helge Uelo Dinkelbach, Oliver Maith
from ANNarchy import *
from ANNarchy.extensions.bold import *
from matplotlib.pylab import *
from matplotlib.image import imread

# A population of 100 izhikevich neurons
pop0 = Population(100, neuron=Izhikevich)
pop1 = Population(100, neuron=Izhikevich)

# Set noise to create some baseline activity
pop0.noise = 5.0; pop1.noise = 5.0

# Compute mean firing rate in Hz on 100ms window
pop0.compute_firing_rate(window=100.0)
pop1.compute_firing_rate(window=100.0)

# Create required monitors
mon_pop0 = Monitor(pop0, ["r"], False)
mon_pop1 = Monitor(pop1, ["r"], False)
m_bold = BoldMonitor(
    populations=[pop0, pop1],               # recorded populations
    input_variables="r",                    # mean firing rate as input
    normalize_input=[2000, 2000],           # time window to compute baseline
                                            # should be multiple of fr-window
    recorded_variables=["sum(exc)", "BOLD"] # we want to analyze the BOLD input
)

# Compile and initialize the network
compile()

# Ramp up time
simulate(1000)

# Start recording
mon_pop0.start()
mon_pop1.start()
m_bold.start()

# we manipulate the noise for the half of the neurons
simulate(5000)      # 5s with low noise
pop0.noise = 7.5
simulate(5000)      # 5s with higher noise (one population)
pop0.noise = 5
simulate(10000)     # 10s with low noise

# An example evaluation, which consists of:
# A) the mean firing activity
# B) the recorded activity which serves as input to BOLD
# C) the resulting BOLD signal
figure(figsize=(20,6))
grid = plt.GridSpec(1, 3, left=0.05, right=0.95)

# mean firing rate
ax1 = subplot(grid[0, 0])
mean_fr1 = np.mean(mon_pop0.get("r"), axis=1)
mean_fr2 = np.mean(mon_pop1.get("r"), axis=1)

ax1.plot(mean_fr1[1000:], label="pop0")
ax1.plot(mean_fr2[1000:], label="pop1")
ax1.text(-3500, 14.5, "A", fontsize=32, fontweight="bold")
legend()
ax1.set_ylabel("average mean firing rate [Hz]", fontweight="bold", fontsize=18)
ax1.set_xlabel("computation time [ms]", fontweight="bold", fontsize=18)

# BOLD input signal
ax2 = subplot(grid[0, 1])

bold_data = m_bold.get("sum(exc)")
ax2.plot(bold_data, color="k")
ax2.set_ylabel("BOLD input signal", fontweight="bold", fontsize=18)
ax2.set_xlabel("computation time [ms]", fontweight="bold", fontsize=18)
ax2.text(-3500, 0.9, "B", fontsize=32, fontweight="bold")

# BOLD input signal
ax3 = subplot(grid[0, 2])

bold_data = m_bold.get("BOLD")
ax3.plot(bold_data, color="k")
ax3.set_ylabel("BOLD signal", fontweight="bold", fontsize=18)
ax3.set_xlabel("computation time [ms]", fontweight="bold", fontsize=18)
ax3.text(-3500, 0.03, "C", fontsize=32, fontweight="bold")

show()