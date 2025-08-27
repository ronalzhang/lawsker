/**
 * Data Visualization System for Lawsker
 * Professional charts and analytics components
 */

class DataVisualization {
  constructor() {
    this.charts = new Map();
    this.colors = {
      primary: '#2563eb',
      secondary: '#7c3aed',
      success: '#059669',
      warning: '#d97706',
      error: '#dc2626',
      gray: '#6b7280'
    };
    this.init();
  }

  init() {
    // Auto-initialize charts on page load
    document.addEventListener('DOMContentLoaded', () => {
      this.initializeCharts();
    });
  }

  initializeCharts() {
    // Initialize all chart elements
    document.querySelectorAll('[data-chart]').forEach(element => {
      const chartType = element.getAttribute('data-chart');
      const chartData = this.getChartData(element);
      
      switch (chartType) {
        case 'donut':
          this.createDonutChart(element, chartData);
          break;
        case 'bar':
          this.createBarChart(element, chartData);
          break;
        case 'line':
          this.createLineChart(element, chartData);
          break;
        case 'progress':
          this.createProgressChart(element, chartData);
          break;
        case 'stats':
          this.createStatsCard(element, chartData);
          break;
      }
    });
  }

  getChartData(element) {
    const dataAttr = element.getAttribute('data-chart-data');
    if (dataAttr) {
      try {
        return JSON.parse(dataAttr);
      } catch (e) {
        console.warn('Invalid chart data:', dataAttr);
        return {};
      }
    }
    return {};
  }

  // Donut Chart
  createDonutChart(container, data) {
    const { value = 75, max = 100, label = '', color = 'primary' } = data;
    const percentage = (value / max) * 100;
    const circumference = 2 * Math.PI * 80; // radius = 80
    const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

    container.innerHTML = `
      <div class="donut-chart">
        <svg viewBox="0 0 200 200">
          <defs>
            <linearGradient id="donut-gradient-${color}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:${this.colors[color]};stop-opacity:1" />
              <stop offset="100%" style="stop-color:${this.colors.secondary};stop-opacity:1" />
            </linearGradient>
          </defs>
          <circle class="donut-segment donut-background" cx="100" cy="100" r="80"></circle>
          <circle class="donut-segment donut-${color}" cx="100" cy="100" r="80" 
                  stroke="url(#donut-gradient-${color})"
                  stroke-dasharray="0 ${circumference}"
                  style="animation: donut-fill 1.5s ease-out forwards 0.5s"></circle>
        </svg>
        <div class="donut-center">
          <div class="donut-value">${value}${data.suffix || ''}</div>
          <div class="donut-label">${label}</div>
        </div>
      </div>
    `;

    // Animate the donut
    setTimeout(() => {
      const donutSegment = container.querySelector(`.donut-${color}`);
      donutSegment.style.strokeDasharray = strokeDasharray;
    }, 500);

    // Add CSS animation
    if (!document.querySelector('#donut-animations')) {
      const style = document.createElement('style');
      style.id = 'donut-animations';
      style.textContent = `
        @keyframes donut-fill {
          from { stroke-dasharray: 0 ${circumference}; }
          to { stroke-dasharray: ${strokeDasharray}; }
        }
      `;
      document.head.appendChild(style);
    }
  }

