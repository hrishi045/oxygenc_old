from typing import Optional
from collections import OrderedDict

from oxygen.oxyast import *
from oxygen.utils import error
from oxygen.lexer import Token
from oxygen.compiler.base import type_map
from oxygen.grammar import *


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.file_name = lexer.file_name
        self.current_token: Optional[Token] = None
        self.indent_level = 0
        self.next_token()
        self.user_types = []
        self.func_args = False

    @property
    def line_num(self) -> int:
        return self.current_token.line_num

    def next_token(self):
        token = self.current_token
        self.current_token = self.lexer.get_next_token()
        return token

    def consume_type(self, *token_type):
        if self.current_token.type in token_type:
            self.next_token()
        else:
            error('file={} line={} OxygenC Error: expected {}'.format(
                self.file_name, self.line_num, ", ".join(token_type)))

    def consume_value(self, *token_value):
        if self.current_token.value in token_value:
            self.next_token()
        else:
            error('file={} line={} OxygenC Error: expected {}'.format(
                self.file_name, self.line_num, ", ".join(token_value)))

    def preview(self, num=1):
        return self.lexer.view_next_token(num)

    def parse_find_until(self, to_find, until):
        num = 0
        x = None
        while x != until:
            num += 1
            x = self.lexer.view_next_token(num).value
            if x == to_find:
                return True
            elif x == EOF:
                error('file={} line={} OxygenC Error: expected {}'.format(
                    self.file_name, self.line_num, to_find))

        return False

    def parse_handle_indents(self):
        while self.current_token.type == NEWLINE:
            self.consume_type(NEWLINE)
        return self.current_token.indent_level == self.indent_level

    def parse_program_text(self):
        root = OxyCompound()
        while self.current_token.type != EOF:
            comp = self.parse_compound_stmt()
            root.children.extend(comp.children)
        return OxyProgram(root)

    def parse_enum_decl(self):
        self.consume_value(ENUM)
        name = self.next_token()
        self.user_types.append(name.value)
        self.consume_type(NEWLINE)
        self.indent_level += 1
        fields = []
        while self.current_token.indent_level > name.indent_level:
            field = self.next_token().value
            fields.append(field)

            self.consume_type(NEWLINE)

        self.indent_level -= 1
        return OxyEnumDecl(name.value, fields, self.line_num)

    def parse_struct_decl(self):
        self.consume_value(STRUCT)
        name = self.next_token()
        self.user_types.append(name.value)
        self.consume_type(NEWLINE)
        self.indent_level += 1
        fields = OrderedDict()
        defaults = {}
        while self.current_token.indent_level > name.indent_level:
            field = self.next_token().value
            self.consume_value(COLON)
            field_type = self.type_spec()
            fields[field] = field_type
            if self.current_token.value == ASSIGN:
                self.consume_value(ASSIGN)
                defaults[field] = self.parse_any_expr()

            self.consume_type(NEWLINE)
        self.indent_level -= 1
        return OxyStructDecl(name.value, fields, defaults, self.line_num)

    def parse_class_decl(self):
        base = None
        methods = []
        fields = OrderedDict()
        instance_fields = None
        self.next_token()
        class_name = self.current_token
        self.user_types.append(class_name.value)
        self.consume_type(NAME)
        if self.current_token.value == COLON:
            self.consume_value(COLON)
            base = self.type_spec()
        self.consume_type(NEWLINE)
        self.indent_level += 1
        while self.parse_handle_indents():
            if self.current_token.type == NEWLINE:
                self.consume_type(NEWLINE)
                continue
            if self.current_token.type == NAME and self.preview().value == COLON:
                field = self.current_token.value
                self.consume_type(NAME)
                self.consume_value(COLON)
                field_type = self.type_spec()
                fields[field] = field_type
                self.consume_type(NEWLINE)
            if self.current_token.value == FUN:
                methods.append(self.method_declaration(class_name))
        self.indent_level -= 1
        return OxyClassDecl(class_name.value, base, methods, fields, instance_fields)

    def parse_var_decl(self):
        var_node = OxyVar(self.current_token.value, self.line_num)
        self.consume_type(NAME)
        self.consume_value(COLON)
        type_node = self.type_spec()
        var = OxyVarDecl(var_node, type_node, self.line_num)
        if self.current_token.value == ASSIGN:
            var = self.parse_var_assingment(var)
        return var

    def parse_var_assingment(self, declaration):
        return OxyAssign(declaration, self.next_token().value, self.parse_any_expr(), self.line_num)

    def parse_type_decl(self):
        self.consume_value(TYPE)
        name = self.next_token()
        self.user_types.append(name.value)
        self.consume_value(ASSIGN)
        return OxyTypeDecl(name.value, self.type_spec(), self.line_num)

    def function_declaration(self):
        op_func = False
        extern_func = False
        self.consume_value(FUN)
        if self.current_token.value == LPAREN:
            name = ANON
        elif self.current_token.value == OPERATOR:
            self.consume_value(OPERATOR)
            op_func = True
            name = self.next_token()
        elif self.current_token.value == EXTERN:
            self.consume_value(EXTERN)
            extern_func = True
            name = self.next_token()
        else:
            name = self.next_token()
        self.consume_value(LPAREN)
        params = OrderedDict()
        param_defaults = {}
        vararg = None
        while self.current_token.value != RPAREN:
            param_name = self.current_token.value
            self.consume_type(NAME)
            if self.current_token.value == COLON:
                self.consume_value(COLON)
                param_type = self.type_spec()
            else:
                param_type = self.variable(self.current_token)

            params[param_name] = param_type
            if self.current_token.value != RPAREN:
                if self.current_token.value == ASSIGN:
                    if extern_func:
                        error("Extern functions cannot have defaults")
                    self.consume_value(ASSIGN)
                    param_defaults[param_name] = self.parse_any_expr()
                if self.current_token.value == ELLIPSIS:
                    key, value = params.popitem()
                    if not vararg:
                        vararg = []
                    vararg.append(key)
                    vararg.append(value)
                    self.consume_value(ELLIPSIS)
                    break
                if self.current_token.value != RPAREN:
                    self.consume_value(COMMA)
        self.consume_value(RPAREN)

        if self.current_token.value != ARROW:
            return_type = OxyVoid()
        else:
            self.consume_value(ARROW)
            if self.current_token.value == VOID:
                return_type = OxyVoid()
                self.next_token()
            else:
                return_type = self.type_spec()

        if extern_func:
            return OxyExternFuncDecl(name.value, return_type, params, self.line_num, vararg)

        self.consume_type(NEWLINE)
        self.indent_level += 1
        stmts = self.parse_compound_stmt()
        self.indent_level -= 1
        if name == ANON:
            return OxyAnonymousFunc(return_type, params, stmts, self.line_num, param_defaults, vararg)
        if op_func:
            if len(params) not in (1, 2):  # TODO: move this to type checker
                error(
                    "Operators can either be unary or binary, and the number of parameters do not match")

            name.value = OPERATOR + '.' + name.value
            for param in params:
                type_name = str(type_map[str(params[param].value)]) if str(
                    params[param].value) in type_map else str(params[param].value)
                name.value += '.' + type_name

        return OxyFuncDecl(name.value, return_type, params, stmts, self.line_num, param_defaults, vararg)

    def method_declaration(self, class_name):
        self.consume_value(FUN)
        name = self.next_token()
        self.consume_value(LPAREN)
        params = OrderedDict()
        param_defaults = {}
        vararg = None
        params[SELF] = class_name
        while self.current_token.value != RPAREN:
            param_name = self.current_token.value
            self.consume_type(NAME)
            if self.current_token.value == COLON:
                self.consume_value(COLON)
                param_type = self.type_spec()
            else:
                param_type = self.variable(self.current_token)

            params[param_name] = param_type
            if self.current_token.value != RPAREN:
                if self.current_token.value == ASSIGN:
                    self.consume_value(ASSIGN)
                    param_defaults[param_name] = self.parse_any_expr()
                if self.current_token.value == ELLIPSIS:
                    key, value = params.popitem()
                    if not vararg:
                        vararg = []
                    vararg.append(key)
                    vararg.append(value)
                    self.consume_value(ELLIPSIS)
                    break
                if self.current_token.value != RPAREN:
                    self.consume_value(COMMA)
        self.consume_value(RPAREN)

        if self.current_token.value != ARROW:
            return_type = OxyVoid()
        else:
            self.consume_value(ARROW)
            if self.current_token.value == VOID:
                return_type = OxyVoid()
                self.next_token()
            else:
                return_type = self.type_spec()

        self.consume_type(NEWLINE)
        self.indent_level += 1
        stmts = self.parse_compound_stmt()
        self.indent_level -= 1

        return OxyFuncDecl("{}.{}".format(class_name.value, name.value), return_type, params, stmts, self.line_num, param_defaults, vararg)

    def bracket_literal(self):
        token = self.next_token()
        if token.value == LBRACE:
            return self.parse_cbrace_expr(token)
        elif token.value == LPAREN:
            return self.parse_tuple_literal(token)

        return self.parse_square_bracket_expr(token)

    def function_call(self, token):
        if token.value == PRINT:
            self.func_args = True
            return OxyPrintStmt(self.parse_any_expr(), self.line_num)
        elif token.value == INPUT:
            self.func_args = True
            return OxyInputStmt(self.parse_any_expr(), self.line_num)

        self.consume_value(LPAREN)
        args = []
        named_args = {}
        while self.current_token.value != RPAREN:
            while self.current_token.type == NEWLINE:
                self.consume_type(NEWLINE)
            if self.current_token.value in (LPAREN, LBRACK, LBRACE):
                args.append(self.bracket_literal())
            elif self.preview().value == ASSIGN:
                name = self.parse_any_expr().value
                self.consume_value(ASSIGN)
                named_args[name] = self.parse_any_expr()
            else:
                args.append(self.parse_any_expr())
            while self.current_token.type == NEWLINE:
                self.consume_type(NEWLINE)
            if self.current_token.value != RPAREN:
                self.consume_value(COMMA)
        func = OxyFuncCall(token.value, args, self.line_num, named_args)
        self.next_token()
        return func

    def type_spec(self):
        token = self.current_token
        if token.value in self.user_types:
            self.consume_type(NAME)
            return OxyType(token.value, self.line_num)
        self.consume_type(LTYPE)
        type_spec = OxyType(token.value, self.line_num)
        func_ret_type = None
        func_params = OrderedDict()
        param_num = 0
        if self.current_token.value == LESS_THAN and token.value in (LIST, TUPLE):
            self.next_token()
            while self.current_token.value != GREATER_THAN:
                param_type = self.type_spec()
                func_params[str(param_num)] = param_type
                param_num += 1
                if self.current_token.value != GREATER_THAN:
                    self.consume_value(COMMA)

            self.consume_value(GREATER_THAN)
            type_spec.func_params = func_params

        elif self.current_token.value == LESS_THAN and token.value == FUNC:
            self.next_token()
            while self.current_token.value != GREATER_THAN:
                param_type = self.type_spec()
                func_params[str(param_num)] = param_type
                param_num += 1
                if self.current_token.value != GREATER_THAN:
                    self.consume_value(COMMA)

            self.consume_value(GREATER_THAN)
            if self.current_token.value == ARROW:
                self.next_token()
                func_ret_type = self.type_spec()
            else:
                func_ret_type = OxyType(VOID, self.line_num)

            type_spec.func_params = func_params
            type_spec.func_ret_type = func_ret_type

        return type_spec

    def parse_compound_stmt(self):
        nodes = self.parse_stmt_list()
        root = OxyCompound()
        for node in nodes:
            root.children.append(node)
        return root

    def parse_stmt_list(self):
        node = self.parse_stmt()
        if self.current_token.type == NEWLINE:
            self.next_token()
        if isinstance(node, OxyReturn):
            return [node]
        results = [node]
        while self.parse_handle_indents():
            results.append(self.parse_stmt())
            if self.current_token.type == NEWLINE:
                self.next_token()
            elif self.current_token.type == EOF:
                results = [x for x in results if x is not None]
                break
        return results

    def parse_stmt(self):
        if self.current_token.value == IF:
            node = self.parse_if_expr()
        elif self.current_token.value == WHILE:
            node = self.parse_while_expr()
        elif self.current_token.value == FOR:
            node = self.parse_for_stmt()
        elif self.current_token.value == FALLTHROUGH:
            self.next_token()
            node = OxyFTStmt(self.line_num)
        elif self.current_token.value == BREAK:
            self.next_token()
            node = OxyBreakStmt(self.line_num)
        elif self.current_token.value == CONTINUE:
            self.next_token()
            node = OxyContinueStmt(self.line_num)
        elif self.current_token.value == PASS:
            self.next_token()
            node = OxyPass(self.line_num)
        elif self.current_token.value == CONST:
            node = self.parse_assign_stmt(self.current_token)
        elif self.current_token.value == DEFER:
            self.next_token()
            node = OxyDeferStmt(self.line_num, self.parse_stmt())
        elif self.current_token.value == SWITCH:
            self.next_token()
            node = self.parse_switch_stmt()
        elif self.current_token.value == RETURN:
            node = self.parse_return_statement()
        elif self.current_token.type == NAME:
            if self.preview().value == DOT:
                node = self.parse_prop_method(self.next_token())
            elif self.preview().value == COLON:
                node = self.parse_var_decl()
            else:
                node = self.parse_name_stmt()
        elif self.current_token.value == FUN:
            node = self.function_declaration()
        elif self.current_token.value == TYPE:
            node = self.parse_type_decl()
        elif self.current_token.type == LTYPE:
            if self.current_token.value == STRUCT:
                node = self.parse_struct_decl()
            elif self.current_token.value == OBJECT:
                node = self.parse_class_decl()
            elif self.current_token.value == ENUM:
                node = self.parse_enum_decl()
        elif self.current_token.value == EOF:
            return
        else:
            self.next_token()
            node = self.parse_stmt()
        return node

    def parse_square_bracket_expr(self, token):
        if token.value == LBRACK:
            items = []
            while self.current_token.value != RBRACK:
                items.append(self.parse_any_expr())
                if self.current_token.value == COMMA:
                    self.next_token()
                else:
                    break
            self.consume_value(RBRACK)
            return OxyCollection(LIST, self.line_num, False, *items)
        elif self.current_token.type == LTYPE:
            type_token = self.next_token()
            if self.current_token.value == COMMA:
                return self.parse_dict_literal(token)
            elif self.current_token.value == RBRACK:
                self.next_token()
                return self.parse_collection_literal(token, type_token)
        elif self.current_token.type == NUMBER:
            tok = self.parse_any_expr()
            if self.current_token.value == COMMA:
                return self.parse_slice_expr(tok)
            else:
                self.consume_value(RBRACK)
                access = self.parse_acc_coll(token, tok)
                if self.current_token.value in ASSIGNMENT_OP:
                    op = self.current_token
                    if op.value in INCREMENTAL_ASSIGNMENT_OP:
                        return OxyIncrementAssign(access, op.value, self.line_num)
                    else:
                        self.next_token()
                        right = self.parse_any_expr()
                        if op.value == ASSIGN:
                            return OxyAssign(access, op.value, right, self.line_num)

                        return OxyOpAssign(access, op.value, right, self.line_num)
                return access
        elif token.type == NAME:
            self.consume_value(LBRACK)
            tok = self.parse_any_expr()
            if self.current_token.value == COMMA:
                return self.parse_slice_expr(tok)

            self.consume_value(RBRACK)
            return self.parse_acc_coll(token, tok)
        else:
            raise SyntaxError

    def parse_slice_expr(self, token):
        pass

    def parse_cbrace_expr(self, token):
        if token.value == LBRACE:
            pairs = OrderedDict()
            while self.current_token.value != RBRACE:
                key = self.parse_any_expr()
                self.consume_value(ASSIGN)
                pairs[key.value] = self.parse_any_expr()
                if self.current_token.value == COMMA:
                    self.next_token()
                else:
                    break
            self.consume_value(RBRACE)
            return OxyHashMap(pairs, self.line_num)
        else:
            raise SyntaxError('Wait... what?')

    def parse_tuple_literal(self, token):
        if token.value == LPAREN:
            items = []
            while self.current_token.value != RPAREN:
                items.append(self.parse_any_expr())
                if self.current_token.value == COMMA:
                    self.next_token()
                else:
                    break
            self.consume_value(RPAREN)
            return OxyCollection(TUPLE, self.line_num, False, *items)

    def parse_collection_literal(self, token, type_token):
        if self.current_token.value == ASSIGN:
            return self.parse_aot_assign(token, type_token)
        else:
            raise NotImplementedError

    def parse_acc_coll(self, collection, key):
        return OxyCollectionAccess(collection, key, self.line_num)

    def parse_aot_assign(self, token, type_token):
        raise NotImplementedError

    def parse_dot_operator(self, token):
        self.consume_value(DOT)
        field = self.current_token.value
        self.next_token()
        return OxyDotAccess(token.value, field, self.line_num)

    def parse_name_stmt(self):
        token = self.next_token()
        if self.current_token.value == LPAREN:
            node = self.function_call(token)
        elif self.current_token.value == LBRACK:
            self.next_token()
            node = self.parse_square_bracket_expr(token)
        elif self.current_token.value in ASSIGNMENT_OP:
            node = self.parse_assign_stmt(token)
        else:
            raise SyntaxError('Line {}'.format(self.line_num))
        return node

    def parse_prop_method(self, token):
        self.consume_value(DOT)
        field = self.current_token.value
        self.next_token()
        left = OxyDotAccess(token.value, field, self.line_num)
        token = self.next_token()
        if token.value in ASSIGNMENT_OP:
            return self.parse_field_assign(token, left)

        return self.parse_method_call(token, left)

    def parse_method_call(self, _, left):
        args = []
        named_args = {}
        while self.current_token.value != RPAREN:
            while self.current_token.type == NEWLINE:
                self.consume_type(NEWLINE)
            if self.current_token.value in (LPAREN, LBRACK, LBRACE):
                args.append(self.bracket_literal())
            elif self.preview().value == ASSIGN:
                name = self.parse_any_expr().value
                self.consume_value(ASSIGN)
                named_args[name] = self.parse_any_expr()
            else:
                args.append(self.parse_any_expr())
            while self.current_token.type == NEWLINE:
                self.consume_type(NEWLINE)
            if self.current_token.value != RPAREN:
                self.consume_value(COMMA)
        method = OxyMethodCall(left.obj, left.field, args,
                               self.line_num, named_args)
        self.next_token()
        return method

    def parse_field_assign(self, token, left):
        if token.value == ASSIGN:
            right = self.parse_any_expr()
            node = OxyAssign(left, token.value, right, self.line_num)
        elif token.value in ARITHMETIC_ASSIGNMENT_OP:
            right = self.parse_any_expr()
            node = OxyOpAssign(left, token.value, right, self.line_num)
        elif token.value in INCREMENTAL_ASSIGNMENT_OP:
            node = OxyIncrementAssign(left, token.value, self.line_num)
        else:
            raise SyntaxError(
                'Unknown assignment operator: {}'.format(token.value))
        return node

    def parse_dict_literal(self, token):
        raise NotImplementedError

    def parse_return_statement(self):
        self.next_token()
        return OxyReturn(self.parse_any_expr(), self.line_num)

    def parse_if_expr(self):
        self.indent_level += 1
        token = self.next_token()
        comp = OxyIfExpr(token.value, [self.parse_any_expr()], [
                         self.parse_compound_stmt()], token.indent_level, self.line_num)
        if self.current_token.indent_level < comp.indent_level:
            self.indent_level -= 1
            return comp
        while self.current_token.value == ELSE_IF:
            self.next_token()
            comp.comps.append(self.parse_any_expr())
            comp.blocks.append(self.parse_compound_stmt())
        if self.current_token.value == ELSE:
            self.next_token()
            comp.comps.append(OxyElseExpr())
            comp.blocks.append(self.parse_compound_stmt())
        self.indent_level -= 1
        return comp

    def parse_while_expr(self):
        self.indent_level += 1
        token = self.next_token()
        comp = OxyWhileExpr(token.value, self.parse_any_expr(),
                            self.parse_loop_block(), self.line_num)
        self.indent_level -= 1
        return comp

    def parse_for_stmt(self):
        self.indent_level += 1
        self.next_token()
        elements = []
        while self.current_token.value != IN:
            elements.append(self.parse_any_expr())
            if self.current_token.value == COMMA:
                self.consume_value(COMMA)
        self.consume_value(IN)
        iterator = self.parse_any_expr()
        if self.current_token.value == NEWLINE:
            self.consume_type(NEWLINE)
        block = self.parse_loop_block()
        loop = OxyForExpr(iterator, block, elements, self.line_num)
        self.indent_level -= 1
        return loop

    def parse_switch_stmt(self):
        self.indent_level += 1
        value = self.parse_any_expr()
        switch = OxySwitchStmt(value, [], self.line_num)
        if self.current_token.type == NEWLINE:
            self.next_token()
        while self.parse_handle_indents():
            switch.cases.append(self.case_statement())
            if self.current_token.type == NEWLINE:
                self.next_token()
            elif self.current_token.type == EOF:
                return switch
        self.indent_level -= 1
        return switch

    def case_statement(self):
        self.indent_level += 1
        if self.current_token.value == CASE:
            self.next_token()
            value = self.parse_any_expr()
        elif self.current_token.value == DEFAULT:
            self.next_token()
            value = DEFAULT
        else:
            raise SyntaxError
        block = self.parse_compound_stmt()
        self.indent_level -= 1
        return OxyCaseStmt(value, block, self.line_num)

    def parse_loop_block(self):
        nodes = self.parse_stmt_list()
        root = OxyLoopBlock()
        for node in nodes:
            root.children.append(node)
        return root

    def parse_assign_stmt(self, token):
        if token.value == CONST:
            read_only = True
            self.next_token()
            token = self.current_token
            self.next_token()
        else:
            read_only = False
        left = self.variable(token, read_only)
        token = self.next_token()
        if token.value == ASSIGN:
            right = self.parse_any_expr()
            node = OxyAssign(left, token.value, right, self.line_num)
        elif token.value in ARITHMETIC_ASSIGNMENT_OP:
            right = self.parse_any_expr()
            node = OxyOpAssign(left, token.value, right, self.line_num)
        elif token.value in INCREMENTAL_ASSIGNMENT_OP:
            node = OxyIncrementAssign(left, token.value, self.line_num)
        elif token.value == COLON:
            type_node = self.type_spec()
            var = OxyVarDecl(left, type_node, self.line_num)
            node = self.parse_var_assingment(var)
        else:
            raise SyntaxError(
                'Unknown assignment operator: {}'.format(token.value))
        return node

    def typ(self, token):
        return OxyType(token.value, self.line_num)

    def variable(self, token, read_only=False):
        return OxyVar(token.value, self.line_num, read_only)

    def parse_const_expr(self, token):
        return OxyConstant(token.value, self.line_num)

    def parse_factoring(self):
        token = self.current_token
        preview = self.preview()
        if preview.value == DOT:
            if self.preview(2).type == NAME and self.preview(3).value == LPAREN:
                return self.parse_prop_method(self.next_token())

            self.next_token()
            return self.parse_dot_operator(token)
        elif token.value in (PLUS, MINUS, BINARY_ONES_COMPLIMENT):
            self.next_token()
            return OxyUnaryOp(token.value, self.parse_factoring(), self.line_num)
        elif token.value == NOT:
            self.next_token()
            return OxyUnaryOp(token.value, self.parse_any_expr(), self.line_num)
        elif token.type == NUMBER:
            self.next_token()
            return OxyNum(token.value, token.value_type, self.line_num)
        elif token.type == STRING:
            self.next_token()
            return OxyStr(token.value, self.line_num)
        elif token.value == FUN:
            return self.function_declaration()
        elif token.type == LTYPE:
            return self.type_spec()
        elif token.value == LPAREN:
            if self.func_args or not self.parse_find_until(COMMA, RPAREN):
                self.func_args = False
                if preview.value == RPAREN:
                    return []

                self.next_token()
                node = self.parse_any_expr()
                self.consume_value(RPAREN)
            else:
                token = self.next_token()
                node = self.parse_tuple_literal(token)

            return node
        elif preview.value == LPAREN:
            self.next_token()
            return self.function_call(token)
        elif preview.value == LBRACK:
            self.next_token()
            return self.parse_square_bracket_expr(token)
        elif token.value == LBRACK:
            self.next_token()
            return self.parse_square_bracket_expr(token)
        elif token.value == LBRACE:
            self.next_token()
            return self.parse_cbrace_expr(token)
        elif token.type == NAME:
            self.next_token()
            if token.value in self.user_types:
                return self.typ(token)
            return self.variable(token)
        elif token.type == CONSTANT:
            self.next_token()
            return self.parse_const_expr(token)
        else:
            raise SyntaxError

    def parse_any_term(self):
        node = self.parse_factoring()
        ops = (MUL, DIV, FLOORDIV, MOD, POWER, CAST, RANGE) + \
            COMPARISON_OP + LOGICAL_OP + BINARY_OP
        while self.current_token.value in ops:
            token = self.next_token()
            if token.value in COMPARISON_OP or token.value in LOGICAL_OP or token.value in BINARY_OP:
                node = OxyBinOp(node, token.value, self.parse_any_expr(), self.line_num)
            elif token.value == RANGE:
                node = OxyRange(node, self.parse_any_expr(), self.line_num)
            else:
                node = OxyBinOp(node, token.value,
                                self.parse_factoring(), self.line_num)
        return node

    def parse_any_expr(self):
        node = self.parse_any_term()
        while self.current_token.value in (PLUS, MINUS):
            token = self.next_token()
            node = OxyBinOp(node, token.value, self.parse_any_term(), self.line_num)
        return node

    def parse(self) -> OxyProgram:
        node = self.parse_program_text()
        if self.current_token.type != EOF:
            raise SyntaxError('Unexpected end of program')
        return node
