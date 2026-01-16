program TesteBasico;
var 
    a, b, res: integer;
begin
    writeln('Teste Basico');
    writeln('Introduza dois numeros:');
    readln(a);
    readln(b);
    
    res := a + b * 2;
    
    writeln('O resultado de ', a, ' + ', b, ' * 2 e: ', res)
end.
