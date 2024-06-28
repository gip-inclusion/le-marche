class UserGuide {
    constructor() {
        this.tour = new Shepherd.Tour({
            useModalOverlay: true,
            defaultStepOptions: {
                classes: 'shepherd-theme-arrows',
                scrollTo: true
            }
        });
    }

    init() {
        document.addEventListener('startUserGuide', (event) => {
            const guideName = event.detail.guideName;
            this.startGuide(guideName);
        });

        // Listen to htmx events
        document.body.addEventListener('htmx:afterSwap', (event) => {
            if (event.detail.target.id === 'guideContainer') {
                const guideName = event.detail.target.getAttribute('data-guide-name');
                this.startGuide(guideName);
            }
        });
    }

    startGuide(guideName) {
        fetch(`http://localhost:8000/django_shepherd/get_guide/${guideName}/`)
            .then(response => response.json())
            .then(data => {
                this.tour.steps = []; // Clear previous steps
                data.steps.forEach(step => {
                    this.tour.addStep({
                        title: step.title,
                        text: step.text,
                        attachTo: {
                            element: step.element,
                            on: step.position
                        },
                        buttons: [
                            {
                                text: 'Next',
                                action: this.tour.next
                            }
                        ]
                    });
                });
                this.tour.start();
            });
    }
}