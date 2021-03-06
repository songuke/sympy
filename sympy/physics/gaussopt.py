# -*- encoding: utf-8 -*-
"""
Gaussian optics.

The module implements:
    Ray transfer matrices for geometrical and gaussian optics
     See RayTransferMatrix, GeometricRay and BeamParameter
    Conjugation relations for geometrical and gaussian optics
     See geometric_conj*, gauss_conj and conjugate_gauss_beams

The conventions for the distances are as follows:
    focal distance - positive for convergent lenses
    object distance - positive for real objects
    image distance - positive for real images
"""

from sympy import atan2, Expr, I, im, Matrix, oo, pi, re, sqrt, sympify, together

###
# A,B,C,D matrices
###

class RayTransferMatrix(Matrix):
    """
    Base class for a Ray Transfer Matrix.

    It should be used if there isn't already a more
    specific subclass (mentioned in See Also).

    Arguments
    =========

    either a 2x2 matrix
      or
    the parameters A, B, C and D

    Examples
    =======

    >>> from sympy.physics.gaussopt import RayTransferMatrix, ThinLens
    >>> from sympy import Symbol, Matrix

    >>> mat = RayTransferMatrix(1,2,3,4)
    >>> mat
    [1,  2]
    [3,  4]

    >>> RayTransferMatrix( Matrix([[1,2],[3,4]]) )
    [1,  2]
    [3,  4]

    >>> mat.A
    1

    >>> f = Symbol('f')
    >>> lens = ThinLens(f)
    >>> lens
    [   1, 0]
    [-1/f, 1]

    >>> lens.C
    -1/f

    See Also
    ========

    GeometricRay, BeamParameter,
    FreeSpace, FlatRefraction, CurvedRefraction,
    FlatMirror, CurvedMirror, ThinLens

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Ray_transfer_matrix_analysis
    """

    def __init__(self, *args):
        if len(args) == 4:
            temp = ((args[0],args[1]),(args[2],args[3]))
        elif len(args) == 1 \
             and isinstance(args[0], Matrix) \
             and args[0].shape == (2,2):
            temp = args[0]
        else:
            raise ValueError('Expecting 2x2 Matrix or the 4 elements of the Matrix but got %s' % str(args))
        Matrix.__init__(self, temp)

    def __mul__(self,other):
        if isinstance(other, RayTransferMatrix):
            return RayTransferMatrix(Matrix.__mul__(self, other))
        elif isinstance(other, GeometricRay):
            return GeometricRay(Matrix.__mul__(self, other))
        elif isinstance(other, BeamParameter):
            temp = self*Matrix(((other.q,),(1,)))
            q = (temp[0]/temp[1]).expand(complex=True)
            return BeamParameter(other.wavelen,\
                                 together(re(q)),\
                                 z_r = together(im(q)))
        else:
            return Matrix.__mul__(self, other)

    @property
    def A(self):
        return self[0,0]

    @property
    def B(self):
        return self[0,1]

    @property
    def C(self):
        return self[1,0]

    @property
    def D(self):
        return self[1,1]

class FreeSpace(RayTransferMatrix):
    """
    Ray Transfer Matrix for free space.

    Arguments: Distance

    See Also: RayTransferMatrix

    Examples
    ========

    >>> from sympy.physics.gaussopt import FreeSpace
    >>> from sympy import symbols
    >>> d = symbols('d')
    >>> FreeSpace(d)
    [1, d]
    [0, 1]
    """
    def __init__(self, d):
        RayTransferMatrix.__init__(self,1,d,0,1)

class FlatRefraction(RayTransferMatrix):
    """
    Ray Transfer Matrix for refraction.

    Arguments: refractive indices of both media

    See Also: RayTransferMatrix

    Examples
    ========

    >>> from sympy.physics.gaussopt import FlatRefraction
    >>> from sympy import symbols
    >>> n1, n2 = symbols('n1 n2')
    >>> FlatRefraction(n1, n2)
    [1,     0]
    [0, n1/n2]
    """
    def __init__(self, n1, n2):
        n1, n2 = sympify((n1, n2))
        RayTransferMatrix.__init__(self,1,0,0,n1/n2)

