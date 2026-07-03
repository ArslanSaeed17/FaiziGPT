const mobileMenu = document.getElementById("mobileMenu");
const mobileNav = document.getElementById("mobileNav");

if (mobileMenu && mobileNav) {
  mobileMenu.addEventListener("click", () => {
    mobileNav.classList.toggle("open");
  });
}
