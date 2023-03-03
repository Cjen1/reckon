import reckon.reckon_types as t


class NoFailure(t.AbstractFailureGenerator):
    def get_failures(self, net, system, restarters, stoppers):
        return [t.NullFault(), t.NullFault()]