class CurvedRefraction(RayTransferMatrix):
    """
    Ray Transfer Matrix for refraction on curved interface.

    Arguments: radius of curvature (positive for concave),
               refractive indices of both media

    See Also: RayTransferMatrix

    Examples
    ========

    >>> from sympy.physics.gaussopt import CurvedRefraction
    >>> from sympy import symbols
    >>> R, n1, n2 = symbols('R n1 n2')
    >>> CurvedRefraction(R, n1, n2)
    [               1,     0]
    [(n1 - n2)/(R*n2), n1/n2]
    """
    def __init__(self, R, n1, n2):
        R, n1 , n2 = sympify((R, n1, n2))
        RayTransferMatrix.__init__(self,1,0,(n1-n2)/R/n2,n1/n2)

class FlatMirror(RayTransferMatrix):
    """
    Ray Transfer Matrix for reflection.

    See Also: RayTransferMatrix

    Examples
    ========

    >>> from sympy.physics.gaussopt import FlatMirror
    >>> FlatMirror()
    [1, 0]
    [0, 1]
    """
    def __init__(self):
        RayTransferMatrix.__init__(self,1,0,0,1)

class CurvedMirror(RayTransferMatrix):
    """
    Ray Transfer Matrix for reflection from curved surface.

    Arguments: radius of curvature (positive for concave)

    See Also: RayTransferMatrix

    Examples
    ========

    >>> from sympy.physics.gaussopt import CurvedMirror
    >>> from sympy import symbols
    >>> R = symbols('R')
    >>> CurvedMirror(R)
    [   1, 0]
    [-2/R, 1]
    """
    def __init__(self, R):
        R = sympify(R)
        RayTransferMatrix.__init__(self,1,0,-2/R,1)

class ThinLens(RayTransferMatrix):
    """
    Ray Transfer Matrix for a thin lens.

    Arguments: the focal distance

    See Also: RayTransferMatrix

    Examples
    ========

    >>> from sympy.physics.gaussopt import ThinLens
    >>> from sympy import symbols
    >>> f = symbols('f')
    >>> ThinLens(f)
    [   1, 0]
    [-1/f, 1]
    """
    def __init__(self, f):
        f = sympify(f)
        RayTransferMatrix.__init__(self,1,0,-1/f,1)


###
# Representation for geometric ray
###

class GeometricRay(Matrix):
    """
    Representation for a geometric ray in the Ray Transfer Matrix formalism.

    Arguments
    =========

    either a 2x1 matrix
      or
    the height followed by the angle of the ray

    Examples
    =======

    >>> from sympy.physics.gaussopt import GeometricRay, FreeSpace
    >>> from sympy import symbols, Matrix
    >>> d,h,angle = symbols('d,h,angle')

    >>> GeometricRay(h,angle)
    [    h]
    [angle]

    >>> FreeSpace(d)*GeometricRay(h,angle)
    [angle*d + h]
    [      angle]

    >>> GeometricRay( Matrix( ((h,),(angle,)) ) )
    [    h]
    [angle]

    See Also
    ========

    RayTransferMatrix
    """

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Matrix) \
                          and args[0].shape == (2,1):
            temp = args[0]
        elif len(args) == 2:
            temp = ((args[0],),(args[1],))
        else:
            raise ValueError('Expecting 2x1 Matrix or the 2 elements of the Matrix but got %s' % str(args))
        Matrix.__init__(self, temp)

    @property
    def height(self):
        """The distance from the optical axis."""
        return self[0]

    @property
    def angle(self):
        """The angle with the optical axis."""
        return self[1]


###
# Representation for gauss beam
###

