document.addEventListener('alpine:init', function() {
    Alpine.data('DropdownMenu', () => ({
        isOpen: false,

        init() {
            this.checkMenuState(); 

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
            document.getElementById('menu-profile')?.classList.remove('dropdown-menu__menu--hidden');
            sessionStorage.setItem('menuOpen', 'true');
        },

        closeMenu() {
            this.isOpen = false;
            document.getElementById('menu-profile')?.classList.add('dropdown-menu__menu--hidden');
            sessionStorage.setItem('menuOpen', 'false');
        },

        checkMenuState() {
            this.isOpen = sessionStorage.getItem('menuOpen') === 'true';
            if (!this.isOpen) {
                document.getElementById('menu-profile')?.classList.add('dropdown-menu__menu--hidden');
            }
        }
    }));
});
