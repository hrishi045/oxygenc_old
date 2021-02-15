from .grammar import *


class OxyAST(object):
    def __str__(self) -> str:
        return '(' + ' '.join(str(value) for key, value in sorted(self.__dict__.items()) if not key.startswith("__") and key != 'read_only' and key != 'line_num' and value is not None) + ')'

    __repr__ = __str__


class OxyCompound(OxyAST):
    def __init__(self):
        self.children = []

    def __str__(self) -> str:
        return '\n'.join(str(child) for child in self.children)

    __repr__ = __str__


class OxyProgram(OxyAST):
    def __init__(self, block: OxyCompound):
        self.block = block

    def __str__(self) -> str:
        return '\n'.join(str(child) for child in self.block.children)

    __repr__ = __str__


class OxyVarDecl(OxyAST):
    def __init__(self, value, type_node, line_num, read_only=False):
        self.value = value
        self.type = type_node
        self.read_only = read_only
        self.line_num = line_num


class OxyVar(OxyAST):
    def __init__(self, value, line_num, read_only=False):
        self.value = value
        self.read_only = read_only
        self.line_num = line_num

    def __str__(self) -> str:
        return ' '.join(str(value) for key, value in sorted(self.__dict__.items()) if not key.startswith("__") and key != 'read_only' and key != 'line_num')

    __repr__ = __str__


class OxyFuncDecl(OxyAST):
    def __init__(self, name, return_type, parameters, body, line_num, parameter_defaults=None, varargs=None):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters
        self.parameter_defaults = parameter_defaults or {}
        self.body = body
        self.line_num = line_num
        self.varargs = varargs


class OxyExternFuncDecl(OxyAST):
    def __init__(self, name, return_type, parameters, line_num, varargs=None):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters
        self.varargs = varargs
        self.line_num = line_num


class OxyAnonymousFunc(OxyAST):
    def __init__(self, return_type, parameters, body, line_num, parameter_defaults=None, varargs=None):
        self.return_type = return_type
        self.parameters = parameters
        self.parameter_defaults = parameter_defaults or {}
        self.varargs = varargs
        self.body = body
        self.line_num = line_num


class OxyFuncCall(OxyAST):
    def __init__(self, name, arguments, line_num, named_arguments=None):
        self.name = name
        self.arguments = arguments
        self.named_arguments = named_arguments or {}
        self.line_num = line_num


class OxyMethodCall(OxyAST):
    def __init__(self, obj, name, arguments, line_num, named_arguments=None):
        self.obj = obj
        self.arguments = arguments
        self.line_num = line_num
        self.named_arguments = named_arguments or {}
        self.name = name


class OxyReturn(OxyAST):
    def __init__(self, value, line_num):
        self.line_num = line_num
        self.value = value


class OxyEnumDecl(OxyAST):
    def __init__(self, name, fields, line_num):
        self.line_num = line_num
        self.name = name
        self.fields = fields


class OxyStructDecl(OxyAST):
    def __init__(self, name, fields, defaults, line_num):
        self.name = name
        self.fields = fields
        self.line_num = line_num
        self.defaults = defaults


class OxyClassDecl(OxyAST):
    def __init__(self, name, base=None, methods=None, fields=None, instance_fields=None):
        self.name = name
        self.fields = fields
        self.instance_fields = instance_fields
        self.base = base
        self.methods = methods


class OxyAssign(OxyAST):
    def __init__(self, left, op, right, line_num):
        self.op = op
        self.line_num = line_num
        self.left = left
        self.right = right


class OxyOpAssign(OxyAST):
    def __init__(self, left, op, right, line_num):
        self.left = left
        self.op = op
        self.right = right
        self.line_num = line_num


class OxyIncrementAssign(OxyAST):
    def __init__(self, left, op, line_num):
        self.left = left
        self.op = op
        self.line_num = line_num


class OxyIfExpr(OxyAST):
    def __init__(self, op, comps, blocks, indent_level, line_num):
        self.op = op
        self.comps = comps
        self.blocks = blocks
        self.indent_level = indent_level
        self.line_num = line_num


class OxyElseExpr(OxyAST):
    pass


class OxyWhileExpr(OxyAST):
    def __init__(self, op, comp, block, line_num):
        self.op = op
        self.comp = comp
        self.block = block
        self.line_num = line_num


class OxyForExpr(OxyAST):
    def __init__(self, iterator, block, elements, line_num):
        self.iterator = iterator
        self.block = block
        self.elements = elements
        self.line_num = line_num


class OxyLoopBlock(OxyAST):
    def __init__(self):
        self.children = []


class OxySwitchStmt(OxyAST):
    def __init__(self, value, cases, line_num):
        self.value = value
        self.cases = cases
        self.line_num = line_num


class OxyCaseStmt(OxyAST):
    def __init__(self, value, block, line_num):
        self.value = value
        self.block = block
        self.line_num = line_num


class OxyBreakStmt(OxyAST):
    def __init__(self, line_num):
        self.line_num = line_num

# TODO
class OxyFTStmt(OxyAST):
    def __init__(self, line_num):
        self.line_num = line_num


class OxyContinueStmt(OxyAST):
    def __init__(self, line_num):
        self.line_num = line_num


# TODO
class OxyPass(OxyAST):
    def __init__(self, line_num):
        self.line_num = line_num


# Kinda works
class OxyDeferStmt(OxyAST):
    def __init__(self, line_num, statement):
        self.line_num = line_num
        self.statement = statement


class OxyBinOp(OxyAST):
    def __init__(self, left, op, right, line_num):
        self.left = left
        self.op = op
        self.right = right
        self.line_num = line_num


class OxyUnaryOp(OxyAST):
    def __init__(self, op, expr, line_num):
        self.op = op
        self.expr = expr
        self.line_num = line_num


class OxyRange(OxyAST):
    def __init__(self, left, right, line_num):
        self.left = left
        self.right = right
        self.value = RANGE
        self.line_num = line_num


class OxyCollectionAccess(OxyAST):
    def __init__(self, collection, key, line_num):
        self.collection = collection
        self.key = key
        self.line_num = line_num


class OxyDotAccess(OxyAST):
    def __init__(self, obj, field, line_num):
        self.obj = obj
        self.field = field
        self.line_num = line_num


class OxyType(OxyAST):
    def __init__(self, value, line_num, func_params=None, func_ret_type=None):
        self.value = value
        self.func_params = func_params
        self.func_ret_type = func_ret_type
        self.line_num = line_num


class OxyTypeDecl(OxyAST):
    def __init__(self, name, collection, line_num):
        self.name = name
        self.collection = collection
        self.line_num = line_num


# TODO
class OxyVoid(OxyAST):
    value = VOID


class OxyConstant(OxyAST):
    def __init__(self, value, line_num):
        self.value = value
        self.line_num = line_num


class OxyNum(OxyAST):
    def __init__(self, value, val_type, line_num):
        self.value = value
        self.line_num = line_num
        self.val_type = val_type


class OxyStr(OxyAST):
    def __init__(self, value, line_num):
        self.line_num = line_num
        self.value = value


class OxyCollection(OxyAST):
    def __init__(self, collection_type, line_num, read_only, *items):
        self.type = collection_type
        self.read_only = read_only
        self.line_num = line_num
        self.items = items


class OxyHashMap(OxyAST):
    def __init__(self, items, line_num):
        self.line_num = line_num
        self.items = items


class OxyPrintStmt(OxyAST):
    def __init__(self, value, line_num):
        self.line_num = line_num
        self.value = value


class OxyInputStmt(OxyAST):
    def __init__(self, value, line_num):
        self.line_num = line_num
        self.value = value
