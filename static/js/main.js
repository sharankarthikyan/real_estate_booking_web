// Global JavaScript for the application

// Enable Bootstrap tooltips and popovers
document.addEventListener("DOMContentLoaded", function () {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
});

// Format currency inputs
function formatCurrency(input) {
  // Remove non-numeric characters
  let value = input.value.replace(/[^0-9.]/g, "");

  // Ensure only one decimal point
  let parts = value.split(".");
  if (parts.length > 2) {
    value = parts[0] + "." + parts.slice(1).join("");
  }

  // Format with 2 decimal places
  if (value && !isNaN(parseFloat(value))) {
    input.value = parseFloat(value).toFixed(2);
  } else {
    input.value = "";
  }
}

// Format date strings to locale format
function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString();
}

// Handle API errors
function handleApiError(error) {
  console.error("API Error:", error);
  let errorMessage = "An error occurred. Please try again.";

  if (error.response && error.response.data && error.response.data.error) {
    errorMessage = error.response.data.error;
  }

  alert(errorMessage);
}
