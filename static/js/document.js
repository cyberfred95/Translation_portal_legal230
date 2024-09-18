$(document).ready(function() {
    let currentStep = 0;
    const totalSteps = 4;

    function updateProgress(step) {
        let percentage;
        switch(step) {
            case 0:
                percentage = 0;
                break;
            case 1:
                percentage = 26;
                break;
            case 2:
                percentage = 52;
                break;
            case 3:
                percentage = 76;
                break;
            case 4:
                percentage = 100;
                break;
            default:
                percentage = 1;
        }

        console.log(percentage);
        $("#progress-bar").css("width", percentage + "%");

        $(".progress-point").parent().find("svg").removeClass("text-green-700").addClass("text-green-400");

        for (let i = 0; i <= step; i++) {
            $(`#point-${i + 1}`).find("svg").removeClass("text-green-400").addClass("text-green-700");
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
    $('.tab-content').hide();
    $('#text-translate-content').show();
    $('#text-translate').addClass('bg-gray-800 text-white border-gray-800');

    $('#text-translate').click(function() {
        $('.tab-content').hide();
        $('#text-translate-content').show();
        $('button').removeClass('bg-gray-800 text-white border-gray-800');
        $(this).addClass('bg-gray-800 text-white border-gray-800');
    });

    $('#document-translate').click(function() {
        $('.tab-content').hide();
        $('#document-translate-content').show();
        $('button').removeClass('bg-gray-800 text-white border-gray-800');
        $(this).addClass('bg-gray-800 text-white border-gray-800');
    });

    $('#writing').click(function() {
        $('.tab-content').hide();
        $('#writing-content').show();
        $('button').removeClass('bg-gray-800 text-white border-gray-800');
        $(this).addClass('bg-gray-800 text-white border-gray-800');
    });

    $('.js-example-basic-single').select2();
});
