from decimal import Decimal
from enum import Enum

from oxygen.oxyast import OxyType
from oxygen.compiler.base import *


class Symbol(object):
    def __init__(self, name, symbol_type=None):
        self.name = name
        self.type = symbol_type


class LLVMTypeSymbol(Symbol):
    def __init__(self, name, llvm_type=None, func=None):
        super().__init__(name)
        self.llvm_type = llvm_type
        self.func = func

    def type(self):
        return self.llvm_type.type()

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


ANY_BUILTIN = LLVMTypeSymbol(ANY)
INT_BUILTIN = LLVMTypeSymbol(INT, Int)
I8_BUILTIN = LLVMTypeSymbol(INT8, Int8)
I16_BUILTIN = LLVMTypeSymbol(INT16, Int16)
I32_BUILTIN = LLVMTypeSymbol(INT32, Int32)
I64_BUILTIN = LLVMTypeSymbol(INT64, Int64)
I128_BUILTIN = LLVMTypeSymbol(INT128, Int128)
UINT_BUILTIN = LLVMTypeSymbol(UINT, UInt)
U8_BUILTIN = LLVMTypeSymbol(UINT8, UInt8)
U16_BUILTIN = LLVMTypeSymbol(UINT16, UInt16)
U32_BUILTIN = LLVMTypeSymbol(UINT32, UInt32)
U64_BUILTIN = LLVMTypeSymbol(UINT64, UInt64)
U128_BUILTIN = LLVMTypeSymbol(UINT128, UInt128)
F64_BUILTIN = LLVMTypeSymbol(DOUBLE, Double)
F32_BUILTIN = LLVMTypeSymbol(FLOAT, Float)
COMPLEX_BUILTIN = LLVMTypeSymbol(COMPLEX, Complex)
BOOL_BUILTIN = LLVMTypeSymbol(BOOL, Bool)
STR_BUILTIN = LLVMTypeSymbol(STR, Str)
FUNC_BUILTIN = LLVMTypeSymbol(FUNC, Func)
LIST_BUILTIN = LLVMTypeSymbol(LIST, List)
TUPLE_BUILTIN = LLVMTypeSymbol(TUPLE, Tuple)
DICT_BUILTIN = LLVMTypeSymbol(DICT, Dict)
STRUCT_BUILTIN = LLVMTypeSymbol(STRUCT, Str)
ENUM_BUILTIN = LLVMTypeSymbol(ENUM, Enum)
CLASS_BUILTIN = LLVMTypeSymbol(OBJECT, Class)


class OxyVarSymbol(Symbol):
    def __init__(self, name, var_type, read_only=False):
        super().__init__(name, var_type)
        self.accessed = False
        self.val_assigned = False
        self.read_only = read_only

    def __str__(self) -> str:
        return '<{name}:{type}>'.format(name=self.name, type=self.type)

    __repr__ = __str__


class OxyEnumSymbol(Symbol):
    def __init__(self, name, fields):
        super().__init__(name)
        self.fields = fields
        self.accessed = False
        self.val_assigned = False

    def __str__(self) -> str:
        return ENUM


class OxyStructSymbol(Symbol):
    def __init__(self, name, fields):
        super().__init__(name)
        self.fields = fields
        self.accessed = False
        self.val_assigned = False


class OxyClassSymbol(Symbol):
    def __init__(self, name, base, fields, methods):
        super().__init__(name)
        self.base = base
        self.fields = fields
        self.methods = methods
        self.accessed = False
        self.val_assigned = False


class OxyCollectionSymbol(Symbol):
    def __init__(self, name, var_type, item_types):
        super().__init__(name, var_type)
        self.item_types = item_types
        self.accessed = False
        self.val_assigned = False
        self.read_only = False


class OxyFuncSymbol(Symbol):
    def __init__(self, name, return_type, parameters, body, parameter_defaults={}):
        super().__init__(name, return_type)
        self.parameters = parameters
        self.parameter_defaults = parameter_defaults
        self.body = body
        self.accessed = False
        self.val_assigned = True

    def __str__(self) -> str:
        return '<{name}:{type} ({params})>'.format(name=self.name, type=self.type, params=', '.join(
            '{}:{}'.format(key, value.value) for key, value in self.parameters.items()))

    __repr__ = __str__


class OxyTypeSymbol(Symbol):
    def __init__(self, name, types):
        super().__init__(name, types)
        self.accessed = False

    def __str__(self) -> str:
        return '<{name}:{type}>'.format(name=self.name, type=self.type)

    __repr__ = __str__


