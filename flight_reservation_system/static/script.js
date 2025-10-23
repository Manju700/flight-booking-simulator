document.addEventListener("DOMContentLoaded", () => {
  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  // Seat map builder
  const grid = document.getElementById("seat-grid");
  if (grid && window.__SEAT_SETUP__) {
    const { rows, cols, booked } = window.__SEAT_SETUP__;
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    const fid = grid.dataset.fid;
    const selected = new Set();
    const selectedWrap = document.getElementById("selected-seats");
    const form = document.getElementById("bookForm");

    // adjust grid columns to account for aisle gaps after each 3 seats
    const gapCount = Math.floor(cols / 3);
    grid.style.gridTemplateColumns = `repeat(${cols + gapCount}, 34px)`;

    function renderSelectedPills(){
      selectedWrap.innerHTML = "";
      // remove existing hidden inputs for seats
      if (form) {
        const olds = Array.from(form.querySelectorAll('input[name="seats"]'));
        olds.forEach(o => o.remove());
      }
      selected.forEach(s => {
        const span = document.createElement("span");
        span.className = "pill";
        span.textContent = s;
        selectedWrap.appendChild(span);
        // hidden input appended to form
        if (form) {
          const input = document.createElement("input");
          input.type = "hidden";
          input.name = "seats";
          input.value = s;
          form.appendChild(input);
        }
      });
    }

    for(let r=1; r<=rows; r++){
      for(let c=0; c<cols; c++){
        const s = `${r}${letters[c]}`;
        const btn = document.createElement("div");
        btn.className = "seat";
        btn.textContent = letters[c];
        if (booked.includes(s)) btn.classList.add("booked");
        btn.addEventListener("click", () => {
          if (btn.classList.contains("booked")) return;
          if (btn.classList.contains("selected")){
            btn.classList.remove("selected");
            selected.delete(s);
          } else {
            btn.classList.add("selected");
            selected.add(s);
          }
          renderSelectedPills();
        });
        grid.appendChild(btn);

        // aisle gap after each 3 seats (if seat layout has >=4)
        if ((c + 1) % 3 === 0 && c !== cols - 1) {
          const gap = document.createElement("div");
          gap.style.width = "20px";
          gap.style.height = "1px";
          gap.style.background = "transparent";
          grid.appendChild(gap);
        }
      }
    }

  }
});

