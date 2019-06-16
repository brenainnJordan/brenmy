'''Continuing from matrix_stuff1...

Created on 15 Jun 2019

@author: Bren
'''
import math
import random
import fbx

import numpy
# from scipy.spatial.transform import Rotation as scipy_rotation

try:
    from maya import cmds
    MAYA_ENVIRONMENT = True
except ImportError:
    MAYA_ENVIRONMENT = False

ROTATE_SEED = 16.6
ROTATE_SEED = None


def get_sine_cosine_angle(sin_value, cos_value, degrees=True):
    """Determine angle from sine and cosine values.

    This method helps to determine if
    the angle is positive or negative
    and if the angle is greater than 90 degrees
    or less than negative 90 degrees

    """

    if cos_value == 1:
        radians = 0.0
    elif cos_value == 0:
        radians = math.radians(180)
    elif sin_value == 1:
        radians = math.radians(90)
    elif sin_value == -1:
        radians = math.radians(-90)
    elif cos_value > 0 and sin_value > 0:
        # positive rotation below 90 degrees
        radians = math.acos(cos_value)
    elif cos_value < 0 and sin_value > 0:
        # positive rotation above 90 degrees
        radians = math.radians(180) - math.asin(sin_value)
    elif cos_value > 0 and sin_value < 0:
        # negative rotation above -90 degrees
        radians = -math.acos(cos_value)
    elif cos_value < 0 and sin_value < 0:
        # negative rotation below -90 degrees
        radians = math.radians(-180) - math.asin(sin_value)
    elif cos_value > 1 or cos_value < -1 or sin_value > 1 or sin_value < -1:
        raise Exception("-1 > cos/sin > 1 out of  bounds")
        # TOOD if neccesary

    if degrees:
        return math.degrees(radians)
    else:
        return radians


class SineCosineAngle(object):
    def __init__(self):
        self.cos_functions = []
        self.sine_functions = []

    def can_solve(self):
        return all([
            len(self.cos_functions) > 0,
            len(self.sine_functions) > 0,
        ])

    def solve(self):
        pass


# represent each axis rotation as a list of functions
# this will allow us to "multiply" sequences of functions
# that allow us to procedurally solve euler rotation
# independent of rotation order
# and ideally independant of world axes (TODO)

class SignPositive():
    @classmethod
    def __eq__(cls, other):
        return other > 0

    @classmethod
    def __ne__(cls, other):
        return other < 0

    @classmethod
    def flip(cls):
        return SignNegative


class SignNegative():
    @classmethod
    def __eq__(self, other):
        return other < 0

    @classmethod
    def __ne__(self, other):
        return other > 0

    @classmethod
    def flip(cls):
        return SignNegative


class Sign():
    positive = SignPositive
    negative = SignNegative

    @classmethod
    def evaluate(cls, value, sign):
        if sign is cls.positive:
            return value
        elif sign is cls.negative:
            return value * -1
        else:
            raise Exception("Sign not recognized: {}".format(sign))

# wip...


class Axis(object):
    pass


class XAxis(Axis):
    @staticmethod
    def __repr__():
        return "x"


class YAxis(Axis):
    @staticmethod
    def __repr__():
        return "y"


class ZAxis(Axis):
    @classmethod
    def __name__(cls):
        return "z"


class Axes():
    null = None
    x = XAxis
    y = YAxis
    z = ZAxis

    axes = [XAxis, YAxis, ZAxis]

    @classmethod
    def get(cls, vector, axis):
        return vector[
            cls.axes.index(axis)
        ]


class MatrixOperationSum(object):
    def __init__(self, operations=[]):
        self._operations = operations

    def __repr__(self):
        return "[{}]".format(
            " + ".join(
                [str(i) for i in self._operations]
            ))

    def __str__(self, *args, **kwargs):
        return self.__repr__()

    def evaluate(self, xyz_values):
        value = 0.0

        for operation in self._operations:
            value += operation.evaluate(xyz_values)

        return value

    def evaluate_axis(self, axis, value):
        evaluated_operations = []

        for operation in self._operations:
            if isinstance(operation, MatrixOperationProduct):

                evaluated_value = operation.evaluate_axis(axis, value)

                if evaluated_value == 0:
                    continue

                if len(evaluated_value._operations) == 1:
                    evaluated_operations.append(evaluated_value._operations[0])
                else:
                    evaluated_operations.append(evaluated_value)

            else:
                if operation.axis == axis:

                    evaluated_value = operation.evaluate(value)

                    if evaluated_value == 0:
                        continue

                    evaluated_operations.append(evaluated_value)

                else:

                    evaluated_operations.append(operation)

        return MatrixOperationSum(evaluated_operations)


