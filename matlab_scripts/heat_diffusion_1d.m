function heat_diffusion_1d()
    % Parameters
    L = 1;          % Length of domain
    T = 0.5;        % Total time
    nx = 50;        % Number of spatial points
    nt = 1000;      % Number of time steps
    alpha = 0.1;    % Thermal diffusivity
    
    % Grid setup
    dx = L/(nx-1);
    dt = T/(nt-1);
    x = linspace(0, L, nx);
    t = linspace(0, T, nt);
    
    % Check stability condition
    r = alpha*dt/(dx^2);
    if r > 0.5
        error('Stability condition not met. Reduce dt or increase dx.');
    end
    
    % Initialize temperature field with initial conditions
    u = zeros(nx, nt);
    % Initial condition: Gaussian pulse
    u(:,1) = exp(-(x-L/2).^2/0.1);
    
    % Boundary conditions (fixed at zero)
    u(1,:) = 0;
    u(end,:) = 0;
    
    % Solve using FTCS scheme
    for n = 1:nt-1
        for i = 2:nx-1
            u(i,n+1) = u(i,n) + r*(u(i+1,n) - 2*u(i,n) + u(i-1,n));
        end
    end
    
    % Create animation
    figure('Position', [100 100 800 400]);
    for n = 1:50:nt
        plot(x, u(:,n), 'b-', 'LineWidth', 2);
        title(sprintf('Heat Diffusion at t = %.3f', t(n)));
        xlabel('Position (x)');
        ylabel('Temperature (u)');
        grid on;
        axis([0 L 0 1]);
        drawnow;
        pause(0.1);
    end
    
    % Create surface plot
    figure('Position', [100 100 800 600]);
    [X, T] = meshgrid(x, t);
    surf(X, T, u');
    colormap('jet');
    colorbar;
    xlabel('Position (x)');
    ylabel('Time (t)');
    zlabel('Temperature (u)');
    title('Heat Diffusion Solution');
    view(45, 45);
end