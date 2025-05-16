# Generated from CMini.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .CMiniParser import CMiniParser
else:
    from CMiniParser import CMiniParser

# This class defines a complete listener for a parse tree produced by CMiniParser.
class CMiniListener(ParseTreeListener):

    # Enter a parse tree produced by CMiniParser#program.
    def enterProgram(self, ctx:CMiniParser.ProgramContext):
        pass

    # Exit a parse tree produced by CMiniParser#program.
    def exitProgram(self, ctx:CMiniParser.ProgramContext):
        pass


    # Enter a parse tree produced by CMiniParser#functionDecl.
    def enterFunctionDecl(self, ctx:CMiniParser.FunctionDeclContext):
        pass

    # Exit a parse tree produced by CMiniParser#functionDecl.
    def exitFunctionDecl(self, ctx:CMiniParser.FunctionDeclContext):
        pass


    # Enter a parse tree produced by CMiniParser#params.
    def enterParams(self, ctx:CMiniParser.ParamsContext):
        pass

    # Exit a parse tree produced by CMiniParser#params.
    def exitParams(self, ctx:CMiniParser.ParamsContext):
        pass


    # Enter a parse tree produced by CMiniParser#param.
    def enterParam(self, ctx:CMiniParser.ParamContext):
        pass

    # Exit a parse tree produced by CMiniParser#param.
    def exitParam(self, ctx:CMiniParser.ParamContext):
        pass


    # Enter a parse tree produced by CMiniParser#block.
    def enterBlock(self, ctx:CMiniParser.BlockContext):
        pass

    # Exit a parse tree produced by CMiniParser#block.
    def exitBlock(self, ctx:CMiniParser.BlockContext):
        pass


    # Enter a parse tree produced by CMiniParser#varDecl.
    def enterVarDecl(self, ctx:CMiniParser.VarDeclContext):
        pass

    # Exit a parse tree produced by CMiniParser#varDecl.
    def exitVarDecl(self, ctx:CMiniParser.VarDeclContext):
        pass


    # Enter a parse tree produced by CMiniParser#statement.
    def enterStatement(self, ctx:CMiniParser.StatementContext):
        pass

    # Exit a parse tree produced by CMiniParser#statement.
    def exitStatement(self, ctx:CMiniParser.StatementContext):
        pass


    # Enter a parse tree produced by CMiniParser#expr.
    def enterExpr(self, ctx:CMiniParser.ExprContext):
        pass

    # Exit a parse tree produced by CMiniParser#expr.
    def exitExpr(self, ctx:CMiniParser.ExprContext):
        pass


    # Enter a parse tree produced by CMiniParser#args.
    def enterArgs(self, ctx:CMiniParser.ArgsContext):
        pass

    # Exit a parse tree produced by CMiniParser#args.
    def exitArgs(self, ctx:CMiniParser.ArgsContext):
        pass


    # Enter a parse tree produced by CMiniParser#type.
    def enterType(self, ctx:CMiniParser.TypeContext):
        pass

    # Exit a parse tree produced by CMiniParser#type.
    def exitType(self, ctx:CMiniParser.TypeContext):
        pass



del CMiniParser