class MatrixOperationProduct(object):
    """Product of multiple trigonometric function as a component of a matrix.
    """

    def __init__(self, operations=[]):
        self._operations = operations

    def __mul__(self, other):
        if other == 1:
            return self

        if isinstance(other, MatrixOperationProduct):
            return list(self._operations) + list(other._operations)

        if isinstance(other, MatrixOperation):
            result = list(self._operations)
            result.append(other)

            return MatrixOperationProduct(operations=result)

        return 0

    def __repr__(self, *args, **kwargs):
        return "{{{}}}".format(
            " * ".join(
                [str(i) for i in self._operations]
            ))

    def __str__(self, *args, **kwargs):
        return self.__repr__()

    def evaluate(self, xyz_values):
        value = 1.0

        for operation in self._operations:
            value *= operation.evaluate(xyz_values)

        return value

    def evaluate_axis(self, axis, value):
        """For each operation in product, attempt to solve.
        Returns:
            (MatrixOperationProduct) if partial or no solve
            or
            (MatrixOperation) if product solve
            or
            (float) if full solve
        """
        evaluated_operations = []

        for operation in self._operations:
            # check if we can solve this operation
            if operation.axis == axis:
                # if we can solve it, then evaluate
                evaluated_value = operation.evaluate(value)
                evaluated_operations.append(evaluated_value)
            else:
                # if we can't solve it, leave operation intact
                evaluated_operations.append(operation)

        # prune operations
        pruned_operations = self.prune_operations(evaluated_operations)

        if isinstance(pruned_operations, list):
            # return new MatrixOperationProduct
            return MatrixOperationProduct(pruned_operations)
        else:
            # return either float or MatrixOperation
            return pruned_operations

    @classmethod
    def prune_operations(cls, operations):
        """Check for evaluated values, and solve accordingly.
        TODO could do other pruning, but for now this will do.
        note: this could be renamed solve_operations()??
        """
        pruned_operations = []
        values = []

        multiplier = 1.0

        # split into operations and solved values
        for obj in operations:
            if isinstance(obj, (float, int)):
                values.append(obj)
            elif isinstance(obj, MatrixOperation):
                pruned_operations.append(obj)
            else:
                raise Exception("Unexpected object found: {}".format(obj))

        # multiply values
        if len(values):
            multiplier = numpy.product(values)

            if not len(pruned_operations):
                # everything solved!
                return multiplier

            if multiplier == -1:
                # flip operations
                flipped_operations = []

                for obj in pruned_operations:
                    f_obj = obj.Copy()
                    f_obj.sign = f_obj.sign.flip()

                pruned_operations = flipped_operations

            elif multiplier == 0:
                # multiplies to 0
                return 0

        # multiply operations
        if len(pruned_operations):

            if multiplier != 1:
                # skip multiplying by 1
                # append multiplier value to operations
                pruned_operations.append(multiplier)

        else:
            raise Exception("No operations")

        # prune length
        if len(pruned_operations) == 1:
            return pruned_operations[0]
        else:
            return pruned_operations

    def get_operation_objects(self):
        return [
            i for i in self._operations if isinstance(i, MatrixOperation)
        ]

    def get_value_objects(self):
        return [
            i for i in self._operations if isinstance(i, (float, int))
        ]

    def can_solve(self):
        """Check to see if we can solve one axis from operations.

        returns:
            (Axis) object of solvable axis, or
            (False) if not solvable

        """
        axes = set([])

        for obj in self.get_operation_objects():
            axes.add(obj.axis)

        if len(axes) == 1:
            if len(self.get_operation_objects()) == 1:
                # for now keep it simple and only solve one operation
                return axes[0]
            else:
                # TODO solve more than one operation
                return False
        else:
            return False

    def solve(self, input_value):
        """Solve an axis from input value.
        """
        if not self.can_solve():
            raise Exception("Operation is not solvable")

        solved_value = self.divide_by_values(input_value)

        operation = self.get_operation_objects()[0]

        operation.inverse(solved_value)

        return solved_value

    def divide_by_values(self, input_value):
        values = self.get_value_objects()

        if len(values):
            return input_value / numpy.product(values)
        else:
            return input_value


