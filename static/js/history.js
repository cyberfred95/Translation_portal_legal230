document.addEventListener('DOMContentLoaded', function () {
    let errorPopup = '#error_popup';
    var downloadButtons = document.querySelectorAll('.download-file');

    function errorHandler() {
        $('<a href=' + errorPopup + '></a>').fancybox({
            arrows: false,
            padding: 0,
            overlay: {
                locked: false
            },
            afterClose: function () {
                location.reload()
            }
        }).click()
    }

    downloadButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var url = this.getAttribute('data-url');
            if (url) {
                var a = document.createElement('A');
                a.href = url;
                a.download = url.substr(url.lastIndexOf('/') + 1);
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
        });
    });

    var statusSpans = document.querySelectorAll('.status');
    statusSpans.forEach(function (span) {
        var status = span.getAttribute('data-project-status');
        switch (status) {
            case 'Being translated':
                span.classList.add('being-translated');
                span.innerHTML = current_language === 'fr' ? 'En cours de traduction' : 'Being translated';
                break;
            case 'Translated':
                span.classList.add('translated');
                span.innerHTML = current_language === 'fr' ? 'Traduit' : 'Translated';
                break;
            case 'Sent to post-editing, not accepted yet':
                span.classList.add('sent-to-post-editing-not-accepted');
                span.innerHTML = current_language === 'fr' ? 'Demande de post-édition envoyée' : 'Request for post-editing sent';
                break
            case 'Sent to post-editing, accepted':
                span.classList.add('sent-to-post-editing-accepted');
                span.innerHTML = current_language === 'fr' ? 'Demande de post-édition acceptée' : 'Request for post-editing accepted';
                break
            case 'Post-edited file uploaded':
                span.classList.add('post-edited');
                span.innerHTML = current_language === 'fr' ? ' Document post-édité' : 'Post-edited file uploaded';
                break
            case 'Error':
                span.classList.add('error');
                span.innerHTML = current_language === 'fr' ? 'Oups ! Erreur' : 'Error';
                break;
        }
    });

    function formatProjectDate(isoDate) {
        var date = new Date(isoDate);
        var day = ('0' + date.getDate()).slice(-2);
        var month = ('0' + (date.getMonth() + 1)).slice(-2);
        var year = date.getFullYear().toString().slice(-2);
        return day + '/' + month + '/' + year;
    }

    var dateElements = document.querySelectorAll('.date');

    dateElements.forEach(function (el) {
        var date = el.textContent.trim();
        el.textContent = formatProjectDate(date);
    });

    const selectBoxes = document.querySelectorAll(".select-box");

    selectBoxes.forEach(function (box) {
        const optionsContainer = box.querySelector(".options-container");
        const options = optionsContainer.querySelectorAll(".option");

        options.forEach(function (option) {
            option.addEventListener("click", function () {
                optionsContainer.classList.remove("active");
            });
        });
    });

    document.addEventListener('click', function (e) {
        selectBoxes.forEach(function (box) {
            const optionsContainer = box.querySelector(".options-container");
            if (!box.contains(e.target)) {
                optionsContainer.classList.remove("active");
            }
        });
    });

    document.querySelectorAll('.delete-button').forEach(function (button) {
        button.addEventListener('click', function () {
            var projectId = this.getAttribute('data-project-id');
            document.querySelector('.approve-delete').setAttribute('data-project-id', projectId);
            var modal = document.querySelector('.delete-modal');
            modal.style.display = 'block';
        });
    });

    document.querySelectorAll('.cancel-delete').forEach(function (button) {
        button.addEventListener('click', closeModal);
    });

    document.querySelectorAll('.approve-delete').forEach(function (button) {
        button.addEventListener('click', function () {
            var projectId = this.getAttribute('data-project-id');
            sendDeleteRequest(projectId);
        });
    });

    document.querySelectorAll('.close').forEach(function (button) {
        button.addEventListener('click', closeModal);
    });

    function closeModal() {
        var modal = document.querySelector('.delete-modal');
        modal.style.display = 'none';
    }

    function sendDeleteRequest(projectId) {
        var formData = new FormData();
        formData.append('project_id', projectId);

        fetch('/project', {
            method: 'DELETE',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
            .then(response => {
                if (response.ok) {
                    location.reload();
                }
            })
            .catch(error => {
                errorHandler()
            });
    }
});
