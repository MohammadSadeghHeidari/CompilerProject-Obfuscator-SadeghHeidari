grammar CMini;

program: (functionDecl)+;



functionDecl: type ID '(' params? ')' block;

params: param (',' param)*;
param: type ID;

block: '{' (varDecl | statement)* '}';

varDecl: type ID ('=' expr)? ';';

statement
    : block
    | 'if' '(' expr ')' statement ('else' statement)?
    | 'while' '(' expr ')' statement
    | 'return' expr? ';'
    | 'printf' '(' STRING (',' expr)* ')' ';'
    | expr ';'
    ;

expr
    : expr op=('*'|'/') expr
    | expr op=('+'|'-') expr
    | expr op=('=='|'!='|'<'|'>'|'<='|'>=') expr
    | ID '=' expr
    | ID '(' args? ')'         // ✅ پشتیبانی از فراخوانی تابع
    | ID
    | INT
    | '(' expr ')'
    ;

args: expr (',' expr)*;

type: 'int' | 'void';

ID: [a-zA-Z_][a-zA-Z_0-9]*;
INT: [0-9]+;
STRING : '"' ( ~["\\] | '\\' . )* '"' ;

WS: [ \t\r\n]+ -> skip;

