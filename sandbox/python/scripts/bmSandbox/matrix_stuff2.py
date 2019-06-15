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


# represent each axis rotation as a list of functions
# this will allow us to "multiply" sequences of functions
# that allow us to procedurally solve euler rotation
# independent of rotation order
# and ideally independant of world axes (TODO)

class SignPositive():
    @classmethod
    def __eq__(self, other):
        return other > 0

    @classmethod
    def __ne__(self, other):
        return other < 1


class SignNegative():
    @classmethod
    def __eq__(self, other):
        return other < 0

    @classmethod
    def __ne__(self, other):
        return other > 1


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


class XAxis():
    @staticmethod
    def __repr__():
        return "x"


class YAxis():
    @staticmethod
    def __repr__():
        return "y"


class ZAxis():
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

    def decompose_xyz(self, xyz_values):
        pass


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