class BeamParameter(Expr):
    """
    Representation for a gaussian ray in the Ray Transfer Matrix formalism.

    Arguments
    =========

    wavelength, distance to waist
    and either
           w = waist
             or
           z_r = rayleigh range

    Examples
    ========

    >>> from sympy.physics.gaussopt import BeamParameter
    >>> p = BeamParameter(530e-9, 1, w=1e-3)
    >>> p.q
    1 + 1.88679245283019*I*pi

    >>> from sympy import N
    >>> N(p.q)
    1.0 + 5.92753330865999*I
    >>> N(p.w_0)
    0.00100000000000000
    >>> N(p.z_r)
    5.92753330865999

    >>> from sympy.physics.gaussopt import FreeSpace
    >>> fs = FreeSpace(10)
    >>> p1 = fs*p
    >>> N(p.w)
    0.00101413072159615
    >>> N(p1.w)
    0.00210803120913829

    See Also
    ========

    RayTransferMatrix

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Complex_beam_parameter
    """
    #TODO A class Complex may be implemented. The BeamParameter may
    # subclass it. See:
    # https://groups.google.com/d/topic/sympy/7XkU07NRBEs/discussion

    __slots__ = ['z', 'z_r', 'wavelen']

    def __new__(cls, wavelen, z, **kwargs):
        wavelen, z = sympify((wavelen, z))
        inst = Expr.__new__(cls, wavelen, z, **kwargs)
        inst.wavelen = wavelen
        inst.z = z
        if len(kwargs) !=1:
            raise ValueError('The constructor expects one and only one named argument')
        elif 'z_r' in kwargs:
            inst.z_r = sympify(kwargs['z_r'])
        elif 'w' in kwargs:
            inst.z_r = waist2rayleigh(sympify(kwargs['w']), wavelen)
        else:
            raise ValueError('The constructor needs named argument w or z_r')
        return inst

    @property
    def q(self):
        """The complex parameter representing the beam."""
        return self.z + I*self.z_r

    @property
    def radius(self):
        """The radius of curvature of the phase front."""
        return self.z*(1+(self.z/self.z_r)**2)

    @property
    def w(self):
        """
        The beam radius at 1/e^2 intensity.

        See Also: BeamParameter.w_0
        """
        return self.w_0*sqrt(1+(self.z/self.z_r)**2)

    @property
    def w_0(self):
        """The beam waist (minimal radius)."""
        return sqrt(self.z_r/pi*self.wavelen)

    @property
    def divergence(self):
        """Half of the total angular spread."""
        return self.wavelen/pi/self.w_0

    @property
    def gouy(self):
        """The Gouy phase."""
        return atan2(self.z, self.z_r)

    @property
    def waist_approximation_limit(self):
        """
        The minimal waist for which the gauss beam approximation is valid.

        The gauss beam is a solution to the paraxial equation. For curvatures
        that are too great it is not a valid approximation.
        """
        return 2*self.wavelen/pi


###
# Utilities
###

def waist2rayleigh(w, wavelen):
    """
    Calculate the rayleigh range from the waist of a gaussian beam.

    See Also: rayleigh2waist, BeamParameter

    Examples
    ========

    >>> from sympy.physics.gaussopt import waist2rayleigh
    >>> from sympy import symbols
    >>> w, wavelen = symbols('w wavelen')
    >>> waist2rayleigh(w, wavelen)
    pi*w**2/wavelen
    """
    w, wavelen = sympify((w, wavelen))
    return w**2*pi/wavelen

def rayleigh2waist(z_r, wavelen):
    """Calculate the waist from the rayleigh range of a gaussian beam.

    See Also: waist2rayleigh, BeamParameter

    Examples
    ========

    >>> from sympy.physics.gaussopt import rayleigh2waist
    >>> from sympy import symbols
    >>> z_r, wavelen = symbols('z_r wavelen')
    >>> rayleigh2waist(z_r, wavelen)
    sqrt(wavelen*z_r)/sqrt(pi)
    """
    z_r, wavelen = sympify((z_r, wavelen))
    return sqrt(z_r/pi*wavelen)


def geometric_conj_ab(a,b):
    """
    Conjugation relation for geometrical beams under paraxial conditions.

    Takes the distances to the optical element and returns the needed
    focal distance.

    See Also:
    geometric_conj_af, geometric_conj_bf

    Examples
    ========

    >>> from sympy.physics.gaussopt import geometric_conj_ab
    >>> from sympy import symbols
    >>> a, b = symbols('a b')
    >>> geometric_conj_ab(a, b)
    a*b/(a + b)
    """
    a, b = sympify((a, b))
    if abs(a) == oo or abs(b) == oo:
        return a if abs(b) == oo else b
    else:
        return a*b/(a+b)

def geometric_conj_af(a,f):
    """
    Conjugation relation for geometrical beams under paraxial conditions.

    Takes the object distance (for geometric_conj_af) or the image distance
    (for geometric_conj_bf) to the optical element and the focal distance.
    Then it returns the other distance needed for conjugation.

    See Also:
    geometric_conj_ab

    Examples
    ========

    >>> from sympy.physics.gaussopt import geometric_conj_af, geometric_conj_bf
    >>> from sympy import symbols
    >>> a, b, f = symbols('a b f')
    >>> geometric_conj_af(a, f)
    a*f/(a - f)
    >>> geometric_conj_bf(b, f)
    b*f/(b - f)
    """
    a, f = sympify((a, f))
    return -geometric_conj_ab(a, -f)

