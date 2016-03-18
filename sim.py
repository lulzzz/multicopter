from __future__ import division

import math

def simulate(dt, v0, v1, v2, vb_0, vb_1, vb_2, R, i_0, i_1, i_2, L):
    zero_current_ports = set()
    #print 'START', v0, v1, v2
    while dt:
        #print i_0, i_1, i_2, zero_current_ports
        realv_0 = v0 if not isinstance(v0, tuple) else (v0[1] if i_0 < 0 else v0[0])
        realv_1 = v1 if not isinstance(v1, tuple) else (v1[1] if i_1 < 0 else v1[0])
        realv_2 = v2 if not isinstance(v2, tuple) else (v2[1] if      i_2 < 0 else v2[0])
        
        vr_0 = i_0*R
        vr_1 = i_1*R
        vr_2 = i_2*R
        
        # realv_0 - v_c = vl_0 + vr_0 + vb_0
        # realv_1 - v_c = vl_1 + vr_1 + vb_1
        # realv_2 - v_c = vl_2 + vr_2 + vb_2
        # vl_0 + vl_1 + vl_2 = 0
        
        # realv_0 - vr_0 - vb_0 = vl_0 + v_c
        # realv_1 - vr_1 - vb_1 = vl_1 + v_c
        # realv_2 - vr_2 - vb_2 = vl_2 + v_c
        
        if zero_current_ports == set([]):
            v_c = ((realv_0 - vr_0 - vb_0) + (realv_1 - vr_1 - vb_1) + (realv_2 - vr_2 - vb_2))/3
            vl_0 = (realv_0 - vr_0 - vb_0) - v_c
            vl_1 = (realv_1 - vr_1 - vb_1) - v_c
            vl_2 = (realv_2 - vr_2 - vb_2) - v_c
        elif zero_current_ports == set([2]):
            v_c = ((realv_0 - vr_0 - vb_0) + (realv_1 - vr_1 - vb_1))/2
            vl_0 = (realv_0 - vr_0 - vb_0) - v_c
            vl_1 = (realv_1 - vr_1 - vb_1) - v_c
            vl_2 = 0
            realv_2 = vl_2 + v_c + vb_2 + vr_2
            assert v2[0] <= realv_2 <= v2[1], realv_2
        else:
            assert False
        
        time_to_zero = dt, None
        if isinstance(v0, tuple) and vl_0 and -i_0*L/vl_0 >= 0:
            time_to_zero = min(time_to_zero, (-i_0*L/vl_0, 0))
        if isinstance(v1, tuple) and vl_1 and -i_1*L/vl_1 >= 0:
            time_to_zero = min(time_to_zero, (-i_1*L/vl_1, 1))
        if isinstance(v2, tuple) and vl_2 and -i_2*L/vl_2 >= 0:
            time_to_zero = min(time_to_zero, (-i_2*L/vl_2, 2))
        
        real_dt, zeroed_port = time_to_zero
        
        i_0 += real_dt * vl_0/L
        i_1 += real_dt * vl_1/L 
        i_2 += real_dt * vl_2/L 
        
        if zeroed_port == 0: assert False
        if zeroed_port == 1: assert False
        if zeroed_port == 2:
            i_1 = -i_0
            i_2 = 0
        
        dt -= real_dt
        
        zero_current_ports.add(zeroed_port)
    return (i_0, i_1, i_2), (realv_0, realv_1, realv_2)

class MotorModel(object):
    # 14 magnet poles, 12 stator poles = ???
    CONV = 7 # electrical radians/radian
    
    L = 50e-6 # inductance, henries
    R = 0.2 # ohms
    
    mechanical_K_v = 920 / 60 * 2*math.pi # motor constant, radians/s/volt
    K_v = mechanical_K_v*CONV # electrical motor constant, electrical radians/s/volt
    mechanical_I = .1*.1 # XXX guess # moment of inertia, kg m^2 = joule/(radian/s)^2
    I = mechanical_I/CONV**2 # electrical moment of inertia, joule/(electrical radian/s)^2
    
    def __init__(self):
        self.omega = 0 # electrical angular velocity
        self.theta = 0 # electrical angle
        
        self.i_0 = 0 # current into port 0
        self.i_1 = 0 # current into port 1
    
    def step(self, dt, v0, v1, v2): # v? can be ranges to signal that they're clamped but otherwise high-Z
        assert isinstance(v0, tuple) + isinstance(v1, tuple) + isinstance(v2, tuple) <= 1
        
        tau = 0
        
        tau += self.i_0 / self.K_v * math.sin(self.theta)
        tau += self.i_1 / self.K_v * math.sin(self.theta - 2*math.pi/3)
        i_2 = - self.i_0 - self.i_1 # i_0 + i_1 + i_2 = 0
        tau += i_2 / self.K_v * math.sin(self.theta - 2*math.pi*2/3)
        tau += -1e-3 * self.omega #* abs(self.omega)
        
        self.theta += dt * self.omega
        self.omega += dt * tau/self.I
        
        vb_0 = 1/self.K_v * self.omega * math.sin(self.theta)
        vb_1 = 1/self.K_v * self.omega * math.sin(self.theta - 2*math.pi/3)
        vb_2 = 1/self.K_v * self.omega * math.sin(self.theta - 2*math.pi*2/3)
        
        (self.i_0, self.i_1, self.i_2), vfinal = simulate(dt, v0, v1, v2, vb_0, vb_1, vb_2, self.R, self.i_0, self.i_1, i_2, self.L)
        self.voltages = vfinal

m = MotorModel()

rate = 30
vmax = 3.7*4
dt = 1e-6
def controller():
    return (
        vmax*(.5+.5*math.sin(rate*t - 2*math.pi*0/3)),
        vmax*(.5+.5*math.sin(rate*t - 2*math.pi*1/3)),
        vmax*(.5+.5*math.sin(rate*t - 2*math.pi*2/3)),
    )

thetas = []
omegas = []
voltages = []
currents = []
for i in xrange(100000):
    t = dt * i
    if (i-1)//1000 != i//1000: print i
    m.step(dt, *controller())
    thetas.append(m.theta % (2*math.pi))
    omegas.append(m.omega)
    voltages.append(m.voltages)
    currents.append((m.i_0, m.i_1, m.i_2))


from matplotlib import pyplot

ax1 = pyplot.subplot(4, 1, 1)
ax1.plot(omegas)
ax1.set_ylabel('Omega')

ax1 = pyplot.subplot(4, 1, 2)
ax1.plot(thetas)
ax1.set_ylabel('Theta')

ax2 = pyplot.subplot(4, 1, 3, sharex=ax1)
for v in zip(*voltages):
    ax2.plot(v)
ax2.set_ylabel('Voltages')

ax2 = pyplot.subplot(4, 1, 4, sharex=ax1)
for v in zip(*currents):
    ax2.plot(v)
ax2.set_ylabel('Currents')

pyplot.show()
