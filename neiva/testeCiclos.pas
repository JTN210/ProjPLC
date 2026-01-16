program TesteLoops;
var 
    n, i: integer;
begin
    writeln('Contar numeros pares ate:');
    readln(n);
    i := 1;
    
    while i <= n do
    begin
        if (i mod 2) = 0 then
            writeln(i, ' e Par');
        
        i := i + 1
    end
end.
