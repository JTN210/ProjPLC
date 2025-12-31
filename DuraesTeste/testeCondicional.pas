program TesteIf;
var 
    idade: integer;
begin
    writeln('Introduza a sua idade:');
    readln(idade);
    
    if idade >= 18 then
    begin
        writeln('Maior de idade.');
        if idade > 65 then
            writeln('Reformado.')
    end
    else
        writeln('Menor de idade.')
end.
