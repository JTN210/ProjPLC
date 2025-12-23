program CalculoFatorial;
var 
    n, fat, contador: integer;
begin
    writeln('--- Calculadora de Fatorial ---');
    n := 5;
    
    fat := 1;
    contador := 1;
    
    while contador <= n do
    begin
        fat := fat * contador;
        contador := contador + 1
    end;
    
    writeln('O Fatorial de 5 e:');
    writeln(fat)
end.