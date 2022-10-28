// This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
// https://gitlab.com/sosy-lab/software/coveriteam
//
// SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
//
// SPDX-License-Identifier: Apache-2.0

grammar CoVeriLang;

/* I see following plausible issues:
1. '{' if we want to go for blocks for function defs as this is used by dict
2. ';' used by sequence as well as statement delimiter. Now ";;" is used for seq but it is ugly
3. Should we go for python like syntax or C like?
*/


program :   (fun_decl)*? stmt_block ;

fun_decl:   'fun' ID '(' id_list?')' '{' stmt_block'}' ;

stmt_block
        :    (stmt DELIMITER)* ;

id_list :    ID (',' ID)* ;

stmt    :    spec_stmt
        |    exec_stmt
        |    return_stmt
        |    print_stmt
        |    set_actor_name_stmt
        ;

spec_stmt
        :    ID '=' assignable  ;

print_stmt
        :    'print(' (actor | artifact | STRING | ID) ')'           # PrintActor
        ;

exec_stmt
        :    'execute(' actor ',' ( ID | arg_map) ')'     # ExecuteActor
        ;

return_stmt
        :    'return' ID ;

set_actor_name_stmt
        :      'set_actor_name(' ID ',' STRING')'     # SetActorName
        ;

arg_map :    '{' map_item_list '}' ;

map_item_list
        :    map_item (',' map_item)*  ;
// Putting the value as optional. Gives opportunity to describe a set of strings.
map_item
        :    quoted_ID (':' (artifact | artifact_type | quoted_ID))?  ;

assignable
        :    exp
        |    artifact
        |    arg_map
        |    actor
        |    STRING
        |    exec_stmt
        ;

actor   :    'ActorFactory.create(' actor_type ',' name=(ID | STRING) (',' version=(STRING | ID))? ')' # Atomic
        |    ID '(' id_list? ')'        # FunCall
        |    utility_actor              # Utility
//These are the composite actors, wanted to put in separate rule but left recursion does not allow it
        |    'SEQUENCE' '('actor ',' actor ')'               # Sequence
        |    'ITE' '(' exp ',' actor (',' actor)? ')'        # ITE
        |    'REPEAT' '(' quoted_ID ',' actor ')'           # Iterative
        |    'PARALLEL' '(' actor ',' actor ')'              # Parallel
        |    'ParallelPortfolio' '('  actor (',' actor )* (',' exp)')'         # ParallelPortfolio
        |    ID                                              # ActorAlias
        |    '(' actor ')'                                   # Parenthesis
        ;

// The arg map in both joiner and copy are actually just list of quoted_IDs
utility_actor
        :    'Joiner' '(' artifact_type ',' arg_map ',' quoted_ID ')'    # Joiner
        |    'Comparator' '(' artifact_type ',' arg_map ',' quoted_ID ')'    # Comparator
        |    'Copy' '(' arg_map ')'                          # Copy
        |    'Rename' '(' arg_map ')'                        # Rename
        |    'TestSpecToSpec()'                              # TestSpecToSpec
        |    'SpecToTestSpec()'                              # SpecToTestSpec
        |    'ClassificationToActorDefinition()'             # ClassificationToActorDefinition
        |    'Identity' '(' (actor | arg_map) ')'            # Identity
        ;


artifact
        :    'ArtifactFactory.create(' artifact_type ',' (ID | STRING) ')'  # CreateArtifact
        |    ID                                                             # ArtifactAlias
        |    ID '.' ID                                                      # ArtifactFromMapItem
        ;

artifact_type
        :    TYPE_NAME ;
actor_type
        :    TYPE_NAME ;


exp     :    exp BIN_OP exp                # BinaryLogical
        |    'NOT' exp                                      # NotLogical
        |    'INSTANCEOF' '(' ID ',' artifact_type ')'      # InstanceOf
        |    'ELEMENTOF'  '(' ID ',' '{' verdict_list '}' ')'    # ElementOf
        |    ID                            # ExpAlias
        |    '(' exp ')'                   # Paren
        ;

verdict_list
        :    VERDICT ( ',' VERDICT)* ;

tc_exp  :    'TODO---'  ;
quoted_ID
        :    '\'' ID '\'' ;
// TODO I think here we can put production rules
VERDICT :    'FALSE' {self.text = "RESULT_CLASS_FALSE"}
        |    'TRUE' {self.text = "RESULT_CLASS_TRUE"}
        |    'UNKNOWN' {self.text = "RESULT_CLASS_OTHER"}
        ;

BIN_OP  :   'AND' | 'OR' | '==' | '!=' ;
// Basically path string and option str are same.
ID      :    LOWER_CASE (LETTER | DIGIT | [_])* ;
// Basically anything in the double quotes.
// TODO Checking if the string is appropriate to be done in the interpreter.
STRING  :    '"' ~('"')* '"' ;
TYPE_NAME
        :    UPPER_CASE (LETTER | DIGIT)* ;
//Maybe do uppercase and lowercase too
LETTER  :    LOWER_CASE | UPPER_CASE  ;
LOWER_CASE
        :    [a-z]  ;
UPPER_CASE
        :    [A-Z]  ;
DIGIT   :    [0-9] ;
NEWLINE :    '\r'? '\n' -> skip;
WS      :    [ \t]+ -> skip ;
DELIMITER
        :    ';'  ;
COMMENT :    '//' ~[\r\n]* -> skip ;