class OxyBuiltinFuncSymbol(Symbol):
    def __init__(self, name, return_type, parameters, body):
        super().__init__(name, return_type)
        self.parameters = parameters
        self.body = body
        self.accessed = False
        self.val_assigned = True

    def __str__(self) -> str:
        return '<{name}:{type} ({params})>'.format(name=self.name, type=self.type, params=', '.join(
            '{}:{}'.format(key, value.value) for key, value in self.parameters.items()))

    __repr__ = __str__


class OxyNodeVisitor(object):
    def __init__(self):
        self._scope = [{}]
        self._init_builtins()

    def _init_builtins(self):
        self.define(ANY, ANY_BUILTIN)
        self.define(INT, INT_BUILTIN)
        self.define(INT8, I8_BUILTIN)
        self.define(INT16, I16_BUILTIN)
        self.define(INT32, I32_BUILTIN)
        self.define(INT64, I64_BUILTIN)
        self.define(INT128, I128_BUILTIN)
        self.define(UINT, UINT_BUILTIN)
        self.define(UINT8, U8_BUILTIN)
        self.define(UINT16, U16_BUILTIN)
        self.define(UINT32, U32_BUILTIN)
        self.define(UINT64, U64_BUILTIN)
        self.define(UINT128, U128_BUILTIN)
        self.define(DOUBLE, F64_BUILTIN)
        self.define(FLOAT, F32_BUILTIN)
        self.define(COMPLEX, COMPLEX_BUILTIN)
        self.define(BOOL, BOOL_BUILTIN)
        self.define(STR, STR_BUILTIN)
        self.define(STRUCT, STRUCT_BUILTIN)
        self.define(LIST, LIST_BUILTIN)
        self.define(TUPLE, TUPLE_BUILTIN)
        self.define(DICT, DICT_BUILTIN)
        self.define(ENUM, ENUM_BUILTIN)
        self.define(FUNC, FUNC_BUILTIN)
        self.define(OBJECT, CLASS_BUILTIN)

    def visit(self, node):
        method_name = 'visit_' + type(node).__name__.lower()
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    @staticmethod
    def generic_visit(node):
        raise Exception('No visit_{} method'.format(type(node).__name__.lower()))

    @property
    def top_scope(self):
        return self._scope[-1] if len(self._scope) >= 1 else None

    @property
    def second_scope(self):
        return self._scope[-2] if len(self._scope) >= 2 else None

    def search_scopes(self, name, level=None):
        if name in (None, []):
            return None
        if level:
            if name in self._scope[level]:
                return self._scope[level][name]
        else:
            for scope in reversed(self._scope):
                if name in scope:
                    return scope[name]

    def define(self, key, value, level=0):
        level = (len(self._scope) - level) - 1
        self._scope[level][key] = value

    def new_scope(self):
        self._scope.append({})

    def drop_top_scope(self):
        self._scope.pop()

    @property
    def symbols(self):
        return [value for scope in self._scope for value in scope.values()]

    @property
    def keys(self):
        return [key for scope in self._scope for key in scope.keys()]

    @property
    def items(self):
        return [(key, value) for scope in self._scope for key, value in scope.items()]

    @property
    def unvisited_symbols(self):
        return [sym_name for sym_name, sym_val in self.items if
                not isinstance(sym_val, (LLVMTypeSymbol, OxyBuiltinFuncSymbol)) and not
                sym_val.accessed and sym_name != '_']

    def infer_type(self, value):
        if isinstance(value, LLVMTypeSymbol):
            return value
        if isinstance(value, OxyFuncSymbol):
            return self.search_scopes(FUNC)
        if isinstance(value, OxyVarSymbol):
            return value.type
        if isinstance(value, OxyType):
            return self.search_scopes(value.value)
        if isinstance(value, int):
            return self.search_scopes(INT)
        if isinstance(value, Decimal):
            return self.search_scopes(DOUBLE)
        if isinstance(value, float):
            return self.search_scopes(FLOAT)
        if isinstance(value, complex):
            return self.search_scopes(COMPLEX)
        if isinstance(value, str):
            return self.search_scopes(STR)
        if isinstance(value, OxyStructSymbol):
            return self.search_scopes(STRUCT)
        if isinstance(value, OxyEnumSymbol):
            return self.search_scopes(ENUM)
        if isinstance(value, OxyClassSymbol):
            return self.search_scopes(OBJECT)
        if isinstance(value, bool):
            return self.search_scopes(BOOL)
        if isinstance(value, list):
            return self.search_scopes(TUPLE)
        if isinstance(value, dict):
            return self.search_scopes(DICT)
        if isinstance(value, Enum):
            return self.search_scopes(ENUM)
        if callable(value):
            return self.search_scopes(FUNC)
        raise TypeError('Type not recognized: {}'.format(value))
