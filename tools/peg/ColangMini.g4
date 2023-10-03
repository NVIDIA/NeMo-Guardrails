grammar ColangMini;

program: stmt* EOF ;

stmts : stmt+ ;

stmt
    : compound_stmt
    | simple_stmt
    ;

simple_stmt
    : assignment
    | bot_stmt
    | user_stmt
    | samples
    | NEWLINE
    ;

// Compound statement
compound_stmt
    : define_user
    | define_bot
    | define_flow
    | define_subflow
    | else_stmt
    | if_stmt
    | while_stmt
    | when_stmt
    ;
// common elements

block
    : NEWLINE INDENT stmt (NEWLINE stmt)* DEDENT
    ;

samples: NEWLINE INDENT sample DEDENT ;
sample: STRING (NEWLINE STRING)* ;
// messages and flows

define_user:    DEFINE role intent samples ; 
define_bot:     DEFINE role intent samples ; 
define_flow:    DEFINE FLOW_KEYWORD flow_name block ;
define_subflow: DEFINE SUBFLOW_KEYWORD flow_name block ;

if_stmt: IF expression block (else_stmt | elif_stmt)* ;
elif_stmt: ELIF expression block ;
else_stmt: ELSE block ;

while_stmt: WHILE expression block ;
when_stmt: WHEN expression block ;

assignment: variable EQUALS expression NEWLINE ;

expression
    :   variable
    |   function_call
    |   arithmetic_expression
    |   STRING
    |   NUMBER

    ;

arithmetic_expression
    :   term (PLUS term)*
    |   term (MINUS term)*
    ;

term
    :   factor (MULTIPLY factor)*
    |   factor (DIVIDE factor)*
    ;

factor
    :   LPAREN expression RPAREN
    |   STRING
    |   NUMBER
    |   variable
    |   function_call
    ;

function_call: ID LPAREN (parameter (COMMA parameter)*)? RPAREN ;
parameter: ID EQUALS expression ;

bot_stmt: BOT_KEYWORD ID+;
user_stmt: USER_KEYWORD ID+;
variable: VARIABLE_DOLLAR | VARIABLE_BRACES ;

role: USER_KEYWORD | BOT_KEYWORD ;
intent: ID+ ; // Intent can be a sequence of identifiers
flow_name: ID+ ; // Flow name can be a sequence of identifiers
type: (USER_KEYWORD | BOT_KEYWORD | FLOW_KEYWORD | SUBFLOW_KEYWORD) ;
utterance: STRING ;

// Lexer rules

BOT_KEYWORD: 'bot';
USER_KEYWORD: 'user';
FLOW_KEYWORD: 'flow';
SUBFLOW_KEYWORD: 'subflow';
DEFINE: 'define' ;

ELSE: 'else';
IF: 'if';
ELIF: 'elif';
WHILE: 'while';
WHEN: 'when';

EQUALS: '=';
PLUS: '+';
MINUS: '-';
MULTIPLY: '*';
DIVIDE: '/';
LPAREN: '(';
RPAREN: ')';
COMMA: ',';

INDENT: 'INDENT';
DEDENT: 'DEDENT';

VARIABLE_DOLLAR: '$' ID ;
VARIABLE_BRACES: '{{' ID '}}' ;

NEWLINE : '\r'? '\n' ;
ID: [a-z_][a-zA-Z0-9_]* ;                // Parameter names
NUMBER: [0-9]+ ('.' [0-9]+)? ;           // Integers and floating-point numbers
STRING : '"' (.)*? '"';
SEPARATOR : [ \t\r\n]+ -> skip;