class MatrixOperation(object):
    """Object to represent a trigonometric function as a component of a matrix.
    """

    def __init__(self, axis, sign, trig_function, inverse_function):
        self.axis = axis
        self.sign = sign
        self.trig_function = trig_function
        self.inverse_function = inverse_function

    def __repr__(self, *args, **kwargs):
        trig_strs = {
            math.sin: "sin",
            math.cos: "cos",
        }

        axis_strs = {
            XAxis: "x",
            YAxis: "y",
            ZAxis: "z"
        }

        repr_str = "{}({})".format(
            trig_strs[self.trig_function],
            axis_strs[self.axis],
        )

        if self.sign is SignNegative:
            repr_str = "-{}".format(repr_str)

        return repr_str

    def __str__(self, *args, **kwargs):
        return self.__repr__()

    def evaluate(self, value):
        if isinstance(value, list):
            value = Axes.get(value, self.axis)

        result = self.trig_function(value)

        if self.sign is SignNegative:
            result *= -1.0

        return result

    def inverse(self, value):
        result = self.inverse_function(value)

        if self.sign is SignNegative:
            result *= -1.0

        return result

    def __mul__(self, other):
        if other == 0:
            return 0

        if other == 1:
            return self

        if isinstance(other, MatrixOperation):
            return MatrixOperationProduct(
                operations=[self, other]
            )

        if isinstance(other, MatrixOperationProduct):
            return other * self

        return 0

    def __eq__(self, other):
        if not isinstance(other, MatrixOperation):
            return False

        return all([
            self.axis == other.axis,
            self.trig_function == other.trig_function,
            #             self.sign == other.sign # ignore this for now
        ])

    def copy(self):
        """Return copy of self
        """
        return MatrixOperation(
            self.axis,
            self.sign,
            self.trig_function,
            self.inverse_function
        )


class MatrixFunctions(object):
    def __init__(self):
        self._matrix = self.GetIdentity()

    def GetIdentity(self):
        return [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]

    def SetRow(self, row_index, row_value):
        if not isinstance(row_value, (list, tuple)):
            raise Exception("Row value must be list or tuple")

        for i, value in enumerate(list(row_value)[:4]):
            if isinstance(value, tuple):
                value = MatrixOperation(*value)

            self._matrix[row_index][i] = value

    def __mul__(self, other):
        """matrix multiplication

        create lists of function tuples per rows and columns

        """

        result = MatrixFunctions()

        for row_index, row in enumerate(self._matrix):
            result_row = []

            for column_index in range(4):
                other_column = [
                    other_row[column_index]
                    for other_row in other._matrix
                ]

                result_row_column = []

                for value, other_value in zip(row, other_column):

                    if value == 0 or other_value == 0:
                        continue

                    elif value == 1:
                        result_row_column.append(other_value)

                    else:
                        # multiplication is supported by
                        # MatrixOperation and MatrixOperationProduct classes
                        result_row_column.append(
                            value * other_value
                        )

#                     elif other_value == 1:
#                         result_row_column.append(value)
#
#                     elif isinstance(value, list):
#                         if not isinstance(other_value, list):
#                             other_value = [other_value]
#
#                         result_row_column.append(value + other_value)
#
#                     elif isinstance(other_value, list):
#                         if not isinstance(value, list):
#                             value = [value]
#
#                         result_row_column.append(value + other_value)
#
#                     else:
#                         result_row_column.append([value, other_value])

                if len(result_row_column):
                    if len(result_row_column) == 1:
                        result_row.append(result_row_column[0])
                    else:
                        result_row.append(
                            MatrixOperationSum(operations=result_row_column)
                        )
                else:
                    result_row.append(0)

            result.SetRow(row_index, result_row)

        return result

    def compose(self, xyz_values, degrees=True):
        composed_matrix = []

        if degrees:
            xyz_values = [math.radians(i) for i in xyz_values]

        for row in self._matrix:
            composed_row = []

            for obj in row:
                if isinstance(obj, (float, int)):
                    composed_row.append(obj)

                elif isinstance(
                    obj,
                    (
                        MatrixOperation,
                        MatrixOperationProduct,
                        MatrixOperationSum
                    )
                ):
                    composed_row.append(
                        obj.evaluate(xyz_values)
                    )

            composed_matrix.append(
                composed_row
            )

        return composed_matrix

    def decompose(self, matrix_values, degrees=True, verbose=True):
        """attempt to solve xyz euler values from matrix
        """

        # sepperate matrix into rows
        # assuming matrix is flat list
        # TODO check
        # maybe use numpy?
        matrix = [
            matrix_values[0:4],
            matrix_values[4:8],
            matrix_values[8:12],
            matrix_values[12:16],
        ]

        # step 1:
        # look for any indices in matrix that are a single operation
        # and solve whatever axis that is
        single_operations = []

        xyz_values = {
            XAxis: None,
            YAxis: None,
            ZAxis: None
        }

        solved_axes = []

        for row_index, row in enumerate(self._matrix):
            for column_index, obj in enumerate(row):
                if isinstance(obj, MatrixOperation):
                    single_operations.append(
                        (row_index, column_index, obj)
                    )

        if len(single_operations) == 1:
            row_index, column_index, operation = single_operations[0]
            # guess direction and +-90
            matrix_value = matrix[row_index][column_index]

            euler_value = operation.inverse(matrix_value)

            xyz_values[operation.axis] = euler_value

            solved_axes.append(operation.axis)

            if verbose:
                print "single operation: {} {} {} {}".format(
                    operation,
                    operation.axis,
                    matrix_value,
                    euler_value
                )

        elif len(single_operations):
            raise NotImplementedError(
                "TODO"
            )
        else:
            raise Exception(
                "Failed to solve Matrix function (no single operations)"
            )

        # step 2:
        # solve matrix for first axis
        solved_matrix = list(self._matrix)

        for solved_axis in solved_axes:
            solved_axis_matrix = []

            axis_value = xyz_values[solved_axis]

            for row_index in range(4):
                solved_row = []
                for column_index in range(4):

                    obj = solved_matrix[row_index][column_index]

                    if isinstance(obj, MatrixOperation):
                        if obj.axis == solved_axis:
                            solved_row.append(
                                obj.evaluate(axis_value)
                            )
                        else:
                            solved_row.append(obj)
                    elif isinstance(obj, MatrixOperationProduct):
                        solved_row.append(
                            obj.evaluate_axis(solved_axis, axis_value)
                        )
                    elif isinstance(obj, MatrixOperationSum):
                        # ignore for now
                        solved_row.append(obj)
                    elif isinstance(obj, (float, int)):
                        # use value
                        solved_row.append(obj)
                    else:
                        raise Exception(
                            "Unexpected object in matrix: {}".format(obj))

                solved_axis_matrix.append(solved_row)

        # check for new single operations
        cos_operations = {
            XAxis: [],
            YAxis: [],
            ZAxis: [],
        }

        sin_operations = {
            XAxis: [],
            YAxis: [],
            ZAxis: [],
        }

        for row_index, row in enumerate(solved_axis_matrix):
            for column_index, obj in enumerate(row):
                if isinstance(obj, MatrixOperation):
                    if obj.trig_function == math.sin:
                        sin_operations[obj.axis].append(
                            (row_index, column_index, obj)
                        )
                    elif obj.trig_function == math.cos:
                        cos_operations[obj.axis].append(
                            (row_index, column_index, obj)
                        )

        if not len(cos_operations) and not len(sin_operations):
            raise Exception(
                "Failed to solve Matrix function (no cos/sin single operations)"
            )

        # check operation axes
        # TODO

        # use first operations
        # TODO
        sin_value = None
        cos_value = None
        get_sine_cosine_angle(sin_value, cos_value, degrees=True)

        # compose xyz list
        rotate = [xyz_values[i] for i in Axes.axes]
        rotate = [i if i else 0 for i in rotate]

        if degrees:
            rotate = [math.degrees(i) for i in rotate]

        return rotate


