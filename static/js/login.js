// Logic for password visibility toggle on the login page
document.addEventListener('DOMContentLoaded', function() {
	var passwordInput = document.getElementById('password');
	var toggleBtn = document.getElementById('toggle-password');
	var eyeOpen = document.getElementById('eye-open');
	var eyeClosed = document.getElementById('eye-closed');
	if (toggleBtn && passwordInput && eyeOpen && eyeClosed) {
		toggleBtn.addEventListener('click', function() {
			if (passwordInput.type === 'password') {
				passwordInput.type = 'text';
				eyeOpen.style.display = 'none';
				eyeClosed.style.display = 'inline';
			} else {
				passwordInput.type = 'password';
				eyeOpen.style.display = 'inline';
				eyeClosed.style.display = 'none';
			}
		});
	}
});


