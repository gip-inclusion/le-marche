document.addEventListener('alpine:init', function() {
    Alpine.data('DropdownMenu', () => ({
        isOpen: false,

        init() {

           // Close menu when clicking on menu links
            this.$nextTick(() => {  // Avoid transitions errors on menu close
                const menuLinks = document.querySelectorAll('#menu-profile a');
                menuLinks.forEach(link => {
                    link.addEventListener('click', () => {
                        this.closeMenu();
                    });
                });
            });
        },
        
        openMenu() {
            this.isOpen = true;
        },

        closeMenu() {
            this.isOpen = false;
        },
    }));
});
