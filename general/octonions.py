import random as randomlib

random = randomlib.SystemRandom()


def summ(o1, o2, modulo):
    """ Summ o1+o2"""
    o1re = int(o1[0])
    o1e1 = int(o1[1])
    o1e2 = int(o1[2])
    o1e3 = int(o1[3])
    o1e4 = int(o1[4])
    o1e5 = int(o1[5])
    o1e6 = int(o1[6])
    o1e7 = int(o1[7])

    o2re = int(o2[0])
    o2e1 = int(o2[1])
    o2e2 = int(o2[2])
    o2e3 = int(o2[3])
    o2e4 = int(o2[4])
    o2e5 = int(o2[5])
    o2e6 = int(o2[6])
    o2e7 = int(o2[7])

    t1 = int(o1re + o2re) % modulo
    t2 = int(o1e1 + o2e1) % modulo
    t3 = int(o1e2 + o2e2) % modulo
    t4 = int(o1e3 + o2e3) % modulo
    t5 = int(o1e4 + o2e4) % modulo
    t6 = int(o1e5 + o2e5) % modulo
    t7 = int(o1e6 + o2e6) % modulo
    t8 = int(o1e7 + o2e7) % modulo

    summ = (t1, t2, t3, t4, t5, t6, t7, t8)
    return summ


def scale(o, sca, modulo):
    """ Multiply an octonion by a value"""
    scale = int(sca)
    ore = int(o[0])
    oe1 = int(o[1])
    oe2 = int(o[2])
    oe3 = int(o[3])
    oe4 = int(o[4])
    oe5 = int(o[5])
    oe6 = int(o[6])
    oe7 = int(o[7])

    t1 = int(sca * ore) % modulo
    t2 = int(sca * oe1) % modulo
    t3 = int(sca * oe2) % modulo
    t4 = int(sca * oe3) % modulo
    t5 = int(sca * oe4) % modulo
    t6 = int(sca * oe5) % modulo
    t7 = int(sca * oe6) % modulo
    t8 = int(sca * oe7) % modulo

    o_scaled = (t1, t2, t3, t4, t5, t6, t7, t8)
    return o_scaled


def multiply(o1, o2, modulo):
    """ multiply two octonions o1*o2"""
    a = int(o1[0])
    b = int(o1[1])
    c = int(o1[2])
    d = int(o1[3])
    e = int(o1[4])
    f = int(o1[5])
    g = int(o1[6])
    h = int(o1[7])

    i = int(o2[0])
    j = int(o2[1])
    k = int(o2[2])
    l = int(o2[3])
    m = int(o2[4])
    n = int(o2[5])
    o = int(o2[6])
    p = int(o2[7])

    t1 = (a * i - b * j - c * k - d * l - e * m - f * n - g * o - h * p) % modulo    # Real
    t2 = (a * j + b * i + c * m + d * p - e * k + f * o - g * n - h * l) % modulo    # e1
    t3 = (a * k - b * m + c * i + d * n + e * j - f * l + g * p - h * o) % modulo    # e2
    t4 = (a * l - b * p - c * n + d * i + e * o + f * k - g * m + h * j) % modulo    # e3
    t5 = (a * m + b * k - c * j - d * o + e * i + f * p + g * l - h * n) % modulo    # e4
    t6 = (a * n - b * o + c * l - d * k - e * p + f * i + g * j + h * m) % modulo    # e5
    t7 = (a * o + b * n - c * p + d * m - e * l - f * j + g * i + h * k) % modulo    # e6
    t8 = (a * p + b * l + c * o - d * j + e * n - f * m - g * k + h * i) % modulo    # e7

    product = (t1, t2, t3, t4, t5, t6, t7, t8)
    return product


def power(oc, potency, modulo):
    res = (0, 0, 0, 0, 0, 0, 0, 0)

    for i in range(1, potency + 1):
        if i == 1:
            res = oc
        else:
            res = multiply(res, oc, modulo)

    if potency == 0:
        res = (1, 0, 0, 0, 0, 0, 0, 0)

    return res


def obtainPolynomial(grade, modulo):
    polynomial = []

    for i in range(grade - 1, -1, -1):
        term = (random.randrange(1, modulo), i)
        polynomial.append(term)

    return polynomial


def calculateF(oa, f, modulo):
    long_f = len(f)
    o_nulo = (0, 0, 0, 0, 0, 0, 0, 0)
    Fa = o_nulo

    for i in range(0, long_f):
        if i == long_f - 1:
            Fa = summ(Fa, (f[i][0], 0, 0, 0, 0, 0, 0, 0), modulo)
        else:
            on = power(oa, f[i][1], modulo)      # on = o exp to n
            ox = scale(on, f[i][0], modulo)      # do c.on
            Fa = summ(Fa, ox, modulo)            # sum c.on to fa

    return Fa