from parglare import Actions


class MyActions(Actions):
    def Calc(self, nodes):
        return nodes[1]

    def Assignment(self, nodes):
        var_name, _, value = nodes
        self.context.extra[var_name] = float(value)

    def E(self, n):
        return [
            lambda _, n: n[0] + n[2],
            lambda _, n: n[0] - n[2],
            lambda _, n: n[0] * n[2],
            lambda _, n: n[0] / n[2],
            lambda _, n: n[1],
            lambda context, n: context.extra[n[0]],
            lambda _, n: float(n[0])
        ][self.prod_idx](self.context, n)
