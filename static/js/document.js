$(document).ready(function() {
    let currentStep = 0;
    const totalSteps = 4;

    function updateProgress(step) {
        const percentage = (step / totalSteps) * 100;
        $("#progress-bar").css("width", percentage + "%");

        $(".progress-point").parent().removeClass("text-green-400").addClass("text-green-700");
        for (let i = 1; i <= step + 1; i++) {
            $(`#point-${i}`).removeClass("text-green-700").addClass("text-green-400");
        }
    }

    $("#next-step").click(function() {
        if (currentStep < totalSteps) {
            currentStep++;
            updateProgress(currentStep);
        }
    });

    $("#prev-step").click(function() {
        if (currentStep > 0) {
            currentStep--;
            updateProgress(currentStep);
        }
    });

    updateProgress(currentStep);
});
