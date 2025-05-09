// API Client for Real Estate Booking System

class ApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
  }

  // Helper method for making API requests
  async request(endpoint, method = "GET", data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
    };

    if (data && (method === "POST" || method === "PUT" || method === "PATCH")) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(responseData.error || "Something went wrong");
      }

      return responseData;
    } catch (error) {
      console.error("API Request Error:", error);
      throw error;
    }
  }

  // User API Methods
  async createUser(userData) {
    return this.request("/api/users", "POST", userData);
  }

  async addCreditCard(userId, cardData) {
    return this.request(`/api/users/${userId}/credit-cards`, "POST", cardData);
  }

  // Property API Methods
  async createNeighborhood(neighborhoodData) {
    return this.request("/api/neighborhoods", "POST", neighborhoodData);
  }

  async createProperty(propertyData) {
    return this.request("/api/properties", "POST", propertyData);
  }

  // Booking API Methods
  async createBooking(bookingData) {
    return this.request("/api/bookings", "POST", bookingData);
  }
}

// Initialize the API client
const api = new ApiClient();

// Example usage:
// async function createNewUser() {
//     try {
//         const userData = {
//             name: 'John Doe',
//             email: 'john@example.com',
//             password: 'password123',
//             is_agent: false,
//             address: {
//                 street: '123 Main St',
//                 city: 'New York',
//                 state: 'NY',
//                 zip_code: '10001',
//                 country: 'United States'
//             },
//             renter_details: {
//                 desired_move_in_date: '2025-06-01',
//                 preferred_location: 'Manhattan',
//                 budget: 2500
//             }
//         };
//         const result = await api.createUser(userData);
//         console.log('User created:', result);
//     } catch (error) {
//         handleApiError(error);
//     }
// }