  // Bar Chart
  createBarChart(container, data) {
    const { items = [], maxValue } = data;
    const max = maxValue || Math.max(...items.map(item => item.value));

    const barsHTML = items.map(item => {
      const height = (item.value / max) * 160; // max height 160px
      return `
        <div class="bar-item">
          <div class="bar" style="height: ${height}px;" data-value="${item.value}">
            <div class="bar-value">${item.value}</div>
          </div>
          <div class="bar-label">${item.label}</div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="bar-chart">
        ${barsHTML}
      </div>
    `;

    // Animate bars
    setTimeout(() => {
      container.querySelectorAll('.bar').forEach((bar, index) => {
        setTimeout(() => {
          bar.style.height = bar.style.height;
        }, index * 100);
      });
    }, 300);
  }

  // Line Chart
  createLineChart(container, data) {
    const { points = [], width = 400, height = 200 } = data;
    const maxValue = Math.max(...points.map(p => p.y));
    const minValue = Math.min(...points.map(p => p.y));
    const range = maxValue - minValue || 1;

    // Generate SVG path
    const pathData = points.map((point, index) => {
      const x = (index / (points.length - 1)) * (width - 40) + 20;
      const y = height - 20 - ((point.y - minValue) / range) * (height - 40);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    // Generate area path
    const areaData = pathData + ` L ${width - 20} ${height - 20} L 20 ${height - 20} Z`;

    container.innerHTML = `
      <div class="line-chart">
        <svg viewBox="0 0 ${width} ${height}">
          <defs>
            <linearGradient id="line-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style="stop-color:${this.colors.primary};stop-opacity:0.3" />
              <stop offset="100%" style="stop-color:${this.colors.primary};stop-opacity:0" />
            </linearGradient>
          </defs>
          
          <!-- Grid lines -->
          ${this.generateGridLines(width, height)}
          
          <!-- Area fill -->
          <path class="area-fill" d="${areaData}" fill="url(#line-gradient)"></path>
          
          <!-- Data line -->
          <path class="data-line" d="${pathData}" stroke-dasharray="${pathData.length}" stroke-dashoffset="${pathData.length}"></path>
          
          <!-- Data points -->
          ${points.map((point, index) => {
            const x = (index / (points.length - 1)) * (width - 40) + 20;
            const y = height - 20 - ((point.y - minValue) / range) * (height - 40);
            return `<circle class="data-point" cx="${x}" cy="${y}" data-value="${point.y}" data-label="${point.label || ''}"></circle>`;
          }).join('')}
        </svg>
      </div>
    `;

    // Animate line
    setTimeout(() => {
      const line = container.querySelector('.data-line');
      line.style.strokeDashoffset = '0';
    }, 500);

    // Add tooltips to data points
    this.addChartTooltips(container);
  }

  generateGridLines(width, height) {
    const lines = [];
    const gridCount = 5;
    
    // Horizontal lines
    for (let i = 0; i <= gridCount; i++) {
      const y = 20 + (i / gridCount) * (height - 40);
      lines.push(`<line class="grid-line" x1="20" y1="${y}" x2="${width - 20}" y2="${y}"></line>`);
    }
    
    // Vertical lines
    for (let i = 0; i <= gridCount; i++) {
      const x = 20 + (i / gridCount) * (width - 40);
      lines.push(`<line class="grid-line" x1="${x}" y1="20" x2="${x}" y2="${height - 20}"></line>`);
    }
    
    return lines.join('');
  }

  // Progress Chart
  createProgressChart(container, data) {
    const { value = 0, max = 100, label = '', color = 'primary' } = data;
    const percentage = Math.min((value / max) * 100, 100);

    container.innerHTML = `
      <div class="progress-chart">
        <div class="progress-labels">
          <span>${label}</span>
          <span>${value}/${max}</span>
        </div>
        <div class="progress-bar-chart">
          <div class="progress-fill-chart progress-${color}" style="width: 0%"></div>
        </div>
        <div class="progress-labels">
          <span>0</span>
          <span>${max}</span>
        </div>
      </div>
    `;

    // Animate progress
    setTimeout(() => {
      const fill = container.querySelector('.progress-fill-chart');
      fill.style.width = `${percentage}%`;
    }, 300);
  }

  // Stats Card
  createStatsCard(container, data) {
    const { 
      value = 0, 
      label = '', 
      icon = 'chart-bar', 
      trend = null, 
      color = 'primary',
      description = ''
    } = data;

    let trendHTML = '';
    if (trend) {
      const trendIcon = trend.direction === 'up' ? 'chevron-up' : 
                       trend.direction === 'down' ? 'chevron-down' : 'minus';
      trendHTML = `
        <div class="stat-trend ${trend.direction}">
          <div data-icon="${trendIcon}" style="width: 16px; height: 16px;"></div>
          ${trend.value}%
        </div>
      `;
    }

    container.innerHTML = `
      <div class="stat-card">
        <div class="stat-header">
          <div class="stat-icon ${color}">
            <div data-icon="${icon}" style="width: 24px; height: 24px;"></div>
          </div>
          ${trendHTML}
        </div>
        <div class="stat-value">${value.toLocaleString()}</div>
        <div class="stat-label">${label}</div>
        ${description ? `<div class="stat-description">${description}</div>` : ''}
      </div>
    `;

    // Animate value counting
    this.animateCounter(container.querySelector('.stat-value'), value);
  }

  // Utility Methods
  animateCounter(element, targetValue) {
    const startValue = 0;
    const duration = 1500;
    const startTime = performance.now();

    const updateCounter = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOut);
      
      element.textContent = currentValue.toLocaleString();
      
      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      }
    };

    requestAnimationFrame(updateCounter);
  }

  addChartTooltips(container) {
    const tooltip = document.createElement('div');
    tooltip.className = 'chart-tooltip';
    document.body.appendChild(tooltip);

    container.querySelectorAll('.data-point').forEach(point => {
      point.addEventListener('mouseenter', (e) => {
        const value = e.target.getAttribute('data-value');
        const label = e.target.getAttribute('data-label');
        tooltip.innerHTML = `${label ? label + ': ' : ''}${value}`;
        tooltip.classList.add('visible');
      });

      point.addEventListener('mousemove', (e) => {
        tooltip.style.left = e.pageX + 10 + 'px';
        tooltip.style.top = e.pageY - 10 + 'px';
      });

      point.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
      });
    });
  }

  // Public API
  updateChart(containerId, newData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const chartType = container.getAttribute('data-chart');
    container.setAttribute('data-chart-data', JSON.stringify(newData));
    
    // Re-create the chart with new data
    switch (chartType) {
      case 'donut':
        this.createDonutChart(container, newData);
        break;
      case 'bar':
        this.createBarChart(container, newData);
        break;
      case 'line':
        this.createLineChart(container, newData);
        break;
      case 'progress':
        this.createProgressChart(container, newData);
        break;
      case 'stats':
        this.createStatsCard(container, newData);
        break;
    }
  }

  createDashboard(containerId, config) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const { title, charts = [] } = config;

    let dashboardHTML = '';
    if (title) {
      dashboardHTML += `<h2 class="text-2xl font-bold text-primary mb-6">${title}</h2>`;
    }

    dashboardHTML += '<div class="stats-grid">';
    charts.forEach((chart, index) => {
      dashboardHTML += `<div data-chart="${chart.type}" data-chart-data='${JSON.stringify(chart.data)}' id="chart-${index}"></div>`;
    });
    dashboardHTML += '</div>';

    container.innerHTML = dashboardHTML;
    this.initializeCharts();
  }
}

// Initialize global instance
window.DataVisualization = new DataVisualization();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DataVisualization;
}