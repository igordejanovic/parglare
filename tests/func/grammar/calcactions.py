from parglare import Actions


class MyActions(Actions):
    def Calc(self, nodes):
        return self.pass_inner(nodes)

    def Assignment(self, nodes):
        name = nodes[0]
        number = nodes[2]

        # Use context.extra to collect variables
        if self.context.extra is None:
            self.context.extra = {}

        self.context.extra[name] = number

    def E(self, nodes):
        return [lambda n: n[0] + n[2],
                lambda n: n[0] - n[2],
                lambda n: n[0] * n[2],
                lambda n: n[0] / n[2],
                lambda n: n[1],
                lambda n: n[0],
                lambda n: n[0]][self.prod_idx](nodes)

    def Number(self, value):
        return float(value)

    def VariableName(self, value):
        return value

    def VariableRef(self, nodes):
        return self.context.extra[nodes[0]]


actions = MyActions()
