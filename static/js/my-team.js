document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.mail-user').forEach(button => {
        button.addEventListener('click', function() {
            const email = this.dataset.email;
            window.location.href = `mailto:${email}`;
        });
    });

    document.querySelectorAll('.edit-user').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.dataset.userId;
            console.log('Edit user:', userId);
            alert(gettext('Edit functionality will be implemented here'));
        });
    });

    document.querySelectorAll('.delete-user').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.dataset.userId;
            if (confirm(gettext('Are you sure you want to delete this user?'))) {
                console.log('Delete user:', userId);
                alert(gettext('Delete functionality will be implemented here'));
            }
        });
    });

    const addUserBtn = document.getElementById('add-user-btn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function() {
            console.log('Add user clicked');
            alert(gettext('Add user functionality will be implemented here'));
        });
    }
});



