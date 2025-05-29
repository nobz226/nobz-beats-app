document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.querySelector(".menu-toggle");
  const dropdown = document.getElementById("menuDropdown");
  let isMenuOpen = false;

  // Toggle menu function
  function toggleMenu(event) {
    event.stopPropagation();
    isMenuOpen = !isMenuOpen;
    dropdown.classList.toggle("show");

    // Animate hamburger icon
    const spans = menuToggle.getElementsByTagName("span");
    if (isMenuOpen) {
      spans[0].style.transform = "rotate(45deg) translate(5px, 5px)";
      spans[1].style.opacity = "0";
      spans[2].style.transform = "rotate(-45deg) translate(5px, -5px)";
    } else {
      spans[0].style.transform = "none";
      spans[1].style.opacity = "1";
      spans[2].style.transform = "none";
    }
  }

  // Close menu function
  function closeMenu() {
    if (isMenuOpen) {
      isMenuOpen = false;
      dropdown.classList.remove("show");

      // Reset hamburger icon
      const spans = menuToggle.getElementsByTagName("span");
      spans[0].style.transform = "none";
      spans[1].style.opacity = "1";
      spans[2].style.transform = "none";
    }
  }

  // Event listeners
  menuToggle.addEventListener("click", toggleMenu);

  // Close menu when clicking outside
  document.addEventListener("click", function (event) {
    if (
      isMenuOpen &&
      !dropdown.contains(event.target) &&
      event.target !== menuToggle
    ) {
      closeMenu();
    }
  });

  // Close menu when pressing Escape key
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeMenu();
    }
  });

  // Prevent clicks inside dropdown from closing it
  dropdown.addEventListener("click", function (event) {
    event.stopPropagation();
  });

  // Auto-dismiss messages (keeping existing functionality)
  const messages = document.querySelector(".messages");
  if (messages) {
    setTimeout(function () {
      messages.style.opacity = "0";
      setTimeout(function () {
        messages.style.display = "none";
      }, 300);
    }, 5000);
  }
});