document.addEventListener("DOMContentLoaded", () => {
  // Helper to find elements
  const grid = document.getElementById("seat-grid");
  const selectedWrap = document.getElementById("selected-seats");
  const farePerSeat = document.getElementById("fare-per-seat");
  const fareCount = document.getElementById("fare-count");
  const fareTotal = document.getElementById("fare-total");
  const previewSeats = document.getElementById("preview-seats");
  const previewTotal = document.getElementById("preview-total");
  const bookForm = document.getElementById("bookForm");

  // Modal elements
  const confirmModal = document.getElementById("confirmModal");
  const modalSeats = document.getElementById("modalSeats");
  const modalTotal = document.getElementById("modalTotal");
  const modalCancel = document.getElementById("modalCancel");
  const modalProceed = document.getElementById("modalProceed");
  const btnConfirm = document.getElementById("btnConfirm");
  const btnReset = document.getElementById("btnReset");

  if (!window.__SEAT_SETUP__ || !grid) return;

  const { rows, cols, booked } = window.__SEAT_SETUP__;
  const flightPrice = (window.__FLIGHT_META__ && window.__FLIGHT_META__.price) ? Number(window.__FLIGHT_META__.price) : 0;

  // set price in UI
  if (farePerSeat) farePerSeat.textContent = flightPrice.toLocaleString('en-IN');

  // prepare grid columns (account for aisle gaps)
  const gapCount = Math.floor(cols / 3);
  grid.style.gridTemplateColumns = `repeat(${cols + gapCount}, 34px)`;

  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const selected = new Set();

  function clearHiddenSeatInputs() {
    const olds = Array.from(bookForm.querySelectorAll('input[name="seats"]'));
    olds.forEach(o => o.remove());
  }

  function renderSelectedPills() {
    selectedWrap.innerHTML = "";
    clearHiddenSeatInputs();
    if (selected.size === 0) {
      selectedWrap.innerHTML = '<div class="muted small">No seats chosen yet</div>';
    } else {
      selected.forEach(s => {
        const span = document.createElement("span");
        span.className = "pill";
        span.textContent = s;
        selectedWrap.appendChild(span);

        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "seats";
        input.value = s;
        bookForm.appendChild(input);
      });
    }
    updateFareUI();
  }

  function updateFareUI() {
    const count = selected.size;
    if (fareCount) fareCount.textContent = count;
    const total = count * flightPrice;
    if (fareTotal) fareTotal.textContent = total.toLocaleString('en-IN');
    if (previewSeats) previewSeats.textContent = count ? Array.from(selected).join(", ") : "—";
    if (previewTotal) previewTotal.textContent = total.toLocaleString('en-IN');
    if (modalSeats) modalSeats.textContent = count;
    if (modalTotal) modalTotal.textContent = total.toLocaleString('en-IN');
  }

  // Build seats
  for (let r = 1; r <= rows; r++) {
    for (let c = 0; c < cols; c++) {
      const seatLabel = `${r}${letters[c]}`;
      const btn = document.createElement("div");
      btn.className = "seat";
      btn.setAttribute("data-seat", seatLabel);
      btn.textContent = letters[c];

      if (Array.isArray(booked) && booked.includes(seatLabel)) {
        btn.classList.add("booked");
      }

      btn.addEventListener("click", () => {
        if (btn.classList.contains("booked")) return;
        if (btn.classList.contains("selected")) {
          btn.classList.remove("selected");
          selected.delete(seatLabel);
        } else {
          // limit selection (optional)
          if (selected.size >= 6) {
            alert("Max 6 seats can be selected in demo.");
            return;
          }
          btn.classList.add("selected");
          selected.add(seatLabel);
        }
        renderSelectedPills();
      });

      grid.appendChild(btn);

      // aisle gap after 3 seats if needed
      if ((c + 1) % 3 === 0 && c !== cols - 1) {
        const gap = document.createElement("div");
        gap.style.width = "20px";
        gap.style.height = "1px";
        gap.style.background = "transparent";
        grid.appendChild(gap);
      }
    }
  }

  // Reset behavior
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      // clear selections visually
      const sel = grid.querySelectorAll(".seat.selected");
      sel.forEach(s => s.classList.remove("selected"));
      selected.clear();
      renderSelectedPills();
    });
  }

  // Confirm button -> open modal or proceed to validation
  if (btnConfirm) {
    btnConfirm.addEventListener("click", (e) => {
      e.preventDefault();
      if (selected.size === 0) {
        alert("Please select at least one seat before booking.");
        return;
      }
      // simple form validation
      const name = document.getElementById("fullname").value.trim();
      const email = document.getElementById("email").value.trim();
      const phone = document.getElementById("phone").value.trim();
      const phoneRegex = /^[0-9]{10}$/;
      if (!name || !email || !phone) {
        alert("Please fill name, email and phone.");
        return;
      }
      if (!phoneRegex.test(phone)) {
        alert("Enter a valid 10-digit phone number.");
        return;
      }

      // show modal
      if (confirmModal) {
        confirmModal.style.display = "flex";
      }
    });
  }

  // modal cancel
  if (modalCancel) {
    modalCancel.addEventListener("click", () => {
      if (confirmModal) confirmModal.style.display = "none";
    });
  }

  // modal proceed -> submit form
  if (modalProceed) {
    modalProceed.addEventListener("click", () => {
      // final check: ensure hidden inputs present
      if (selected.size === 0) {
        alert("No seats selected.");
        if (confirmModal) confirmModal.style.display = "none";
        return;
      }
      // Submit the form (it will POST to /book)
      bookForm.submit();
    });
  }

  // Click outside modal to close
  window.addEventListener("click", (ev) => {
    if (ev.target === confirmModal) confirmModal.style.display = "none";
  });

  // initialize ui
  renderSelectedPills();
  updateFareUI();
});

