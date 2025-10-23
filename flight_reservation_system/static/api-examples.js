/**
 * Flight Reservation System REST API Integration Examples
 * Demonstrates how to use the comprehensive REST API endpoints
 */

class FlightReservationAPI {
    constructor(baseURL = 'http://127.0.0.1:5000') {
        this.baseURL = baseURL;
    }

    // Helper method for making API calls
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // ==================== FLIGHT APIs ====================
    
    /**
     * Get all flights with optional filtering
     */
    async getFlights(filters = {}) {
        const params = new URLSearchParams();
        
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.append(key, filters[key]);
            }
        });
        
        const queryString = params.toString();
        const endpoint = `/api/flights${queryString ? '?' + queryString : ''}`;
        
        return await this.makeRequest(endpoint);
    }

    /**
     * Get specific flight by ID
     */
    async getFlight(flightId) {
        return await this.makeRequest(`/api/flights/${flightId}`);
    }

    /**
     * Get seat availability for specific flight
     */
    async getFlightSeats(flightId) {
        return await this.makeRequest(`/api/flights/${flightId}/seats`);
    }

    /**
     * Search flights with comprehensive filtering
     */
    async searchFlights(searchParams) {
        return await this.getFlights(searchParams);
    }

    /**
     * Get flight dynamic pricing information
     */
    async getFlightPrice(flightId) {
        return await this.makeRequest(`/api/flight/${flightId}/price`);
    }

    /**
     * Get dynamic prices for all flights
     */
    async getAllFlightPrices() {
        return await this.makeRequest('/api/flights/prices');
    }

    // ==================== BOOKING APIs ====================
    
    /**
     * Get all bookings with optional filtering
     */
    async getBookings(filters = {}) {
        const params = new URLSearchParams();
        
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.append(key, filters[key]);
            }
        });
        
        const queryString = params.toString();
        const endpoint = `/api/bookings${queryString ? '?' + queryString : ''}`;
        
        return await this.makeRequest(endpoint);
    }

    /**
     * Get specific booking by PNR
     */
    async getBooking(pnr) {
        return await this.makeRequest(`/api/bookings/${pnr}`);
    }

    /**
     * Create new booking
     */
    async createBooking(bookingData) {
        return await this.makeRequest('/api/bookings', {
            method: 'POST',
            body: JSON.stringify(bookingData)
        });
    }

    /**
     * Update booking
     */
    async updateBooking(pnr, updateData) {
        return await this.makeRequest(`/api/bookings/${pnr}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    /**
     * Cancel booking
     */
    async cancelBooking(pnr) {
        return await this.makeRequest(`/api/bookings/${pnr}`, {
            method: 'DELETE'
        });
    }

    // ==================== UTILITY APIs ====================

    /**
     * Get available airports/cities
     */
    async getAirports() {
        return await this.makeRequest('/api/airports');
    }

    /**
     * Get available airlines with statistics
     */
    async getAirlines() {
        return await this.makeRequest('/api/airlines');
    }

    /**
     * Get system statistics
     */
    async getStats() {
        return await this.makeRequest('/api/stats');
    }

    /**
     * Get API documentation
     */
    async getApiDoc() {
        return await this.makeRequest('/api');
    }
}

// ==================== USAGE EXAMPLES ====================

// Initialize API client
const api = new FlightReservationAPI();

// Example: Search flights from Delhi to Mumbai on specific date
async function searchDelToMumbai() {
    try {
        const result = await api.searchFlights({
            origin: 'DEL',
            destination: 'BOM',
            date: '2025-01-15',
            dynamic_pricing: 'true',
            sort_by: 'price',
            order: 'asc'
        });
        
        console.log('Search Results:', result);
        console.log(`Found ${result.meta.total_results} flights`);
        
        result.flights.forEach(flight => {
            console.log(`${flight.airline}: ${flight.origin} → ${flight.destination}`);
            console.log(`Price: ₹${flight.dynamic_price} (Base: ₹${flight.price})`);
            console.log(`Trend: ${flight.price_trend}, Occupancy: ${flight.occupancy_rate * 100}%`);
            console.log('---');
        });
        
    } catch (error) {
        console.error('Search failed:', error.message);
    }
}

// Example: Get seat availability for specific flight
async function checkSeatAvailability(flightId) {
    try {
        const result = await api.getFlightSeats(flightId);
        
        console.log('Seat Availability:', result.seats);
        console.log(`Available seats: ${result.seats.available}/${result.seats.total}`);
        console.log(`Occupancy: ${result.seats.occupancy_rate}%`);
        
        const availableSeats = result.seats.seat_map.filter(seat => seat.available);
        console.log('Available seats:', availableSeats.map(seat => seat.seat));
        
    } catch (error) {
        console.error('Seat check failed:', error.message);
    }
}

// Example: Create a new booking
async function createNewBooking() {
    try {
        const bookingData = {
            flight_id: 'AI101',
            fullname: 'John Doe',
            email: 'john.doe@example.com',
            phone: '+91-9876543210',
            seats: ['1A', '1B'],
            status: 'PENDING'
        };
        
        const result = await api.createBooking(bookingData);
        
        console.log('Booking Created:', result);
        console.log(`PNR: ${result.booking.pnr}`);
        console.log(`Amount: ₹${result.booking.amount}`);
        
    } catch (error) {
        console.error('Booking creation failed:', error.message);
    }
}

// Example: Get bookings by status
async function getConfirmedBookings() {
    try {
        const result = await api.getBookings({
            status: 'CONFIRMED',
            sort_by: 'created_at',
            order: 'desc'
        });
        
        console.log('Confirmed Bookings:', result);
        console.log(`Total confirmed bookings: ${result.meta.total_results}`);
        
        result.bookings.forEach(booking => {
            console.log(`PNR: ${booking.pnr} - ${booking.fullname}`);
            console.log(`Flight: ${booking.flight_details?.airline} ${booking.flight_id}`);
            console.log(`Route: ${booking.flight_details?.origin} → ${booking.flight_details?.destination}`);
            console.log(`Amount: ₹${booking.amount}`);
            console.log('---');
        });
        
    } catch (error) {
        console.error('Failed to get bookings:', error.message);
    }
}

// Example: Get system statistics
async function getSystemStats() {
    try {
        const result = await api.getStats();
        
        console.log('System Statistics:', result.stats);
        console.log(`Total Flights: ${result.stats.flights.total}`);
        console.log(`Total Bookings: ${result.stats.bookings.total}`);
        console.log(`Confirmed Bookings: ${result.stats.bookings.confirmed}`);
        console.log(`Total Revenue: ₹${result.stats.bookings.total_revenue}`);
        console.log(`Overall Occupancy: ${result.stats.flights.overall_occupancy_percent}%`);
        
    } catch (error) {
        console.error('Failed to get stats:', error.message);
    }
}

// Example: Real-time price monitoring
async function monitorPrices(flightIds) {
    try {
        console.log('Starting price monitoring...');
        
        for (const flightId of flightIds) {
            const result = await api.getFlightPrice(flightId);
            
            console.log(`Flight ${flightId}:`);
            console.log(`  Base Price: ₹${result.base_price}`);
            console.log(`  Dynamic Price: ₹${result.dynamic_price}`);
            console.log(`  Trend: ${result.price_trend}`);
            console.log(`  Occupancy: ${result.occupancy_rate}%`);
            console.log(`  Days until departure: ${result.days_until_departure}`);
            console.log('---');
        }
        
    } catch (error) {
        console.error('Price monitoring failed:', error.message);
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FlightReservationAPI;
}

// Example usage (uncomment to test)
// searchDelToMumbai();
// checkSeatAvailability('AI101');
// createNewBooking();
// getConfirmedBookings();
// getSystemStats();
// monitorPrices(['AI101', 'SG404', '6E123']);