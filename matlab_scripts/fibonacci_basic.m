% Generate and display first 10 Fibonacci numbers
fib = zeros(1,10);
fib(1) = 1;
fib(2) = 1;
for i = 3:10
    fib(i) = fib(i-1) + fib(i-2);
end

% Display the numbers
disp('The first 10 Fibonacci numbers are:');
disp(fib);