document.addEventListener("DOMContentLoaded", () => {
  const setup = window.__SEAT_SETUP__;
  if (!setup) return;

  const grid = document.getElementById("seat-grid");
  const selectedSeatsDiv = document.getElementById("selected-seats");

  grid.style.gridTemplateColumns = `repeat(${setup.cols}, 1fr)`;

  const selected = new Set();

  for (let r = 1; r <= setup.rows; r++) {
    for (let c = 1; c <= setup.cols; c++) {
      const seat = document.createElement("div");
      const seatId = `${r}${String.fromCharCode(64 + c)}`; // Example: 1A, 1B...

      seat.className = "seat";
      if (setup.booked.includes(seatId)) {
        seat.classList.add("booked");
      }

      seat.addEventListener("click", () => {
        if (seat.classList.contains("booked")) return;

        if (selected.has(seatId)) {
          selected.delete(seatId);
          seat.classList.remove("selected");
        } else {
          selected.add(seatId);
          seat.classList.add("selected");
        }

        // Update selected seats in form
        selectedSeatsDiv.innerHTML = Array.from(selected).join(", ");
        let hidden = document.querySelector("input[name=seats]");
        if (!hidden) {
          hidden = document.createElement("input");
          hidden.type = "hidden";
          hidden.name = "seats";
          document.getElementById("bookForm").appendChild(hidden);
        }
        hidden.value = Array.from(selected).join(",");
      });

      grid.appendChild(seat);
    }
  }
});
// optional: enhance payment button with small animation
document.addEventListener('DOMContentLoaded', () => {
  const payForm = document.querySelector('form[action^="/payment"]');
  if (payForm) {
    payForm.addEventListener('submit', (e) => {
      const btn = payForm.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Processing…";
      }
    });
  }
});
// Show footer only when user scrolls to bottom
document.addEventListener("scroll", () => {
  const footer = document.querySelector(".site-footer");
  if (!footer) return;
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 10) {
    footer.style.display = "block";
    footer.style.opacity = 1;
  } else {
    footer.style.display = "none";
  }
});

// Dynamic Pricing Functionality
class DynamicPricing {
  constructor() {
    this.updateInterval = 30000; // Update every 30 seconds
    this.isActive = false;
    this.init();
  }

  init() {
    // Only activate on search results page
    if (window.location.pathname === '/search') {
      this.startRealTimeUpdates();
    }
  }

  async updateFlightPrices() {
    try {
      const response = await fetch('/api/flights/prices');
      const data = await response.json();
      
      if (data.flights) {
        this.updatePriceDisplay(data.flights);
      }
    } catch (error) {
      console.log('Price update failed:', error);
    }
  }

  updatePriceDisplay(flights) {
    flights.forEach(flight => {
      const flightCard = document.querySelector(`[data-flight-id="${flight.flight_id}"]`);
      if (!flightCard) return;

      const priceSection = flightCard.querySelector('.price-section');
      if (!priceSection) return;

      const currentPriceEl = priceSection.querySelector('.current-price');
      const trendBadgeEl = priceSection.querySelector('.trend-badge');
      const occupancyInfoEl = priceSection.querySelector('.occupancy-info');

      // Update current price
      if (currentPriceEl) {
        const oldPrice = parseInt(currentPriceEl.textContent.replace(/[₹,]/g, ''));
        const newPrice = flight.dynamic_price;

        if (oldPrice !== newPrice) {
          currentPriceEl.textContent = `₹${newPrice.toLocaleString()}`;
          currentPriceEl.classList.add('price-updated');
          
          setTimeout(() => {
            currentPriceEl.classList.remove('price-updated');
          }, 1000);
        }
      }

      // Update trend badge
      if (trendBadgeEl) {
        const trendIcons = {
          'high': '🔥 High Demand',
          'moderate': '📈 Rising', 
          'low': '💰 Great Deal',
          'stable': '📊 Stable'
        };
        
        trendBadgeEl.textContent = trendIcons[flight.price_trend] || '📊 Stable';
        trendBadgeEl.className = `trend-badge trend-${flight.price_trend}`;
      }

      // Update occupancy info
      if (occupancyInfoEl) {
        occupancyInfoEl.innerHTML = `${Math.round(flight.occupancy_rate * 100)}% booked`;
      }
      
      // Add detailed pricing tooltip on hover
      this.addPricingTooltip(flightCard, flight);
    });
  }

