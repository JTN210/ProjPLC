program ErroVar;
var 
    x: integer;
begin
    x := 10;
    y := 5; { ERRO: y nao foi declarado }
    writeln(x + y)
end.
