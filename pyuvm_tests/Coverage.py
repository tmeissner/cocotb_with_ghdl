import vsc


# Random stimuli model class
@vsc.randobj
class constraints:
    def __init__(self):
        self.key = vsc.rand_bit_t(128)
        self.data = vsc.rand_bit_t(128)

    @vsc.constraint
    def c(self):
        self.data >= 0 and self.data <= 2**128 - 1
        vsc.dist(
            self.key,
            [
                vsc.weight(0, 15),
                vsc.weight((1, 2**128 - 2), 70),
                vsc.weight((2**128 - 1), 15),
            ],
        )


# Stimuli covergroup
@vsc.covergroup
class covergroup:
    def __init__(self, name="bla"):
        self.options.name = name
        self.with_sample(mode=vsc.bit_t(1), key=vsc.bit_t(128))

        self.enc = vsc.coverpoint(self.mode, bins=dict(enc=vsc.bin(0)))

        self.dec = vsc.coverpoint(self.mode, bins=dict(dec=vsc.bin(1)))

        self.key0 = vsc.coverpoint(self.key, bins=dict(key0=vsc.bin(0)))

        self.keyF = vsc.coverpoint(self.key, bins=dict(keyF=vsc.bin(2**128 - 1)))

        self.encXkey0 = vsc.cross([self.enc, self.key0])
        self.encXkeyF = vsc.cross([self.enc, self.keyF])

        self.decXkey0 = vsc.cross([self.dec, self.key0])
        self.decXkeyF = vsc.cross([self.dec, self.keyF])
