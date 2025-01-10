% Script to generate first 10 Fibonacci numbers

% Initialize array with first two Fibonacci numbers
fib = zeros(1, 10);
fib(1) = 1;
fib(2) = 1;

% Generate remaining Fibonacci numbers
for i = 3:10
    fib(i) = fib(i-1) + fib(i-2);
end

% Display the results
disp('The first 10 Fibonacci numbers are:');
disp(fib);