geometric_conj_bf = geometric_conj_af

def gaussian_conj(s_in, z_r_in, f):
    """
    Conjugation relation for gaussian beams.

    Arguments
    =========

    s_in - distance to optical element from the waist
    z_r_in - the rayleigh range of the incident beam
    f - the focal length of the optical element

    Returns
    =======

    A tuple containing (s_out, z_r_out, m)
     - s_out - distance between the new waist and the optical element
     - z_r_out - rayleigh range of the emergent beam
     - m - the ration between the new and the old waists

    Examples
    ========

    >>> from sympy.physics.gaussopt import gaussian_conj
    >>> from sympy import symbols
    >>> s_in, z_r_in, f = symbols('s_in z_r_in f')

    >>> gaussian_conj(s_in, z_r_in, f)[0]
    1/(-1/(s_in + z_r_in**2/(-f + s_in)) + 1/f)

    >>> gaussian_conj(s_in, z_r_in, f)[1]
    z_r_in/(1 - s_in**2/f**2 + z_r_in**2/f**2)

    >>> gaussian_conj(s_in, z_r_in, f)[2]
    1/sqrt(1 - s_in**2/f**2 + z_r_in**2/f**2)
    """
    s_in, z_r_in, f = sympify((s_in, z_r_in, f))
    s_out = 1 / ( -1/(s_in + z_r_in**2/(s_in-f)) + 1/f )
    m = 1/sqrt((1-(s_in/f)**2) + (z_r_in/f)**2)
    z_r_out = z_r_in / ((1-(s_in/f)**2) + (z_r_in/f)**2)
    return (s_out, z_r_out, m)

def conjugate_gauss_beams(wavelen, waist_in, waist_out, **kwargs):
    """
    Find the optical setup conjugating the object/image waists.

    Arguments
    =========

    wavelen - the wavelength of the beam
    waist_in and waits_out - the waists to be conjugated
    f - the focal distance of the element used in the conjugation

    Returns
    =======

    A tuple containing (s_in, s_out, f)
     - s_in - distance before the optical element
     - s_out - distance after the optical element
     - f -  focal distance of the optical element

    Examples
    ========

    >>> from sympy.physics.gaussopt import conjugate_gauss_beams
    >>> from sympy import symbols, factor
    >>> l, w_i, w_o, f = symbols('l w_i w_o f')

    >>> conjugate_gauss_beams(l, w_i, w_o, f=f)[0]
    f*(-sqrt(w_i**2/w_o**2 - pi**2*w_i**4/(f**2*l**2)) + 1)

    >>> factor(conjugate_gauss_beams(l, w_i, w_o, f=f)[1])
    f*w_o**2*(w_i**2/w_o**2 - sqrt(w_i**2/w_o**2 - pi**2*w_i**4/(f**2*l**2)))/w_i**2

    >>> conjugate_gauss_beams(l, w_i, w_o, f=f)[2]
    f
    """
    #TODO add the other possible arguments
    wavelen, waist_in, waist_out = sympify((wavelen, waist_in, waist_out))
    m = waist_out / waist_in
    z = waist2rayleigh(waist_in, wavelen)
    if len(kwargs) != 1:
        raise ValueError("The function expects only one named argument")
    elif 'dist' in kwargs:
        raise NotImplementedError("Currently only focal length is supported as a parameter")
    elif 'f' in kwargs:
        f = sympify(kwargs['f'])
        s_in = f * (1 - sqrt(1/m**2 - z**2/f**2))
        s_out = gaussian_conj(s_in, z, f)[0]
    elif 's_in' in kwargs:
        raise NotImplementedError("Currently only focal length is supported as a parameter")
    else:
        raise ValueError("The functions expects the focal length as a named argument")
    return (s_in, s_out, f)

#TODO
#def plot_beam():
#    """Plot the beam radius as it propagates in space."""
#    pass

#TODO
#def plot_beam_conjugation():
#    """
#    Plot the intersection of two beams.
#
#    Represents the conjugation relation.
#    See Also: conjugate_gauss_beams
#    """
#    pass
