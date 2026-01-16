program TesteFunc;
var 
    x, y, r: integer;

{ Funcao auxiliar }
procedure Saudacao;
begin
    writeln('Inicio do Calculo')
end;

begin
    Saudacao;
    x := 10;
    y := 20;
    
    { Simulacao de funcao simples usando variaveis globais }
    writeln('Valores: ', x, ' e ', y);
    
    if x < y then
        writeln('O maior e ', y)
    else
        writeln('O maior e ', x)
end.
