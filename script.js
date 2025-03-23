document.addEventListener("DOMContentLoaded", function () {
    let links = document.querySelectorAll(".navbar ul li a");
    let currentPage = window.location.pathname.split("/").pop();

    links.forEach(link => {
        if (link.getAttribute("href") === currentPage) {
            link.style.fontWeight = "bold";
            link.style.textDecoration = "underline";
            link.style.color = "#28a745"; // Green highlight
        }
    });
});
