% Generate first 10 Fibonacci numbers
fib = zeros(1,10);
fib(1) = 1;
fib(2) = 1;
for i = 3:10
    fib(i) = fib(i-1) + fib(i-2);
end

disp('Fibonacci numbers:');
disp(fib);

% Create x-axis values (position indices)
x = 1:10;

% Create the plot
figure;
plot(x, fib, '-o');
grid on;
title('First 10 Fibonacci Numbers');
xlabel('Position');
ylabel('Value');