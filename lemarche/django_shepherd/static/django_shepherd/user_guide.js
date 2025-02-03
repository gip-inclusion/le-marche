class UserGuide {
    constructor() {
        this.tour = new Shepherd.Tour({
            useModalOverlay: true,
            defaultStepOptions: {
                classes: 'shepherd-theme-arrows',
                scrollTo: {
                    behavior: 'smooth',
                    block: 'center'
                },
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
        fetch(`/django_shepherd/get_guide/${guideName}/`)
            .then(response => response.json())
            .then(data => {
                this.tour.steps = []; // Clear previous steps
                data.steps.forEach((step, index) => {
                    const isFirstStep = index === 0;
                    const isLastStep = index === data.steps.length - 1;
                    this.tour.addStep({
                        title: step.title,
                        text: step.text,
                        attachTo: {
                            element: step.element,
                            on: step.position
                        },
                        buttons: [
                            {
                                text: 'Ignorer',
                                action: this.tour.cancel,
                                classes: 'btn btn-secondary'
                            },
                            !isFirstStep && {
                                text: 'Précédent',
                                action: this.tour.back,
                                classes: 'btn btn-primary'
                            },
                            {
                                text: isLastStep ? 'Finir' : 'Suivant',
                                action: this.tour.next,
                                classes: 'btn ' + (isLastStep ? 'btn-success' : 'btn-primary')
                            }
                        ].filter(Boolean)
                    });
                });
                this.tour.start();
            });
    }
}
