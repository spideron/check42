document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    $.ajax({
        method: 'POST',
        url: check42.apiUrl + '/login',
        data: JSON.stringify({
            username: username,
            password: password
        }),
        contentType: 'application/json',
        crossDomain: true, // Enable CORS support
        success: (response) => {
            if (response.status === 'success') {
                // Store tokens
                localStorage.setItem('token', response.token);

                console.log('Login successful');
                console.log('Token:', response.token);

                // Redirect to main page
                window.location.href = '/checks/checks.html';            }
        },
        error: (jqXHR, textStatus, errorThrown) => {
            console.error('Response: ', jqXHR.responseText);
            document.getElementById('errorMessage').textContent = 'Login failed: ' + jqXHR.responseText;
            document.getElementById('errorMessage').style.display = 'block';
        }
    });
});
