from __future__ import division
import numpy as np; npl = np.linalg


class Pose(object):
    """
    lin: position 3-vector in A-coordinates
    ang: attitude unit-quaternion [x, y, z, w] of B-coordinates relative to A-coordinates

    """
    def __init__(self, position, attitude):
        self.lin = np.array(position, dtype=np.float64)
        self.ang = np.array(attitude, dtype=np.float64) / npl.norm(attitude)

    def rotate_vector(self, v, reverse=False):
        """
        Applies the attitude quaternion to a vector v, i.e. rotates v from basis B to A.
        If reverse is set to True, the inverse quaternion is applied instead.

        """
        uv = 2*np.cross(self.ang[:-1], v)
        if reverse: return v - self.ang[-1]*uv + np.cross(self.ang[:-1], uv)
        else: return v + self.ang[-1]*uv + np.cross(self.ang[:-1], uv)

    def transform_point(self, p, reverse=False):
        """
        Rotates p and adds the position vector for origin offset, i.e. transforms p from B to A coordinates.
        If reverse is set to True, the inverse transformation of the pose is applied instead.

        """
        if reverse: return self.rotate_vector(p - self.lin, True)
        return self.lin + self.rotate_vector(p, False)


class Twist(object):
    """
    lin: velocity 3-vector
    ang: angular velocity 3-vector

    """
    def __init__(self, velocity, angvel):
        self.lin = np.array(velocity, dtype=np.float64)
        self.ang = np.array(angvel, dtype=np.float64)


class State(object):
    """
    Rigid-body state of a multicopter at a specific time.

    Body-coordinates are Forward-Left-Up with origin at the center of mass (COM).
    World-coordinates are East-North-Up (ENU) with origin at the location of system start-up.

    pose:  Pose object with position of the COM expressed in world-coordinates
           and attitude of body-coordinates relative to world-coordinates
    twist: Twist object with linear velocity of the COM and angular velocity of
           body-frame relative to world-frame both expressed in body-coordinates
    time:  timestamp for this state

    """
    def __init__(self, pose, twist, time):
        self.pose = pose
        self.twist = twist
        self.time = float(time)


class Wrench(object):
    """
    lin: force 3-vector
    ang: torque 3-vector

    """
    def __init__(self, force, torque):
        self.lin = np.array(force, dtype=np.float64)
        self.ang = np.array(torque, dtype=np.float64)


class Accel(object):
    """
    lin: acceleration 3-vector
    ang: angular acceleration 3-vector

    """
    def __init__(self, acceleration, angaccel):
        self.lin = np.array(acceleration, dtype=np.float64)
        self.ang = np.array(angaccel, dtype=np.float64)


class StateDeriv(object):
    """
    Derivative of a rigid-body state at a specific time.

    pose_deriv:  Twist object with the derivative of the state's pose
    twist_deriv: Accel object with the derivative of the state's twist
    time:        timestamp for this state derivative

    """
    def __init__(self, pose_deriv, twist_deriv, time):
        self.pose_deriv = pose_deriv
        self.twist_deriv = twist_deriv
        self.time = float(time)


def quaternion_multiply(ql, qr):
    """
    Returns the quaternion multiplication ql * qr all in the form [x, y, z, w].

    """
    return np.array((ql[0]*qr[3] + ql[1]*qr[2] - ql[2]*qr[1] + ql[3]*qr[0],
                    -ql[0]*qr[2] + ql[1]*qr[3] + ql[2]*qr[0] + ql[3]*qr[1],
                     ql[0]*qr[1] - ql[1]*qr[0] + ql[2]*qr[3] + ql[3]*qr[2],
                    -ql[0]*qr[0] - ql[1]*qr[1] - ql[2]*qr[2] + ql[3]*qr[3]))

def rotvec_from_quaternion(q):
    """
    Returns the rotation vector corresponding to the quaternion q = [x, y, z, w].
    A rotation vector is the product of the angle of rotation (0 to pi) and
    axis of rotation (unit vector) of an SO3 quantity like a quaternion.

    """
    q = np.array(q, dtype=np.float64)
    sina2 = npl.norm(q[:-1])
    if np.isclose(sina2, 0): return np.zeros(3, dtype=np.float64)
    if q[-1] < 0: q = -q
    return 2*np.arccos(q[-1]) * q[:-1]/sina2

def quaternion_from_rotvec(r):
    """
    Returns the quaternion [x, y, z, w] equivalent to the given rotation vector r.

    """
    angle = np.mod(npl.norm(r), 2*np.pi)
    if np.isclose(angle, 0): return np.array([0, 0, 0, 1], dtype=np.float64)
    return np.concatenate((np.sin(angle/2)*np.divide(r, angle), [np.cos(angle/2)]))

def euler_from_quaternion(q):
    """
    Returns the [roll, pitch, yaw] associated with the quaternion q = [x, y, z, w].

    """
    return np.array((np.arctan2(2*(q[3]*q[0] + q[1]*q[2]), 1 - 2*(q[0]**2 + q[1]**2)),
                     np.arcsin(2*(q[3]*q[1] - q[2]*q[0])),
                     np.arctan2(2*(q[3]*q[2] + q[0]*q[1]), 1 - 2*(q[1]**2 + q[2]**2))))