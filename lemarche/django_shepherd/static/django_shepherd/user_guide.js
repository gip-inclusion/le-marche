import Shepherd from "shepherd_map";

const tour = new Shepherd.Tour({
    useModalOverlay: true,
    confirmCancel: true,
    confirmCancelMessage: "Êtes-vous sûr d'annuler ce guide des fonctionnalités ? Il ne vous sera plus proposé",
    defaultStepOptions: {
        classes: 'shepherd-theme-arrows',
        scrollTo: {
            behavior: 'smooth',
            block: 'center'
        },
    }
});

// Once cancelled or completed
tour.on("cancel", onTourEnd);
tour.on("complete", onTourEnd);

/*Called on ending tour events. Call an url to add the user to already viewed guides*/
function onTourEnd() {
    // "this" refers to a "tour" instance
    fetch(this.displayGuideViewedUrl)
}

function startGuide(displayGuidePayload, displayGuideViewedUrl) {
    tour.displayGuideViewedUrl = displayGuideViewedUrl
    tour.steps = []; // Clear previous steps
    displayGuidePayload.steps.forEach((step, index) => {
        const isFirstStep = index === 0;
        const isLastStep = index === displayGuidePayload.steps.length - 1;
        tour.addStep({
            title: step.title,
            text: step.text,
            attachTo: {
                element: step.element,
                on: step.position
            },
            buttons: [
                !isLastStep && {
                    text: 'Ignorer',
                    action: tour.cancel,
                    classes: 'btn btn-secondary'
                },
                !isFirstStep && {
                    text: 'Précédent',
                    action: tour.back,
                    classes: 'btn btn-primary'
                },
                {
                    text: isLastStep ? 'Finir' : 'Suivant',
                    action: tour.next,
                    classes: 'btn ' + (isLastStep ? 'btn-success' : 'btn-primary')
                }
            ].filter(Boolean)
        });
    });
    tour.start();
}

export {startGuide as default}
