"""This example is inspired by an example from LISA tool
(http://labraj.uni-mb.si/lisa/) presented during the lecture given by prof.
Marjan Mernik (http://lpm.uni-mb.si/mernik/) at the University of Novi Sad in
June, 2011.

An example of the robot program:
   begin
       initial 3, 1
       up 4
       left 9
       down
       right 1
   end

"""
from __future__ import unicode_literals, print_function
import os
from parglare import Grammar, Parser, Actions


class MyActions(Actions):
    def INT(self, value):
        return int(value)

    def initial(self, nodes, x, y):
        print("Robot initial position set to: {}, {}".format(x, y))
        # We use context.extra to keep robot position state.
        self.context.extra = (x, y)

    def program(self, nodes, commands):
        return self.context.extra

    def move(self, nodes, direction, steps):
        steps = 1 if steps is None else steps
        print("Moving robot {} for {} steps.".format(direction, steps))

        move = {
            "up": (0, 1),
            "down": (0, -1),
            "left": (-1, 0),
            "right": (1, 0)
        }[direction]

        # Calculate new robot position
        x, y = self.context.extra
        self.context.extra = (x + steps * move[0], y + steps * move[1])


def main(debug=False):
    this_folder = os.path.dirname(__file__)
    g = Grammar.from_file(os.path.join(this_folder, 'robot.pg'),
                          debug=debug, debug_colors=True)
    parser = Parser(g, actions=MyActions(), debug=debug,
                    debug_colors=True)

    end_position = parser.parse_file(os.path.join(this_folder, 'program.rbt'))

    print("Robot stops at position: {}".format(end_position))


if __name__ == "__main__":
    main(debug=False)
