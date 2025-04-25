class SettingsApp {
    constructor() {
        this.apiUrl = check42.apiUrl;
        this.sessionToken = localStorage.getItem('token');
        this.init();
        this.initTimeSelectors();
    }

    init() {
        this.fetchSettings();
        // Add frequency change event listener
        document.getElementById('save-frequency').addEventListener('click', () => {
            const frequency = document.getElementById('frequency-select').value;
            this.handleFrequencyChange(frequency);
        });
        // Existing button listeners
        document.querySelectorAll('.update-button').forEach(button => {
            button.addEventListener('click', (event) => this.updateSetting(event.target.dataset.field));
        });
    }

    initTimeSelectors() {
        const hourSelect = document.getElementById('hour-select');
        const minuteSelect = document.getElementById('minute-select');

        // Populate hours (00-23)
        for (let i = 0; i < 24; i++) {
            const hour = i.toString().padStart(2, '0');
            const option = new Option(hour, hour);
            hourSelect.appendChild(option);
        }

        // Populate minutes (00-59)
        for (let i = 0; i < 60; i++) {
            const minute = i.toString().padStart(2, '0');
            const option = new Option(minute, minute);
            minuteSelect.appendChild(option);
        }
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
        const parsedSettings = JSON.parse(settings);
        document.getElementById('password').placeholder = '********';
        document.getElementById('subscriber').placeholder = parsedSettings.subscriber || 'No subscriber set';
        // Set frequency and time if available
        if (parsedSettings.schedule) {
            document.getElementById('frequency-select').value = parsedSettings.schedule.frequency;
            document.getElementById('hour-select').value = parsedSettings.schedule.hour.toString().padStart(2, '0');
            document.getElementById('minute-select').value = parsedSettings.schedule.minute.toString().padStart(2, '0');
        }
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

    handleFrequencyChange(newFrequency) {
        const hour = document.getElementById('hour-select').value;
        const minute = document.getElementById('minute-select').value;

        $.ajax({
            method: 'PUT',
            url: this.apiUrl + '/schedule',
            contentType: 'application/json',
            data: JSON.stringify({
                frequency: newFrequency,
                hour: parseInt(hour),
                minute: parseInt(minute)
            }),
            crossDomain: true,
            headers: {
                'Accept': 'application/json',
                'Authorization': this.sessionToken
            },
            success: (response) => {
                console.log('Schedule update success:', response);
                this.showSuccessBanner();
            },
            error: (jqXHR, textStatus, errorThrown) => {
                if (!this.handleAjaxError(jqXHR)) {
                    console.error('Schedule update error:', errorThrown);
                    alert('Failed to update schedule: ' + (jqXHR.responseText || errorThrown));
                }
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