  addPricingTooltip(flightCard, flight) {
    // Remove existing tooltip if any
    const existingTooltip = flightCard.querySelector('.pricing-tooltip');
    if (existingTooltip) {
      existingTooltip.remove();
    }

    const tooltip = document.createElement('div');
    tooltip.className = 'pricing-tooltip';
    
    const changePercent = ((flight.dynamic_price - flight.base_price) / flight.base_price * 100).toFixed(1);
    const changeColor = changePercent > 0 ? '#ef4444' : '#10b981';
    const changeSymbol = changePercent > 0 ? '+' : '';
    
    tooltip.innerHTML = `
      <div class="tooltip-header">Dynamic Pricing Analysis</div>
      <div class="tooltip-row">
        <span>Base Price:</span>
        <span>₹${flight.base_price.toLocaleString()}</span>
      </div>
      <div class="tooltip-row">
        <span>Current Price:</span>
        <span>₹${flight.dynamic_price.toLocaleString()}</span>
      </div>
      <div class="tooltip-row highlight">
        <span>Price Change:</span>
        <span style="color: ${changeColor}">${changeSymbol}${changePercent}%</span>
      </div>
      <div class="tooltip-row">
        <span>Occupancy:</span>
        <span>${Math.round(flight.occupancy_rate * 100)}% filled</span>
      </div>
      <div class="tooltip-footer">
        <small>Prices update every 30 seconds based on demand</small>
      </div>
    `;

    tooltip.style.cssText = `
      position: absolute;
      top: -10px;
      right: 100%;
      margin-right: 10px;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid rgba(34, 211, 238, 0.3);
      border-radius: 8px;
      padding: 12px;
      width: 250px;
      font-size: 12px;
      color: #e5e7eb;
      backdrop-filter: blur(10px);
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      z-index: 1000;
      opacity: 0;
      transform: translateX(10px);
      transition: all 0.2s ease;
      pointer-events: none;
    `;

    // Add CSS for tooltip elements
    const style = tooltip.style;
    const tooltipCSS = `
      .pricing-tooltip .tooltip-header {
        font-weight: 600;
        margin-bottom: 8px;
        color: #22d3ee;
        border-bottom: 1px solid rgba(34, 211, 238, 0.2);
        padding-bottom: 4px;
      }
      .pricing-tooltip .tooltip-row {
        display: flex;
        justify-content: space-between;
        margin: 4px 0;
      }
      .pricing-tooltip .tooltip-row.highlight {
        font-weight: 600;
        margin: 8px 0;
      }
      .pricing-tooltip .tooltip-footer {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(255,255,255,0.1);
        text-align: center;
        opacity: 0.8;
      }
    `;

    if (!document.getElementById('pricing-tooltip-styles')) {
      const styleSheet = document.createElement('style');
      styleSheet.id = 'pricing-tooltip-styles';
      styleSheet.textContent = tooltipCSS;
      document.head.appendChild(styleSheet);
    }

    flightCard.style.position = 'relative';
    flightCard.appendChild(tooltip);

    // Show/hide tooltip on hover
    flightCard.addEventListener('mouseenter', () => {
      tooltip.style.opacity = '1';
      tooltip.style.transform = 'translateX(0)';
    });

    flightCard.addEventListener('mouseleave', () => {
      tooltip.style.opacity = '0';
      tooltip.style.transform = 'translateX(10px)';
    });
  }

  startRealTimeUpdates() {
    if (this.isActive) return;
    
    this.isActive = true;
    this.updateFlightPrices(); // Initial update
    
    this.intervalId = setInterval(() => {
      this.updateFlightPrices();
    }, this.updateInterval);

    // Add visual indicator for real-time updates
    this.addUpdateIndicator();
  }