class XMatrixFunctions(MatrixFunctions):
    """

    1    0       0     0
    0  cos(n)  sin(n)  0
    0 -sin(n)  cos(n)  0
    0    0       0     1

    """

    def __init__(self):
        super(XMatrixFunctions, self).__init__()

        self.SetRow(1, [
            0,
            (Axes.x, Sign.positive, math.cos, math.acos),
            (Axes.x, Sign.positive, math.sin, math.asin),
            0
        ])

        self.SetRow(2, [
            0,
            (Axes.x, Sign.negative, math.sin, math.asin),
            (Axes.x, Sign.positive, math.cos, math.acos),
            0
        ])


class YMatrixFunctions(MatrixFunctions):
    """

    cos(n)  0 -sin(n)  0
    0       1    0     0 
    sin(n)  0  cos(n)  0
    0       0    0     1

    """

    def __init__(self):
        super(YMatrixFunctions, self).__init__()

        self.SetRow(0, [
            (Axes.y, Sign.positive, math.cos, math.acos),
            0,
            (Axes.y, Sign.negative, math.sin, math.asin),
            0
        ])

        self.SetRow(2, [
            (Axes.y, Sign.positive, math.sin, math.asin),
            0,
            (Axes.y, Sign.positive, math.cos, math.acos),
            0
        ])


class ZMatrixFunctions(MatrixFunctions):
    """

     cos(n)  sin(n)  0   0
    -sin(n)  cos(n)  0   0
       0       0     1   0
       0       0     0   1

    """

    def __init__(self):
        super(ZMatrixFunctions, self).__init__()

        self.SetRow(0, [
            (Axes.z, Sign.positive, math.cos, math.acos),
            (Axes.z, Sign.positive, math.sin, math.asin),
            0,
            0
        ])

        self.SetRow(1, [
            (Axes.z, Sign.negative, math.sin, math.asin),
            (Axes.z, Sign.positive, math.cos, math.acos),
            0,
            0
        ])


if __name__ == "__main__":
    x_mat = XMatrixFunctions()
    y_mat = YMatrixFunctions()
    z_mat = ZMatrixFunctions()

    test = x_mat * y_mat * z_mat
#     test = z_mat * y_mat * x_mat

    for i in test._matrix:
        print i

    for i in test.compose([0, 0, -90]):
        print i
