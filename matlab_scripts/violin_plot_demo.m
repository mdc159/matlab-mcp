% Generate synthetic data for 5 violin plots
rng(42); % Set random seed for reproducibility

% Generate data with different means and same standard deviation
n_samples = 1000;
std_dev = 1.5;
means = [2, 4, 3, 5, 3.5];
data = cell(1, 5);

for i = 1:5
    % Using randn for normal distribution
    data{i} = std_dev * randn(n_samples, 1) + means(i);
end

% Create plot
figure('Position', [100, 100, 800, 600]);
hold on;

colors = [0.3 0.5 0.7; 0.7 0.3 0.5; 0.5 0.7 0.3; 0.3 0.7 0.7; 0.7 0.5 0.3];

for i = 1:5
    % Create simple distribution visualization
    [counts, edges] = hist(data{i}, 30);
    centers = (edges(1:end-1) + edges(2:end)) / 2;
    scaled_counts = 0.4 * counts / max(counts);
    
    % Plot the distribution on both sides
    plot(i + scaled_counts, centers, 'Color', colors(i,:), 'LineWidth', 2);
    plot(i - scaled_counts, centers, 'Color', colors(i,:), 'LineWidth', 2);
    
    % Fill the area
    patch([i + scaled_counts, i - fliplr(scaled_counts)], ...
          [centers, fliplr(centers)], ...
          colors(i,:), 'FaceAlpha', 0.3);
    
    % Add median line
    median_val = median(data{i});
    line([i-0.2 i+0.2], [median_val median_val], 'Color', 'k', 'LineWidth', 2);
    
    % Add mean marker
    plot(i, mean(data{i}), 'k*', 'MarkerSize', 8);
end

% Customize plot appearance
title('Distribution of Values Across Groups', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('Groups', 'FontSize', 12);
ylabel('Values', 'FontSize', 12);
grid on;
set(gca, 'XTick', 1:5, 'XTickLabel', {'Group A', 'Group B', 'Group C', 'Group D', 'Group E'});

% Add mean values as text
for i = 1:5
    max_val = max(data{i});
    text(i, max_val+0.5, sprintf('μ=%.1f', means(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 10);
end

% Set axis limits
ylim([min([data{:}])-1, max([data{:}])+1]);
xlim([0.5, 5.5]);

hold off;