  stopRealTimeUpdates() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isActive = false;
  }

  addUpdateIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'price-update-indicator';
    indicator.innerHTML = '🔄 Prices updating every 30 seconds';
    indicator.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      background: rgba(34, 211, 238, 0.1);
      color: #22d3ee;
      padding: 8px 12px;
      border-radius: 20px;
      font-size: 12px;
      border: 1px solid rgba(34, 211, 238, 0.3);
      backdrop-filter: blur(10px);
      z-index: 100;
      animation: fadeInOut 3s ease-in-out infinite;
    `;
    
    // Add to page
    document.body.appendChild(indicator);
    
    // Add CSS animation
    if (!document.getElementById('dynamic-pricing-styles')) {
      const style = document.createElement('style');
      style.id = 'dynamic-pricing-styles';
      style.textContent = `
        @keyframes fadeInOut {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
      `;
      document.head.appendChild(style);
    }
  }
}

// Initialize dynamic pricing when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Add flight-id data attributes to cards for easy identification
  const flightCards = document.querySelectorAll('.card');
  flightCards.forEach(card => {
    const viewButton = card.querySelector('a[href*="/flight/"]');
    if (viewButton) {
      const flightId = viewButton.href.split('/flight/')[1];
      card.setAttribute('data-flight-id', flightId);
    }
  });

  // Initialize dynamic pricing
  window.dynamicPricing = new DynamicPricing();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.dynamicPricing) {
    window.dynamicPricing.stopRealTimeUpdates();
  }
});

// Admin Pricing Dashboard
class AdminPricingDashboard {
  constructor() {
    this.isUpdating = false;
    this.updateInterval = null;
    this.init();
  }

  init() {
    // Only initialize on admin page
    if (window.location.pathname === '/admin') {
      this.setupEventListeners();
      this.loadPricingData();
    }
  }

  setupEventListeners() {
    const refreshBtn = document.getElementById('refreshPricing');
    const toggleBtn = document.getElementById('togglePricingUpdates');

    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        this.loadPricingData();
      });
    }

    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        this.toggleLiveUpdates();
      });
    }
  }

  async loadPricingData() {
    try {
      const content = document.getElementById('pricingContent');
      if (!content) return;

      // Show loading state
      content.innerHTML = `
        <div class="loading-state">
          <div class="spinner"></div>
          <p>Loading dynamic pricing data...</p>
        </div>
      `;

      const response = await fetch('/api/pricing/analysis');
      const data = await response.json();

      this.renderPricingDashboard(data);
    } catch (error) {
      console.error('Error loading pricing data:', error);
      document.getElementById('pricingContent').innerHTML = `
        <div class="loading-state">
          <p style="color: #ef4444;">Error loading pricing data. Please try again.</p>
        </div>
      `;
    }
  }

  renderPricingDashboard(data) {
    const content = document.getElementById('pricingContent');
    const { flights, market_summary } = data;

    const marketStatus = market_summary.market_status === 'high_demand' ? 
      '🔥 High Demand Market' : '📊 Stable Market';

    const html = `
      <div class="market-summary">
        <h4>${marketStatus}</h4>
        <div class="market-stats">
          <div class="market-stat">
            <div class="market-stat-value">${market_summary.total_flights}</div>
            <div class="market-stat-label">Total Flights</div>
          </div>
          <div class="market-stat">
            <div class="market-stat-value">${market_summary.average_price_change}</div>
            <div class="market-stat-label">Avg Price Change</div>
          </div>
          <div class="market-stat">
            <div class="market-stat-value">${market_summary.trend_distribution.high}</div>
            <div class="market-stat-label">High Demand</div>
          </div>
          <div class="market-stat">
            <div class="market-stat-value">${market_summary.trend_distribution.low}</div>
            <div class="market-stat-label">Great Deals</div>
          </div>
        </div>
      </div>

      <div class="pricing-grid">
        ${flights.map(flight => this.renderFlightCard(flight)).join('')}
      </div>

      <div class="update-indicator ${this.isUpdating ? 'active' : ''}">
        ${this.isUpdating ? '<div class="pulse-dot"></div>' : ''}
        Last updated: ${new Date(data.timestamp).toLocaleTimeString()}
      </div>
    `;

    content.innerHTML = html;
  }

  renderFlightCard(flight) {
    const trendColors = {
      'high': 'price-change-positive',
      'moderate': 'price-change-positive', 
      'stable': 'price-change-neutral',
      'low': 'price-change-negative'
    };

    const trendIcons = {
      'high': '🔥',
      'moderate': '📈',
      'stable': '📊',
      'low': '💰'
    };

    const changeClass = trendColors[flight.trend] || 'price-change-neutral';
    const changeSymbol = flight.price_change_percent > 0 ? '+' : '';

    return `
      <div class="pricing-card">
        <div class="flight-header">
          <div>
            <div class="flight-id">${flight.flight_id}</div>
            <div class="route">${flight.route}</div>
          </div>
          <div class="trend-badge trend-${flight.trend}">
            ${trendIcons[flight.trend]} ${flight.trend.toUpperCase()}
          </div>
        </div>

        <div class="pricing-metrics">
          <div class="metric">
            <div class="metric-value">₹${flight.base_price.toLocaleString()}</div>
            <div class="metric-label">Base Price</div>
          </div>
          <div class="metric">
            <div class="metric-value">₹${flight.dynamic_price.toLocaleString()}</div>
            <div class="metric-label">Current Price</div>
          </div>
          <div class="metric">
            <div class="metric-value ${changeClass}">
              ${changeSymbol}${flight.price_change_percent}%
            </div>
            <div class="metric-label">Price Change</div>
          </div>
          <div class="metric">
            <div class="metric-value">${flight.factors.occupancy}</div>
            <div class="metric-label">Occupancy</div>
          </div>
        </div>

        <div style="margin-top: 12px; font-size: 12px; color: var(--muted);">
          <div>⏰ ${flight.factors.timing}</div>
          <div>🕐 Peak Hours: ${flight.factors.peak_hours ? 'Yes' : 'No'}</div>
          <div>📊 Factors: Occupancy ${flight.factors.multipliers.occupancy_factor}x, 
               Time ${flight.factors.multipliers.time_factor}x, 
               Peak ${flight.factors.multipliers.peak_hour_factor}x</div>
        </div>
      </div>
    `;
  }

  toggleLiveUpdates() {
    const toggleBtn = document.getElementById('togglePricingUpdates');
    
    if (this.isUpdating) {
      this.stopLiveUpdates();
      toggleBtn.textContent = '📊 Enable Live Updates';
      toggleBtn.className = 'btn primary';
    } else {
      this.startLiveUpdates();
      toggleBtn.textContent = '⏸️ Disable Live Updates';
      toggleBtn.className = 'btn warn';
    }
  }

  startLiveUpdates() {
    this.isUpdating = true;
    this.updateInterval = setInterval(() => {
      this.loadPricingData();
    }, 15000); // Update every 15 seconds for admin

    // Update indicator
    const indicator = document.querySelector('.update-indicator');
    if (indicator) {
      indicator.classList.add('active');
    }
  }

  stopLiveUpdates() {
    this.isUpdating = false;
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }

    // Update indicator
    const indicator = document.querySelector('.update-indicator');
    if (indicator) {
      indicator.classList.remove('active');
    }
  }
}

// Initialize admin pricing dashboard
document.addEventListener('DOMContentLoaded', () => {
  window.adminPricingDashboard = new AdminPricingDashboard();
});

// Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = document.querySelector('.theme-icon');
  const body = document.body;
  
  if (!themeToggle || !themeIcon) return;
  
  // Initialize theme from localStorage or default to dark
  const savedTheme = localStorage.getItem('theme') || 'dark';
  body.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);
  
  // Theme toggle click handler
  themeToggle.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Update body theme
    body.setAttribute('data-theme', newTheme);
    
    // Save to localStorage
    localStorage.setItem('theme', newTheme);
    
    // Update icon
    updateThemeIcon(newTheme);
    
    // Add animation effect
    themeToggle.style.transform = 'scale(0.9)';
    setTimeout(() => {
      themeToggle.style.transform = '';
    }, 150);
  });
  
  function updateThemeIcon(theme) {
    if (theme === 'dark') {
      themeIcon.textContent = '🌙';
      themeToggle.setAttribute('aria-label', 'Switch to light mode');
    } else {
      themeIcon.textContent = '☀️';
      themeToggle.setAttribute('aria-label', 'Switch to dark mode');
    }
  }
});
