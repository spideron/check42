class SettingsApp {
    constructor() {
        this.apiUrl = check42.apiUrl;
        this.sessionToken = localStorage.getItem('token');
        this.init();
    }

    init() {
        this.fetchSettings();
        document.querySelectorAll('.update-button').forEach(button => {
            button.addEventListener('click', (event) => this.updateSetting(event.target.dataset.field));
        });
    }

    fetchSettings() {
        $.ajax({
            method: 'GET',
            url: this.apiUrl + 'settings',
            contentType: 'application/json',
            crossDomain: true,
            headers: {
                'Authorization': this.sessionToken
            },
            success: (response) => {
                this.populateForm(response);
            },
            error: (jqXHR, textStatus, errorThrown) => {
                console.error('Failed to fetch settings:', jqXHR.responseText);
                alert('Failed to load settings: ' + (jqXHR.responseText || errorThrown));
            }
        });
    }

    populateForm(settings) {
        console.log(settings)
        const parsedSettings = JSON.parse(settings);
        console.log(parsedSettings)
        document.getElementById('password').placeholder = parsedSettings.password ? '********' : 'No password set';
        document.getElementById('sender').placeholder = parsedSettings.sender || 'No sender set';
        document.getElementById('subscriber').placeholder = parsedSettings.subscriber || 'No subscriber set';
    }

    updateSetting(field) {
        const value = document.getElementById(field).value;
        if (!value) {
            alert('Please enter a value before updating.');
            return;
        }

        const data = {};
        data[field] = value;

        $.ajax({
            method: 'PUT',
            url: this.apiUrl + '/settings',
            contentType: 'application/json',
            data: JSON.stringify(data),
            crossDomain: true,
            headers: {
                'Accept': 'application/json',
                'Authorization': this.sessionToken
            },
            success: (response) => {
                console.log(`${field} updated successfully:`, response);
                this.showSuccessBanner();
                document.getElementById(field).value = '';
                this.fetchSettings(); // Refresh the placeholders
            },
            error: (jqXHR, textStatus, errorThrown) => {
                console.error(`Failed to update ${field}:`, jqXHR.responseText);
                alert(`Failed to update ${field}: ` + (jqXHR.responseText || errorThrown));
            }
        });
    }

    showSuccessBanner() {
        const banner = document.getElementById('success-banner');
        banner.style.display = 'block';
        banner.style.opacity = '1';

        setTimeout(() => {
            banner.style.opacity = '0';
            setTimeout(() => {
                banner.style.display = 'none';
            }, 300);
        }, 3000);
    }
}

// Initialize the app when the page loads
$(document).ready(() => {
    new SettingsApp();
});
