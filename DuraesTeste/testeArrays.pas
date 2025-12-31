program TesteArrays;
var 
    numeros: array [1..5] of integer;
    i, soma: integer;
begin
    soma := 0;
    writeln('Introduza 5 numeros para o array:');
    
    for i := 1 to 5 do
    begin
        readln(numeros[i]);
        soma := soma + numeros[i]
    end;
    
    writeln('A soma dos elementos e: ', soma);
    writeln('O ultimo elemento foi: ', numeros[5])
end.
