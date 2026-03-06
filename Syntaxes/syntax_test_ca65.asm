; SYNTAX TEST "Packages/65816.tmbundle/Syntaxes/ca65.sublime-syntax"

; foo
; ^ source.asm.ca65 comment.line
; <- punctuation.definition.comment

/* something */
;  ^ source.asm.ca65 comment.block
; <- punctuation.definition.comment.begin
;            ^ punctuation.definition.comment.end